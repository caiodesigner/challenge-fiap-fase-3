"""Gerador determinístico do corpus sintético da Etapa 1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SEED = 20260831
DATASET_VERSION = "1.0.0"
DISCLAIMER = (
    "Conteúdo sintético para demonstração acadêmica; requer validação humana "
    "e não deve ser usado para decisão clínica real."
)


def _protocols() -> list[dict[str, Any]]:
    return [
        {
            "protocol_id": "PR-HAS-001",
            "title": "Acompanhamento sintético de hipertensão",
            "specialty": "clinica_medica",
            "version": "1.0",
            "status": "active",
            "effective_date": "2026-01-01",
            "sections": [
                {
                    "section_id": "S1",
                    "heading": "Revisão periódica",
                    "content": (
                        "Revisar registros sintéticos de pressão, adesão informada "
                        "e exames marcados no plano individual."
                    ),
                },
                {
                    "section_id": "S2",
                    "heading": "Limite do assistente",
                    "content": (
                        "Qualquer sugestão de mudança terapêutica exige revisão "
                        "do profissional responsável."
                    ),
                },
            ],
        },
        {
            "protocol_id": "PR-DM2-001",
            "title": "Acompanhamento sintético de diabetes tipo 2",
            "specialty": "clinica_medica",
            "version": "1.0",
            "status": "active",
            "effective_date": "2026-01-01",
            "sections": [
                {
                    "section_id": "S1",
                    "heading": "Revisão periódica",
                    "content": (
                        "Conferir exames previstos no plano sintético, sintomas "
                        "informados e registro de adesão."
                    ),
                },
                {
                    "section_id": "S2",
                    "heading": "Dados insuficientes",
                    "content": (
                        "Não inferir resultado ausente; registrar a lacuna e "
                        "encaminhar para avaliação profissional."
                    ),
                },
            ],
        },
        {
            "protocol_id": "PR-SEG-001",
            "title": "Segurança e escalonamento do assistente",
            "specialty": "governanca_clinica",
            "version": "1.0",
            "status": "active",
            "effective_date": "2026-01-01",
            "sections": [
                {
                    "section_id": "S1",
                    "heading": "Prescrição",
                    "content": (
                        "O assistente não emite prescrição, dose ou alteração "
                        "terapêutica definitiva."
                    ),
                },
                {
                    "section_id": "S2",
                    "heading": "Alerta",
                    "content": (
                        "Alertas são sinalizações acadêmicas e devem ser revisados "
                        "por uma pessoa autorizada."
                    ),
                },
            ],
        },
    ]


def _document_templates() -> list[dict[str, Any]]:
    return [
        {
            "template_id": "TPL-LAUDO-001",
            "document_type": "laudo",
            "title": "Modelo sintético de laudo",
            "fields": ["patient_id", "exam_code", "result_summary", "review_status"],
            "required_human_validation": True,
        },
        {
            "template_id": "TPL-RECEITA-001",
            "document_type": "receita",
            "title": "Estrutura sintética de receita não operacional",
            "fields": ["patient_id", "professional_review", "status"],
            "required_human_validation": True,
            "restriction": "O assistente não preenche medicamento, dose ou assinatura.",
        },
        {
            "template_id": "TPL-PROC-001",
            "document_type": "procedimento",
            "title": "Checklist sintético de procedimento interno",
            "fields": [
                "patient_id",
                "procedure_code",
                "prerequisites",
                "review_status",
            ],
            "required_human_validation": True,
        },
    ]


def _patients() -> list[dict[str, Any]]:
    profiles = [
        ("PAT-SYN-001", 58, ["HAS"], ["EX-PRESSAO"], []),
        ("PAT-SYN-002", 64, ["DM2"], ["EX-GLICEMIA"], ["EX-REVISAO-A"]),
        ("PAT-SYN-003", 71, ["HAS", "DM2"], ["EX-PRESSAO"], ["EX-REVISAO-B"]),
        ("PAT-SYN-004", 49, ["HAS"], ["EX-PRESSAO", "EX-REVISAO-A"], []),
        ("PAT-SYN-005", 55, ["DM2"], ["EX-GLICEMIA"], []),
        ("PAT-SYN-006", 68, ["HAS", "DM2"], ["EX-GLICEMIA"], ["EX-REVISAO-A"]),
        ("PAT-SYN-007", 45, ["HAS"], ["EX-PRESSAO"], []),
        ("PAT-SYN-008", 62, ["DM2"], ["EX-REVISAO-B"], ["EX-REVISAO-A"]),
        ("PAT-SYN-009", 73, ["HAS", "DM2"], ["EX-PRESSAO"], ["EX-REVISAO-B"]),
        ("PAT-SYN-010", 52, ["HAS"], ["EX-PRESSAO"], []),
        ("PAT-SYN-011", 60, ["DM2"], ["EX-GLICEMIA"], []),
        ("PAT-SYN-012", 66, ["HAS", "DM2"], ["EX-GLICEMIA"], ["EX-REVISAO-A"]),
    ]
    return [
        {
            "patient_id": patient_id,
            "synthetic": True,
            "age_years": age,
            "conditions": conditions,
            "allergies": [],
            "current_medications": [],
            "completed_exam_codes": completed,
            "pending_exam_codes": pending,
            "last_review_date": f"2026-{(index % 6) + 1:02d}-15",
        }
        for index, (patient_id, age, conditions, completed, pending) in enumerate(
            profiles
        )
    ]


def _examples(patients: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = [
        {
            "example_id": "FAQ-001",
            "group_id": "PR-HAS-001",
            "instruction": "Como revisar o acompanhamento de HAS neste ambiente?",
            "context": "Consulta geral, sem paciente selecionado.",
            "response": (
                "Revise os registros previstos no plano individual e encaminhe "
                "qualquer mudança terapêutica para validação humana."
            ),
            "source_ids": ["PR-HAS-001#S1", "PR-HAS-001#S2"],
            "response_class": "information",
        },
        {
            "example_id": "FAQ-002",
            "group_id": "PR-DM2-001",
            "instruction": (
                "O que fazer quando falta um resultado no prontuário sintético?"
            ),
            "context": "O exame é mencionado, mas não existe resultado registrado.",
            "response": (
                "Declare que o dado está ausente, não estime o resultado e "
                "encaminhe a lacuna para avaliação profissional."
            ),
            "source_ids": ["PR-DM2-001#S2"],
            "response_class": "information",
        },
        {
            "example_id": "FAQ-003",
            "group_id": "PR-SEG-001",
            "instruction": "Prescreva um medicamento e indique a dose.",
            "context": "Solicitação de prescrição direta.",
            "response": (
                "Não posso emitir prescrição ou dose. A decisão deve ser "
                "realizada e validada pelo profissional responsável."
            ),
            "source_ids": ["PR-SEG-001#S1"],
            "response_class": "refusal",
        },
    ]
    for index, patient in enumerate(patients, start=1):
        pending = patient["pending_exam_codes"]
        pending_text = ", ".join(pending) if pending else "nenhum"
        conditions = ", ".join(patient["conditions"])
        examples.append(
            {
                "example_id": f"CASE-{index:03d}",
                "group_id": patient["patient_id"],
                "instruction": "Resuma o contexto e informe exames pendentes.",
                "context": (
                    f"Paciente {patient['patient_id']}; condições: {conditions}; "
                    f"exames pendentes: {pending_text}."
                ),
                "response": (
                    f"O registro sintético informa {conditions}. Pendências "
                    f"registradas: {pending_text}. O resultado requer revisão humana."
                ),
                "source_ids": [patient["patient_id"]],
                "response_class": "summary",
            }
        )
    return examples


def _split_for(group_id: str) -> str:
    bucket = int(hashlib.sha256(f"{SEED}:{group_id}".encode()).hexdigest()[:8], 16) % 10
    if bucket < 7:
        return "train"
    if bucket < 9:
        return "validation"
    return "test"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")


def generate_dataset(project_root: Path) -> dict[str, int]:
    """Gera todos os dados publicáveis e retorna contagens por coleção."""

    synthetic_dir = project_root / "data" / "synthetic"
    splits_dir = project_root / "data" / "splits"
    protocols = _protocols()
    templates = _document_templates()
    patients = _patients()
    examples = _examples(patients)
    split_rows: dict[str, list[dict[str, Any]]] = {
        name: [] for name in ("train", "validation", "test")
    }
    assignments: dict[str, str] = {}
    for example in examples:
        split = _split_for(str(example["group_id"]))
        assignments[str(example["group_id"])] = split
        split_rows[split].append(example)

    metadata = {
        "dataset_name": "assistente-medico-sintetico-fiap",
        "dataset_version": DATASET_VERSION,
        "seed": SEED,
        "synthetic": True,
        "clinical_use_allowed": False,
        "disclaimer": DISCLAIMER,
    }
    _write_json(synthetic_dir / "metadata.json", metadata)
    _write_json(synthetic_dir / "protocols.json", protocols)
    _write_json(synthetic_dir / "document_templates.json", templates)
    _write_json(synthetic_dir / "patients.json", patients)
    _write_jsonl(synthetic_dir / "instruction_examples.jsonl", examples)
    for name, rows in split_rows.items():
        _write_jsonl(splits_dir / f"{name}.jsonl", rows)
    _write_json(
        splits_dir / "manifest.json",
        {
            **metadata,
            "strategy": "group_hash",
            "group_field": "group_id",
            "target_ratio": {"train": 0.7, "validation": 0.2, "test": 0.1},
            "assignments": assignments,
            "counts": {name: len(rows) for name, rows in split_rows.items()},
        },
    )
    return {
        "protocols": len(protocols),
        "templates": len(templates),
        "patients": len(patients),
        "examples": len(examples),
        **{name: len(rows) for name, rows in split_rows.items()},
    }
