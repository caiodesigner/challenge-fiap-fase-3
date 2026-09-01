from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from assistente_medico.retrieval import VectorIndex, chunks_from_protocols


class FakeEmbedder:
    model_id = "fake-v1"

    def embed_passages(self, texts: object) -> list[list[float]]:
        del texts
        return [[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]]

    def embed_queries(self, texts: object) -> list[list[float]]:
        del texts
        return [[1.0, 0.0]]


def _protocols() -> list[dict[str, object]]:
    return [
        {
            "protocol_id": "PR-A",
            "title": "Ativo",
            "specialty": "clinica",
            "version": "1",
            "status": "active",
            "effective_date": "2026-01-01",
            "sections": [
                {"section_id": "S1", "heading": "Um", "content": "Conteúdo"},
                {"section_id": "S2", "heading": "Dois", "content": "Outro"},
            ],
        },
        {
            "protocol_id": "PR-B",
            "title": "Inativo",
            "specialty": "clinica",
            "version": "1",
            "status": "inactive",
            "effective_date": "2026-01-01",
            "sections": [{"section_id": "S1", "heading": "Três", "content": "Antigo"}],
        },
    ]


def test_build_search_filters_and_citations(tmp_path: Path) -> None:
    chunks = chunks_from_protocols(_protocols())
    index = VectorIndex.build(chunks, FakeEmbedder())
    results = index.search(
        "consulta",
        FakeEmbedder(),
        top_k=3,
        specialty="clinica",
        as_of=date(2026, 9, 1),
    )
    assert [result.chunk.source_id for result in results] == ["PR-A#S1", "PR-A#S2"]
    assert results[0].citation == {
        "source_id": "PR-A#S1",
        "document": "PR-A",
        "section": "S1",
        "version": "1",
        "effective_date": "2026-01-01",
    }
    path = tmp_path / "index.json"
    index.save(path)
    assert VectorIndex.load(path).model_id == "fake-v1"


def test_rejects_duplicate_sources() -> None:
    protocols = _protocols()
    sections = protocols[0]["sections"]
    assert isinstance(sections, list)
    sections.append(sections[0])
    with pytest.raises(ValueError, match="duplicado"):
        chunks_from_protocols(protocols)


def test_rejects_wrong_embedder_and_invalid_top_k() -> None:
    index = VectorIndex.build(chunks_from_protocols(_protocols()), FakeEmbedder())
    other = FakeEmbedder()
    other.model_id = "other"
    with pytest.raises(ValueError, match="difere"):
        index.search("x", other)
    with pytest.raises(ValueError, match="positivo"):
        index.search("x", FakeEmbedder(), top_k=0)


def test_filters_sources_not_yet_effective() -> None:
    protocols = _protocols()
    protocols[0]["effective_date"] = "2027-01-01"
    index = VectorIndex.build(chunks_from_protocols(protocols), FakeEmbedder())
    assert index.search("x", FakeEmbedder(), as_of=date(2026, 9, 1)) == []
