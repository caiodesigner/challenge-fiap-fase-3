"""Grafo clínico com ramificações seguras e human-in-the-loop."""

from __future__ import annotations

import time
from typing import Any, Protocol, cast
from uuid import uuid4

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import ValidationError

from assistente_medico.audit import (
    AuditEvent,
    AuditMetadata,
    InMemoryAuditRecorder,
    mask_identifier,
)
from assistente_medico.audit.recorder import AuditRecorder
from assistente_medico.chains.assistant import DISCLAIMER
from assistente_medico.chains.schemas import AssistantRequest, AssistantResponse
from assistente_medico.graph.rules import Intent, classify_intent, flags_for_intent
from assistente_medico.graph.state import HumanReview, WorkflowState
from assistente_medico.safety import SafetyPolicy


class AssistantInvoker(Protocol):
    def invoke(
        self, request: AssistantRequest | dict[str, Any]
    ) -> AssistantResponse: ...


class ClinicalWorkflow:
    """Fachada para iniciar, inspecionar e retomar uma execução persistida."""

    def __init__(
        self,
        assistant: AssistantInvoker,
        *,
        checkpointer: BaseCheckpointSaver[Any] | None = None,
        safety_policy: SafetyPolicy | None = None,
        audit_recorder: AuditRecorder | None = None,
        audit_metadata: AuditMetadata | None = None,
    ) -> None:
        self.assistant = assistant
        self.checkpointer = checkpointer or InMemorySaver()
        self.safety_policy = safety_policy or SafetyPolicy()
        self.audit_recorder = audit_recorder or InMemoryAuditRecorder()
        self.audit_metadata = audit_metadata or AuditMetadata(
            safety_policy_version=self.safety_policy.version
        )
        self.graph = self._build_graph().compile(checkpointer=self.checkpointer)

    def invoke(self, request: dict[str, Any], *, thread_id: str) -> WorkflowState:
        execution_id = str(uuid4())
        started = time.perf_counter()
        actor_role = str(request.get("requester_role", "professional"))
        initial: WorkflowState = {
            "execution_id": execution_id,
            "request": request,
            "errors": [],
            "alert_flags": [],
            "safety_flags": [],
        }
        self._record(
            execution_id=execution_id,
            thread_id=thread_id,
            event_type="execution_started",
            actor_role=actor_role,
            status="started",
            patient_id=request.get("patient_id"),
            details={"question_length": len(str(request.get("question", "")))},
        )
        try:
            result = cast(
                WorkflowState,
                self.graph.invoke(initial, config=self._config(thread_id)),
            )
        except Exception as error:
            self._record(
                execution_id=execution_id,
                thread_id=thread_id,
                event_type="execution_failed",
                actor_role="system",
                status="failed",
                duration_ms=self._elapsed_ms(started),
                details={"error_type": type(error).__name__},
            )
            raise
        self._record_result(
            result,
            thread_id=thread_id,
            actor_role=actor_role,
            duration_ms=self._elapsed_ms(started),
        )
        return result

    def resume(
        self,
        *,
        thread_id: str,
        decision: str,
        feedback: str,
    ) -> WorkflowState:
        review = HumanReview.model_validate(
            {"decision": decision, "feedback": feedback}
        )
        previous = self.get_state(thread_id=thread_id)
        execution_id = previous.get("execution_id")
        if execution_id is None:
            raise ValueError("checkpoint sem execution_id")
        self._record(
            execution_id=execution_id,
            thread_id=thread_id,
            event_type="human_review_submitted",
            actor_role="reviewer",
            status=review.decision,
            details={
                "decision": review.decision,
                "feedback_length": len(review.feedback),
            },
        )
        started = time.perf_counter()
        result = cast(
            WorkflowState,
            self.graph.invoke(
                Command[Any](resume=review.model_dump()),
                config=self._config(thread_id),
            ),
        )
        self._record_result(
            result,
            thread_id=thread_id,
            actor_role="reviewer",
            duration_ms=self._elapsed_ms(started),
        )
        return result

    def get_state(self, *, thread_id: str) -> WorkflowState:
        snapshot = self.graph.get_state(self._config(thread_id))
        return cast(WorkflowState, snapshot.values)

    def audit_trail(self, execution_id: str) -> list[AuditEvent]:
        return self.audit_recorder.events_for(execution_id)

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return round((time.perf_counter() - started) * 1000, 3)

    def _record_result(
        self,
        state: WorkflowState,
        *,
        thread_id: str,
        actor_role: str,
        duration_ms: float,
    ) -> None:
        paused = "__interrupt__" in state
        response = state.get("response", {})
        sources = response.get("sources", []) if isinstance(response, dict) else []
        details = {
            "intent": state.get("intent"),
            "alert_flags": state.get("alert_flags", []),
            "safety_flags": state.get("safety_flags", []),
            "errors": state.get("errors", []),
            "response_status": response.get("status") if response else None,
            "response_class": response.get("response_class") if response else None,
            "patient_context_used": (
                response.get("patient_context_used", []) if response else []
            ),
            "source_ids": [source["source_id"] for source in sources],
            "review_status": state.get("review_status"),
        }
        self._record(
            execution_id=state["execution_id"],
            thread_id=thread_id,
            event_type="execution_paused" if paused else "execution_completed",
            actor_role=actor_role,
            status=str(state.get("graph_status", "unknown")),
            duration_ms=duration_ms,
            details=details,
        )

    def _record(
        self,
        *,
        execution_id: str,
        thread_id: str,
        event_type: str,
        actor_role: str,
        status: str,
        patient_id: object = None,
        duration_ms: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.audit_recorder.record(
            AuditEvent(
                execution_id=execution_id,
                event_type=event_type,
                actor_role=actor_role,
                status=status,
                thread_ref=mask_identifier(thread_id),
                patient_ref=(
                    mask_identifier(str(patient_id)) if patient_id is not None else None
                ),
                duration_ms=duration_ms,
                metadata=self.audit_metadata,
                details=details or {},
            )
        )

    @staticmethod
    def _config(thread_id: str) -> RunnableConfig:
        if not thread_id.strip():
            raise ValueError("thread_id não pode ser vazio")
        return {"configurable": {"thread_id": thread_id}}

    def _build_graph(self) -> StateGraph[WorkflowState]:
        builder = StateGraph(WorkflowState)
        builder.add_node("validate_request", self._validate_request)
        builder.add_node("screen_input", self._screen_input)
        builder.add_node("create_safety_refusal", self._safety_refusal)
        builder.add_node("classify_intent", self._classify_intent)
        builder.add_node("apply_deterministic_rules", self._apply_rules)
        builder.add_node("create_guardrail_response", self._guardrail_response)
        builder.add_node("run_assistant_chain", self._run_chain)
        builder.add_node("validate_output", self._validate_output)
        builder.add_node("decide_human_review", self._decide_review)
        builder.add_node("human_review", self._human_review)
        builder.add_node("apply_human_review", self._apply_review)
        builder.add_node("finalize", self._finalize)

        builder.add_edge(START, "validate_request")
        builder.add_conditional_edges(
            "validate_request",
            self._route_validity,
            {"valid": "screen_input", "invalid": "finalize"},
        )
        builder.add_conditional_edges(
            "screen_input",
            self._route_input_safety,
            {"allowed": "classify_intent", "blocked": "create_safety_refusal"},
        )
        builder.add_edge("create_safety_refusal", "finalize")
        builder.add_edge("classify_intent", "apply_deterministic_rules")
        builder.add_conditional_edges(
            "apply_deterministic_rules",
            self._route_risk,
            {"sensitive": "create_guardrail_response", "normal": "run_assistant_chain"},
        )
        builder.add_edge("create_guardrail_response", "validate_output")
        builder.add_edge("run_assistant_chain", "validate_output")
        builder.add_edge("validate_output", "decide_human_review")
        builder.add_conditional_edges(
            "decide_human_review",
            self._route_review,
            {"review": "human_review", "complete": "finalize"},
        )
        builder.add_edge("human_review", "apply_human_review")
        builder.add_edge("apply_human_review", "finalize")
        builder.add_edge("finalize", END)
        return builder

    @staticmethod
    def _validate_request(state: WorkflowState) -> WorkflowState:
        try:
            request = AssistantRequest.model_validate(state.get("request", {}))
        except ValidationError as error:
            return {
                "errors": [
                    f"invalid_request:{item['type']}" for item in error.errors()
                ],
                "graph_status": "invalid_request",
            }
        return {"request": request.model_dump(), "graph_status": "validated"}

    @staticmethod
    def _route_validity(state: WorkflowState) -> str:
        return "invalid" if state.get("errors") else "valid"

    def _screen_input(self, state: WorkflowState) -> WorkflowState:
        request = AssistantRequest.model_validate(state["request"])
        result = self.safety_policy.validate_input(request)
        return {
            "safety_flags": list(result.flags),
            "safety_reason": result.reason,
            "graph_status": "input_allowed" if result.allowed else "input_blocked",
        }

    @staticmethod
    def _route_input_safety(state: WorkflowState) -> str:
        return "blocked" if state.get("safety_flags") else "allowed"

    @staticmethod
    def _safety_refusal(state: WorkflowState) -> WorkflowState:
        response = AssistantResponse(
            status="insufficient_evidence",
            response_class="refusal",
            summary="Solicitação bloqueada pela política de segurança.",
            patient_context_used=[],
            guidance="Reformule a solicitação dentro do escopo autorizado.",
            pending_exams=[],
            alerts=state.get("safety_flags", []),
            sources=[],
            confidence="low",
            requires_human_validation=False,
            validation_reason=state.get("safety_reason"),
            limitations=[str(state.get("safety_reason"))],
            disclaimer=DISCLAIMER,
        )
        return {
            "response": response.model_dump(mode="json"),
            "graph_status": "safety_refusal",
        }

    @staticmethod
    def _classify_intent(state: WorkflowState) -> WorkflowState:
        intent = classify_intent(str(state["request"]["question"]))
        return {"intent": intent, "graph_status": "intent_classified"}

    @staticmethod
    def _apply_rules(state: WorkflowState) -> WorkflowState:
        intent = cast(Intent, state["intent"])
        return {
            "alert_flags": flags_for_intent(intent),
            "graph_status": "rules_applied",
        }

    @staticmethod
    def _route_risk(state: WorkflowState) -> str:
        return "sensitive" if state.get("alert_flags") else "normal"

    def _run_chain(self, state: WorkflowState) -> WorkflowState:
        response = self.assistant.invoke(state["request"])
        return {
            "response": response.model_dump(mode="json"),
            "graph_status": "generated",
        }

    def _validate_output(self, state: WorkflowState) -> WorkflowState:
        response = AssistantResponse.model_validate(state["response"])
        result = self.safety_policy.validate_output(response)
        if result.allowed:
            return {"graph_status": "output_validated"}
        safe_response = AssistantResponse(
            status="model_output_rejected",
            response_class="refusal",
            summary="A resposta foi bloqueada pela validação de segurança.",
            patient_context_used=response.patient_context_used,
            guidance="Não utilize a saída; encaminhe para revisão profissional.",
            pending_exams=response.pending_exams,
            alerts=list(result.flags),
            sources=[],
            confidence="low",
            requires_human_validation=True,
            validation_reason=result.reason,
            limitations=[*response.limitations, str(result.reason)],
            disclaimer=DISCLAIMER,
        )
        return {
            "response": safe_response.model_dump(mode="json"),
            "safety_flags": list(result.flags),
            "safety_reason": result.reason,
            "graph_status": "output_blocked",
        }

    @staticmethod
    def _guardrail_response(state: WorkflowState) -> WorkflowState:
        prescription = state["intent"] == "prescription"
        response = AssistantResponse(
            status="insufficient_evidence",
            response_class="refusal" if prescription else "alert",
            summary=(
                "Pedido de prescrição ou dose bloqueado por regra determinística."
                if prescription
                else "Foram identificados termos associados a possível urgência."
            ),
            patient_context_used=[],
            guidance=(
                "A definição de medicamento ou dose exige avaliação do "
                "profissional responsável."
                if prescription
                else "Encaminhe imediatamente para avaliação profissional e "
                "siga o fluxo local de urgência."
            ),
            pending_exams=[],
            alerts=state["alert_flags"],
            sources=[],
            confidence="low",
            requires_human_validation=True,
            validation_reason="Regra sensível exige revisão humana.",
            limitations=["Resposta criada sem inferência da LLM."],
            disclaimer=DISCLAIMER,
        )
        return {
            "response": response.model_dump(mode="json"),
            "graph_status": "guardrail_applied",
        }

    @staticmethod
    def _decide_review(state: WorkflowState) -> WorkflowState:
        response = AssistantResponse.model_validate(state["response"])
        needs_review = (
            bool(state.get("alert_flags"))
            or bool(state.get("safety_flags"))
            or response.requires_human_validation
        )
        return {"graph_status": "awaiting_human_review" if needs_review else "ready"}

    @staticmethod
    def _route_review(state: WorkflowState) -> str:
        if state["graph_status"] == "awaiting_human_review":
            return "review"
        return "complete"

    @staticmethod
    def _human_review(state: WorkflowState) -> WorkflowState:
        resumed = interrupt(
            {
                "kind": "clinical_response_review",
                "allowed_decisions": ["approve", "reject"],
                "intent": state["intent"],
                "alert_flags": state.get("alert_flags", []),
                "safety_flags": state.get("safety_flags", []),
                "response": state["response"],
            }
        )
        review = HumanReview.model_validate(resumed)
        return {
            "review_status": review.decision,
            "review_feedback": review.feedback,
            "graph_status": "human_reviewed",
        }

    @staticmethod
    def _apply_review(state: WorkflowState) -> WorkflowState:
        if state["review_status"] == "approve":
            return {"graph_status": "approved"}
        response = AssistantResponse.model_validate(state["response"])
        response.status = "insufficient_evidence"
        response.response_class = "refusal"
        response.guidance = "A resposta foi rejeitada na revisão humana; não a utilize."
        response.confidence = "low"
        response.requires_human_validation = False
        response.validation_reason = state.get("review_feedback")
        response.limitations.append("Resposta rejeitada pelo revisor humano.")
        return {
            "response": response.model_dump(mode="json"),
            "graph_status": "rejected",
        }

    @staticmethod
    def _finalize(state: WorkflowState) -> WorkflowState:
        if state.get("errors"):
            return {"graph_status": "failed_closed"}
        return {"graph_status": "completed"}
