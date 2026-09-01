"""Construção determinística do banco clínico sintético."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
DATASET_VERSION = "1.0.0"


def _load_patients(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("patients.json deve conter uma lista")
    return value


def _seed_patient(connection: sqlite3.Connection, patient: dict[str, Any]) -> None:
    patient_id = str(patient["patient_id"])
    if patient.get("synthetic") is not True:
        raise ValueError(f"paciente não sintético recusado: {patient_id}")
    connection.execute(
        "INSERT INTO patients VALUES (?, ?, ?, ?)",
        (
            patient_id,
            1,
            int(patient["age_years"]),
            str(patient["last_review_date"]),
        ),
    )
    connection.executemany(
        "INSERT INTO conditions VALUES (?, ?)",
        [(patient_id, str(code)) for code in patient["conditions"]],
    )
    connection.executemany(
        "INSERT INTO allergies VALUES (?, ?)",
        [(patient_id, str(item)) for item in patient["allergies"]],
    )
    connection.executemany(
        "INSERT INTO medications VALUES (?, ?, 1)",
        [(patient_id, str(item)) for item in patient["current_medications"]],
    )
    completed_at = str(patient["last_review_date"])
    requested_at = f"{completed_at[:8]}01"
    for exam_code in patient["completed_exam_codes"]:
        connection.execute(
            """INSERT INTO exams
               (patient_id, exam_code, status, requested_at,
                completed_at, result_summary)
               VALUES (?, ?, 'completed', ?, ?, ?)""",
            (
                patient_id,
                str(exam_code),
                requested_at,
                completed_at,
                "Resultado sintético disponível; valor clínico não modelado.",
            ),
        )
    for exam_code in patient["pending_exam_codes"]:
        connection.execute(
            """INSERT INTO exams
               (patient_id, exam_code, status, requested_at)
               VALUES (?, ?, 'pending', ?)""",
            (patient_id, str(exam_code), requested_at),
        )
    connection.execute(
        """INSERT INTO visits
           (patient_id, occurred_at, visit_type, synthetic_summary)
           VALUES (?, ?, 'outpatient_review', ?)""",
        (
            patient_id,
            completed_at,
            "Atendimento inteiramente sintético para demonstração acadêmica.",
        ),
    )


def build_database(
    database_path: Path, *, patients_path: Path, schema_path: Path
) -> dict[str, Any]:
    """Cria atomicamente um banco novo sem sobrescrever o arquivo de destino."""

    if database_path.exists():
        raise FileExistsError(
            "banco já existe; remova-o explicitamente antes de reconstruir: "
            f"{database_path}"
        )
    patients = _load_patients(patients_path)
    schema = schema_path.read_text(encoding="utf-8")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(schema)
        connection.executemany(
            "INSERT INTO schema_metadata VALUES (?, ?)",
            [
                ("schema_version", SCHEMA_VERSION),
                ("dataset_version", DATASET_VERSION),
                ("synthetic_only", "true"),
            ],
        )
        for patient in patients:
            _seed_patient(connection, patient)
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError(f"violações de chave estrangeira: {violations}")
        connection.commit()
    except Exception:
        connection.rollback()
        connection.close()
        database_path.unlink(missing_ok=True)
        raise
    finally:
        connection.close()
    digest = hashlib.sha256(database_path.read_bytes()).hexdigest()
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_version": DATASET_VERSION,
        "patients": len(patients),
        "sha256": digest,
    }
