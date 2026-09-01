"""Executa e documenta o baseline da Etapa 2."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.evaluation import run_baseline  # noqa: E402
from assistente_medico.evaluation.baseline import load_cases  # noqa: E402


def _percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def _report(payload: dict[str, Any]) -> str:
    run = payload["run"]
    aggregate = payload["aggregate"]
    lines = [
        "# Baseline — modelo sem customização",
        "",
        f"- Modelo: `{run['model']}`",
        "- Fine-tuning: não",
        "- RAG: não",
        "- Ferramentas: não",
        f"- Casos: {aggregate['cases']}",
        f"- Taxa de aprovação automática: {_percentage(aggregate['passed_rate'])}",
        f"- JSON válido: {_percentage(aggregate['valid_json_rate'])}",
        f"- Classe correta: {_percentage(aggregate['class_match_rate'])}",
        "- Validação humana correta: "
        f"{_percentage(aggregate['human_validation_match_rate'])}",
        f"- Recall de termos: {_percentage(aggregate['expected_term_recall'])}",
        f"- Latência média: {aggregate['mean_latency_seconds']:.2f}s",
        "",
        "## Resultados por caso",
        "",
        "| Caso | Categoria | Classe | Validação | Termos | Aprovado |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for item in payload["results"]:
        case = item["case"]
        metrics = item["metrics"]
        lines.append(
            f"| {case['case_id']} | {case['category']} | "
            f"{'sim' if metrics['class_match'] else 'não'} | "
            f"{'sim' if metrics['human_validation_match'] else 'não'} | "
            f"{_percentage(metrics['expected_term_recall'])} | "
            f"{'sim' if metrics['passed'] else 'não'} |"
        )
    lines.extend(
        [
            "",
            "## Interpretação",
            "",
            "As métricas são heurísticas transparentes e não representam "
            "validação clínica. Este resultado será a referência para comparar "
            "o modelo fine-tuned, a versão "
            "com RAG e a solução completa.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    config_path = PROJECT_ROOT / "configs" / "baseline.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    cases = load_cases(PROJECT_ROOT / config["evaluation_dataset"])
    payload = run_baseline(config, cases)
    output = PROJECT_ROOT / config["output"]
    report = PROJECT_ROOT / config["report"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report.write_text(_report(payload), encoding="utf-8")
    print(f"Baseline concluído: {output}")
    print(f"Relatório: {report}")


if __name__ == "__main__":
    main()
