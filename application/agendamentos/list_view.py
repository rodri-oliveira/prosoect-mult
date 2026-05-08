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
    # NOTA: rolar_agendamentos_pendentes foi removido propositalmente.
    # Ele movia datas passadas para 'hoje', impedindo que aparecessem como
    # 'Retornos Atrasados'. As queries SQL já separam corretamente entre
    # data_retorno = hoje (Hoje), data_retorno < hoje (Atrasados) e
    # data_retorno > hoje (Próximos).
    view_data = repo.get_view_data(req.data, req.mostrar_todos)
    return ListAgendamentosResponse(view_data=view_data)
