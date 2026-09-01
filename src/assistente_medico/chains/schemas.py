"""Contratos tipados da integração LangChain."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=3, max_length=1000)
    patient_id: str | None = Field(default=None, pattern=r"^PAT-SYN-\d{3}$")
    specialty: Literal["clinica_medica", "governanca_clinica"] | None = None
    requester_role: Literal["professional", "reviewer"] = "professional"


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    document: str
    section: str
    version: str
    effective_date: str
    score: float = Field(ge=-1, le=1)


class PendingExam(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exam_code: str
    requested_at: str
    status: Literal["pending"]


class AssistantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    status: Literal["completed", "insufficient_evidence", "model_output_rejected"]
    response_class: Literal[
        "information", "summary", "pending", "alert", "refusal", "insufficient_evidence"
    ]
    summary: str
    patient_context_used: list[str]
    guidance: str
    pending_exams: list[PendingExam]
    alerts: list[str]
    sources: list[Citation]
    confidence: Literal["low", "medium", "high"]
    requires_human_validation: bool
    validation_reason: str | None
    limitations: list[str]
    disclaimer: str
