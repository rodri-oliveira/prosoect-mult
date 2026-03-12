from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.repositories.lead_repository import LeadRepository
from infrastructure.repositories.sqlite_lead_repository import SqliteLeadRepository


@dataclass(frozen=True)
class AddLeadContatoRequest:
    lead_id: int
    tipo_contato: str
    resultado: str
    observacao: str | None
    data_retorno: str | None
    hora_retorno: str | None


@dataclass(frozen=True)
class AddLeadContatoResult:
    ok: bool
    redirect_to: str
    redirect_kwargs: dict[str, Any]
    message: str | None = None


def add_lead_contato(req: AddLeadContatoRequest) -> AddLeadContatoResult:
    return add_lead_contato_with_repo(req, SqliteLeadRepository())


def add_lead_contato_with_repo(req: AddLeadContatoRequest, repo: LeadRepository) -> AddLeadContatoResult:
    resultado = req.resultado

    # Validações para resultados que exigem data/hora de retorno
    if resultado in ("Envio do portifólio", "Agendar retorno"):
        if not req.data_retorno:
            return AddLeadContatoResult(
                ok=False,
                redirect_to="lead_detail",
                redirect_kwargs={"lead_id": req.lead_id, "erro": "Informe a data de retorno para continuar."},
            )
        if not req.hora_retorno:
            return AddLeadContatoResult(
                ok=False,
                redirect_to="lead_detail",
                redirect_kwargs={"lead_id": req.lead_id, "erro": "Informe o horário de retorno."},
            )

    # Validação de segmento para envio do portfólio
    if resultado == "Envio do portifólio":
        row = repo.get_by_id(req.lead_id)
        if not row:
            return AddLeadContatoResult(
                ok=False,
                redirect_to="leads_list",
                redirect_kwargs={},
                message="Lead não encontrado.",
            )
        _, _, segmentos = row
        if not segmentos:
            return AddLeadContatoResult(
                ok=False,
                redirect_to="lead_detail",
                redirect_kwargs={"lead_id": req.lead_id, "erro": "Informe o segmento do lead antes de registrar o envio do portifólio."},
            )

    # Adicionar contato
    repo.add_contato(
        lead_id=req.lead_id,
        tipo_contato=req.tipo_contato,
        resultado=resultado,
        observacao=req.observacao,
        data_retorno=req.data_retorno,
        hora_retorno=req.hora_retorno,
    )

    return AddLeadContatoResult(
        ok=True,
        redirect_to="leads_list",
        redirect_kwargs={},
    )
