"""Indexação e recuperação rastreável de protocolos."""

from .index import (
    ProtocolChunk,
    SearchResult,
    VectorIndex,
    chunks_from_protocols,
)

__all__ = [
    "ProtocolChunk",
    "SearchResult",
    "VectorIndex",
    "chunks_from_protocols",
]
