import os
from database import init_db
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from io import BytesIO
from services.relatorio_service import get_resumo_hoje, get_relatorio_completo
from services.relatorio_pdf_service import (
    build_relatorio_pdf_bytes,
    default_pdf_filename,
    save_pdf_copy,
)
from services.cnpj_service import is_valid_cnpj, normalize_cnpj, consultar_cnpj_brasilapi
from services.lead_service import get_leads, get_lead_by_id, create_lead, update_lead_status
from services.fila_service import get_proximo_lead, processa_acao_fila, get_total_fila
from services.prospeccao_service import (
    get_prospeccoes_temp, add_prospeccao_temp, update_status_prospeccao,
    converter_para_lead, delete_prospeccao_temp, get_resumo_prospeccao,
    get_relatorio_prospeccao, get_retornos_agendados, get_total_retornos_hoje,
    get_retornos_atrasados, registrar_tentativa_retorno, rolar_agendamentos_pendentes
)
from services.prospeccao_service import arquivar_prospeccao
from services.prospeccao_service import update_segmento_prospeccao, registrar_resultado_retorno
app = Flask(__name__)

# Context processor para disponibilizar dados globais em todos os templates
@app.context_processor
def inject_globals():
    from datetime import date
    return {
        'total_retornos_hoje': get_total_retornos_hoje()
    }

# Auto-init db se não existir
init_db()

@app.route('/')
def index():
    resumo = get_resumo_hoje()
    return render_template('dashboard.html', resumo=resumo, active_page='dashboard')

@app.route('/prospeccao')
def prospeccao_view():
    from datetime import date, timedelta
    
    filtro_status = request.args.get('status')
    segmento = request.args.get('segmento')
    cidade = request.args.get('cidade')
    estado = request.args.get('estado')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    mostrar_arquivados = request.args.get('arquivados') == '1'
    
    # Se não tem filtro de data, mostra apenas de hoje por padrão
    if not data_inicio and not data_fim and not mostrar_arquivados:
        data_inicio = date.today().isoformat()
        data_fim = date.today().isoformat()
    
    prospeccoes = get_prospeccoes_temp(filtro_status, segmento, cidade, estado, 
                                       data_inicio, data_fim, mostrar_arquivados)
    resumo_prospeccao = get_resumo_prospeccao(data_inicio, data_fim, mostrar_arquivados)
    
    return render_template('prospeccao.html', 
                          prospeccoes=prospeccoes, 
                          resumo_prospeccao=resumo_prospeccao,
                          active_page='prospeccao',
                          filtro_status=filtro_status,
                          segmento=segmento,
                          cidade=cidade,
                          estado=estado,
                          data_inicio=data_inicio,
                          data_fim=data_fim,
                          mostrar_arquivados=mostrar_arquivados)

@app.route('/prospeccao/rascunho/novo', methods=['POST'])
def rascunho_novo():
    data = dict(request.form)

    cnpj = (data.get('cnpj') or '').strip()
    if cnpj:
        cnpj_norm = normalize_cnpj(cnpj)
        if not is_valid_cnpj(cnpj_norm):
            data['cnpj'] = ''
        else:
            data['cnpj'] = cnpj_norm

    add_prospeccao_temp(data)
    next_url = request.form.get('next') or request.form.get('next_url')
    return redirect(next_url or url_for('prospeccao_view'))

@app.route('/prospeccao/rascunho/<int:prospeccao_id>/status', methods=['POST'])
def rascunho_status(prospeccao_id):
    novo_status = (request.form.get('status') or '').strip()
    observacao = (request.form.get('observacao') or '').strip() or None
    data_retorno = (request.form.get('data_retorno') or '').strip() or None
    hora_retorno = (request.form.get('hora_retorno') or '').strip() or None

    if not novo_status:
        return redirect(request.form.get('next', url_for('prospeccao_view')))

    if novo_status == 'Pediu para retornar' and not data_retorno:
        return redirect(url_for('prospeccao_view', erro='Informe a data de retorno.'))
    if novo_status == 'Pediu para retornar' and data_retorno and not hora_retorno:
        return redirect(url_for('prospeccao_view', erro='Informe o horário de retorno.'))

    update_status_prospeccao(
        prospeccao_id,
        novo_status,
        observacao=observacao,
        data_retorno=data_retorno,
        hora_retorno=hora_retorno,
    )

    if novo_status == 'Sem interesse':
        arquivar_prospeccao(prospeccao_id)

    return redirect(request.form.get('next', url_for('prospeccao_view')))

@app.route('/leads', methods=['GET'])
def leads_list():
    status = request.args.get('status')
    leads = get_leads(status)
    return render_template('leads.html', leads=leads, active_page='leads')

@app.route('/leads/novo', methods=['POST'])
def leads_create():
    create_lead(request.form)
    next_url = request.form.get('next_url')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('leads_list'))

@app.route('/leads/<int:lead_id>')
def lead_detail(lead_id):
    lead, contatos, segmentos = get_lead_by_id(lead_id)
    return render_template('lead_detalhe.html', lead=lead, contatos=contatos, segmentos=segmentos, active_page='leads')

@app.route('/leads/<int:lead_id>/status', methods=['POST'])
def lead_update_status(lead_id):
    novo_status = request.form.get('status')
    if novo_status:
        update_lead_status(lead_id, novo_status)
    return redirect(request.form.get('next', url_for('leads_list')))

@app.route('/leads/<int:lead_id>/contato', methods=['POST'])
def add_lead_contato(lead_id):
    from services.lead_service import add_contato
    resultado = (request.form.get('resultado') or '').strip()
    data_retorno = (request.form.get('data_retorno') or '').strip()
    hora_retorno = (request.form.get('hora_retorno') or '').strip()

    if resultado in ('Envio do portifólio', 'Agendar retorno'):
        if not data_retorno:
            return redirect(url_for('lead_detail', lead_id=lead_id, erro='Informe a data de retorno para continuar.'))
        if not hora_retorno:
            return redirect(url_for('lead_detail', lead_id=lead_id, erro='Informe o horário de retorno.'))

    if resultado == 'Envio do portifólio':
        _lead, _contatos, segmentos = get_lead_by_id(lead_id)
        if not segmentos:
            return redirect(url_for('lead_detail', lead_id=lead_id, erro='Informe o segmento do lead antes de registrar o envio do portifólio.'))

    add_contato(lead_id, request.form)
    return redirect(request.form.get('next', url_for('leads_list')))

@app.route('/api/cnpj/consultar', methods=['GET'])
def api_consultar_cnpj():
    cnpj_raw = request.args.get('cnpj', '')
    cnpj = normalize_cnpj(cnpj_raw)
    valid_local = is_valid_cnpj(cnpj)

    if not cnpj:
        return jsonify({'ok': False, 'cnpj': None, 'valid_local': False, 'message': 'CNPJ vazio'}), 400
    if not valid_local:
        return jsonify({'ok': False, 'cnpj': cnpj, 'valid_local': False, 'message': 'CNPJ inválido'}), 400

    data = consultar_cnpj_brasilapi(cnpj)
    if isinstance(data, dict) and data.get('error'):
        return jsonify({'ok': False, 'cnpj': cnpj, 'valid_local': True, 'message': 'Falha ao consultar', 'data': data}), 502

    return jsonify({'ok': True, 'cnpj': cnpj, 'valid_local': True, 'data': data})

@app.route('/fila/acao/<int:lead_id>', methods=['POST'])
def fila_acao(lead_id):
    acao = request.form.get('acao')
    observacao = request.form.get('observacao', '')
    if acao and acao != 'Pular':
        processa_acao_fila(lead_id, acao, observacao)
    
    if acao == 'Pular':
        from services.lead_service import add_contato
    novo_status = request.form.get('status')
    observacao = request.form.get('observacao', '')
    data_retorno = request.form.get('data_retorno')
    hora_retorno = request.form.get('hora_retorno')
    next_url = request.form.get('next')

    if novo_status == 'Pediu portfólio':
        novo_status = 'Envio do portfólio'

    if novo_status in ('Pediu para retornar', 'Envio do portfólio') and not data_retorno:
        return redirect(url_for('prospeccao_view', erro='Informe a data de retorno para continuar.'))
    if novo_status in ('Pediu para retornar', 'Envio do portfólio') and data_retorno and not hora_retorno:
        return redirect(url_for('prospeccao_view', erro='Informe o horário de retorno para continuar.'))

    if novo_status == 'Envio do portfólio':
        prospeccao = None
        try:
            from services.prospeccao_service import get_prospeccao_by_id
            prospeccao = get_prospeccao_by_id(prospeccao_id)
        except Exception:
            prospeccao = None
        segmento = request.form.get('segmento')
        if not segmento and prospeccao:
            segmento = prospeccao.get('segmento')
        if not segmento:
            return redirect(url_for('prospeccao_view', erro='Informe o segmento antes de registrar envio do portfólio.'))
    
    if data_retorno:
        update_status_prospeccao(prospeccao_id, novo_status, data_retorno=data_retorno, hora_retorno=hora_retorno)
    elif observacao:
        update_status_prospeccao(prospeccao_id, novo_status, observacao=observacao)
    else:
        update_status_prospeccao(prospeccao_id, novo_status)

    if novo_status == 'Sem interesse':
        arquivar_prospeccao(prospeccao_id)

    if next_url:
        return redirect(next_url)
    return redirect(url_for('prospeccao_view'))

@app.route('/agendamentos/<int:prospeccao_id>/nao-atendeu', methods=['POST'])
def agendamento_nao_atendeu(prospeccao_id):
    observacao = request.form.get('observacao', '')
    registrar_tentativa_retorno(prospeccao_id, observacao=observacao)
    return redirect(request.form.get('next', url_for('agendamentos_view')))

@app.route('/agendamentos/<int:prospeccao_id>/registrar-tentativa', methods=['POST'])
def agendamento_registrar_tentativa(prospeccao_id):
    resultado = (request.form.get('resultado') or '').strip()
    observacao = (request.form.get('observacao') or '').strip()
    data_retorno = (request.form.get('data_retorno') or '').strip()
    hora_retorno = (request.form.get('hora_retorno') or '').strip()
    segmento = (request.form.get('segmento') or '').strip()
    pos_acao = (request.form.get('pos_acao') or '').strip()
    next_url = request.form.get('next', url_for('agendamentos_view'))

    def _err(msg):
        sep = '&' if ('?' in next_url) else '?'
        return redirect(f"{next_url}{sep}erro={msg}")

    if not resultado:
        return _err('Selecione o resultado da tentativa.')

    resultados_tentativa = ('Não atendeu', 'Caixa postal', 'Sem contato')
    resultados_proximo_passo = ('Envio do portfólio', 'Agendar retorno', 'Pediu preço')

    if resultado in resultados_proximo_passo and not observacao:
        return _err('Observação obrigatória para registrar o próximo passo.')

    if resultado in ('Envio do portfólio', 'Agendar retorno') and not data_retorno:
        return _err('Informe a data de retorno para continuar.')
    if resultado in ('Envio do portfólio', 'Agendar retorno') and data_retorno and not hora_retorno:
        return _err('Informe o horário de retorno para continuar.')

    if resultado == 'Envio do portfólio':
        if not segmento:
            prospeccao, _contatos, _seg = None, None, None
            try:
                from services.prospeccao_service import get_prospeccao_by_id
                prospeccao = get_prospeccao_by_id(prospeccao_id)
            except Exception:
                prospeccao = None
            if not prospeccao or not prospeccao.get('segmento'):
                return _err('Informe o segmento antes de registrar envio do portfólio.')
        else:
            update_segmento_prospeccao(prospeccao_id, segmento)

    if resultado in resultados_tentativa:
        detalhe = resultado
        if observacao:
            detalhe = f"{resultado} | {observacao}"
        registrar_tentativa_retorno(prospeccao_id, observacao=detalhe)
        return redirect(next_url)

    if resultado == 'Sem interesse':
        update_status_prospeccao(prospeccao_id, 'Sem interesse', observacao=observacao or None)
        registrar_resultado_retorno(prospeccao_id, 'Sem interesse', observacao=observacao or None)
        arquivar_prospeccao(prospeccao_id)
        return redirect(next_url)

    if resultado == 'Interessado':
        update_status_prospeccao(prospeccao_id, 'Interessado', observacao=observacao or None)
        registrar_resultado_retorno(prospeccao_id, 'Interessado', observacao=observacao or None)
        if pos_acao == 'converter':
            lead_id = converter_para_lead(prospeccao_id)
            if lead_id:
                return redirect(url_for('lead_detail', lead_id=lead_id))
        return redirect(next_url)

    if resultado in ('Envio do portfólio', 'Agendar retorno'):
        update_status_prospeccao(
            prospeccao_id,
            'Pediu para retornar',
            observacao=observacao or None,
            data_retorno=data_retorno,
            hora_retorno=hora_retorno,
        )
        registrar_resultado_retorno(prospeccao_id, resultado, observacao=observacao or None)
        return redirect(next_url)

    if resultado == 'Pediu preço':
        registrar_resultado_retorno(prospeccao_id, 'Pediu preço', observacao=observacao)
        return redirect(next_url)

    return _err('Resultado inválido.')

@app.route('/prospeccao/rascunho/<int:prospeccao_id>/converter', methods=['POST'])
def rascunho_converter(prospeccao_id):
    lead_id = converter_para_lead(prospeccao_id)
    if lead_id:
        return redirect(url_for('lead_detail', lead_id=lead_id))
    return redirect(url_for('prospeccao_view'))

@app.route('/prospeccao/rascunho/<int:prospeccao_id>/excluir', methods=['POST'])
def rascunho_excluir(prospeccao_id):
    delete_prospeccao_temp(prospeccao_id)
    return redirect(url_for('prospeccao_view'))

@app.route('/relatorio/prospeccao')
def relatorio_prospeccao():
    from datetime import date, timedelta
    
    periodo = request.args.get('periodo', 'hoje')  # hoje, ontem, semana, mes, personalizado
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Calcula datas baseado no período
    hoje = date.today()
    if periodo == 'hoje':
        data_inicio = hoje.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == 'ontem':
        ontem = hoje - timedelta(days=1)
        data_inicio = ontem.isoformat()
        data_fim = ontem.isoformat()
    elif periodo == 'semana':
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        data_inicio = inicio_semana.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == 'mes':
        inicio_mes = hoje.replace(day=1)
        data_inicio = inicio_mes.isoformat()
        data_fim = hoje.isoformat()
    
    relatorio = get_relatorio_prospeccao(data_inicio, data_fim)
    
    return render_template('relatorio_prospeccao.html', 
                          relatorio=relatorio, 
                          periodo=periodo,
                          data_inicio=data_inicio,
                          data_fim=data_fim,
                          active_page='relatorio')

@app.route('/relatorio')
def relatorio_diario():
    from datetime import date, timedelta
    
    periodo = request.args.get('periodo', 'hoje')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Calcula datas baseado no período
    hoje = date.today()
    if periodo == 'hoje':
        data_inicio = hoje.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == 'ontem':
        ontem = hoje - timedelta(days=1)
        data_inicio = ontem.isoformat()
        data_fim = ontem.isoformat()
    elif periodo == 'semana':
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        data_inicio = inicio_semana.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == 'mes':
        inicio_mes = hoje.replace(day=1)
        data_inicio = inicio_mes.isoformat()
        data_fim = hoje.isoformat()
    
    relatorio = get_relatorio_completo(data_inicio, data_fim)
    
    return render_template('relatorio.html', 
                          relatorio=relatorio,
                          periodo=periodo,
                          data_inicio=data_inicio,
                          data_fim=data_fim,
                          active_page='relatorio')

@app.route('/relatorio/pdf')
def relatorio_pdf():
    from datetime import date, timedelta

    periodo = request.args.get('periodo', 'hoje')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    hoje = date.today()
    if periodo == 'hoje':
        data_inicio = hoje.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == 'ontem':
        ontem = hoje - timedelta(days=1)
        data_inicio = ontem.isoformat()
        data_fim = ontem.isoformat()
    elif periodo == 'semana':
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        data_inicio = inicio_semana.isoformat()
        data_fim = hoje.isoformat()
    elif periodo == 'mes':
        inicio_mes = hoje.replace(day=1)
        data_inicio = inicio_mes.isoformat()
        data_fim = hoje.isoformat()

    relatorio = get_relatorio_completo(data_inicio, data_fim)

    pdf_bytes = build_relatorio_pdf_bytes(relatorio, data_inicio, data_fim)
    filename = default_pdf_filename(data_inicio, data_fim)

    export_dir = os.path.join(app.root_path, 'exports', 'relatorios')
    save_pdf_copy(pdf_bytes, export_dir, filename)

    return send_file(
        BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf',
    )

@app.route('/agendamentos')
def agendamentos_view():
    from datetime import date
    from services.lead_service import get_retornos_leads, get_retornos_leads_atrasados
    
    data_filtro = request.args.get('data')
    mostrar_todos = request.args.get('todos') == '1'
    
    hoje = date.today().isoformat()

    rolar_agendamentos_pendentes(hoje)
    
    retornos_hoje = get_retornos_agendados(hoje)
    retornos_atrasados = get_retornos_atrasados()

    retornos_leads_hoje = get_retornos_leads(hoje)
    retornos_leads_atrasados = get_retornos_leads_atrasados(hoje)
    retornos_leads_futuros = get_retornos_leads(hoje, mostrar_todos=True)
    total_leads_futuros = len([r for r in retornos_leads_futuros if r['data_retorno'] != hoje])
    
    # Sempre busca futuros para contagem no card, mesmo que não mostre a lista
    retornos_futuros = get_retornos_agendados(hoje, mostrar_todos=True)
    # Conta apenas os que são depois de hoje (exclui hoje)
    total_futuros = len([r for r in retornos_futuros if r['data_retorno'] != hoje])
    
    total_retornos_hoje = len(retornos_hoje)
    total_atrasados = len(retornos_atrasados)

    total_leads_hoje = len(retornos_leads_hoje)
    total_leads_atrasados = len(retornos_leads_atrasados)
    
    return render_template('agendamentos.html',
                          retornos_hoje=retornos_hoje,
                          retornos_atrasados=retornos_atrasados,
                          retornos_futuros=retornos_futuros if mostrar_todos else [],
                          retornos_leads_hoje=retornos_leads_hoje,
                          retornos_leads_atrasados=retornos_leads_atrasados,
                          retornos_leads_futuros=retornos_leads_futuros,
                          hoje=hoje,
                          mostrar_todos=mostrar_todos,
                          total_hoje=total_retornos_hoje,
                          total_atrasados=total_atrasados,
                          total_futuros=total_futuros,
                          total_leads_hoje=total_leads_hoje,
                          total_leads_atrasados=total_leads_atrasados,
                          total_leads_futuros=total_leads_futuros,
                          data_filtro=data_filtro,
                          active_page='agendamentos')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
