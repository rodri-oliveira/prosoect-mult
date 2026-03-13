from __future__ import annotations

import os
from io import BytesIO

from flask import Flask, current_app, jsonify, redirect, render_template, request, send_file, url_for

from application.prospeccao.create_draft import CreateProspecctionDraftRequest, create_prospeccao_draft_with_repo
from application.prospeccao.list_view import ProspecctionListViewRequest, build_prospeccao_list_view_with_repo
from application.prospeccao.update_status import UpdateProspecctionStatusRequest, update_prospecction_status_with_repo
from application.agendamentos.list_view import ListAgendamentosRequest, list_agendamentos_with_repo
from application.agendamentos.nao_atendeu import NaoAtendeuRequest, nao_atendeu_with_repo
from application.agendamentos.registrar_tentativa import RegistrarTentativaRequest, registrar_tentativa_with_repo
from application.leads.add_contato import AddLeadContatoRequest, add_lead_contato_with_repo
from application.leads.create_lead import CreateLeadRequest, create_lead_with_repo
from application.leads.list_leads import ListLeadsRequest, list_leads_with_repo
from application.leads.update_status import UpdateLeadStatusRequest, update_lead_status_with_repo
from application.relatorios.relatorio_completo import RelatorioCompletoRequest, get_relatorio_completo_with_repo
from application.relatorios.relatorio_completo_pdf import RelatorioCompletoPdfRequest, build_relatorio_completo_pdf_with_repo
from application.relatorios.relatorio_prospeccao import RelatorioProspeccaoRequest, get_relatorio_prospeccao_with_repo
from application.relatorios.relatorio_prospeccao_pdf import (
    RelatorioProspeccaoPdfRequest,
    build_relatorio_prospeccao_pdf_with_repo,
)
from infrastructure.container import agendamentos_repository, lead_repository, prospeccao_repository, relatorio_repository

from services.cnpj_service import (
    consultar_cnpj_brasilapi,
    is_cnpj_ativo_brasilapi,
    is_valid_cnpj,
    normalize_cnpj,
)
from services.relatorio_pdf_service import (
    default_pdf_filename,
    save_pdf_copy,
)
from services.relatorio_service import get_resumo_hoje


def index():
    resumo = get_resumo_hoje()
    return render_template("dashboard.html", resumo=resumo, active_page="dashboard")


def prospeccao_view():
    filtro_status = request.args.get("status")
    segmento = request.args.get("segmento")
    cidade = request.args.get("cidade")
    estado = request.args.get("estado")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    mostrar_arquivados = request.args.get("arquivados") == "1"

    view = build_prospeccao_list_view_with_repo(
        ProspecctionListViewRequest(
            filtro_status=filtro_status,
            segmento=segmento,
            cidade=cidade,
            estado=estado,
            data_inicio=data_inicio,
            data_fim=data_fim,
            mostrar_arquivados=mostrar_arquivados,
        ),
        prospeccao_repository(),
    )

    return render_template(
        "prospeccao.html",
        prospeccoes=view.prospeccoes,
        resumo_prospeccao=view.resumo_prospeccao,
        active_page="prospeccao",
        filtro_status=filtro_status,
        segmento=segmento,
        cidade=cidade,
        estado=estado,
        data_inicio=view.data_inicio,
        data_fim=view.data_fim,
        mostrar_arquivados=mostrar_arquivados,
    )


def rascunho_novo():
    from services.cnpj_service import is_valid_cnpj, normalize_cnpj

    segmentos = [s.strip() for s in request.form.getlist("segmento") if (s or "").strip()]
    segmento_str = ", ".join(segmentos) if segmentos else None

    cnpj_raw = (request.form.get("cnpj") or "").strip()
    cnpj_norm = normalize_cnpj(cnpj_raw) if cnpj_raw else None
    cnpj_valid = cnpj_norm if (cnpj_norm and is_valid_cnpj(cnpj_norm)) else None

    status_prospeccao = (request.form.get("status_prospeccao") or "").strip()
    
    # Validar status obrigatório
    if not status_prospeccao:
        return redirect(url_for("prospeccao_view"))

    result = create_prospeccao_draft_with_repo(
        CreateProspecctionDraftRequest(
            nome_loja=(request.form.get("nome_loja") or "").strip(),
            cnpj=cnpj_valid,
            telefone=(request.form.get("telefone") or "").strip() or None,
            whatsapp=(request.form.get("whatsapp") or "").strip() or None,
            endereco=(request.form.get("endereco") or "").strip() or None,
            cidade=(request.form.get("cidade") or "").strip() or None,
            estado=(request.form.get("estado") or "").strip() or None,
            segmento=segmento_str,
            maps_place_id=(request.form.get("maps_place_id") or "").strip() or None,
            maps_url=(request.form.get("maps_url") or "").strip() or None,
            site=(request.form.get("site") or "").strip() or None,
            observacoes=(request.form.get("observacoes") or "").strip() or None,
            status_prospeccao=status_prospeccao,
            data_retorno=(request.form.get("data_retorno") or "").strip() or None,
            hora_retorno=(request.form.get("hora_retorno") or "").strip() or None,
        ),
        prospeccao_repository(),
    )

    next_url = request.form.get("next") or request.form.get("next_url")
    return redirect(next_url or url_for("prospeccao_view"))


def rascunho_status(prospeccao_id: int):
    novo_status = (request.form.get("status") or "").strip()
    observacao = (request.form.get("observacao") or "").strip() or None
    data_retorno = (request.form.get("data_retorno") or "").strip() or None
    hora_retorno = (request.form.get("hora_retorno") or "").strip() or None
    next_url = request.form.get("next")

    if not novo_status:
        return redirect(next_url or url_for("prospeccao_view"))

    result = update_prospecction_status_with_repo(
        UpdateProspecctionStatusRequest(
            prospeccao_id=prospeccao_id,
            novo_status=novo_status,
            observacao=observacao,
            data_retorno=data_retorno,
            hora_retorno=hora_retorno,
        ),
        prospeccao_repository(),
    )

    if next_url and result.ok and not result.redirect_kwargs:
        return redirect(next_url)
    return redirect(url_for(result.redirect_to, **result.redirect_kwargs))


def rascunho_converter(prospeccao_id: int):
    lead_id = prospeccao_repository().converter_para_lead(prospeccao_id)
    if lead_id:
        return redirect(url_for("lead_detail", lead_id=lead_id))
    return redirect(url_for("prospeccao_view"))


def rascunho_excluir(prospeccao_id: int):
    prospeccao_repository().arquivar(prospeccao_id)
    return redirect(url_for("prospeccao_view"))


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


def agendamentos_view():
    from datetime import date

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


def relatorio_prospeccao():
    from datetime import date, timedelta

    periodo = request.args.get("periodo", "hoje")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    hoje = date.today()
    if periodo == "hoje":
        data_inicio = hoje.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == "ontem":
        ontem = hoje - timedelta(days=1)
        data_inicio = ontem.isoformat()
        data_fim = ontem.isoformat()
    elif periodo == "semana":
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        data_inicio = inicio_semana.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == "mes":
        inicio_mes = hoje.replace(day=1)
        data_inicio = inicio_mes.isoformat()
        data_fim = hoje.isoformat()

    res = get_relatorio_prospeccao_with_repo(
        RelatorioProspeccaoRequest(data_inicio=data_inicio, data_fim=data_fim),
        relatorio_repository(),
    )

    return render_template(
        "relatorio_prospeccao.html",
        relatorio=res.relatorio,
        periodo=periodo,
        data_inicio=data_inicio,
        data_fim=data_fim,
        active_page="relatorio",
    )


def relatorio_prospeccao_pdf():
    from datetime import date, timedelta

    periodo = request.args.get("periodo", "hoje")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    hoje = date.today()
    if periodo == "hoje":
        data_inicio = hoje.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == "ontem":
        ontem = hoje - timedelta(days=1)
        data_inicio = ontem.isoformat()
        data_fim = ontem.isoformat()
    elif periodo == "semana":
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        data_inicio = inicio_semana.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == "mes":
        inicio_mes = hoje.replace(day=1)
        data_inicio = inicio_mes.isoformat()
        data_fim = hoje.isoformat()

    pdf_res = build_relatorio_prospeccao_pdf_with_repo(
        RelatorioProspeccaoPdfRequest(data_inicio=data_inicio, data_fim=data_fim),
        relatorio_repository(),
    )
    pdf_bytes = pdf_res.pdf_bytes
    filename = f"analise_prospeccao_{data_inicio}_a_{data_fim}_{date.today().strftime('%Y%m%d')}.pdf"

    export_dir = os.path.join(current_app.root_path, "exports", "relatorios")
    save_pdf_copy(pdf_bytes, export_dir, filename)

    return send_file(
        BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )


def relatorio_diario():
    from datetime import date, timedelta

    periodo = request.args.get("periodo", "hoje")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    hoje = date.today()
    if periodo == "hoje":
        data_inicio = hoje.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == "ontem":
        ontem = hoje - timedelta(days=1)
        data_inicio = ontem.isoformat()
        data_fim = ontem.isoformat()
    elif periodo == "semana":
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        data_inicio = inicio_semana.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == "mes":
        inicio_mes = hoje.replace(day=1)
        data_inicio = inicio_mes.isoformat()
        data_fim = hoje.isoformat()

    view = get_relatorio_completo_with_repo(
        RelatorioCompletoRequest(data_inicio=data_inicio, data_fim=data_fim),
        relatorio_repository(),
    )

    return render_template(
        "relatorio.html",
        relatorio=view.relatorio,
        periodo=periodo,
        data_inicio=view.data_inicio,
        data_fim=view.data_fim,
        active_page="relatorio",
    )


def relatorio_pdf():
    from datetime import date, timedelta

    periodo = request.args.get("periodo", "hoje")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    hoje = date.today()
    if periodo == "hoje":
        data_inicio = hoje.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == "ontem":
        ontem = hoje - timedelta(days=1)
        data_inicio = ontem.isoformat()
        data_fim = ontem.isoformat()
    elif periodo == "semana":
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        data_inicio = inicio_semana.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == "mes":
        inicio_mes = hoje.replace(day=1)
        data_inicio = inicio_mes.isoformat()
        data_fim = hoje.isoformat()

    pdf_view = build_relatorio_completo_pdf_with_repo(
        RelatorioCompletoPdfRequest(data_inicio=data_inicio, data_fim=data_fim),
        relatorio_repository(),
    )

    pdf_bytes = pdf_view.pdf_bytes
    filename = default_pdf_filename(pdf_view.data_inicio, pdf_view.data_fim)

    export_dir = os.path.join(current_app.root_path, "exports", "relatorios")
    save_pdf_copy(pdf_bytes, export_dir, filename)

    return send_file(
        BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )


def api_consultar_cnpj():
    cnpj_raw = request.args.get("cnpj", "")
    cnpj = normalize_cnpj(cnpj_raw)
    valid_local = is_valid_cnpj(cnpj)

    if not cnpj:
        return jsonify({"ok": False, "cnpj": None, "valid_local": False, "message": "CNPJ vazio"}), 400
    if not valid_local:
        return jsonify({"ok": False, "cnpj": cnpj, "valid_local": False, "message": "CNPJ inválido"}), 400

    data = consultar_cnpj_brasilapi(cnpj)
    if isinstance(data, dict) and data.get("error"):
        return (
            jsonify(
                {
                    "ok": False,
                    "cnpj": cnpj,
                    "valid_local": True,
                    "message": "Falha ao consultar",
                    "data": data,
                }
            ),
            502,
        )

    ativo = is_cnpj_ativo_brasilapi(data or {})
    situacao = ""
    if isinstance(data, dict):
        situacao = (data.get("descricao_situacao_cadastral") or data.get("situacao_cadastral") or "").strip()

    return jsonify({"ok": True, "cnpj": cnpj, "valid_local": True, "ativo": ativo, "situacao": situacao, "data": data})


def register_web_routes(app: Flask) -> None:
    app.add_url_rule("/", endpoint="index", view_func=index)
    app.add_url_rule("/prospeccao", endpoint="prospeccao_view", view_func=prospeccao_view)
    app.add_url_rule(
        "/prospeccao/rascunho/novo",
        endpoint="rascunho_novo",
        view_func=rascunho_novo,
        methods=["POST"],
    )
    app.add_url_rule(
        "/prospeccao/rascunho/<int:prospeccao_id>/status",
        endpoint="rascunho_status",
        view_func=rascunho_status,
        methods=["POST"],
    )
    app.add_url_rule(
        "/prospeccao/rascunho/<int:prospeccao_id>/converter",
        endpoint="rascunho_converter",
        view_func=rascunho_converter,
        methods=["POST"],
    )
    app.add_url_rule(
        "/prospeccao/rascunho/<int:prospeccao_id>/excluir",
        endpoint="rascunho_excluir",
        view_func=rascunho_excluir,
        methods=["POST"],
    )

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

    app.add_url_rule(
        "/api/cnpj/consultar",
        endpoint="api_consultar_cnpj",
        view_func=api_consultar_cnpj,
        methods=["GET"],
    )

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

    app.add_url_rule("/relatorio", endpoint="relatorio_diario", view_func=relatorio_diario)
    app.add_url_rule("/relatorio/pdf", endpoint="relatorio_pdf", view_func=relatorio_pdf)
    app.add_url_rule(
        "/relatorio/prospeccao",
        endpoint="relatorio_prospeccao",
        view_func=relatorio_prospeccao,
    )
    app.add_url_rule(
        "/relatorio/prospeccao/pdf",
        endpoint="relatorio_prospeccao_pdf",
        view_func=relatorio_prospeccao_pdf,
    )
