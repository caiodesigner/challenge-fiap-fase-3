from __future__ import annotations

from pathlib import Path

import pytest

from assistente_medico.repositories import ClinicalRepository, build_database
from assistente_medico.tools import ClinicalToolRegistry, ToolNotAllowedError


@pytest.fixture
def tools(tmp_path: Path) -> ClinicalToolRegistry:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "clinical.db"
    build_database(
        database,
        patients_path=root / "data/synthetic/patients.json",
        schema_path=root / "data/database/schema.sql",
    )
    return ClinicalToolRegistry(ClinicalRepository(database))


def test_exposes_only_allowlisted_tools(tools: ClinicalToolRegistry) -> None:
    assert tools.allowed_tools == (
        "buscar_resultados_recentes",
        "buscar_resumo_paciente",
        "listar_alergias",
        "listar_exames_pendentes",
        "listar_medicamentos_ativos",
    )
    result = tools.invoke("listar_exames_pendentes", {"patient_id": "PAT-SYN-003"})
    assert result[0]["exam_code"] == "EX-REVISAO-B"


def test_rejects_unknown_tool_and_sql_like_arguments(
    tools: ClinicalToolRegistry,
) -> None:
    with pytest.raises(ToolNotAllowedError, match="não permitida"):
        tools.invoke("executar_sql", {"query": "SELECT * FROM patients"})
    with pytest.raises(ToolNotAllowedError, match="argumentos"):
        tools.invoke(
            "buscar_resumo_paciente",
            {"patient_id": "PAT-SYN-001", "query": "DROP TABLE patients"},
        )
    with pytest.raises(ToolNotAllowedError, match="argumentos"):
        tools.invoke(
            "buscar_resumo_paciente", {"patient_id": "PAT-SYN-001", "limit": 1}
        )
    with pytest.raises(ToolNotAllowedError, match="obrigatório"):
        tools.invoke("listar_alergias", {})
