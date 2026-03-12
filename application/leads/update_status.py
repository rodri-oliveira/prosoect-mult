from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.repositories.lead_repository import LeadRepository
from infrastructure.repositories.sqlite_lead_repository import SqliteLeadRepository


@dataclass(frozen=True)
class UpdateLeadStatusRequest:
    lead_id: int
    novo_status: str


@dataclass(frozen=True)
class UpdateLeadStatusResponse:
    ok: bool


def update_lead_status(req: UpdateLeadStatusRequest) -> UpdateLeadStatusResponse:
    return update_lead_status_with_repo(req, SqliteLeadRepository())


def update_lead_status_with_repo(req: UpdateLeadStatusRequest, repo: LeadRepository) -> UpdateLeadStatusResponse:
    ok = repo.update_status(req.lead_id, req.novo_status)
    return UpdateLeadStatusResponse(ok=ok)
