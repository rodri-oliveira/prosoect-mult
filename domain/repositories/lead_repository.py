from __future__ import annotations

from typing import Protocol


class LeadRepository(Protocol):
    def get_by_id(self, lead_id: int) -> tuple[dict, list[dict], list[str]] | None:
        """Retorna lead, contatos e segmentos pelo ID ou None se não existir."""
        raise NotImplementedError

    def list_by_status(self, status: str | None = None) -> list[dict]:
        """Lista leads por status. Se status=None, retorna todos exceto 'Sem interesse'."""
        raise NotImplementedError

    def create(self, data: dict) -> int:
        """Cria um novo lead e retorna o ID."""
        raise NotImplementedError

    def update_status(self, lead_id: int, novo_status: str) -> bool:
        """Atualiza o status de um lead. Retorna True se atualizado."""
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
        """Adiciona um contato ao lead."""
        raise NotImplementedError

    def get_retornos_agendados(self, data: str, mostrar_todos: bool = False) -> list[dict]:
        """Retorna retornos agendados. Se mostrar_todos=True, retorna todos agendados."""
        raise NotImplementedError

    def get_retornos_atrasados(self, data_ref: str) -> list[dict]:
        """Retorna retornos agendados antes da data de referência."""
        raise NotImplementedError

    def update(self, lead_id: int, data: dict) -> bool:
        """Atualiza campos de um lead. Retorna True se atualizado."""
        raise NotImplementedError

    def devolver_para_prospeccao(self, lead_id: int) -> bool:
        """Devolve lead para prospecção: desarquiva prospecção original e atualiza status."""
        raise NotImplementedError
