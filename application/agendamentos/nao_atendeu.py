from __future__ import annotations

from dataclasses import dataclass

from domain.repositories.agendamentos_repository import AgendamentosRepository
from infrastructure.repositories.sqlite_agendamentos_repository import SqliteAgendamentosRepository


@dataclass(frozen=True)
class NaoAtendeuRequest:
    prospeccao_id: int
    observacao: str


@dataclass(frozen=True)
class NaoAtendeuResponse:
    ok: bool


def nao_atendeu(req: NaoAtendeuRequest) -> NaoAtendeuResponse:
    return nao_atendeu_with_repo(req, SqliteAgendamentosRepository())


def nao_atendeu_with_repo(req: NaoAtendeuRequest, repo: AgendamentosRepository) -> NaoAtendeuResponse:
    ok = repo.registrar_tentativa_retorno(req.prospeccao_id, req.observacao)
    return NaoAtendeuResponse(ok=ok)
