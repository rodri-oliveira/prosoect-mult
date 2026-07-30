from __future__ import annotations

import logging
import unicodedata
from datetime import date
from flask import Flask, jsonify, request

from application.maps.add_selected import AddMapsItemsRequest, add_maps_items_with_repo
from application.maps.place_details import GetMapsPlaceDetailsRequest, get_maps_place_details
from application.maps.search_results import (
    SearchMapsResultsRequest, 
    search_maps_results_with_repo,
    generate_queries_for_segments,
)
from application.prospeccao.create_draft import CreateProspecctionDraftRequest, create_prospeccao_draft_with_repo
from application.shared.cnpj_utils import is_valid_cnpj, normalize_cnpj
from infrastructure.container import (
    agendamentos_repository,
    maps_existing_keys_repository,
    prospeccao_repository,
    prospeccao_temp_repository,
)

logger = logging.getLogger(__name__)

def _is_em_negociacao(status: str | None) -> bool:
    normalized = unicodedata.normalize("NFD", (status or "").strip()).encode("ascii", "ignore").decode().casefold()
    return normalized == "em negociacao"


def api_maps_queries():
    """API: Gerar queries para segmentos (sem executar scraper).
    
    Usado pelo botão Buscar para sincronizar com o Resultado Beta.
    """
    try:
        cidade = (request.args.get("cidade") or "").strip()
        estado = (request.args.get("estado") or "").strip()
        segmentos = request.args.getlist("segmentos")
        extra = (request.args.get("extra") or "").strip()

        res = generate_queries_for_segments(
            segmentos=segmentos,
            cidade=cidade,
            estado=estado,
            extra=extra,
        )

        return jsonify({
            "ok": res.ok,
            "queries": res.queries,
            "primary_query": res.primary_query,
            "total_queries": res.total_queries,
        })
    except Exception as e:
        logger.error(f"Erro em api_maps_queries: {e}", exc_info=True)
        return jsonify({"ok": False, "message": "Erro ao gerar queries"}), 500


def api_maps_resultados():
    """API: Buscar resultados do Maps."""
    try:
        query = (request.args.get("query") or "").strip()
        cidade = (request.args.get("cidade") or "").strip()
        estado = (request.args.get("estado") or "").strip()
        segmentos = request.args.getlist("segmentos")

        try:
            limit = int((request.args.get("limit") or "20").strip())
        except (ValueError, TypeError):
            limit = 20

        res = search_maps_results_with_repo(
            SearchMapsResultsRequest(
                query=query,
                cidade=cidade,
                estado=estado,
                segmentos=segmentos,
                limit=limit,
            ),
            maps_existing_keys_repository(),
        )

        return jsonify({
            "ok": True,
            "modo": res.modo,
            "query": res.query,
            "message": res.message,
            "existing_keys": res.existing_keys,
            "items": res.items,
            "executed_queries": res.executed_queries,
            "query_stats": res.query_stats,
            "merged_before_dedupe": res.merged_before_dedupe,
            "merged_after_dedupe": res.merged_after_dedupe,
        })
    except Exception as e:
        logger.error(f"Erro em api_maps_resultados: {e}", exc_info=True)
        return jsonify({"ok": False, "message": "Erro ao buscar resultados"}), 500


def api_maps_adicionar():
    """API: Adicionar itens do Maps à lista temporária."""
    try:
        payload = request.get_json(silent=True) or {}
        items = payload.get("items") or []

        if not isinstance(items, list):
            return jsonify({"ok": False, "message": "Formato inválido. Esperado lista de itens."}), 400

        if len(items) == 0:
            return jsonify({"ok": False, "message": "Nenhum item fornecido."}), 400

        res = add_maps_items_with_repo(AddMapsItemsRequest(items=items), prospeccao_temp_repository())

        return jsonify({
            "ok": True,
            "added_count": res.added_count,
            "duplicate_count": res.duplicate_count,
            "added_ids": res.added_ids,
            "duplicate_ids": res.duplicate_ids,
            "added_keys": res.added_keys,
            "duplicate_keys": res.duplicate_keys,
        })
    except Exception as e:
        logger.error(f"Erro em api_maps_adicionar: {e}", exc_info=True)
        return jsonify({"ok": False, "message": "Erro ao adicionar itens"}), 500


def api_maps_detalhe():
    """API: Obter detalhes de um local do Maps."""
    try:
        payload = request.get_json(silent=True) or {}
        maps_url = (payload.get("maps_url") or "").strip()

        if not maps_url:
            return jsonify({"ok": False, "message": "URL do Maps é obrigatória."}), 400

        res = get_maps_place_details(GetMapsPlaceDetailsRequest(maps_url=maps_url))
        return jsonify({"ok": True, "item": res.item})
    except ValueError as e:
        logger.warning(f"Validação em api_maps_detalhe: {e}")
        return jsonify({"ok": False, "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro em api_maps_detalhe: {e}", exc_info=True)
        return jsonify({"ok": False, "message": "Erro ao obter detalhes"}), 500


def api_rascunho_novo():
    """API: Criar novo rascunho de prospecção."""
    try:
        payload = request.get_json(silent=True)
        if isinstance(payload, dict):
            data = dict(payload)
            segmentos = data.get("segmento")
            if isinstance(segmentos, list):
                segmentos = [s.strip() for s in segmentos if (s or "").strip()]
                data["segmento"] = ", ".join(segmentos) if segmentos else ""
            else:
                data["segmento"] = (segmentos or "").strip()
        else:
            data = dict(request.form)
            segmentos = [s.strip() for s in request.form.getlist("segmento") if (s or "").strip()]
            data["segmento"] = ", ".join(segmentos) if segmentos else ""

        # Validar e normalizar CNPJ
        cnpj = (data.get("cnpj") or "").strip()
        if cnpj:
            cnpj_norm = normalize_cnpj(cnpj)
            if not is_valid_cnpj(cnpj_norm):
                data["cnpj"] = ""
            else:
                data["cnpj"] = cnpj_norm

        data["maps_place_id"] = (data.get("maps_place_id") or "").strip()
        data["maps_url"] = (data.get("maps_url") or "").strip()
        data["site"] = (data.get("site") or data.get("website") or "").strip()

        repo = prospeccao_repository()
        res = create_prospeccao_draft_with_repo(
            CreateProspecctionDraftRequest(
                nome_loja=(data.get("nome_loja") or "").strip(),
                cnpj=(data.get("cnpj") or "").strip() or None,
                telefone=(data.get("telefone") or "").strip() or None,
                whatsapp=(data.get("whatsapp") or "").strip() or None,
                endereco=(data.get("endereco") or "").strip() or None,
                cidade=(data.get("cidade") or "").strip() or None,
                estado=(data.get("estado") or "").strip() or None,
                segmento=(data.get("segmento") or "").strip() or None,
                maps_place_id=(data.get("maps_place_id") or "").strip() or None,
                maps_url=(data.get("maps_url") or "").strip() or None,
                site=(data.get("site") or "").strip() or None,
                observacoes=(data.get("observacoes") or "").strip() or None,
                status_prospeccao=(data.get("status_prospeccao") or "").strip() or None,
                data_retorno=(data.get("data_retorno") or "").strip() or None,
                hora_retorno=(data.get("hora_retorno") or "").strip() or None,
                responsavel=(data.get("responsavel") or "").strip() or None,
                email=(data.get("email") or "").strip() or None,
            ),
            repo,
        )

        lead_id = None
        if _is_em_negociacao(data.get("status_prospeccao")):
            lead_id = repo.converter_para_lead(res.prospeccao_id)
            if not lead_id:
                raise ValueError("Nao foi possivel converter o contato em Lead.")

        return jsonify({
            "ok": True,
            "id": res.prospeccao_id,
            "lead_id": lead_id,
            "redirect_to": "/leads" if lead_id else None,
            "created": bool(res.created),
            "key": (data.get("maps_place_id") or data.get("maps_url") or "").strip(),
            "maps_place_id": data.get("maps_place_id") or "",
            "maps_url": data.get("maps_url") or "",
        })
    except ValueError as e:
        logger.warning(f"Validação em api_rascunho_novo: {e}")
        return jsonify({"ok": False, "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro em api_rascunho_novo: {e}", exc_info=True)
        return jsonify({"ok": False, "message": "Erro ao criar rascunho"}), 500


def api_prospeccao_eventos(prospeccao_id: int):
    """API: Obter histórico de eventos de uma prospecção."""
    try:
        eventos = prospeccao_repository().get_eventos(prospeccao_id)
        return jsonify({"ok": True, "eventos": eventos})
    except Exception as e:
        logger.error(f"Erro em api_prospeccao_eventos: {e}", exc_info=True)
        return jsonify({"ok": False, "message": "Erro ao buscar histórico"}), 500


def api_retornos_stats():
    """API: Obter estatísticas de agendamento (hoje, atrasados, urgentes)."""
    try:
        stats = prospeccao_repository().get_retornos_stats()
        view = agendamentos_repository().get_view_data(date.today().isoformat(), mostrar_todos=False)

        # Badge lateral consolidado: prospeccao + leads.
        stats["hoje"] = int(stats.get("hoje", 0)) + int(view.total_leads_hoje or 0)
        stats["atrasados"] = int(stats.get("atrasados", 0)) + int(view.total_leads_atrasados or 0)
        stats["total"] = int(stats.get("hoje", 0)) + int(stats.get("atrasados", 0))
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Erro em api_retornos_stats: {e}", exc_info=True)
        return jsonify({"hoje": 0, "atrasados": 0, "urgentes": 0, "total": 0}), 500


def api_leads_historico(lead_id: int):
    """API: Obter histórico de contatos de um lead."""
    try:
        from infrastructure.container import lead_repository
        res = lead_repository().get_by_id(lead_id)
        if not res:
            return jsonify({"ok": False, "message": "Lead não encontrado"}), 404
        _, contatos, _ = res
        return jsonify({"ok": True, "historico": contatos})
    except Exception as e:
        logger.error(f"Erro em api_leads_historico: {e}", exc_info=True)
        return jsonify({"ok": False, "message": "Erro ao buscar histórico"}), 500


def register_api_routes(app: Flask) -> None:
    """Registra todas as rotas de API."""
    app.add_url_rule(
        "/api/maps/queries",
        endpoint="api_maps_queries",
        view_func=api_maps_queries,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/maps/resultados",
        endpoint="api_maps_resultados",
        view_func=api_maps_resultados,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/maps/adicionar",
        endpoint="api_maps_adicionar",
        view_func=api_maps_adicionar,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/maps/detalhe",
        endpoint="api_maps_detalhe",
        view_func=api_maps_detalhe,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/prospeccao/rascunho/novo",
        endpoint="api_rascunho_novo",
        view_func=api_rascunho_novo,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/prospeccao/<int:prospeccao_id>/eventos",
        endpoint="api_prospeccao_eventos",
        view_func=api_prospeccao_eventos,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/leads/<int:lead_id>/historico",
        endpoint="api_leads_historico",
        view_func=api_leads_historico,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/retornos/stats",
        endpoint="api_retornos_stats",
        view_func=api_retornos_stats,
        methods=["GET"],
    )
