"""Constrói a base SQLite a partir dos prontuários sintéticos versionados."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.repositories import build_database  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data/database/clinical-synthetic.db",
    )
    args = parser.parse_args()
    result = build_database(
        args.output,
        patients_path=PROJECT_ROOT / "data/synthetic/patients.json",
        schema_path=PROJECT_ROOT / "data/database/schema.sql",
    )
    report = PROJECT_ROOT / "reports/database/build.json"
    report.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
