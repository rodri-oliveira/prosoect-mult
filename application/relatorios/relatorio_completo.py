from __future__ import annotations

from dataclasses import dataclass

from domain.repositories.relatorio_repository import RelatorioRepository
from infrastructure.repositories.sqlite_relatorio_repository import SqliteRelatorioRepository


@dataclass(frozen=True)
class RelatorioCompletoRequest:
    data_inicio: str | None
    data_fim: str | None


@dataclass(frozen=True)
class RelatorioCompletoResponse:
    relatorio: dict
    data_inicio: str
    data_fim: str


def get_relatorio_completo(req: RelatorioCompletoRequest) -> RelatorioCompletoResponse:
    return get_relatorio_completo_with_repo(req, SqliteRelatorioRepository())


def get_relatorio_completo_with_repo(req: RelatorioCompletoRequest, repo: RelatorioRepository) -> RelatorioCompletoResponse:
    relatorio = repo.get_relatorio_completo(req.data_inicio, req.data_fim)

    periodo = relatorio.get("periodo") or {}
    data_inicio = str(periodo.get("inicio") or req.data_inicio or "")
    data_fim = str(periodo.get("fim") or req.data_fim or data_inicio)

    return RelatorioCompletoResponse(relatorio=relatorio, data_inicio=data_inicio, data_fim=data_fim)
