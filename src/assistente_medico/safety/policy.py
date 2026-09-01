"""Validação de entrada e saída independente da LLM."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date

from assistente_medico.chains.schemas import AssistantRequest, AssistantResponse

_INJECTION_PATTERNS = (
    "ignore as instrucoes",
    "ignore instrucoes",
    "revele o prompt",
    "mostre o prompt",
    "system prompt",
    "modo desenvolvedor",
    "developer mode",
    "jailbreak",
)
_OUT_OF_SCOPE_PATTERNS = (
    "pediatr",
    "crianca",
    "gestante",
    "gravidez",
    "obstetric",
)
_WRITE_PATTERNS = (
    "altere o prontuario",
    "apague o prontuario",
    "delete o prontuario",
    "atualize o prontuario",
    "registre no prontuario",
)
_PRESCRIPTION_OUTPUT = re.compile(
    r"\b(?:prescrev\w*|administr\w*|tomar|iniciar)\b.{0,40}"
    r"\b\d+(?:[.,]\d+)?\s*(?:mg|ml|mcg|g|unidades?)\b",
    re.IGNORECASE,
)
_CITATION_ID = re.compile(r"^[A-Z0-9][A-Z0-9._-]*#[A-Z0-9][A-Z0-9._-]*$")


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )


@dataclass(frozen=True)
class SafetyResult:
    allowed: bool
    flags: tuple[str, ...] = ()
    reason: str | None = None


class SafetyPolicy:
    """Aplica limites de escopo, integridade de fonte e não prescrição."""

    version = "safety-v1"

    def validate_input(self, request: AssistantRequest) -> SafetyResult:
        question = _normalize(request.question)
        if any(pattern in question for pattern in _INJECTION_PATTERNS):
            return SafetyResult(
                False,
                ("PROMPT_INJECTION_ATTEMPT",),
                "A solicitação tentou substituir as instruções do sistema.",
            )
        if any(pattern in question for pattern in _WRITE_PATTERNS):
            return SafetyResult(
                False,
                ("RECORD_WRITE_ATTEMPT",),
                "Alterações autônomas no prontuário não são permitidas.",
            )
        if any(pattern in question for pattern in _OUT_OF_SCOPE_PATTERNS):
            return SafetyResult(
                False,
                ("OUT_OF_SCOPE_POPULATION",),
                "A população informada está fora do escopo adulto HAS/DM2.",
            )
        return SafetyResult(True)

    def validate_output(
        self,
        response: AssistantResponse,
        *,
        as_of: date | None = None,
    ) -> SafetyResult:
        reference_date = as_of or date.today()
        searchable = _normalize(f"{response.summary} {response.guidance}")
        if _PRESCRIPTION_OUTPUT.search(searchable):
            return SafetyResult(
                False,
                ("OPERATIONAL_PRESCRIPTION",),
                "A saída continha prescrição ou dose operacional.",
            )
        source_ids = [source.source_id for source in response.sources]
        if len(source_ids) != len(set(source_ids)):
            return SafetyResult(
                False,
                ("DUPLICATE_CITATION",),
                "A saída continha citações duplicadas.",
            )
        for source in response.sources:
            if not _CITATION_ID.fullmatch(source.source_id):
                return SafetyResult(
                    False,
                    ("INVALID_CITATION",),
                    "A saída continha uma citação com identificador inválido.",
                )
            if date.fromisoformat(source.effective_date) > reference_date:
                return SafetyResult(
                    False,
                    ("INACTIVE_CITATION",),
                    "A saída citou uma fonte ainda não vigente.",
                )
        grounded_classes = {"information", "pending"}
        if response.response_class in grounded_classes and not response.sources:
            return SafetyResult(
                False,
                ("UNGROUNDED_INSTITUTIONAL_CLAIM",),
                "Informações institucionais exigem ao menos uma fonte válida.",
            )
        if response.response_class in {"alert", "refusal"} and not (
            response.requires_human_validation
        ):
            return SafetyResult(
                False,
                ("MISSING_HUMAN_VALIDATION",),
                "Classe sensível não foi marcada para validação humana.",
            )
        return SafetyResult(True)
