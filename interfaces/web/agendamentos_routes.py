"""Rotas web de Agendamentos."""
from __future__ import annotations
from datetime import date

from flask import Flask, redirect, render_template, request, url_for

from application.agendamentos.list_view import ListAgendamentosRequest, list_agendamentos_with_repo
from application.agendamentos.nao_atendeu import NaoAtendeuRequest, nao_atendeu_with_repo
from application.agendamentos.registrar_tentativa import RegistrarTentativaRequest, registrar_tentativa_with_repo
from infrastructure.container import agendamentos_repository, prospeccao_repository


def agendamentos_view():
    data_filtro = request.args.get("data")
    mostrar_todos = request.args.get("todos") == "1"

    hoje = date.today().isoformat()

    result = list_agendamentos_with_repo(
        ListAgendamentosRequest(data=hoje, mostrar_todos=mostrar_todos),
        agendamentos_repository(),
    )

    view = result.view_data

    return render_template(
        "agendamentos.html",
        retornos_hoje=view.retornos_hoje,
        retornos_atrasados=view.retornos_atrasados,
        retornos_futuros=view.retornos_futuros,
        retornos_leads_hoje=view.retornos_leads_hoje,
        retornos_leads_atrasados=view.retornos_leads_atrasados,
        retornos_leads_futuros=view.retornos_leads_futuros,
        hoje=view.hoje,
        mostrar_todos=mostrar_todos,
        total_hoje=view.total_hoje,
        total_atrasados=view.total_atrasados,
        total_futuros=view.total_futuros,
        total_leads_hoje=view.total_leads_hoje,
        total_leads_atrasados=view.total_leads_atrasados,
        total_leads_futuros=view.total_leads_futuros,
        data_filtro=data_filtro,
        active_page="agendamentos",
    )


def agendamento_nao_atendeu(prospeccao_id: int):
    nao_atendeu_with_repo(
        NaoAtendeuRequest(
            prospeccao_id=prospeccao_id,
            observacao=request.form.get("observacao", ""),
        ),
        agendamentos_repository(),
    )
    return redirect(request.form.get("next", url_for("agendamentos_view")))


def agendamento_registrar_tentativa(prospeccao_id: int):
    segmentos = [s.strip() for s in request.form.getlist("segmento") if (s or "").strip()]
    segmento = ", ".join(segmentos) if segmentos else None

    result = registrar_tentativa_with_repo(
        RegistrarTentativaRequest(
            prospeccao_id=prospeccao_id,
            resultado=(request.form.get("resultado") or "").strip(),
            observacao=(request.form.get("observacao") or "").strip() or None,
            data_retorno=(request.form.get("data_retorno") or "").strip() or None,
            hora_retorno=(request.form.get("hora_retorno") or "").strip() or None,
            segmento=segmento,
            pos_acao=(request.form.get("pos_acao") or "").strip() or None,
        ),
        agendamentos_repository(),
        prospeccao_repository(),
    )

    if not result.ok:
        return redirect(url_for(result.redirect_to, **result.redirect_kwargs))
    return redirect(request.form.get("next", url_for("agendamentos_view")))


def register_agendamentos_routes(app: Flask) -> None:
    app.add_url_rule("/agendamentos", endpoint="agendamentos_view", view_func=agendamentos_view)
    app.add_url_rule(
        "/agendamentos/<int:prospeccao_id>/nao-atendeu",
        endpoint="agendamento_nao_atendeu",
        view_func=agendamento_nao_atendeu,
        methods=["POST"],
    )
    app.add_url_rule(
        "/agendamentos/<int:prospeccao_id>/registrar-tentativa",
        endpoint="agendamento_registrar_tentativa",
        view_func=agendamento_registrar_tentativa,
        methods=["POST"],
    )
