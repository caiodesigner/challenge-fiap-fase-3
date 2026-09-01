"""Contratos serializáveis do estado e da revisão humana."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field


class WorkflowState(TypedDict, total=False):
    """Estado persistido entre os nós e interrupções do grafo."""

    execution_id: str
    request: dict[str, Any]
    intent: str
    alert_flags: list[str]
    safety_flags: list[str]
    safety_reason: str | None
    response: dict[str, Any]
    errors: list[str]
    graph_status: str
    review_status: str
    review_feedback: str | None


class HumanReview(BaseModel):
    """Decisão aceita ao retomar um checkpoint interrompido."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject"]
    feedback: str = Field(min_length=3, max_length=500)
