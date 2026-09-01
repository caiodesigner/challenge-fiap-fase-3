from __future__ import annotations

import json
from pathlib import Path

from assistente_medico.training import build_fine_tuning_dataset


def _read(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def test_builds_balanced_isolated_dataset(tmp_path: Path) -> None:
    manifest = build_fine_tuning_dataset(tmp_path)
    train = _read(tmp_path / "data/processed/fine_tuning_train.jsonl")
    validation = _read(tmp_path / "data/processed/fine_tuning_validation.jsonl")
    assert len(train) + len(validation) == 120
    assert manifest["categories"] == {
        "summary": 20,
        "pending": 20,
        "missing": 20,
        "prescription": 20,
        "source": 20,
        "alert": 20,
    }
    assert {row["group_id"] for row in train}.isdisjoint(
        {row["group_id"] for row in validation}
    )
    assert all(str(row["example_id"]).startswith("FT-") for row in train)


def test_generation_is_deterministic(tmp_path: Path) -> None:
    first = build_fine_tuning_dataset(tmp_path)
    second = build_fine_tuning_dataset(tmp_path)
    assert first == second
