from __future__ import annotations

from dataclasses import dataclass

from domain.repositories.lead_repository import LeadRepository
from infrastructure.repositories.sqlite_lead_repository import SqliteLeadRepository


@dataclass(frozen=True)
class CreateLeadRequest:
    nome_loja: str
    cidade: str | None
    estado: str | None
    cnpj: str | None
    telefone: str | None
    whatsapp: str | None
    site: str | None
    email: str | None
    endereco: str | None
    responsavel: str | None
    segmentos: list[str] | None
    observacoes: str | None
    maps_place_id: str | None
    maps_url: str | None
    status: str = "Novo Lead"


@dataclass(frozen=True)
class CreateLeadResponse:
    lead_id: int


def create_lead(req: CreateLeadRequest) -> CreateLeadResponse:
    return create_lead_with_repo(req, SqliteLeadRepository())


def create_lead_with_repo(req: CreateLeadRequest, repo: LeadRepository) -> CreateLeadResponse:
    data = {
        "nome_loja": req.nome_loja,
        "cidade": req.cidade,
        "estado": req.estado,
        "cnpj": req.cnpj,
        "telefone": req.telefone,
        "whatsapp": req.whatsapp,
        "site": req.site,
        "email": req.email,
        "endereco": req.endereco,
        "responsavel": req.responsavel,
        "segmentos": req.segmentos,
        "observacoes": req.observacoes,
        "maps_place_id": req.maps_place_id,
        "maps_url": req.maps_url,
        "status": req.status,
    }
    lead_id = repo.create(data)
    return CreateLeadResponse(lead_id=lead_id)
