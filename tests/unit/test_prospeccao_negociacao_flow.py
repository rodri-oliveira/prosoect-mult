from flask import Flask

from interfaces.api import routes as api_routes
from interfaces.web import prospeccao_routes


class FakeProspeccaoRepository:
    def __init__(self):
        self.added = []
        self.converted = []
        self.updated = []

    def add(self, dados):
        self.added.append(dados)
        return 41, True

    def converter_para_lead(self, prospeccao_id):
        self.converted.append(prospeccao_id)
        return 77

    def update_status(self, *args, **kwargs):
        self.updated.append((args, kwargs))
        return True


def _app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.add_url_rule("/leads", endpoint="leads_list", view_func=lambda: "leads")
    app.add_url_rule("/prospeccao", endpoint="prospeccao_view", view_func=lambda: "prospeccao")
    app.add_url_rule("/agendamentos", endpoint="agendamentos_view", view_func=lambda: "agendamentos")
    return app


def test_maps_submission_with_negotiation_creates_lead_and_returns_redirect(monkeypatch):
    repo = FakeProspeccaoRepository()
    monkeypatch.setattr(api_routes, "prospeccao_repository", lambda: repo)
    app = _app()
    app.add_url_rule(
        "/api/prospeccao/rascunho/novo",
        endpoint="api_rascunho_novo",
        view_func=api_routes.api_rascunho_novo,
        methods=["POST"],
    )

    response = app.test_client().post(
        "/api/prospeccao/rascunho/novo",
        json={"nome_loja": "Loja de teste", "status_prospeccao": "Em negocia\u00e7\u00e3o"},
    )

    assert response.status_code == 200
    assert response.get_json()["redirect_to"] == "/leads"
    assert response.get_json()["lead_id"] == 77
    assert repo.converted == [41]


def test_form_submission_with_negotiation_creates_lead_and_redirects(monkeypatch):
    repo = FakeProspeccaoRepository()
    monkeypatch.setattr(prospeccao_routes, "prospeccao_repository", lambda: repo)
    app = _app()
    app.add_url_rule(
        "/prospeccao/rascunho/novo",
        endpoint="rascunho_novo",
        view_func=prospeccao_routes.rascunho_novo,
        methods=["POST"],
    )

    response = app.test_client().post(
        "/prospeccao/rascunho/novo",
        data={"nome_loja": "Loja de teste", "status_prospeccao": "EM NEGOCIACAO"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/leads")
    assert repo.converted == [41]


def test_status_change_with_negotiation_creates_lead_and_redirects(monkeypatch):
    repo = FakeProspeccaoRepository()
    monkeypatch.setattr(prospeccao_routes, "prospeccao_repository", lambda: repo)
    app = _app()
    app.add_url_rule(
        "/prospeccao/rascunho/<int:prospeccao_id>/status",
        endpoint="rascunho_status",
        view_func=prospeccao_routes.rascunho_status,
        methods=["POST"],
    )

    response = app.test_client().post(
        "/prospeccao/rascunho/41/status",
        data={"status": "Em negocia\u00e7\u00e3o"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/leads")
    assert repo.converted == [41]