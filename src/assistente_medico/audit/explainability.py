"""Explicação factual derivada do estado, sem nova inferência."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from assistente_medico.chains.schemas import AssistantResponse


class Explanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_id: str
    intent: str | None
    patient_data_categories: list[str]
    sources: list[dict[str, Any]]
    deterministic_rules: list[str]
    safety_decisions: list[str]
    human_review: dict[str, str | None]
    errors: list[str]
    limitations: list[str]


def explain_state(state: dict[str, Any]) -> Explanation:
    """Lista somente os elementos observáveis que influenciaram a resposta."""

    response_payload = state.get("response")
    response = (
        AssistantResponse.model_validate(response_payload)
        if response_payload is not None
        else None
    )
    return Explanation(
        execution_id=str(state.get("execution_id", "unknown")),
        intent=state.get("intent"),
        patient_data_categories=(response.patient_context_used if response else []),
        sources=(
            [source.model_dump(mode="json") for source in response.sources]
            if response
            else []
        ),
        deterministic_rules=list(state.get("alert_flags", [])),
        safety_decisions=list(state.get("safety_flags", [])),
        human_review={
            "status": state.get("review_status"),
            "feedback": "recorded" if state.get("review_feedback") else None,
        },
        errors=list(state.get("errors", [])),
        limitations=response.limitations if response else [],
    )
