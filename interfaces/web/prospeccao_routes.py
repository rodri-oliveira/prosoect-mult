"""Rotas web de Prospecção."""
from __future__ import annotations

from flask import Flask, redirect, render_template, request, url_for

from application.prospeccao.create_draft import CreateProspecctionDraftRequest, create_prospeccao_draft_with_repo
from application.prospeccao.list_view import ProspecctionListViewRequest, build_prospeccao_list_view_with_repo
from application.prospeccao.update_status import UpdateProspecctionStatusRequest, update_prospecction_status_with_repo
from application.shared.cnpj_utils import is_valid_cnpj, normalize_cnpj
from infrastructure.container import prospeccao_repository


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
    segmentos = [s.strip() for s in request.form.getlist("segmento") if (s or "").strip()]
    segmento_str = ", ".join(segmentos) if segmentos else None

    cnpj_raw = (request.form.get("cnpj") or "").strip()
    cnpj_norm = normalize_cnpj(cnpj_raw) if cnpj_raw else None
    cnpj_valid = cnpj_norm if (cnpj_norm and is_valid_cnpj(cnpj_norm)) else None

    status_prospeccao = (request.form.get("status_prospeccao") or "").strip()
    
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


def rascunho_observacao(prospeccao_id: int):
    observacao = (request.form.get("observacao") or "").strip() or None
    repo = prospeccao_repository()
    repo.update_observacao(prospeccao_id, observacao)
    return redirect(url_for("prospeccao_view"))


def register_prospeccao_routes(app: Flask) -> None:
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
    app.add_url_rule(
        "/prospeccao/rascunho/<int:prospeccao_id>/observacao",
        endpoint="rascunho_observacao",
        view_func=rascunho_observacao,
        methods=["POST"],
    )
