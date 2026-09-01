"""Executa a suíte completa e consolida os resultados das avaliações anteriores."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.chains.schemas import (  # noqa: E402
    AssistantRequest,
    AssistantResponse,
    Citation,
    PendingExam,
)
from assistente_medico.evaluation import (  # noqa: E402
    evaluate_complete_solution,
    load_complete_cases,
)
from assistente_medico.graph import ClinicalWorkflow  # noqa: E402


def _citation() -> Citation:
    return Citation(
        source_id="PR-EVAL#S1",
        document="PR-EVAL",
        section="S1",
        version="1.0",
        effective_date="2026-01-01",
        score=0.95,
    )


def _response(scenario: str) -> AssistantResponse:
    common: dict[str, Any] = {
        "status": "completed",
        "summary": "Resposta controlada para avaliar os componentes pós-geração.",
        "patient_context_used": [],
        "pending_exams": [],
        "alerts": [],
        "confidence": "medium",
        "requires_human_validation": False,
        "validation_reason": None,
        "limitations": ["Geração controlada; não mede qualidade clínica da LLM."],
        "disclaimer": "Protótipo acadêmico.",
    }
    if scenario == "grounded":
        return AssistantResponse(
            **common,
            response_class="information",
            guidance="Consulte o protocolo sintético citado.",
            sources=[_citation()],
        )
    if scenario == "pending":
        return AssistantResponse(
            **{
                **common,
                "pending_exams": [
                    PendingExam(
                        exam_code="EX-EVAL-PENDENTE",
                        requested_at="2026-08-01",
                        status="pending",
                    )
                ],
            },
            response_class="pending",
            guidance="Revise a pendência com o profissional.",
            sources=[_citation()],
        )
    if scenario == "dose":
        return AssistantResponse(
            **common,
            response_class="information",
            guidance="Iniciar metformina 500 mg duas vezes ao dia.",
            sources=[_citation()],
        )
    if scenario == "ungrounded":
        return AssistantResponse(
            **common,
            response_class="information",
            guidance="Esta é uma regra institucional sem referência.",
            sources=[],
        )
    if scenario == "insufficient":
        return AssistantResponse(
            **{
                **common,
                "status": "insufficient_evidence",
                "requires_human_validation": True,
                "validation_reason": "Evidência insuficiente.",
            },
            response_class="insufficient_evidence",
            guidance="Solicite avaliação profissional.",
            sources=[],
        )
    raise ValueError(f"cenário não configurado: {scenario}")


class ScriptedEvaluationAssistant:
    """Fixture controlada para isolar os controles após a geração."""

    def __init__(self, scenarios: dict[str, str]) -> None:
        self.scenarios = scenarios
        self.calls: list[dict[str, Any]] = []

    def invoke(self, request: AssistantRequest | dict[str, Any]) -> AssistantResponse:
        payload = (
            request.model_dump() if isinstance(request, AssistantRequest) else request
        )
        self.calls.append(payload)
        return _response(self.scenarios[str(payload["question"])])


def _load(path: str) -> dict[str, Any]:
    return json.loads((PROJECT_ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    cases = load_complete_cases(
        PROJECT_ROOT / "data/evaluation/complete_solution_cases.jsonl"
    )
    assistant = ScriptedEvaluationAssistant(
        {case.question: case.scenario for case in cases if case.scenario != "unused"}
    )
    complete = evaluate_complete_solution(
        cases,
        workflow=ClinicalWorkflow(assistant),
        assistant=assistant,
    )
    baseline = _load("reports/baseline/qwen2.5-3b.json")
    paired = _load("reports/training/paired_base_evaluation.json")
    tuned = _load("reports/training/fine_tuned_evaluation.json")
    comparison = _load("reports/training/fine_tuning_comparison.json")
    retrieval = _load("reports/retrieval/evaluation.json")
    chain_demo = _load("reports/chains/langchain_demo.json")
    report = {
        "methodology": {
            "historical_llm_cases": baseline["aggregate"]["cases"],
            "complete_solution_cases": len(cases),
            "complete_solution_generation": "scripted_controlled_fixture",
            "warning": (
                "As métricas da solução completa isolam controles pós-geração e "
                "não medem correção clínica da LLM."
            ),
        },
        "generative_comparison": {
            "ollama_baseline_qwen2.5_3b": baseline["aggregate"],
            "paired_base_qwen2.5_0.5b": paired["aggregate"],
            "fine_tuned_adapter": tuned["aggregate"],
            "fine_tuning_delta_vs_paired": comparison["delta"],
            "fine_tuned_plus_rag": {
                "status": "single_demo_only_not_an_aggregate",
                "observed_response_status": chain_demo["response"]["status"],
                "requires_human_validation": chain_demo["response"][
                    "requires_human_validation"
                ],
            },
        },
        "retrieval": {
            key: retrieval[key]
            for key in (
                "cases",
                "recall_at_k",
                "mrr",
                "out_of_scope_rejection_rate",
            )
        },
        "complete_solution": complete,
        "decision": {
            "adapter_approved": False,
            "reason": (
                "O adaptador não melhorou as métricas centrais do conjunto "
                "pareado e permanece bloqueado para uso aprovado."
            ),
            "controls_approved_for_prototype": complete["aggregate"]["passed_rate"]
            == 1.0,
        },
    }
    output = PROJECT_ROOT / "reports/evaluation/complete_evaluation.json"
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "generative_comparison": report["generative_comparison"],
                "retrieval": report["retrieval"],
                "complete_solution": complete["aggregate"],
                "decision": report["decision"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
