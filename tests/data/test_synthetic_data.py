from __future__ import annotations

import hashlib
from pathlib import Path

from assistente_medico.data import generate_dataset, validate_dataset


def _digest_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((root / "data").rglob("*.json*")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_generation_is_deterministic(tmp_path: Path) -> None:
    first = generate_dataset(tmp_path)
    first_digest = _digest_tree(tmp_path)
    second = generate_dataset(tmp_path)
    assert second == first
    assert _digest_tree(tmp_path) == first_digest


def test_generated_dataset_is_valid(tmp_path: Path) -> None:
    counts = generate_dataset(tmp_path)
    validated = validate_dataset(tmp_path)
    assert validated["patients"] == counts["patients"] == 12
    assert validated["examples"] == counts["examples"] == 15
    assert sum(validated[name] for name in ("train", "validation", "test")) == 15
