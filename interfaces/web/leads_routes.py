"""Rotas web de Leads."""
from __future__ import annotations

from flask import Flask, redirect, render_template, request, url_for

from application.leads.add_contato import AddLeadContatoRequest, add_lead_contato_with_repo
from application.leads.create_lead import CreateLeadRequest, create_lead_with_repo
from application.leads.list_leads import ListLeadsRequest, list_leads_with_repo
from application.leads.update_status import UpdateLeadStatusRequest, update_lead_status_with_repo
from infrastructure.container import lead_repository


def leads_list():
    result = list_leads_with_repo(
        ListLeadsRequest(status=request.args.get("status")),
        lead_repository(),
    )
    return render_template("leads.html", leads=result.leads, active_page="leads")


def leads_create():
    segmentos = [s.strip() for s in request.form.getlist("segmento") if (s or "").strip()]
    result = create_lead_with_repo(
        CreateLeadRequest(
            nome_loja=(request.form.get("nome_loja") or "").strip(),
            cidade=(request.form.get("cidade") or "").strip() or None,
            estado=(request.form.get("estado") or "").strip() or None,
            cnpj=(request.form.get("cnpj") or "").strip() or None,
            telefone=(request.form.get("telefone") or "").strip() or None,
            whatsapp=(request.form.get("whatsapp") or "").strip() or None,
            site=(request.form.get("site") or "").strip() or None,
            email=(request.form.get("email") or "").strip() or None,
            endereco=(request.form.get("endereco") or "").strip() or None,
            responsavel=(request.form.get("responsavel") or "").strip() or None,
            segmentos=segmentos if segmentos else None,
            observacoes=(request.form.get("observacoes") or request.form.get("observacao") or "").strip() or None,
            maps_place_id=(request.form.get("maps_place_id") or "").strip() or None,
            maps_url=(request.form.get("maps_url") or "").strip() or None,
            status=(request.form.get("status") or "Novo Lead").strip() or "Novo Lead",
        ),
        lead_repository(),
    )
    next_url = request.form.get("next_url")
    if next_url:
        return redirect(next_url)
    return redirect(url_for("leads_list"))


def lead_detail(lead_id: int):
    result = lead_repository().get_by_id(lead_id)
    if not result:
        return redirect(url_for("leads_list"))
    lead, contatos, segmentos = result
    return render_template(
        "lead_detalhe.html",
        lead=lead,
        contatos=contatos,
        segmentos=segmentos,
        active_page="leads",
    )


def lead_update_status(lead_id: int):
    novo_status = request.form.get("status")
    if novo_status:
        update_lead_status_with_repo(
            UpdateLeadStatusRequest(lead_id=lead_id, novo_status=novo_status),
            lead_repository(),
        )
    return redirect(request.form.get("next", url_for("leads_list")))


def add_lead_contato(lead_id: int):
    result = add_lead_contato_with_repo(
        AddLeadContatoRequest(
            lead_id=lead_id,
            tipo_contato=(request.form.get("tipo_contato") or "").strip(),
            resultado=(request.form.get("resultado") or "").strip(),
            observacao=(request.form.get("observacao") or "").strip() or None,
            data_retorno=(request.form.get("data_retorno") or "").strip() or None,
            hora_retorno=(request.form.get("hora_retorno") or "").strip() or None,
        ),
        lead_repository(),
    )
    if not result.ok:
        return redirect(url_for(result.redirect_to, **result.redirect_kwargs))
    return redirect(request.form.get("next", url_for("leads_list")))


def register_leads_routes(app: Flask) -> None:
    app.add_url_rule("/leads", endpoint="leads_list", view_func=leads_list, methods=["GET"])
    app.add_url_rule(
        "/leads/novo",
        endpoint="leads_create",
        view_func=leads_create,
        methods=["POST"],
    )
    app.add_url_rule("/leads/<int:lead_id>", endpoint="lead_detail", view_func=lead_detail)
    app.add_url_rule(
        "/leads/<int:lead_id>/status",
        endpoint="lead_update_status",
        view_func=lead_update_status,
        methods=["POST"],
    )
    app.add_url_rule(
        "/leads/<int:lead_id>/contato",
        endpoint="add_lead_contato",
        view_func=add_lead_contato,
        methods=["POST"],
    )
