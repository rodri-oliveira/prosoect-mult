from __future__ import annotations

from dataclasses import dataclass

from application.relatorios.relatorio_completo import RelatorioCompletoRequest, get_relatorio_completo_with_repo
from domain.repositories.relatorio_repository import RelatorioRepository
from infrastructure.repositories.sqlite_relatorio_repository import SqliteRelatorioRepository


@dataclass(frozen=True)
class RelatorioCompletoPdfRequest:
    data_inicio: str | None
    data_fim: str | None


@dataclass(frozen=True)
class RelatorioCompletoPdfResponse:
    pdf_bytes: bytes
    data_inicio: str
    data_fim: str


def build_relatorio_completo_pdf(req: RelatorioCompletoPdfRequest) -> RelatorioCompletoPdfResponse:
    return build_relatorio_completo_pdf_with_repo(req, SqliteRelatorioRepository())


def build_relatorio_completo_pdf_with_repo(
    req: RelatorioCompletoPdfRequest,
    repo: RelatorioRepository,
) -> RelatorioCompletoPdfResponse:
    view = get_relatorio_completo_with_repo(RelatorioCompletoRequest(req.data_inicio, req.data_fim), repo)

    from services.relatorio_pdf_service import build_relatorio_pdf_bytes

    pdf_bytes = build_relatorio_pdf_bytes(view.relatorio, view.data_inicio, view.data_fim)
    return RelatorioCompletoPdfResponse(pdf_bytes=pdf_bytes, data_inicio=view.data_inicio, data_fim=view.data_fim)
