from __future__ import annotations

from pathlib import Path

from assistente_medico.audit import (
    AuditEvent,
    AuditMetadata,
    InMemoryAuditRecorder,
    JsonlAuditRecorder,
    explain_state,
    mask_identifier,
)


def _event(execution_id: str = "exec-1") -> AuditEvent:
    return AuditEvent(
        execution_id=execution_id,
        event_type="execution_started",
        actor_role="professional",
        status="started",
        thread_ref=mask_identifier("thread-secret"),
        patient_ref=mask_identifier("PAT-SYN-001"),
        metadata=AuditMetadata(prompt_version="1.0.0"),
        details={"question_length": 20},
    )


def test_masks_identifiers_deterministically() -> None:
    masked = mask_identifier("PAT-SYN-001")
    assert masked == mask_identifier("PAT-SYN-001")
    assert masked != mask_identifier("PAT-SYN-002")
    assert "PAT-SYN" not in masked


def test_memory_recorder_filters_by_execution() -> None:
    recorder = InMemoryAuditRecorder()
    recorder.record(_event("exec-1"))
    recorder.record(_event("exec-2"))
    assert [event.execution_id for event in recorder.events_for("exec-1")] == ["exec-1"]


def test_jsonl_recorder_is_append_only_and_reconstructs_execution(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.jsonl"
    recorder = JsonlAuditRecorder(path)
    recorder.record(_event("exec-1"))
    recorder.record(_event("exec-2"))
    recorder.record(_event("exec-1"))
    events = recorder.events_for("exec-1")
    assert len(events) == 2
    content = path.read_text(encoding="utf-8")
    assert content.count("\n") == 3
    assert "PAT-SYN-001" not in content
    assert "thread-secret" not in content


def test_jsonl_recorder_returns_empty_for_missing_file(tmp_path: Path) -> None:
    assert JsonlAuditRecorder(tmp_path / "missing.jsonl").events_for("x") == []


def test_explanation_uses_only_observable_state() -> None:
    explanation = explain_state(
        {
            "execution_id": "exec-1",
            "intent": "pending_exam",
            "alert_flags": ["RULE-1"],
            "safety_flags": [],
            "review_status": "approve",
            "review_feedback": "Conferido.",
            "errors": [],
            "response": {
                "status": "completed",
                "response_class": "pending",
                "summary": "Resumo.",
                "patient_context_used": ["listar_exames_pendentes"],
                "guidance": "Revisar.",
                "pending_exams": [],
                "alerts": [],
                "sources": [
                    {
                        "source_id": "PR-X#S1",
                        "document": "PR-X",
                        "section": "S1",
                        "version": "1",
                        "effective_date": "2026-01-01",
                        "score": 0.9,
                    }
                ],
                "confidence": "medium",
                "requires_human_validation": False,
                "validation_reason": None,
                "limitations": ["Dados sintéticos."],
                "disclaimer": "Protótipo.",
            },
        }
    )
    assert explanation.execution_id == "exec-1"
    assert explanation.patient_data_categories == ["listar_exames_pendentes"]
    assert explanation.sources[0]["source_id"] == "PR-X#S1"
    assert explanation.deterministic_rules == ["RULE-1"]
    assert explanation.human_review["status"] == "approve"
    assert explanation.human_review["feedback"] == "recorded"


def test_explanation_handles_failed_state() -> None:
    explanation = explain_state({"execution_id": "failed", "errors": ["invalid"]})
    assert explanation.sources == []
    assert explanation.errors == ["invalid"]
