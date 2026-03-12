from __future__ import annotations

from dataclasses import dataclass

from application.relatorios.relatorio_prospeccao import RelatorioProspeccaoRequest, get_relatorio_prospeccao_with_repo
from domain.repositories.relatorio_repository import RelatorioRepository
from infrastructure.repositories.sqlite_relatorio_repository import SqliteRelatorioRepository


@dataclass(frozen=True)
class RelatorioProspeccaoPdfRequest:
    data_inicio: str | None
    data_fim: str | None


@dataclass(frozen=True)
class RelatorioProspeccaoPdfResponse:
    pdf_bytes: bytes
    data_inicio: str
    data_fim: str


def build_relatorio_prospeccao_pdf(req: RelatorioProspeccaoPdfRequest) -> RelatorioProspeccaoPdfResponse:
    return build_relatorio_prospeccao_pdf_with_repo(req, SqliteRelatorioRepository())


def build_relatorio_prospeccao_pdf_with_repo(
    req: RelatorioProspeccaoPdfRequest,
    repo: RelatorioRepository,
) -> RelatorioProspeccaoPdfResponse:
    res = get_relatorio_prospeccao_with_repo(RelatorioProspeccaoRequest(req.data_inicio, req.data_fim), repo)

    from services.relatorio_pdf_service import build_relatorio_prospeccao_pdf_bytes

    data_inicio = req.data_inicio or ""
    data_fim = req.data_fim or (req.data_inicio or "")

    pdf_bytes = build_relatorio_prospeccao_pdf_bytes(res.relatorio, data_inicio, data_fim)
    return RelatorioProspeccaoPdfResponse(pdf_bytes=pdf_bytes, data_inicio=data_inicio, data_fim=data_fim)
