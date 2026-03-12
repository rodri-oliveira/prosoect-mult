from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AgendamentosViewData:
    retornos_hoje: list[dict]
    retornos_atrasados: list[dict]
    retornos_futuros: list[dict]
    retornos_leads_hoje: list[dict]
    retornos_leads_atrasados: list[dict]
    retornos_leads_futuros: list[dict]
    total_hoje: int
    total_atrasados: int
    total_futuros: int
    total_leads_hoje: int
    total_leads_atrasados: int
    total_leads_futuros: int
    hoje: str


class AgendamentosRepository(Protocol):
    def rolar_agendamentos_pendentes(self, data_limite: str) -> int:
        """Rola agendamentos pendentes para o dia atual. Retorna quantidade rolada."""
        raise NotImplementedError

    def get_view_data(self, data: str, mostrar_todos: bool = False) -> AgendamentosViewData:
        """Retorna todos os dados necessários para a view de agendamentos."""
        raise NotImplementedError

    def registrar_tentativa_retorno(self, prospeccao_id: int, observacao: str) -> bool:
        """Registra uma tentativa de retorno."""
        raise NotImplementedError

    def registrar_resultado_retorno(
        self,
        prospeccao_id: int,
        resultado: str,
        observacao: str | None = None,
    ) -> bool:
        """Registra o resultado de uma tentativa de retorno."""
        raise NotImplementedError

    def update_segmento(self, prospeccao_id: int, segmento: str) -> bool:
        """Atualiza o segmento de uma prospecção."""
        raise NotImplementedError
