"""Rotas web de CNPJ."""
from __future__ import annotations

from flask import Flask, jsonify, request

from application.shared.cnpj_utils import is_valid_cnpj, normalize_cnpj
from infrastructure.container import cnpj_gateway


def api_consultar_cnpj():
    cnpj_raw = request.args.get("cnpj", "")
    cnpj = normalize_cnpj(cnpj_raw)
    valid_local = is_valid_cnpj(cnpj)

    if not cnpj:
        return jsonify({"ok": False, "cnpj": None, "valid_local": False, "message": "CNPJ vazio"}), 400
    if not valid_local:
        return jsonify({"ok": False, "cnpj": cnpj, "valid_local": False, "message": "CNPJ inválido"}), 400

    gateway = cnpj_gateway()
    info = gateway.consultar(cnpj)
    
    if not info:
        return jsonify({"ok": False, "cnpj": cnpj, "valid_local": True, "message": "Falha ao consultar"}), 502

    return jsonify({
        "ok": True,
        "cnpj": info.cnpj,
        "valid_local": True,
        "ativo": info.ativo,
        "situacao": info.situacao,
        "data": {
            "razao_social": info.razao_social,
            "nome_fantasia": info.nome_fantasia,
            "data_abertura": info.data_abertura,
            "endereco": info.endereco,
            "cidade": info.cidade,
            "estado": info.estado,
            "telefone": info.telefone,
            "email": info.email,
        }
    })


def register_cnpj_routes(app: Flask) -> None:
    app.add_url_rule(
        "/api/cnpj/consultar",
        endpoint="api_consultar_cnpj",
        view_func=api_consultar_cnpj,
        methods=["GET"],
    )
