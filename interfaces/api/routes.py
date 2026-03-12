from __future__ import annotations

from flask import Flask, jsonify, request

from application.maps.add_selected import AddMapsItemsRequest, add_maps_items_with_repo
from application.maps.place_details import GetMapsPlaceDetailsRequest, get_maps_place_details
from application.maps.search_results import SearchMapsResultsRequest, search_maps_results_with_repo
from application.prospeccao.create_draft import CreateProspecctionDraftRequest, create_prospeccao_draft_with_repo
from infrastructure.container import maps_existing_keys_repository, prospeccao_repository, prospeccao_temp_repository


def api_maps_resultados():
    query = (request.args.get("query") or "").strip()
    cidade = (request.args.get("cidade") or "").strip()
    estado = (request.args.get("estado") or "").strip()
    segmentos = request.args.getlist("segmentos")

    try:
        limit = int((request.args.get("limit") or "20").strip())
    except Exception:
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

    return jsonify(
        {
            "ok": True,
            "modo": res.modo,
            "query": res.query,
            "message": res.message,
            "existing_keys": res.existing_keys,
            "items": res.items,
        }
    )


def api_maps_adicionar():
    payload = request.get_json(silent=True) or {}
    items = payload.get("items") or []

    if not isinstance(items, list):
        return jsonify({"ok": False, "message": "Formato inválido."}), 400

    res = add_maps_items_with_repo(AddMapsItemsRequest(items=items), prospeccao_temp_repository())

    return jsonify(
        {
            "ok": True,
            "added_count": res.added_count,
            "duplicate_count": res.duplicate_count,
            "added_ids": res.added_ids,
            "duplicate_ids": res.duplicate_ids,
            "added_keys": res.added_keys,
            "duplicate_keys": res.duplicate_keys,
        }
    )


def api_maps_detalhe():
    payload = request.get_json(silent=True) or {}
    maps_url = (payload.get("maps_url") or "").strip()

    try:
        res = get_maps_place_details(GetMapsPlaceDetailsRequest(maps_url=maps_url))
        return jsonify({"ok": True, "item": res.item})
    except ValueError as e:
        return jsonify({"ok": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


def register_api_routes(app: Flask) -> None:
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


def api_rascunho_novo():
    from services.cnpj_service import is_valid_cnpj, normalize_cnpj

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
        if segmentos:
            data["segmento"] = ", ".join(segmentos)
        else:
            data["segmento"] = ""

    cnpj = (data.get("cnpj") or "").strip()
    if cnpj:
        cnpj_norm = normalize_cnpj(cnpj)
        if not is_valid_cnpj(cnpj_norm):
            data["cnpj"] = ""
        else:
            data["cnpj"] = cnpj_norm

    data["maps_place_id"] = (data.get("maps_place_id") or "").strip()
    data["maps_url"] = (data.get("maps_url") or "").strip()

    try:
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
            ),
            prospeccao_repository(),
        )
        prospeccao_id = res.prospeccao_id
        created = res.created
        key = (data.get("maps_place_id") or "").strip() or (data.get("maps_url") or "").strip()
        return jsonify(
            {
                "ok": True,
                "id": prospeccao_id,
                "created": bool(created),
                "key": key,
                "maps_place_id": data.get("maps_place_id") or "",
                "maps_url": data.get("maps_url") or "",
            }
        )
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500
