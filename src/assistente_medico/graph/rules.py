"""Regras determinísticas que não podem depender da LLM."""

from __future__ import annotations

import unicodedata
from typing import Literal

Intent = Literal["prescription", "urgent", "pending_exam", "protocol", "general"]

_PRESCRIPTION_TERMS = (
    "prescrev",
    "receita",
    "posologia",
    "qual dose",
    "dose de",
    "inicie medicamento",
    "troque o medicamento",
)
_URGENT_TERMS = (
    "dor no peito",
    "falta de ar",
    "desmaio",
    "convulsao",
    "perda de consciencia",
    "sangramento intenso",
    "sinal grave",
    "potencialmente grave",
)


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )


def classify_intent(question: str) -> Intent:
    """Classifica primeiro as rotas que possuem maior risco."""

    normalized = normalize(question)
    if any(term in normalized for term in _PRESCRIPTION_TERMS):
        return "prescription"
    if any(term in normalized for term in _URGENT_TERMS):
        return "urgent"
    if any(term in normalized for term in ("exame", "resultado", "pendente")):
        return "pending_exam"
    if any(term in normalized for term in ("protocolo", "procedimento", "diretriz")):
        return "protocol"
    return "general"


def flags_for_intent(intent: Intent) -> list[str]:
    if intent == "prescription":
        return ["PRESCRIPTION_REQUEST"]
    if intent == "urgent":
        return ["POTENTIALLY_URGENT_SYMPTOM"]
    return []
