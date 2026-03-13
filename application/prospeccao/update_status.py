from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.repositories.prospeccao_repository import ProspeccaoRepository
from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository


@dataclass(frozen=True)
class UpdateProspecctionStatusRequest:
    prospeccao_id: int
    novo_status: str
    observacao: str | None
    data_retorno: str | None
    hora_retorno: str | None


@dataclass(frozen=True)
class UpdateProspecctionStatusResult:
    ok: bool
    redirect_to: str
    redirect_kwargs: dict[str, Any]
    message: str | None = None


def update_prospecction_status(req: UpdateProspecctionStatusRequest) -> UpdateProspecctionStatusResult:
    return update_prospecction_status_with_repo(req, SqliteProspeccaoRepository())


def update_prospecction_status_with_repo(
    req: UpdateProspecctionStatusRequest,
    repo: ProspeccaoRepository,
) -> UpdateProspecctionStatusResult:
    from services.cnpj_service import is_valid_cnpj, normalize_cnpj

    novo_status = req.novo_status
    observacao = req.observacao
    data_retorno = req.data_retorno
    hora_retorno = req.hora_retorno

    # Validação de regras de negócio
    if novo_status == "Pediu para retornar" and not data_retorno:
        return UpdateProspecctionStatusResult(
            ok=False,
            redirect_to="prospeccao_view",
            redirect_kwargs={"erro": "Informe a data de retorno."},
        )
    if novo_status == "Pediu para retornar" and data_retorno and not hora_retorno:
        return UpdateProspecctionStatusResult(
            ok=False,
            redirect_to="prospeccao_view",
            redirect_kwargs={"erro": "Informe o horário de retorno."},
        )

    # Atualização de status via repository
    repo.update_status(
        req.prospeccao_id,
        novo_status,
        observacao=observacao,
        data_retorno=data_retorno,
        hora_retorno=hora_retorno,
    )

    # Ações derivadas por status
    if novo_status == "Interessado":
        prospeccao = repo.get_by_id(req.prospeccao_id)

        if not prospeccao:
            return UpdateProspecctionStatusResult(
                ok=True,
                redirect_to="prospeccao_view",
                redirect_kwargs={},
            )

        if prospeccao.get("convertido_lead_id"):
            return UpdateProspecctionStatusResult(
                ok=True,
                redirect_to="lead_detail",
                redirect_kwargs={"lead_id": prospeccao["convertido_lead_id"]},
            )

        cnpj = normalize_cnpj((prospeccao.get("cnpj") or "").strip())
        if not cnpj or not is_valid_cnpj(cnpj):
            return UpdateProspecctionStatusResult(
                ok=False,
                redirect_to="prospeccao_view",
                redirect_kwargs={"erro": "Para converter em Lead, informe um CNPJ válido."},
            )

        lead_id = repo.converter_para_lead(req.prospeccao_id)
        if lead_id:
            return UpdateProspecctionStatusResult(
                ok=True,
                redirect_to="lead_detail",
                redirect_kwargs={"lead_id": lead_id},
            )

    if novo_status == "Descartado":
        repo.arquivar(req.prospeccao_id)

    return UpdateProspecctionStatusResult(
        ok=True,
        redirect_to="prospeccao_view",
        redirect_kwargs={},
    )
