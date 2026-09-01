from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from assistente_medico.repositories import (
    ClinicalRepository,
    PatientNotFoundError,
    build_database,
)


@pytest.fixture
def database(tmp_path: Path) -> Path:
    root = Path(__file__).resolve().parents[2]
    output = tmp_path / "clinical.db"
    build_database(
        output,
        patients_path=root / "data/synthetic/patients.json",
        schema_path=root / "data/database/schema.sql",
    )
    return output


def test_builds_valid_synthetic_database(database: Path) -> None:
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM patients").fetchone()[0] == 12
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert (
            connection.execute(
                "SELECT value FROM schema_metadata WHERE key = 'synthetic_only'"
            ).fetchone()[0]
            == "true"
        )


def test_returns_minimized_patient_context(database: Path) -> None:
    repository = ClinicalRepository(database)
    assert repository.patient_summary("PAT-SYN-003") == {
        "patient_id": "PAT-SYN-003",
        "age_years": 71,
        "conditions": ["DM2", "HAS"],
        "last_review_date": "2026-03-15",
        "synthetic": True,
    }
    assert repository.pending_exams("PAT-SYN-003")[0]["exam_code"] == "EX-REVISAO-B"
    assert (
        repository.recent_results("PAT-SYN-003", limit=1)[0]["exam_code"]
        == "EX-PRESSAO"
    )
    assert repository.allergies("PAT-SYN-003") == []
    assert repository.active_medications("PAT-SYN-003") == []


def test_rejects_invalid_and_unknown_patient(database: Path) -> None:
    repository = ClinicalRepository(database)
    with pytest.raises(PatientNotFoundError, match="inválido"):
        repository.patient_summary("' OR 1=1 --")
    with pytest.raises(PatientNotFoundError, match="não encontrado"):
        repository.patient_summary("PAT-SYN-999")
    with pytest.raises(ValueError, match="entre 1 e 20"):
        repository.recent_results("PAT-SYN-001", limit=100)


def test_database_is_opened_read_only(database: Path) -> None:
    repository = ClinicalRepository(database)
    with (
        repository._connect() as connection,
        pytest.raises(sqlite3.OperationalError),
    ):
        connection.execute("DELETE FROM patients")


def test_builder_refuses_overwrite(database: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    with pytest.raises(FileExistsError, match="já existe"):
        build_database(
            database,
            patients_path=root / "data/synthetic/patients.json",
            schema_path=root / "data/database/schema.sql",
        )
