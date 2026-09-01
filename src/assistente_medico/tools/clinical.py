"""Allowlist de ferramentas clínicas sem acesso arbitrário ao banco."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from assistente_medico.repositories import ClinicalRepository


class ToolNotAllowedError(PermissionError):
    """Ferramenta desconhecida ou fora do conjunto explicitamente autorizado."""


class ClinicalToolRegistry:
    """Expõe operações específicas, com argumentos validados pelo repositório."""

    def __init__(self, repository: ClinicalRepository) -> None:
        self._tools: dict[str, tuple[Callable[..., Any], frozenset[str]]] = {
            "buscar_resumo_paciente": (
                repository.patient_summary,
                frozenset({"patient_id"}),
            ),
            "listar_exames_pendentes": (
                repository.pending_exams,
                frozenset({"patient_id"}),
            ),
            "buscar_resultados_recentes": (
                repository.recent_results,
                frozenset({"patient_id", "limit"}),
            ),
            "listar_alergias": (
                repository.allergies,
                frozenset({"patient_id"}),
            ),
            "listar_medicamentos_ativos": (
                repository.active_medications,
                frozenset({"patient_id"}),
            ),
        }

    @property
    def allowed_tools(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def invoke(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        definition = self._tools.get(tool_name)
        if definition is None:
            raise ToolNotAllowedError(f"ferramenta não permitida: {tool_name}")
        tool, allowed_arguments = definition
        unexpected = set(arguments) - allowed_arguments
        if unexpected:
            raise ToolNotAllowedError(
                f"argumentos não permitidos: {sorted(unexpected)}"
            )
        if "patient_id" not in arguments:
            raise ToolNotAllowedError("argumento obrigatório ausente: patient_id")
        return tool(**arguments)
