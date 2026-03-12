from __future__ import annotations

from typing import Protocol


class RelatorioRepository(Protocol):
    def get_resumo_hoje(self) -> dict:
        raise NotImplementedError

    def get_relatorio_completo(self, data_inicio: str | None = None, data_fim: str | None = None) -> dict:
        raise NotImplementedError

    def get_relatorio_prospeccao(self, data_inicio: str | None = None, data_fim: str | None = None) -> dict:
        raise NotImplementedError
