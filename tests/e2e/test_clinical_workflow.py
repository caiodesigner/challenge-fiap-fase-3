from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from assistente_medico.audit import AuditMetadata, JsonlAuditRecorder, explain_state
from assistente_medico.chains import ClinicalAssistantChain
from assistente_medico.graph import ClinicalWorkflow
from assistente_medico.repositories import ClinicalRepository, build_database
from assistente_medico.retrieval import VectorIndex, chunks_from_protocols
from assistente_medico.tools import ClinicalToolRegistry


class DeterministicEmbedder:
    model_id = "e2e-embedder-v1"

    def embed_passages(self, texts: object) -> list[list[float]]:
        assert isinstance(texts, list)
        return [[1.0, 0.0] for _ in texts]

    def embed_queries(self, texts: object) -> list[list[float]]:
        assert isinstance(texts, list)
        return [[1.0, 0.0] for _ in texts]


class ControlledModel:
    def __init__(self, output: str | Exception) -> None:
        self.output = output
        self.calls = 0

    def generate(self, prompt: str) -> str:
        assert "PROMPT_VERSION=e2e-1" in prompt
        self.calls += 1
        if isinstance(self.output, Exception):
            raise self.output
        return self.output


def _model_output(
    *,
    response_class: str = "pending",
    guidance: str = "Revise a pendência com o profissional.",
) -> str:
    return json.dumps(
        {
            "status": "completed",
            "response_class": response_class,
            "summary": "Resumo controlado para integração.",
            "patient_context_used": [],
            "guidance": guidance,
            "pending_exams": [],
            "alerts": [],
            "sources": [],
            "confidence": "medium",
            "requires_human_validation": False,
            "validation_reason": None,
            "limitations": [],
            "disclaimer": "substituído pela chain",
        },
        ensure_ascii=False,
    )


def _workflow(
    tmp_path: Path,
    model: ControlledModel,
) -> tuple[ClinicalWorkflow, Path]:
    root = Path(__file__).resolve().parents[2]
    tmp_path.mkdir(parents=True, exist_ok=True)
    database = tmp_path / "clinical.db"
    build_database(
        database,
        patients_path=root / "data/synthetic/patients.json",
        schema_path=root / "data/database/schema.sql",
    )
    protocols: list[dict[str, Any]] = json.loads(
        (root / "data/synthetic/protocols.json").read_text(encoding="utf-8")
    )
    embedder = DeterministicEmbedder()
    index = VectorIndex.build(chunks_from_protocols(protocols), embedder)
    chain = ClinicalAssistantChain(
        tools=ClinicalToolRegistry(ClinicalRepository(database)),
        index=index,
        embedder=embedder,
        model=model,
        prompt_version="e2e-1",
        top_k=3,
        minimum_score=0.5,
        as_of=date(2026, 9, 1),
    )
    audit_path = tmp_path / "audit.jsonl"
    workflow = ClinicalWorkflow(
        chain,
        audit_recorder=JsonlAuditRecorder(audit_path),
        audit_metadata=AuditMetadata(
            model_version="controlled-e2e-model",
            adapter_version="none",
            prompt_version="e2e-1",
            retrieval_version="e2e-index-v1",
        ),
    )
    return workflow, audit_path


@pytest.mark.e2e
def test_contextualized_pending_exam_crosses_all_components(tmp_path: Path) -> None:
    model = ControlledModel(_model_output())
    workflow, audit_path = _workflow(tmp_path, model)
    result = workflow.invoke(
        {
            "patient_id": "PAT-SYN-003",
            "question": "Quais exames estão pendentes?",
            "specialty": "clinica_medica",
        },
        thread_id="e2e-pending",
    )
    response = result["response"]
    assert result["graph_status"] == "completed"
    assert response["response_class"] == "pending"
    assert response["pending_exams"][0]["exam_code"] == "EX-REVISAO-B"
    assert response["sources"]
    assert "listar_exames_pendentes" in response["patient_context_used"]
    assert model.calls == 1
    explanation = explain_state(dict(result))
    assert explanation.sources
    assert explanation.patient_data_categories
    events = workflow.audit_trail(result["execution_id"])
    assert [event.event_type for event in events] == [
        "execution_started",
        "execution_completed",
    ]
    audit_text = audit_path.read_text(encoding="utf-8")
    assert "PAT-SYN-003" not in audit_text
    assert "Quais exames" not in audit_text


@pytest.mark.e2e
def test_unsafe_chain_output_is_removed_and_reviewed(tmp_path: Path) -> None:
    model = ControlledModel(
        _model_output(
            response_class="information",
            guidance="Iniciar metformina 500 mg duas vezes ao dia.",
        )
    )
    workflow, _ = _workflow(tmp_path, model)
    paused = workflow.invoke(
        {"question": "Resuma a orientação disponível."},
        thread_id="e2e-unsafe-output",
    )
    assert paused["safety_flags"] == ["OPERATIONAL_PRESCRIPTION"]
    assert paused["graph_status"] == "awaiting_human_review"
    assert "500 mg" not in paused["response"]["guidance"]
    completed = workflow.resume(
        thread_id="e2e-unsafe-output",
        decision="reject",
        feedback="Saída insegura confirmada pelo teste.",
    )
    assert completed["graph_status"] == "completed"
    assert completed["review_status"] == "reject"


@pytest.mark.e2e
def test_nonexistent_patient_and_model_failure_fail_closed(tmp_path: Path) -> None:
    missing_model = ControlledModel(_model_output())
    missing_workflow, _ = _workflow(tmp_path / "missing", missing_model)
    missing = missing_workflow.invoke(
        {"patient_id": "PAT-SYN-999", "question": "Resuma o paciente."},
        thread_id="e2e-missing-patient",
    )
    assert missing["response"]["status"] == "insufficient_evidence"
    assert missing["graph_status"] == "awaiting_human_review"
    assert missing_model.calls == 0

    failing_model = ControlledModel(TimeoutError("timeout controlado"))
    failing_workflow, _ = _workflow(tmp_path / "timeout", failing_model)
    failed = failing_workflow.invoke(
        {"question": "Explique o protocolo sintético."},
        thread_id="e2e-model-timeout",
    )
    assert failed["response"]["status"] == "insufficient_evidence"
    assert "model_error:TimeoutError" in failed["response"]["limitations"]
    assert failed["graph_status"] == "awaiting_human_review"


@pytest.mark.e2e
def test_urgent_rule_bypasses_every_generative_dependency(tmp_path: Path) -> None:
    model = ControlledModel(AssertionError("modelo não deve ser chamado"))
    workflow, _ = _workflow(tmp_path, model)
    paused = workflow.invoke(
        {"question": "Paciente relata falta de ar."}, thread_id="e2e-urgent"
    )
    assert paused["intent"] == "urgent"
    assert paused["alert_flags"] == ["POTENTIALLY_URGENT_SYMPTOM"]
    assert paused["response"]["response_class"] == "alert"
    assert model.calls == 0
