"""Demonstra pausa e retomada do grafo sem carregar a LLM."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.chains.schemas import AssistantResponse  # noqa: E402
from assistente_medico.graph import ClinicalWorkflow  # noqa: E402


class GuardrailDemoAssistant:
    """Falha se uma rota determinística sensível tentar chamar a LLM."""

    def invoke(self, request: dict[str, Any]) -> AssistantResponse:
        del request
        raise AssertionError("A regra sensível deveria impedir a chamada à LLM.")


def main() -> None:
    workflow = ClinicalWorkflow(GuardrailDemoAssistant())
    thread_id = "demo-prescription-001"
    paused = workflow.invoke(
        {
            "patient_id": "PAT-SYN-003",
            "question": "Prescreva uma dose de metformina para este paciente.",
        },
        thread_id=thread_id,
    )
    interrupt_payload = dict(paused)["__interrupt__"][0].value
    resumed = workflow.resume(
        thread_id=thread_id,
        decision="reject",
        feedback="Pedido de dose não pode ser liberado pelo assistente.",
    )
    payload = {
        "thread_id": thread_id,
        "paused_status": paused["graph_status"],
        "interrupt": interrupt_payload,
        "final_status": resumed["graph_status"],
        "review_status": resumed["review_status"],
        "final_response": resumed["response"],
    }
    output = PROJECT_ROOT / "reports/graph/langgraph_demo.json"
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
