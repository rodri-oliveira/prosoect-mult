from __future__ import annotations

from dataclasses import dataclass

from domain.repositories.prospeccao_repository import ProspeccaoRepository
from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository


@dataclass(frozen=True)
class ProspecctionListViewRequest:
    filtro_status: str | None
    filtro_nome: str | None
    segmento: str | None
    cidade: str | None
    estado: str | None
    telefone: str | None
    data_inicio: str | None
    data_fim: str | None
    mostrar_arquivados: bool
    tipo_telefone: str | None = None
    default_to_today_when_no_dates: bool = True


@dataclass(frozen=True)
class ProspecctionListViewResponse:
    prospeccoes: object
    resumo_prospeccao: object
    data_inicio: str | None
    data_fim: str | None


def build_prospeccao_list_view(req: ProspecctionListViewRequest) -> ProspecctionListViewResponse:
    return build_prospeccao_list_view_with_repo(req, SqliteProspeccaoRepository())


def build_prospeccao_list_view_with_repo(
    req: ProspecctionListViewRequest,
    repo: ProspeccaoRepository,
) -> ProspecctionListViewResponse:
    from datetime import date

    data_inicio = req.data_inicio
    data_fim = req.data_fim

    has_other_filters = any(
        [
            req.filtro_status,
            req.filtro_nome,
            req.segmento,
            req.cidade,
            req.estado,
            req.telefone,
            req.tipo_telefone,
        ]
    )
    if (
        req.default_to_today_when_no_dates
        and not data_inicio
        and not data_fim
        and not req.mostrar_arquivados
        and not has_other_filters
    ):
        data_inicio = date.today().isoformat()
        data_fim = date.today().isoformat()

    prospeccoes = repo.list_by_filters(
        status=req.filtro_status,
        nome=req.filtro_nome,
        segmento=req.segmento,
        cidade=req.cidade,
        estado=req.estado,
        telefone=req.telefone,
        data_inicio=data_inicio,
        data_fim=data_fim,
        mostrar_arquivados=req.mostrar_arquivados,
        tipo_telefone=req.tipo_telefone,
    )

    # Adicionar eventos em cada prospecção
    for p in prospeccoes:
        p["eventos"] = repo.get_eventos(p["id"])

    resumo = repo.get_summary(
        data_inicio,
        data_fim,
        req.mostrar_arquivados,
        status=req.filtro_status,
        nome=req.filtro_nome,
        segmento=req.segmento,
        cidade=req.cidade,
        estado=req.estado,
        telefone=req.telefone,
        tipo_telefone=req.tipo_telefone,
    )
    resumo_prospeccao = {
        "total": resumo.total,
        "por_status": list((resumo.por_status or {}).items()),
        "cidades": resumo.cidades or [],
    }

    return ProspecctionListViewResponse(
        prospeccoes=prospeccoes,
        resumo_prospeccao=resumo_prospeccao,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
