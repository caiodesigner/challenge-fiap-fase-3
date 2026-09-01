"""Demonstra somente as ferramentas allowlisted, sem LLM ou SQL externo."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.repositories import ClinicalRepository  # noqa: E402, I001
from assistente_medico.tools import ClinicalToolRegistry  # noqa: E402


if __name__ == "__main__":
    repository = ClinicalRepository(
        PROJECT_ROOT / "data/database/clinical-synthetic.db"
    )
    tools = ClinicalToolRegistry(repository)
    result = {
        name: tools.invoke(name, {"patient_id": "PAT-SYN-003"})
        for name in tools.allowed_tools
        if name != "buscar_resultados_recentes"
    }
    result["buscar_resultados_recentes"] = tools.invoke(
        "buscar_resultados_recentes", {"patient_id": "PAT-SYN-003", "limit": 3}
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
