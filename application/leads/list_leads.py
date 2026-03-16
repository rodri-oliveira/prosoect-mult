from __future__ import annotations

from dataclasses import dataclass

from domain.repositories.lead_repository import LeadRepository
from infrastructure.repositories.sqlite_lead_repository import SqliteLeadRepository
from application.shared.dto import LeadItem


@dataclass(frozen=True)
class ListLeadsRequest:
    status: str | None = None


@dataclass(frozen=True)
class ListLeadsResponse:
    leads: list[LeadItem]


def _to_lead_item(row: dict) -> LeadItem:
    """Converte dict do repository para LeadItem DTO."""
    created_at = row.get("created_at") or row.get("data_criacao")
    return LeadItem(
        id=row.get("id", 0),
        nome_loja=row.get("nome_loja") or "",
        cnpj=row.get("cnpj"),
        telefone=row.get("telefone"),
        whatsapp=row.get("whatsapp"),
        cidade=row.get("cidade"),
        estado=row.get("estado"),
        segmentos=row.get("segmentos") or row.get("segmento"),
        status=row.get("status"),
        resultado=row.get("resultado") or row.get("ultimo_resultado"),
        site=row.get("site"),
        created_at=created_at,
        ultimo_tipo_contato=row.get("ultimo_tipo_contato"),
        ultimo_resultado=row.get("ultimo_resultado"),
        ultimo_observacao=row.get("ultimo_observacao"),
        ultimo_contato_data=row.get("ultimo_contato_data"),
        data_criacao=created_at,
    )


def list_leads(req: ListLeadsRequest) -> ListLeadsResponse:
    return list_leads_with_repo(req, SqliteLeadRepository())


def list_leads_with_repo(req: ListLeadsRequest, repo: LeadRepository) -> ListLeadsResponse:
    rows = repo.list_by_status(req.status)
    leads = [_to_lead_item(row) for row in rows]
    return ListLeadsResponse(leads=leads)
