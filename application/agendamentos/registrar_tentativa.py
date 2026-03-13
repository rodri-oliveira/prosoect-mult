from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.repositories.agendamentos_repository import AgendamentosRepository
from domain.repositories.prospeccao_repository import ProspeccaoRepository
from infrastructure.repositories.sqlite_agendamentos_repository import SqliteAgendamentosRepository
from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository


@dataclass(frozen=True)
class RegistrarTentativaRequest:
    prospeccao_id: int
    resultado: str
    observacao: str | None
    data_retorno: str | None
    hora_retorno: str | None
    segmento: str | None
    pos_acao: str | None  # "converter" ou None


@dataclass(frozen=True)
class RegistrarTentativaResult:
    ok: bool
    redirect_to: str
    redirect_kwargs: dict[str, Any]
    message: str | None = None


def registrar_tentativa(req: RegistrarTentativaRequest) -> RegistrarTentativaResult:
    return registrar_tentativa_with_repo(
        req,
        SqliteAgendamentosRepository(),
        SqliteProspeccaoRepository(),
    )


def registrar_tentativa_with_repo(
    req: RegistrarTentativaRequest,
    agendamentos_repo: AgendamentosRepository,
    prospeccao_repo: ProspeccaoRepository,
) -> RegistrarTentativaResult:
    resultado = req.resultado

    # Validações
    if not resultado:
        return RegistrarTentativaResult(
            ok=False,
            redirect_to="agendamentos_view",
            redirect_kwargs={"erro": "Selecione o resultado da tentativa."},
        )

    resultados_tentativa = ("Não atendeu", "Caixa postal", "Sem contato")
    resultados_proximo_passo = ("Em negociação", "Agendar retorno", "Pediu preço")

    if resultado in resultados_proximo_passo and not req.observacao:
        return RegistrarTentativaResult(
            ok=False,
            redirect_to="agendamentos_view",
            redirect_kwargs={"erro": "Observação obrigatória para registrar o próximo passo."},
        )

    if resultado in ("Em negociação", "Agendar retorno") and not req.data_retorno:
        return RegistrarTentativaResult(
            ok=False,
            redirect_to="agendamentos_view",
            redirect_kwargs={"erro": "Informe a data de retorno para continuar."},
        )
    if resultado in ("Em negociação", "Agendar retorno") and req.data_retorno and not req.hora_retorno:
        return RegistrarTentativaResult(
            ok=False,
            redirect_to="agendamentos_view",
            redirect_kwargs={"erro": "Informe o horário de retorno para continuar."},
        )

    # Validação de segmento para início de negociação
    if resultado == "Em negociação":
        if not req.segmento:
            prospeccao = prospeccao_repo.get_by_id(req.prospeccao_id)
            if not prospeccao or not prospeccao.get("segmento"):
                return RegistrarTentativaResult(
                    ok=False,
                    redirect_to="agendamentos_view",
                    redirect_kwargs={"erro": "Informe o segmento antes de registrar início de negociação."},
                )
        else:
            agendamentos_repo.update_segmento(req.prospeccao_id, req.segmento)

    # Processar resultado
    if resultado in resultados_tentativa:
        detalhe = resultado
        if req.observacao:
            detalhe = f"{resultado} | {req.observacao}"
        agendamentos_repo.registrar_tentativa_retorno(req.prospeccao_id, detalhe)
        return RegistrarTentativaResult(
            ok=True,
            redirect_to="agendamentos_view",
            redirect_kwargs={},
        )

    if resultado == "Descartado":
        prospeccao_repo.update_status(req.prospeccao_id, "Descartado", observacao=req.observacao)
        agendamentos_repo.registrar_resultado_retorno(req.prospeccao_id, "Descartado", observacao=req.observacao)
        prospeccao_repo.arquivar(req.prospeccao_id)
        return RegistrarTentativaResult(
            ok=True,
            redirect_to="agendamentos_view",
            redirect_kwargs={},
        )

    if resultado == "Interessado":
        prospeccao_repo.update_status(req.prospeccao_id, "Interessado", observacao=req.observacao)
        agendamentos_repo.registrar_resultado_retorno(req.prospeccao_id, "Interessado", observacao=req.observacao)
        if req.pos_acao == "converter":
            lead_id = prospeccao_repo.converter_para_lead(req.prospeccao_id)
            if lead_id:
                return RegistrarTentativaResult(
                    ok=True,
                    redirect_to="lead_detail",
                    redirect_kwargs={"lead_id": lead_id},
                )
        return RegistrarTentativaResult(
            ok=True,
            redirect_to="agendamentos_view",
            redirect_kwargs={},
        )

    if resultado in ("Em negociação", "Agendar retorno"):
        prospeccao_repo.update_status(
            req.prospeccao_id,
            "Pediu para retornar",
            observacao=req.observacao,
            data_retorno=req.data_retorno,
            hora_retorno=req.hora_retorno,
        )
        agendamentos_repo.registrar_resultado_retorno(req.prospeccao_id, resultado, observacao=req.observacao)
        return RegistrarTentativaResult(
            ok=True,
            redirect_to="agendamentos_view",
            redirect_kwargs={},
        )

    if resultado == "Pediu preço":
        agendamentos_repo.registrar_resultado_retorno(req.prospeccao_id, "Pediu preço", observacao=req.observacao)
        return RegistrarTentativaResult(
            ok=True,
            redirect_to="agendamentos_view",
            redirect_kwargs={},
        )

    return RegistrarTentativaResult(
        ok=False,
        redirect_to="agendamentos_view",
        redirect_kwargs={"erro": "Resultado inválido."},
    )
