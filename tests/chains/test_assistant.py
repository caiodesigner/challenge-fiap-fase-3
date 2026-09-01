from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from assistente_medico.chains import ClinicalAssistantChain
from assistente_medico.repositories import ClinicalRepository, build_database
from assistente_medico.retrieval import VectorIndex, chunks_from_protocols
from assistente_medico.tools import ClinicalToolRegistry


class FakeEmbedder:
    model_id = "fake-chain"

    def embed_passages(self, texts: object) -> list[list[float]]:
        del texts
        return [[1.0, 0.0], [0.0, 1.0]]

    def embed_queries(self, texts: object) -> list[list[float]]:
        del texts
        return [[1.0, 0.0]]


class FakeModel:
    def __init__(self, response: str | Exception) -> None:
        self.response = response
        self.prompt = ""

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _valid_response() -> str:
    return json.dumps(
        {
            "status": "completed",
            "response_class": "pending",
            "summary": "Resumo sintético.",
            "patient_context_used": [],
            "guidance": "Revisar a pendência com o profissional.",
            "pending_exams": [],
            "alerts": [],
            "sources": [],
            "confidence": "medium",
            "requires_human_validation": True,
            "validation_reason": "Revisão necessária.",
            "limitations": [],
            "disclaimer": "será substituído",
        },
        ensure_ascii=False,
    )


@pytest.fixture
def dependencies(tmp_path: Path) -> tuple[ClinicalToolRegistry, VectorIndex]:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "clinical.db"
    build_database(
        database,
        patients_path=root / "data/synthetic/patients.json",
        schema_path=root / "data/database/schema.sql",
    )
    protocols = [
        {
            "protocol_id": "PR-T",
            "title": "Teste",
            "specialty": "clinica_medica",
            "version": "1",
            "status": "active",
            "effective_date": "2026-01-01",
            "sections": [
                {"section_id": "S1", "heading": "Exame", "content": "Pendência"},
                {"section_id": "S2", "heading": "Outro", "content": "Conteúdo"},
            ],
        }
    ]
    index = VectorIndex.build(chunks_from_protocols(protocols), FakeEmbedder())
    return ClinicalToolRegistry(ClinicalRepository(database)), index


def _chain(
    dependencies: tuple[ClinicalToolRegistry, VectorIndex], model: FakeModel
) -> ClinicalAssistantChain:
    tools, index = dependencies
    return ClinicalAssistantChain(
        tools=tools,
        index=index,
        embedder=FakeEmbedder(),
        model=model,
        prompt_version="test",
        minimum_score=0.5,
        as_of=date(2026, 9, 1),
    )


def test_integrates_minimized_context_sources_and_schema(
    dependencies: tuple[ClinicalToolRegistry, VectorIndex],
) -> None:
    model = FakeModel(_valid_response())
    response = _chain(dependencies, model).invoke(
        {
            "patient_id": "PAT-SYN-003",
            "question": "Quais exames estão pendentes?",
            "specialty": "clinica_medica",
        }
    )
    assert response.status == "completed"
    assert response.pending_exams[0].exam_code == "EX-REVISAO-B"
    assert response.sources[0].source_id == "PR-T#S1"
    assert response.patient_context_used == [
        "buscar_resultados_recentes",
        "buscar_resumo_paciente",
        "listar_exames_pendentes",
    ]
    assert "PAT-SYN-003" in model.prompt
    assert "PROMPT_VERSION=test" in model.prompt


def test_rejects_invalid_model_output(
    dependencies: tuple[ClinicalToolRegistry, VectorIndex],
) -> None:
    response = _chain(dependencies, FakeModel("não é JSON")).invoke(
        {"question": "Explique o protocolo."}
    )
    assert response.status == "model_output_rejected"
    assert response.requires_human_validation is True
    assert "rejeitada" in response.validation_reason


def test_fails_closed_when_model_fails(
    dependencies: tuple[ClinicalToolRegistry, VectorIndex],
) -> None:
    response = _chain(dependencies, FakeModel(RuntimeError("offline"))).invoke(
        {"question": "Explique o protocolo."}
    )
    assert response.status == "insufficient_evidence"
    assert "model_error:RuntimeError" in response.limitations


def test_rejects_invalid_request(
    dependencies: tuple[ClinicalToolRegistry, VectorIndex],
) -> None:
    with pytest.raises(ValidationError):
        _chain(dependencies, FakeModel(_valid_response())).invoke(
            {"patient_id": "1 OR 1=1", "question": "x"}
        )


def test_sensitive_class_is_forced_to_human_validation(
    dependencies: tuple[ClinicalToolRegistry, VectorIndex],
) -> None:
    payload: dict[str, Any] = json.loads(_valid_response())
    payload["response_class"] = "refusal"
    payload["requires_human_validation"] = False
    payload["validation_reason"] = None
    response = _chain(dependencies, FakeModel(json.dumps(payload))).invoke(
        {"question": "Prescreva uma dose."}
    )
    assert response.requires_human_validation is True
    assert response.validation_reason == "Classe sensível exige revisão humana."


def test_does_not_call_model_without_patient_or_source(
    dependencies: tuple[ClinicalToolRegistry, VectorIndex],
) -> None:
    tools, index = dependencies
    model = FakeModel(_valid_response())
    chain = ClinicalAssistantChain(
        tools=tools,
        index=index,
        embedder=FakeEmbedder(),
        model=model,
        prompt_version="test",
        minimum_score=1.1,
        as_of=date(2026, 9, 1),
    )
    response = chain.invoke({"question": "Pergunta sem evidência."})
    assert response.status == "insufficient_evidence"
    assert "evidence_not_found" in response.limitations
    assert model.prompt == ""


def test_fails_closed_for_nonexistent_patient(
    dependencies: tuple[ClinicalToolRegistry, VectorIndex],
) -> None:
    model = FakeModel(_valid_response())
    response = _chain(dependencies, model).invoke(
        {"patient_id": "PAT-SYN-999", "question": "Resuma o paciente."}
    )
    assert response.status == "insufficient_evidence"
    assert "patient_context_error:PatientNotFoundError" in response.limitations
    assert model.prompt == ""
