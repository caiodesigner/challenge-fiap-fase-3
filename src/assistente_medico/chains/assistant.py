"""Chain segura que integra prontuário, RAG e LLM customizada."""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Literal

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable, RunnableLambda
from pydantic import ValidationError

from assistente_medico.chains.schemas import (
    AssistantRequest,
    AssistantResponse,
    Citation,
)
from assistente_medico.inference import TextGenerationProvider
from assistente_medico.repositories import PatientNotFoundError
from assistente_medico.retrieval import VectorIndex
from assistente_medico.retrieval.index import Embedder
from assistente_medico.tools import ClinicalToolRegistry

DISCLAIMER = (
    "Protótipo acadêmico de apoio à decisão; não substitui avaliação profissional."
)


class ClinicalAssistantChain:
    """RunnableSequence com fail-closed para banco, RAG, modelo e schema."""

    def __init__(
        self,
        *,
        tools: ClinicalToolRegistry,
        index: VectorIndex,
        embedder: Embedder,
        model: TextGenerationProvider,
        prompt_version: str,
        top_k: int = 3,
        minimum_score: float = 0.84,
        as_of: date | None = None,
    ) -> None:
        self.tools = tools
        self.index = index
        self.embedder = embedder
        self.model = model
        self.prompt_version = prompt_version
        self.top_k = top_k
        self.minimum_score = minimum_score
        self.as_of = as_of or date.today()
        self.parser = JsonOutputParser()
        self.runnable: Runnable[Any, AssistantResponse] = (
            RunnableLambda(self._validate, name="validate_request")
            | RunnableLambda(self._enrich, name="retrieve_context")
            | RunnableLambda(self._generate, name="generate_with_custom_llm")
            | RunnableLambda(self._parse, name="validate_structured_response")
        )

    def invoke(self, request: AssistantRequest | dict[str, Any]) -> AssistantResponse:
        return self.runnable.invoke(request)

    def _validate(self, request: AssistantRequest | dict[str, Any]) -> dict[str, Any]:
        validated = (
            request
            if isinstance(request, AssistantRequest)
            else AssistantRequest.model_validate(request)
        )
        return {"request": validated, "errors": []}

    @staticmethod
    def _selected_tools(question: str) -> tuple[str, ...]:
        normalized = question.casefold()
        selected = ["buscar_resumo_paciente"]
        if any(word in normalized for word in ("exame", "resultado", "pendente")):
            selected.extend(["listar_exames_pendentes", "buscar_resultados_recentes"])
        if "alerg" in normalized:
            selected.append("listar_alergias")
        if any(
            word in normalized
            for word in ("medicamento", "medicação", "prescrev", "dose")
        ):
            selected.append("listar_medicamentos_ativos")
        return tuple(selected)

    def _enrich(self, state: dict[str, Any]) -> dict[str, Any]:
        request: AssistantRequest = state["request"]
        patient_context: dict[str, Any] = {}
        if request.patient_id:
            try:
                for tool_name in self._selected_tools(request.question):
                    arguments: dict[str, Any] = {"patient_id": request.patient_id}
                    if tool_name == "buscar_resultados_recentes":
                        arguments["limit"] = 5
                    patient_context[tool_name] = self.tools.invoke(tool_name, arguments)
            except (PatientNotFoundError, OSError, ValueError) as error:
                state["errors"].append(f"patient_context_error:{type(error).__name__}")
        try:
            results = self.index.search(
                request.question,
                self.embedder,
                top_k=self.top_k,
                minimum_score=self.minimum_score,
                specialty=request.specialty,
                as_of=self.as_of,
            )
        except (OSError, RuntimeError, ValueError) as error:
            state["errors"].append(f"retrieval_error:{type(error).__name__}")
            results = []
        state["patient_context"] = patient_context
        state["retrieved_context"] = [
            {
                "source_id": result.chunk.source_id,
                "content": result.chunk.content,
                "score": result.score,
                "citation": {**result.citation, "score": result.score},
            }
            for result in results
        ]
        if not patient_context and not results:
            state["errors"].append("evidence_not_found")
        return state

    def _generate(self, state: dict[str, Any]) -> dict[str, Any]:
        if state["errors"]:
            state["raw_model_output"] = None
            return state
        request: AssistantRequest = state["request"]
        prompt = self._build_prompt(
            request, state["patient_context"], state["retrieved_context"]
        )
        try:
            state["raw_model_output"] = self.model.generate(prompt)
        except (RuntimeError, OSError, TimeoutError) as error:
            state["errors"].append(f"model_error:{type(error).__name__}")
            state["raw_model_output"] = None
        return state

    def _build_prompt(
        self,
        request: AssistantRequest,
        patient_context: dict[str, Any],
        retrieved_context: list[dict[str, Any]],
    ) -> str:
        schema = AssistantResponse.model_json_schema()
        return (
            f"PROMPT_VERSION={self.prompt_version}\n"
            "Você é um assistente acadêmico. Use somente CONTEXTO_PACIENTE e "
            "FONTES_RECUPERADAS. Não invente fatos, fontes ou resultados. Não "
            "prescreva nem defina dose. Responda somente com um objeto JSON que "
            "obedeça exatamente ao schema. Toda sugestão ou alerta requer "
            "validação humana.\n"
            f"SCHEMA={json.dumps(schema, ensure_ascii=False)}\n"
            f"PERGUNTA={request.question}\n"
            f"CONTEXTO_PACIENTE={json.dumps(patient_context, ensure_ascii=False)}\n"
            f"FONTES_RECUPERADAS={json.dumps(retrieved_context, ensure_ascii=False)}"
        )

    def _parse(self, state: dict[str, Any]) -> AssistantResponse:
        if state["errors"] or not state.get("raw_model_output"):
            return self._fallback(state, "Falha controlada em dependência da chain.")
        try:
            parsed = self.parser.parse(str(state["raw_model_output"]))
            response = AssistantResponse.model_validate(parsed)
        except (ValidationError, ValueError, TypeError):
            return self._fallback(
                state, "A saída da LLM foi rejeitada por não cumprir o schema."
            )
        citations = [
            Citation.model_validate(item["citation"])
            for item in state["retrieved_context"]
        ]
        response.sources = citations
        response.patient_context_used = sorted(state["patient_context"])
        response.pending_exams = state["patient_context"].get(
            "listar_exames_pendentes", []
        )
        response.disclaimer = DISCLAIMER
        if response.response_class in {"alert", "refusal"}:
            response.requires_human_validation = True
            response.validation_reason = (
                response.validation_reason or "Classe sensível exige revisão humana."
            )
        return response

    def _fallback(self, state: dict[str, Any], reason: str) -> AssistantResponse:
        citations = [
            Citation.model_validate(item["citation"])
            for item in state.get("retrieved_context", [])
        ]
        pending = state.get("patient_context", {}).get("listar_exames_pendentes", [])
        status: Literal["insufficient_evidence", "model_output_rejected"] = (
            "model_output_rejected"
            if state.get("raw_model_output")
            else "insufficient_evidence"
        )
        return AssistantResponse(
            status=status,
            response_class="insufficient_evidence",
            summary="Não foi possível produzir uma resposta validada.",
            patient_context_used=sorted(state.get("patient_context", {})),
            guidance="Encaminhe a solicitação para avaliação profissional.",
            pending_exams=pending,
            alerts=[],
            sources=citations,
            confidence="low",
            requires_human_validation=True,
            validation_reason=reason,
            limitations=[*state.get("errors", []), reason],
            disclaimer=DISCLAIMER,
        )
