"""Rotas web de Relatórios."""
from __future__ import annotations
import os
from datetime import date, timedelta
from io import BytesIO

from flask import Flask, current_app, render_template, request, send_file

from application.relatorios.dashboard_resumo import get_dashboard_resumo_with_repo
from application.relatorios.relatorio_completo import RelatorioCompletoRequest, get_relatorio_completo_with_repo
from application.relatorios.relatorio_completo_pdf import RelatorioCompletoPdfRequest, build_relatorio_completo_pdf_with_repo
from application.relatorios.relatorio_prospeccao import RelatorioProspeccaoRequest, get_relatorio_prospeccao_with_repo
from application.relatorios.relatorio_prospeccao_pdf import RelatorioProspeccaoPdfRequest, build_relatorio_prospeccao_pdf_with_repo
from infrastructure.container import relatorio_repository
from infrastructure.reporting import default_pdf_filename, save_pdf_copy


def index():
    resumo = get_dashboard_resumo_with_repo(relatorio_repository())
    return render_template("dashboard.html", resumo=resumo, active_page="dashboard")


def _resolve_periodo(periodo: str) -> tuple[str, str]:
    """Resolve período para datas início/fim."""
    hoje = date.today()
    if periodo == "hoje":
        return hoje.isoformat(), hoje.isoformat()
    elif periodo == "ontem":
        ontem = hoje - timedelta(days=1)
        return ontem.isoformat(), ontem.isoformat()
    elif periodo == "semana":
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        return inicio_semana.isoformat(), hoje.isoformat()
    elif periodo == "mes":
        inicio_mes = hoje.replace(day=1)
        return inicio_mes.isoformat(), hoje.isoformat()
    return hoje.isoformat(), hoje.isoformat()


def relatorio_prospeccao():
    periodo = request.args.get("periodo", "hoje")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    if not data_inicio or not data_fim:
        data_inicio, data_fim = _resolve_periodo(periodo)

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
    periodo = request.args.get("periodo", "hoje")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    if not data_inicio or not data_fim:
        data_inicio, data_fim = _resolve_periodo(periodo)

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
    periodo = request.args.get("periodo", "hoje")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    if not data_inicio or not data_fim:
        data_inicio, data_fim = _resolve_periodo(periodo)

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
    periodo = request.args.get("periodo", "hoje")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    if not data_inicio or not data_fim:
        data_inicio, data_fim = _resolve_periodo(periodo)

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


def register_relatorios_routes(app: Flask) -> None:
    app.add_url_rule("/", endpoint="index", view_func=index)
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
