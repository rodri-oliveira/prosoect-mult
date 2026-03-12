from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LeadSummary:
    total: int
    por_status: dict[str, int]


class LeadRepository(Protocol):
    def get_by_id(self, lead_id: int) -> tuple[dict, list[dict], list[str]] | None:
        """Retorna (lead, contatos, segmentos) ou None."""
        raise NotImplementedError

    def list_by_status(self, status: str | None = None) -> list[dict]:
        """Lista leads com filtro opcional de status."""
        raise NotImplementedError

    def create(self, data: dict) -> int:
        """Cria um novo lead e retorna o ID."""
        raise NotImplementedError

    def update_status(self, lead_id: int, novo_status: str) -> bool:
        """Atualiza o status de um lead."""
        raise NotImplementedError

    def add_contato(
        self,
        lead_id: int,
        tipo_contato: str,
        resultado: str,
        observacao: str | None = None,
        data_retorno: str | None = None,
        hora_retorno: str | None = None,
    ) -> bool:
        """Adiciona um contato/histórico ao lead."""
        raise NotImplementedError

    def get_retornos_agendados(self, data: str, mostrar_todos: bool = False) -> list[dict]:
        """Retorna retornos agendados para uma data."""
        raise NotImplementedError

    def get_retornos_atrasados(self, data_ref: str) -> list[dict]:
        """Retorna retornos atrasados até uma data de referência."""
        raise NotImplementedError
