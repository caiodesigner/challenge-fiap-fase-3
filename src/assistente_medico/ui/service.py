"""Bootstrap e transformação de estado para a interface."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

from assistente_medico.audit import (
    AuditMetadata,
    JsonlAuditRecorder,
    explain_state,
)
from assistente_medico.chains import ClinicalAssistantChain
from assistente_medico.chains.schemas import AssistantResponse
from assistente_medico.graph import ClinicalWorkflow
from assistente_medico.inference import FineTunedLocalProvider
from assistente_medico.repositories import ClinicalRepository, build_database
from assistente_medico.retrieval import VectorIndex, chunks_from_protocols
from assistente_medico.retrieval.e5 import E5Embedder
from assistente_medico.tools import ClinicalToolRegistry


class ControlledEmbedder:
    """Embedding determinístico exclusivo do modo de demonstração."""

    model_id = "controlled-ui-embedder-v1"

    def embed_passages(self, texts: Sequence[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]

    def embed_queries(self, texts: Sequence[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


class ControlledDemoModel:
    """Geração válida e previsível; não representa desempenho clínico."""

    def generate(self, prompt: str) -> str:
        pending = any(term in prompt.casefold() for term in ("exame", "pendente"))
        payload = {
            "status": "completed",
            "response_class": "pending" if pending else "information",
            "summary": "Resposta controlada baseada no contexto sintético recuperado.",
            "patient_context_used": [],
            "guidance": (
                "Revise as pendências exibidas com o profissional responsável."
                if pending
                else "Consulte as fontes institucionais sintéticas apresentadas."
            ),
            "pending_exams": [],
            "alerts": [],
            "sources": [],
            "confidence": "medium",
            "requires_human_validation": False,
            "validation_reason": None,
            "limitations": ["Modo controlado: não avalia a qualidade da LLM."],
            "disclaimer": "substituído pela chain",
        }
        return json.dumps(payload, ensure_ascii=False)


def load_synthetic_patients(project_root: Path) -> list[dict[str, Any]]:
    payload = json.loads(
        (project_root / "data/synthetic/patients.json").read_text(encoding="utf-8")
    )
    if not isinstance(payload, list):
        raise ValueError("arquivo de pacientes deve conter uma lista")
    return payload


def _database(project_root: Path) -> Path:
    database = project_root / "data/database/clinical-synthetic.db"
    if not database.exists():
        build_database(
            database,
            patients_path=project_root / "data/synthetic/patients.json",
            schema_path=project_root / "data/database/schema.sql",
        )
    return database


def _workflow(
    project_root: Path,
    *,
    index: VectorIndex,
    embedder: Any,
    model: Any,
    mode: str,
    prompt_version: str,
    minimum_score: float,
    top_k: int,
    as_of: date,
) -> ClinicalWorkflow:
    chain = ClinicalAssistantChain(
        tools=ClinicalToolRegistry(ClinicalRepository(_database(project_root))),
        index=index,
        embedder=embedder,
        model=model,
        prompt_version=prompt_version,
        top_k=top_k,
        minimum_score=minimum_score,
        as_of=as_of,
    )
    return ClinicalWorkflow(
        chain,
        audit_recorder=JsonlAuditRecorder(
            project_root / f"outputs/interface-audit-{mode}.jsonl"
        ),
        audit_metadata=AuditMetadata(
            model_version=(
                "controlled-demo-model"
                if mode == "controlled"
                else "Qwen/Qwen2.5-0.5B-Instruct"
            ),
            adapter_version=(
                "not_applicable"
                if mode == "controlled"
                else "qwen2.5-0.5b-medical-assistant-v2"
            ),
            prompt_version=prompt_version,
            retrieval_version=index.model_id,
        ),
    )


def build_controlled_workflow(project_root: Path) -> ClinicalWorkflow:
    protocols = json.loads(
        (project_root / "data/synthetic/protocols.json").read_text(encoding="utf-8")
    )
    embedder = ControlledEmbedder()
    index = VectorIndex.build(chunks_from_protocols(protocols), embedder)
    return _workflow(
        project_root,
        index=index,
        embedder=embedder,
        model=ControlledDemoModel(),
        mode="controlled",
        prompt_version="ui-controlled-1.0",
        minimum_score=0.5,
        top_k=3,
        as_of=date(2026, 9, 1),
    )


def build_real_workflow(project_root: Path) -> ClinicalWorkflow:
    assistant = json.loads(
        (project_root / "configs/assistant.json").read_text(encoding="utf-8")
    )
    retrieval = json.loads(
        (project_root / assistant["retrieval_config"]).read_text(encoding="utf-8")
    )
    index = VectorIndex.load(project_root / retrieval["index_file"])
    embedder = E5Embedder(
        retrieval["embedding_model"],
        batch_size=retrieval["batch_size"],
        max_length=retrieval["max_length"],
    )
    model = FineTunedLocalProvider(
        assistant["base_model"],
        project_root / assistant["adapter_dir"],
        max_new_tokens=assistant["max_new_tokens"],
    )
    return _workflow(
        project_root,
        index=index,
        embedder=embedder,
        model=model,
        mode="real",
        prompt_version=assistant["prompt_version"],
        minimum_score=retrieval["minimum_score"],
        top_k=retrieval["top_k"],
        as_of=date.fromisoformat(retrieval["as_of"]),
    )


def build_view_model(state: dict[str, Any]) -> dict[str, Any]:
    response_payload = state.get("response")
    response = (
        AssistantResponse.model_validate(response_payload)
        if response_payload is not None
        else None
    )
    return {
        "execution_id": state.get("execution_id"),
        "graph_status": state.get("graph_status", "unknown"),
        "awaiting_review": "__interrupt__" in state,
        "response": response.model_dump(mode="json") if response else None,
        "explanation": explain_state(state).model_dump(mode="json"),
    }
