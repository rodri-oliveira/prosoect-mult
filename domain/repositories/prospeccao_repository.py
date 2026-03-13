from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ProspecctionSummary:
    total: int
    por_status: dict[str, int]


class ProspeccaoRepository(Protocol):
    def get_by_id(self, prospeccao_id: int) -> dict | None:
        """Retorna uma prospecção pelo ID ou None se não existir."""
        raise NotImplementedError

    def list_by_filters(
        self,
        status: str | None = None,
        segmento: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        mostrar_arquivados: bool = False,
    ) -> list[dict]:
        """Lista prospecções com filtros."""
        raise NotImplementedError

    def get_summary(self, data_inicio: str | None, data_fim: str | None, mostrar_arquivados: bool = False) -> ProspecctionSummary:
        """Retorna resumo de prospecções (total e por status)."""
        raise NotImplementedError

    def add(self, dados: dict) -> tuple[int, bool]:
        """
        Adiciona ou atualiza uma prospecção.
        Retorna (id, created) onde created indica se foi criado novo ou existente.
        """
        raise NotImplementedError

    def update_status(
        self,
        prospeccao_id: int,
        novo_status: str,
        observacao: str | None = None,
        data_retorno: str | None = None,
        hora_retorno: str | None = None,
    ) -> bool:
        """Atualiza o status de uma prospecção."""
        raise NotImplementedError

    def arquivar(self, prospeccao_id: int) -> bool:
        """Arquiva uma prospecção."""
        raise NotImplementedError

    def converter_para_lead(self, prospeccao_id: int) -> int | None:
        """Converte prospecção em lead. Retorna lead_id ou None."""
        raise NotImplementedError

    def delete(self, prospeccao_id: int) -> bool:
        """Exclui uma prospecção permanentemente."""
        raise NotImplementedError

    def get_total_retornos_hoje(self) -> int:
        """Retorna quantidade de retornos agendados para hoje (somente não arquivados)."""
        raise NotImplementedError

    def get_eventos(self, prospeccao_id: int) -> list[dict]:
        """Retorna histórico de eventos de uma prospecção."""
        raise NotImplementedError
