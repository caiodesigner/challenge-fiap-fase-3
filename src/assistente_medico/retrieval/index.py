"""Índice vetorial local, versionado e independente de frameworks de agentes."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Protocol


class Embedder(Protocol):
    """Contrato mínimo para permitir testes sem baixar um modelo."""

    model_id: str

    def embed_passages(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_queries(self, texts: Sequence[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class ProtocolChunk:
    source_id: str
    protocol_id: str
    title: str
    specialty: str
    version: str
    status: str
    effective_date: str
    section_id: str
    heading: str
    content: str

    @property
    def passage(self) -> str:
        return f"{self.title}. {self.heading}. {self.content}"

    @property
    def citation(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "document": self.protocol_id,
            "section": self.section_id,
            "version": self.version,
            "effective_date": self.effective_date,
        }


@dataclass(frozen=True)
class SearchResult:
    chunk: ProtocolChunk
    score: float

    @property
    def citation(self) -> dict[str, str]:
        return self.chunk.citation


def chunks_from_protocols(protocols: Iterable[dict[str, Any]]) -> list[ProtocolChunk]:
    """Cria um chunk por seção e preserva todos os metadados auditáveis."""

    chunks: list[ProtocolChunk] = []
    seen: set[str] = set()
    for protocol in protocols:
        for section in protocol["sections"]:
            source_id = f"{protocol['protocol_id']}#{section['section_id']}"
            if source_id in seen:
                raise ValueError(f"source_id duplicado: {source_id}")
            seen.add(source_id)
            chunks.append(
                ProtocolChunk(
                    source_id=source_id,
                    protocol_id=str(protocol["protocol_id"]),
                    title=str(protocol["title"]),
                    specialty=str(protocol["specialty"]),
                    version=str(protocol["version"]),
                    status=str(protocol["status"]),
                    effective_date=str(protocol["effective_date"]),
                    section_id=str(section["section_id"]),
                    heading=str(section["heading"]),
                    content=str(section["content"]),
                )
            )
    return chunks


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("dimensões de embedding incompatíveis")
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


class VectorIndex:
    """Índice exato por produto escalar sobre vetores previamente normalizados."""

    def __init__(
        self,
        chunks: Sequence[ProtocolChunk],
        embeddings: Sequence[Sequence[float]],
        *,
        model_id: str,
    ) -> None:
        if not chunks or len(chunks) != len(embeddings):
            raise ValueError("chunks e embeddings devem ser não vazios e alinhados")
        dimensions = {len(vector) for vector in embeddings}
        if len(dimensions) != 1 or 0 in dimensions:
            raise ValueError("todos os embeddings devem ter a mesma dimensão")
        self.chunks = list(chunks)
        self.embeddings = [list(vector) for vector in embeddings]
        self.model_id = model_id

    @classmethod
    def build(cls, chunks: Sequence[ProtocolChunk], embedder: Embedder) -> VectorIndex:
        return cls(
            chunks,
            embedder.embed_passages([chunk.passage for chunk in chunks]),
            model_id=embedder.model_id,
        )

    def search(
        self,
        query: str,
        embedder: Embedder,
        *,
        top_k: int = 3,
        minimum_score: float = 0.0,
        specialty: str | None = None,
        as_of: date | None = None,
    ) -> list[SearchResult]:
        if top_k < 1:
            raise ValueError("top_k deve ser positivo")
        if embedder.model_id != self.model_id:
            raise ValueError("modelo de consulta difere do modelo do índice")
        query_vector = embedder.embed_queries([query])[0]
        reference_date = as_of or date.today()
        candidates = (
            SearchResult(chunk=chunk, score=_dot(query_vector, embedding))
            for chunk, embedding in zip(self.chunks, self.embeddings, strict=True)
            if chunk.status == "active"
            and date.fromisoformat(chunk.effective_date) <= reference_date
            and (specialty is None or chunk.specialty == specialty)
        )
        ranked = sorted(candidates, key=lambda result: result.score, reverse=True)
        return [result for result in ranked if result.score >= minimum_score][:top_k]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "format_version": "1.0",
            "model_id": self.model_id,
            "dimensions": len(self.embeddings[0]),
            "items": [
                {"chunk": asdict(chunk), "embedding": embedding}
                for chunk, embedding in zip(self.chunks, self.embeddings, strict=True)
            ],
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> VectorIndex:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("format_version") != "1.0":
            raise ValueError("versão de índice não suportada")
        return cls(
            [ProtocolChunk(**item["chunk"]) for item in payload["items"]],
            [item["embedding"] for item in payload["items"]],
            model_id=str(payload["model_id"]),
        )
