"""Auditoria estruturada, mascarada e reconstruível."""

from assistente_medico.audit.explainability import Explanation, explain_state
from assistente_medico.audit.recorder import (
    AuditEvent,
    AuditMetadata,
    InMemoryAuditRecorder,
    JsonlAuditRecorder,
    mask_identifier,
)

__all__ = [
    "AuditEvent",
    "AuditMetadata",
    "Explanation",
    "InMemoryAuditRecorder",
    "JsonlAuditRecorder",
    "explain_state",
    "mask_identifier",
]
