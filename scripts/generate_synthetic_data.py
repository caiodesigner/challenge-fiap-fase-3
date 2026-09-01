"""Gera o corpus sintético publicável da Etapa 1."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.data import generate_dataset, validate_dataset  # noqa: E402


def main() -> None:
    counts = generate_dataset(PROJECT_ROOT)
    validate_dataset(PROJECT_ROOT)
    print(f"Dataset sintético gerado e validado: {counts}")


if __name__ == "__main__":
    main()
