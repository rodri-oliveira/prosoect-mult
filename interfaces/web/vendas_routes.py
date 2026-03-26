from __future__ import annotations
from datetime import date
from flask import Flask, redirect, render_template, request, url_for
from domain.repositories.pedido_repository import Pedido, PedidoItem
from infrastructure.container import pedido_repository, lead_repository

def vendas_list_view():
    repo = pedido_repository()
    clientes = repo.list_all_active_clients()
    total_carteira = sum(c['faturado_total'] for c in clientes)
    
    return render_template(
        "vendas.html",
        clientes=clientes,
        total_carteira=total_carteira,
        active_page="vendas"
    )

def vendas_registrar_view(lead_id: int):
    l_repo = lead_repository()
    lead = l_repo.get_by_id(lead_id)
    if not lead:
        return redirect(url_for('leads_list'))
        
    return render_template(
        "vendas_registrar.html",
        lead=lead,
        hoje=date.today().isoformat(),
        active_page="vendas"
    )

def vendas_registrar_action():
    lead_id = int(request.form.get('lead_id'))
    data_pedido = request.form.get('data_pedido')
    numero_pedido = request.form.get('numero_pedido')
    proximo_contato = request.form.get('data_proximo_contato') or None
    obs = request.form.get('observacoes') or None

    # Processar itens
    familias = request.form.getlist('familias[]')
    codigos = request.form.getlist('codigos[]')
    descricoes = request.form.getlist('descricoes[]')
    quantidades = request.form.getlist('quantidades[]')
    precos_unt = request.form.getlist('precos_unt[]')

    itens = []
    valor_total = 0.0
    for i in range(len(descricoes)):
        if not descricoes[i].strip():
            continue
            
        qtd = int(quantidades[i])
        unt = float(precos_unt[i])
        total_item = qtd * unt
        valor_total += total_item
        
        itens.append(PedidoItem(
            familia=familias[i],
            codigo_produto=codigos[i],
            descricao=descricoes[i],
            quantidade=qtd,
            preco_unitario=unt,
            preco_total=total_item
        ))

    pedido = Pedido(
        id=None,
        lead_id=lead_id,
        data_pedido=data_pedido,
        numero_pedido=numero_pedido,
        valor_total=valor_total,
        status_faturamento="Faturado",
        data_proximo_contato=proximo_contato,
        observacoes=obs,
        itens=itens
    )

    repo = pedido_repository()
    repo.registrar(pedido)
    
    return redirect(url_for('vendas_list_view'))

def register_vendas_routes(app: Flask) -> None:
    app.add_url_rule("/vendas", endpoint="vendas_list_view", view_func=vendas_list_view)
    app.add_url_rule("/vendas/registrar/<int:lead_id>", endpoint="vendas_registrar_view", view_func=vendas_registrar_view)
    app.add_url_rule("/vendas/registrar", endpoint="vendas_registrar_action", view_func=vendas_registrar_action, methods=["POST"])
