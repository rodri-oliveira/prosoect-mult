import infrastructure.repositories.sqlite_lead_repository as lead_repo_module
from infrastructure.repositories.sqlite_lead_repository import SqliteLeadRepository


class FakeCursor:
    def __init__(self):
        self.executed: list[tuple[str, tuple | None]] = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return []


class FakeConnection:
    def __init__(self):
        self.row_factory = None
        self.cursor_instance = FakeCursor()

    def cursor(self):
        return self.cursor_instance

    def close(self):
        pass


def test_listagem_padrao_exclui_sem_interesse(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(lead_repo_module.sqlite3, "connect", lambda _: conn)

    repo = SqliteLeadRepository()
    repo.list_by_status()

    sql, params = conn.cursor_instance.executed[0]
    assert "WHERE COALESCE(l.status, '') <> 'Sem interesse'" in sql
    assert params is None


def test_filtro_explicito_por_status_permanece_disponivel(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(lead_repo_module.sqlite3, "connect", lambda _: conn)

    repo = SqliteLeadRepository()
    repo.list_by_status("Sem interesse")

    sql, params = conn.cursor_instance.executed[0]
    assert "WHERE l.status = ?" in sql
    assert params == ("Sem interesse",)
