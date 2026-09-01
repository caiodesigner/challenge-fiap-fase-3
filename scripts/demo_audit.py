"""Demonstra reconstrução e explicabilidade por execution_id."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.audit import (  # noqa: E402
    AuditMetadata,
    JsonlAuditRecorder,
    explain_state,
)
from assistente_medico.chains.schemas import AssistantResponse  # noqa: E402
from assistente_medico.graph import ClinicalWorkflow  # noqa: E402


class AuditDemoAssistant:
    def invoke(self, request: dict[str, Any]) -> AssistantResponse:
        del request
        raise AssertionError("A rota determinística não deve chamar a LLM.")


def main() -> None:
    audit_path = PROJECT_ROOT / "reports/audit/demo_events.jsonl"
    recorder = JsonlAuditRecorder(audit_path)
    workflow = ClinicalWorkflow(
        AuditDemoAssistant(),
        audit_recorder=recorder,
        audit_metadata=AuditMetadata(
            model_version="Qwen/Qwen2.5-0.5B-Instruct",
            adapter_version="qwen2.5-0.5b-medical-assistant-v2",
            prompt_version="1.0.0",
            retrieval_version="protocols-e5-small",
        ),
    )
    thread_id = "demo-audit-sensitive-thread"
    paused = workflow.invoke(
        {
            "patient_id": "PAT-SYN-003",
            "question": "Paciente relata dor no peito.",
            "requester_role": "professional",
        },
        thread_id=thread_id,
    )
    completed = workflow.resume(
        thread_id=thread_id,
        decision="reject",
        feedback="Encaminhamento conferido pelo revisor.",
    )
    execution_id = completed["execution_id"]
    events = workflow.audit_trail(execution_id)
    payload = {
        "execution_id": execution_id,
        "events": [event.model_dump(mode="json") for event in events],
        "explanation": explain_state(dict(completed)).model_dump(mode="json"),
        "privacy_checks": {
            "raw_patient_in_log": "PAT-SYN-003" in audit_path.read_text("utf-8"),
            "raw_thread_in_log": thread_id in audit_path.read_text("utf-8"),
            "raw_question_in_log": "dor no peito" in audit_path.read_text("utf-8"),
        },
        "paused_execution_id_matches": paused["execution_id"] == execution_id,
    }
    output = PROJECT_ROOT / "reports/audit/demo_summary.json"
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
