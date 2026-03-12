import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database import DB_PATH
from datetime import datetime, timedelta


def _norm_text(v: str) -> str:
    return ' '.join((v or '').strip().lower().split())


def add_prospeccao_temp_info(dados):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    obs = dados.get('observacoes')
    if obs is None:
        obs = dados.get('observacao', '')

    status = dados.get('status_prospeccao') if dados.get('status_prospeccao') else 'Não contatado'
    if status == 'Pediu portfólio':
        status = 'Envio do portfólio'

    data_retorno = dados.get('data_retorno') if status in ('Pediu para retornar', 'Envio do portfólio') else None
    hora_retorno = dados.get('hora_retorno') if data_retorno else None

    maps_place_id = (dados.get('maps_place_id') or '').strip() or None
    maps_url = (dados.get('maps_url') or '').strip() or None
    cnpj = (dados.get('cnpj') or '').strip() or None

    existente_id = None
    if maps_place_id:
        c.execute('''
            SELECT id FROM prospeccao_temp
            WHERE maps_place_id = ?
            ORDER BY id DESC
            LIMIT 1
        ''', (maps_place_id,))
        row = c.fetchone()
        existente_id = row[0] if row else None

    if not existente_id and cnpj:
        c.execute('''
            SELECT id FROM prospeccao_temp
            WHERE cnpj = ?
            ORDER BY id DESC
            LIMIT 1
        ''', (cnpj,))
        row = c.fetchone()
        existente_id = row[0] if row else None

    if not existente_id:
        nome_n = _norm_text(dados.get('nome_loja'))
        cidade_n = _norm_text(dados.get('cidade'))
        estado_n = _norm_text(dados.get('estado'))
        if nome_n and cidade_n and estado_n:
            c.execute('''
                SELECT id, nome_loja, cidade, estado
                FROM prospeccao_temp
                ORDER BY id DESC
                LIMIT 200
            ''')
            rows = c.fetchall() or []
            for r in rows:
                if _norm_text(r[1]) == nome_n and _norm_text(r[2]) == cidade_n and _norm_text(r[3]) == estado_n:
                    existente_id = r[0]
                    break

    if existente_id:
        conn.close()
        return existente_id, False

    c.execute('''
        INSERT INTO prospeccao_temp (nome_loja, cnpj, telefone, whatsapp, endereco, cidade, estado, segmento, observacao, data_prospeccao, status_prospeccao, data_retorno, hora_retorno, maps_place_id, maps_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, DATE('now')), COALESCE(?, 'Não contatado'), ?, ?, ?, ?)
    ''', (
        dados.get('nome_loja'),
        cnpj,
        dados.get('telefone'),
        dados.get('whatsapp'),
        dados.get('endereco'),
        dados.get('cidade'),
        dados.get('estado'),
        dados.get('segmento'),
        obs,
        dados.get('data_prospeccao'),
        status,
        data_retorno,
        hora_retorno,
        maps_place_id,
        maps_url,
    ))
    conn.commit()
    new_id = c.lastrowid
    conn.close()

    return new_id, True

def get_prospeccoes_temp(filtro_status=None, segmento=None, cidade=None, estado=None, 
                         data_inicio=None, data_fim=None, mostrar_arquivados=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = '''
        SELECT * FROM prospeccao_temp 
        WHERE 1=1
    '''
    params = []
    
    if not mostrar_arquivados:
        query += ' AND (arquivado = 0 OR arquivado IS NULL)'
    
    if filtro_status:
        query += ' AND status_prospeccao = ?'
        params.append(filtro_status)
    if segmento:
        query += ' AND segmento LIKE ?'
        params.append(f'%{segmento}%')
    if cidade:
        query += ' AND cidade LIKE ?'
        params.append(f'%{cidade}%')
    if estado:
        query += ' AND estado = ?'
        params.append(estado)
    if data_inicio:
        query += ' AND data_prospeccao >= ?'
        params.append(data_inicio)
    if data_fim:
        query += ' AND data_prospeccao <= ?'
        params.append(data_fim)
    
    query += ' ORDER BY data_prospeccao DESC, data_criacao DESC'
    
    c.execute(query, params)
    prospeccoes = c.fetchall()
    conn.close()
    return prospeccoes

def add_prospeccao_temp(dados):
    prospeccao_id, _ = add_prospeccao_temp_info(dados)
    return prospeccao_id

def update_segmento_prospeccao(prospeccao_id, segmento):
    if not segmento:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE prospeccao_temp SET segmento = ? WHERE id = ?', (segmento, prospeccao_id))
    conn.commit()
    conn.close()

def registrar_resultado_retorno(prospeccao_id, resultado, observacao=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT data_retorno FROM prospeccao_temp WHERE id = ?', (prospeccao_id,))
    row = c.fetchone()
    data_retorno_atual = row[0] if row else None

    detalhe = (resultado or '').strip()
    if observacao:
        detalhe = f"{detalhe} | {observacao}" if detalhe else observacao

    c.execute('''
        INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe, data_retorno_antes, data_retorno_depois)
        VALUES (?, ?, ?, ?, ?)
    ''', (prospeccao_id, 'RETORNO_RESULTADO', detalhe, data_retorno_atual, data_retorno_atual))

    conn.commit()
    conn.close()

def update_status_prospeccao(prospeccao_id, novo_status, observacao=None, data_retorno=None, hora_retorno=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('SELECT data_retorno FROM prospeccao_temp WHERE id = ?', (prospeccao_id,))
    row = c.fetchone()
    data_retorno_antes = row[0] if row else None
    
    set_clause = 'status_prospeccao = ?'
    params = [novo_status]
    
    if observacao:
        set_clause += ', observacao = ?'
        params.append(observacao)
    if data_retorno:
        set_clause += ', data_retorno = ?'
        params.append(data_retorno)
        set_clause += ', hora_retorno = ?'
        params.append(hora_retorno)
        if novo_status == 'Pediu para retornar':
            set_clause += ', data_primeiro_agendamento = COALESCE(data_primeiro_agendamento, ?)'
            params.append(data_retorno)
    
    params.append(prospeccao_id)
    c.execute(f'UPDATE prospeccao_temp SET {set_clause} WHERE id = ?', params)

    data_retorno_depois = data_retorno if data_retorno else data_retorno_antes
    detalhe = novo_status
    if observacao:
        detalhe = f"{novo_status} | {observacao}"
    c.execute('''
        INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe, data_retorno_antes, data_retorno_depois)
        VALUES (?, ?, ?, ?, ?)
    ''', (prospeccao_id, 'STATUS_ATUALIZADO', detalhe, data_retorno_antes, data_retorno_depois))
    conn.commit()
    conn.close()

def registrar_tentativa_retorno(prospeccao_id, observacao=None, data_tentativa=None):
    from datetime import date

    if not data_tentativa:
        data_tentativa = date.today().isoformat()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('SELECT data_retorno FROM prospeccao_temp WHERE id = ?', (prospeccao_id,))
    row = c.fetchone()
    data_retorno_atual = row[0] if row else None

    c.execute('''
        UPDATE prospeccao_temp
        SET tentativas_retorno = COALESCE(tentativas_retorno, 0) + 1,
            data_ultima_tentativa = ?
        WHERE id = ?
    ''', (data_tentativa, prospeccao_id))

    c.execute('''
        INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe, data_retorno_antes, data_retorno_depois)
        VALUES (?, ?, ?, ?, ?)
    ''', (prospeccao_id, 'RETORNO_TENTATIVA', observacao or '', data_retorno_atual, data_retorno_atual))

    conn.commit()
    conn.close()

def rolar_agendamentos_pendentes(hoje=None):
    from datetime import date

    if not hoje:
        hoje = date.today().isoformat()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT id, data_retorno
        FROM prospeccao_temp
        WHERE status_prospeccao = 'Pediu para retornar'
          AND data_retorno IS NOT NULL
          AND data_retorno < ?
          AND (arquivado = 0 OR arquivado IS NULL)
    ''', (hoje,))
    pendentes = c.fetchall()

    c.execute('''
        UPDATE prospeccao_temp
        SET data_primeiro_agendamento = COALESCE(data_primeiro_agendamento, data_retorno),
            data_retorno = ?
        WHERE status_prospeccao = 'Pediu para retornar'
          AND data_retorno IS NOT NULL
          AND data_retorno < ?
          AND (arquivado = 0 OR arquivado IS NULL)
    ''', (hoje, hoje))

    if pendentes:
        c.executemany('''
            INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe, data_retorno_antes, data_retorno_depois)
            VALUES (?, ?, ?, ?, ?)
        ''', [(row[0], 'RETORNO_REAGENDADO_AUTO', '', row[1], hoje) for row in pendentes])

    conn.commit()
    conn.close()

def arquivar_prospeccao(prospeccao_id):
    """Arquiva ao invés de excluir - mantém histórico"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE prospeccao_temp SET arquivado = 1 WHERE id = ?', (prospeccao_id,))
    conn.commit()
    conn.close()

def desarquivar_prospeccao(prospeccao_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE prospeccao_temp SET arquivado = 0 WHERE id = ?', (prospeccao_id,))
    conn.commit()
    conn.close()

def converter_para_lead(prospeccao_id):
    from services.lead_service import create_lead
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM prospeccao_temp WHERE id = ?', (prospeccao_id,))
    prospeccao = c.fetchone()
    
    if not prospeccao:
        conn.close()
        return None
    
    # Cria lead no CRM
    dados_lead = {
        'nome_loja': prospeccao['nome_loja'],
        'cnpj': prospeccao['cnpj'],
        'telefone': prospeccao['telefone'],
        'whatsapp': prospeccao['whatsapp'],
        'endereco': prospeccao['endereco'],
        'cidade': prospeccao['cidade'],
        'estado': prospeccao['estado'],
        'segmentos': prospeccao['segmento'],
        'observacoes': prospeccao['observacao'] or 'Convertido da prospecção',
        'status': 'Interessado' if prospeccao['status_prospeccao'] == 'Interessado' else 'Novo Lead'
    }
    
    lead_id = create_lead(dados_lead)
    
    # Atualiza prospeccao_temp com referência ao lead e arquiva
    c.execute('UPDATE prospeccao_temp SET convertido_lead_id = ?, arquivado = 1, status_prospeccao = ? WHERE id = ?', 
              (lead_id, 'Convertido em Lead', prospeccao_id))
    conn.commit()
    conn.close()
    
    return lead_id

def delete_prospeccao_temp(prospeccao_id):
    """Agora arquiva ao invés de excluir"""
    arquivar_prospeccao(prospeccao_id)

def get_prospeccao_by_id(prospeccao_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM prospeccao_temp WHERE id = ?', (prospeccao_id,))
    prospeccao = c.fetchone()
    conn.close()
    return prospeccao

def get_resumo_prospeccao(data_inicio=None, data_fim=None, mostrar_arquivados=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    where_clause = '1=1'
    params = []
    
    if not mostrar_arquivados:
        where_clause += ' AND (arquivado = 0 OR arquivado IS NULL)'
    if data_inicio:
        where_clause += ' AND data_prospeccao >= ?'
        params.append(data_inicio)
    if data_fim:
        where_clause += ' AND data_prospeccao <= ?'
        params.append(data_fim)
    
    # Resumo por status
    c.execute(f'''
        SELECT status_prospeccao, COUNT(*) as total 
        FROM prospeccao_temp 
        WHERE {where_clause}
        GROUP BY status_prospeccao
    ''', params)
    resumo = c.fetchall()
    
    # Total
    c.execute(f'SELECT COUNT(*) FROM prospeccao_temp WHERE {where_clause}', params)
    total = c.fetchone()[0]
    
    # Convertidos
    c.execute(f'''
        SELECT COUNT(*) FROM prospeccao_temp 
        WHERE convertido_lead_id IS NOT NULL
        {'' if mostrar_arquivados else ' AND (arquivado = 0 OR arquivado IS NULL)'}
        {' AND data_prospeccao >= ?' if data_inicio else ''}
        {' AND data_prospeccao <= ?' if data_fim else ''}
    ''', params)
    convertidos = c.fetchone()[0]
    
    conn.close()
    return {'total': total, 'por_status': resumo, 'convertidos': convertidos}

def get_relatorio_prospeccao(data_inicio=None, data_fim=None):
    """Relatório completo de prospecção para gestora"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    where_clause = '1=1'
    params = []
    
    if data_inicio:
        where_clause += ' AND data_prospeccao >= ?'
        params.append(data_inicio)
    if data_fim:
        where_clause += ' AND data_prospeccao <= ?'
        params.append(data_fim)
    
    # Lista completa do período
    c.execute(f'''
        SELECT * FROM prospeccao_temp 
        WHERE {where_clause}
        ORDER BY data_prospeccao DESC, data_criacao DESC
    ''', params)
    items = c.fetchall()
    
    # Resumo por dia
    c.execute(f'''
        SELECT data_prospeccao, status_prospeccao, COUNT(*) as total
        FROM prospeccao_temp
        WHERE {where_clause}
        GROUP BY data_prospeccao, status_prospeccao
        ORDER BY data_prospeccao DESC
    ''', params)
    por_dia = c.fetchall()
    
    # Resumo geral do período
    c.execute(f'''
        SELECT status_prospeccao, COUNT(*) as total
        FROM prospeccao_temp
        WHERE {where_clause}
        GROUP BY status_prospeccao
    ''', params)
    resumo = c.fetchall()
    
    # Total tentativas (tudo que não é 'Não contatado')
    c.execute(f'''
        SELECT COUNT(*) FROM prospeccao_temp
        WHERE {where_clause} AND status_prospeccao != 'Não contatado'
    ''', params)
    total_tentativas = c.fetchone()[0]
    
    # Convertidos em leads
    c.execute(f'''
        SELECT COUNT(*) FROM prospeccao_temp
        WHERE {where_clause} AND convertido_lead_id IS NOT NULL
    ''', params)
    total_convertidos = c.fetchone()[0]
    
    conn.close()
    
    return {
        'items': items,
        'por_dia': por_dia,
        'resumo': resumo,
        'total_geral': len(items),
        'total_tentativas': total_tentativas,
        'total_convertidos': total_convertidos,
        'periodo': {'inicio': data_inicio, 'fim': data_fim}
    }

def get_retornos_agendados(data=None, mostrar_todos=False):
    """Busca prospecções com data de retorno agendada"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if not data:
        from datetime import date
        data = date.today().isoformat()
    
    if mostrar_todos:
        # Todos os retornos futuros
        c.execute('''
            SELECT
                *,
                (
                    SELECT e.detalhe
                    FROM prospeccao_eventos e
                    WHERE e.prospeccao_id = prospeccao_temp.id
                      AND e.tipo_evento = 'RETORNO_TENTATIVA'
                    ORDER BY e.data_evento DESC
                    LIMIT 1
                ) AS ultima_tentativa_detalhe,
                (
                    SELECT e.data_evento
                    FROM prospeccao_eventos e
                    WHERE e.prospeccao_id = prospeccao_temp.id
                      AND e.tipo_evento = 'RETORNO_TENTATIVA'
                    ORDER BY e.data_evento DESC
                    LIMIT 1
                ) AS ultima_tentativa_data_evento
            FROM prospeccao_temp
            WHERE data_retorno IS NOT NULL 
              AND data_retorno >= ?
              AND status_prospeccao = 'Pediu para retornar'
              AND (arquivado = 0 OR arquivado IS NULL)
            ORDER BY data_retorno ASC
        ''', (data,))
    else:
        # Apenas retornos para data específica
        c.execute('''
            SELECT
                *,
                (
                    SELECT e.detalhe
                    FROM prospeccao_eventos e
                    WHERE e.prospeccao_id = prospeccao_temp.id
                      AND e.tipo_evento = 'RETORNO_TENTATIVA'
                    ORDER BY e.data_evento DESC
                    LIMIT 1
                ) AS ultima_tentativa_detalhe,
                (
                    SELECT e.data_evento
                    FROM prospeccao_eventos e
                    WHERE e.prospeccao_id = prospeccao_temp.id
                      AND e.tipo_evento = 'RETORNO_TENTATIVA'
                    ORDER BY e.data_evento DESC
                    LIMIT 1
                ) AS ultima_tentativa_data_evento
            FROM prospeccao_temp
            WHERE data_retorno = ?
              AND status_prospeccao = 'Pediu para retornar'
              AND (arquivado = 0 OR arquivado IS NULL)
            ORDER BY (hora_retorno IS NULL) ASC, hora_retorno ASC, data_criacao ASC
        ''', (data,))
    
    retornos = c.fetchall()
    conn.close()
    return retornos

def get_total_retornos_hoje():
    """Retorna quantidade de retornos agendados para hoje"""
    from datetime import date
    hoje = date.today().isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM prospeccao_temp 
        WHERE data_retorno = ?
          AND status_prospeccao = 'Pediu para retornar'
          AND (arquivado = 0 OR arquivado IS NULL)
    ''', (hoje,))
    total = c.fetchone()[0]
    conn.close()
    return total

def get_retornos_atrasados():
    """Busca retornos que já passaram da data"""
    from datetime import date
    hoje = date.today().isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT
            *,
            (
                SELECT e.detalhe
                FROM prospeccao_eventos e
                WHERE e.prospeccao_id = prospeccao_temp.id
                  AND e.tipo_evento = 'RETORNO_TENTATIVA'
                ORDER BY e.data_evento DESC
                LIMIT 1
            ) AS ultima_tentativa_detalhe,
            (
                SELECT e.data_evento
                FROM prospeccao_eventos e
                WHERE e.prospeccao_id = prospeccao_temp.id
                  AND e.tipo_evento = 'RETORNO_TENTATIVA'
                ORDER BY e.data_evento DESC
                LIMIT 1
            ) AS ultima_tentativa_data_evento
        FROM prospeccao_temp
        WHERE data_retorno < ?
          AND data_retorno IS NOT NULL
          AND status_prospeccao = 'Pediu para retornar'
          AND (arquivado = 0 OR arquivado IS NULL)
        ORDER BY data_retorno ASC
    ''', (hoje,))
    retornos = c.fetchall()
    conn.close()
    return retornos
