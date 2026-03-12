from __future__ import annotations

from dataclasses import dataclass

from domain.repositories.lead_repository import LeadRepository
from infrastructure.repositories.sqlite_lead_repository import SqliteLeadRepository


@dataclass(frozen=True)
class ListLeadsRequest:
    status: str | None = None


@dataclass(frozen=True)
class ListLeadsResponse:
    leads: list[dict]


def list_leads(req: ListLeadsRequest) -> ListLeadsResponse:
    return list_leads_with_repo(req, SqliteLeadRepository())


def list_leads_with_repo(req: ListLeadsRequest, repo: LeadRepository) -> ListLeadsResponse:
    leads = repo.list_by_status(req.status)
    return ListLeadsResponse(leads=leads)
