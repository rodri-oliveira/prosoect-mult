from __future__ import annotations

from dataclasses import dataclass

from domain.repositories.agendamentos_repository import AgendamentosRepository
from infrastructure.repositories.sqlite_agendamentos_repository import SqliteAgendamentosRepository


@dataclass(frozen=True)
class ListAgendamentosRequest:
    data: str
    mostrar_todos: bool = False


@dataclass(frozen=True)
class ListAgendamentosResponse:
    view_data: object


def list_agendamentos(req: ListAgendamentosRequest) -> ListAgendamentosResponse:
    return list_agendamentos_with_repo(req, SqliteAgendamentosRepository())


def list_agendamentos_with_repo(
    req: ListAgendamentosRequest,
    repo: AgendamentosRepository,
) -> ListAgendamentosResponse:
    # Rolar agendamentos pendentes antes de listar
    repo.rolar_agendamentos_pendentes(req.data)

    view_data = repo.get_view_data(req.data, req.mostrar_todos)
    return ListAgendamentosResponse(view_data=view_data)
