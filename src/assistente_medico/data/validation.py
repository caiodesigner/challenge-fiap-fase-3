"""Validação estrutural e de segurança do corpus sintético."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .anonymization import forbidden_keys, scan_text


class DatasetValidationError(ValueError):
    """Indica que o corpus não atende às invariantes da Etapa 1."""


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _walk(value: Any, location: str = "root") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        blocked = forbidden_keys(value.keys())
        if blocked:
            errors.append(f"{location}: campos proibidos: {sorted(blocked)}")
        for key, child in value.items():
            errors.extend(_walk(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_walk(child, f"{location}[{index}]"))
    elif isinstance(value, str):
        findings = scan_text(value)
        if findings:
            errors.append(
                f"{location}: possíveis identificadores: "
                f"{[item.kind for item in findings]}"
            )
    return errors


def validate_dataset(project_root: Path) -> dict[str, int]:
    """Valida arquivos obrigatórios, IDs, anonimização e isolamento dos splits."""

    synthetic_dir = project_root / "data" / "synthetic"
    splits_dir = project_root / "data" / "splits"
    json_files = [
        synthetic_dir / "metadata.json",
        synthetic_dir / "protocols.json",
        synthetic_dir / "document_templates.json",
        synthetic_dir / "patients.json",
        splits_dir / "manifest.json",
    ]
    jsonl_files = [
        synthetic_dir / "instruction_examples.jsonl",
        splits_dir / "train.jsonl",
        splits_dir / "validation.jsonl",
        splits_dir / "test.jsonl",
    ]
    missing = [str(path) for path in [*json_files, *jsonl_files] if not path.is_file()]
    if missing:
        raise DatasetValidationError(f"Arquivos ausentes: {missing}")

    values = [_read_json(path) for path in json_files]
    rows_by_split = {path.stem: _read_jsonl(path) for path in jsonl_files[1:]}
    all_examples = _read_jsonl(jsonl_files[0])
    errors = [error for value in values for error in _walk(value)]
    errors.extend(error for row in all_examples for error in _walk(row))

    patients = values[3]
    patient_ids = [item["patient_id"] for item in patients]
    example_ids = [item["example_id"] for item in all_examples]
    if len(patient_ids) != len(set(patient_ids)):
        errors.append("patient_id duplicado")
    if len(example_ids) != len(set(example_ids)):
        errors.append("example_id duplicado")
    if not all(item.get("synthetic") is True for item in patients):
        errors.append("todos os pacientes devem declarar synthetic=true")

    split_groups = {
        name: {str(row["group_id"]) for row in rows}
        for name, rows in rows_by_split.items()
    }
    names = list(split_groups)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            overlap = split_groups[left] & split_groups[right]
            if overlap:
                errors.append(f"vazamento entre {left} e {right}: {sorted(overlap)}")
    split_ids = {
        str(row["example_id"]) for rows in rows_by_split.values() for row in rows
    }
    if split_ids != set(example_ids):
        errors.append("splits não cobrem exatamente os exemplos publicados")
    if errors:
        raise DatasetValidationError("; ".join(errors))
    return {
        "patients": len(patients),
        "examples": len(all_examples),
        **{name: len(rows) for name, rows in rows_by_split.items()},
    }
