"""Rotas web - Registro centralizado."""
from __future__ import annotations

from flask import Flask

from interfaces.web.prospeccao_routes import register_prospeccao_routes
from interfaces.web.leads_routes import register_leads_routes
from interfaces.web.agendamentos_routes import register_agendamentos_routes
from interfaces.web.relatorios_routes import register_relatorios_routes
from interfaces.web.cnpj_routes import register_cnpj_routes


def register_web_routes(app: Flask) -> None:
    """Registra todas as rotas web por contexto."""
    register_relatorios_routes(app)
    register_prospeccao_routes(app)
    register_leads_routes(app)
    register_agendamentos_routes(app)
    register_cnpj_routes(app)
