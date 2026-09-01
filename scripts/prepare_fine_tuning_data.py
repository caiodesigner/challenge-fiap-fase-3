"""Prepara o corpus instrucional ampliado para QLoRA."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.training import build_fine_tuning_dataset  # noqa: E402, I001


if __name__ == "__main__":
    result = build_fine_tuning_dataset(PROJECT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
