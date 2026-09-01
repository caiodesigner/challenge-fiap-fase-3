"""Valida o corpus sintético já gerado."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.data import validate_dataset  # noqa: E402, I001


if __name__ == "__main__":
    print(f"Dataset válido: {validate_dataset(PROJECT_ROOT)}")
