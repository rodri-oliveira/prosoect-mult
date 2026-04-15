from flask import Flask

from interfaces.web.leads_routes import lead_update_status


def test_lead_sem_interesse_redireciona_para_prospeccao(monkeypatch):
    app = Flask(__name__)
    app.add_url_rule("/leads", endpoint="leads_list", view_func=lambda: "leads")
    app.add_url_rule("/prospeccao", endpoint="prospeccao_view", view_func=lambda: "prospeccao")

    class FakeResult:
        devolvido_para_prospeccao = True

    monkeypatch.setattr(
        "interfaces.web.leads_routes.update_lead_status_with_repo",
        lambda req, repo: FakeResult(),
    )
    monkeypatch.setattr("interfaces.web.leads_routes.lead_repository", lambda: object())

    with app.test_request_context(
        "/leads/10/status",
        method="POST",
        data={"status": "Sem interesse", "next": "/leads/10"},
    ):
        response = lead_update_status(10)

    assert response.status_code == 302
    assert response.location.endswith("/prospeccao")


def test_lead_outro_status_mantem_redirecionamento_original(monkeypatch):
    app = Flask(__name__)
    app.add_url_rule("/leads", endpoint="leads_list", view_func=lambda: "leads")
    app.add_url_rule("/prospeccao", endpoint="prospeccao_view", view_func=lambda: "prospeccao")

    class FakeResult:
        devolvido_para_prospeccao = False

    monkeypatch.setattr(
        "interfaces.web.leads_routes.update_lead_status_with_repo",
        lambda req, repo: FakeResult(),
    )
    monkeypatch.setattr("interfaces.web.leads_routes.lead_repository", lambda: object())

    with app.test_request_context(
        "/leads/10/status",
        method="POST",
        data={"status": "Interessado", "next": "/leads/10"},
    ):
        response = lead_update_status(10)

    assert response.status_code == 302
    assert response.location.endswith("/leads/10")
