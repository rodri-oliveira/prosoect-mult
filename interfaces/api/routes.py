from __future__ import annotations

import logging
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
from infrastructure.container import maps_existing_keys_repository, prospeccao_repository, prospeccao_temp_repository

logger = logging.getLogger(__name__)


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
            ),
            prospeccao_repository(),
        )

        return jsonify({
            "ok": True,
            "id": res.prospeccao_id,
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
