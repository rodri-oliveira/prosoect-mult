import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database import DB_PATH
from datetime import datetime, timedelta

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
        query += ' AND segmento = ?'
        params.append(segmento)
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO prospeccao_temp (nome_loja, telefone, whatsapp, endereco, cidade, estado, segmento, observacao, data_prospeccao, status_prospeccao, data_retorno)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, DATE('now')), COALESCE(?, 'Não contatado'), ?)
    ''', (
        dados.get('nome_loja'),
        dados.get('telefone'),
        dados.get('whatsapp'),
        dados.get('endereco'),
        dados.get('cidade'),
        dados.get('estado'),
        dados.get('segmento'),
        dados.get('observacoes', ''),
        dados.get('data_prospeccao'),
        dados.get('status_prospeccao') if dados.get('status_prospeccao') else 'Não contatado',
        dados.get('data_retorno') if dados.get('status_prospeccao') == 'Pediu para retornar' else None
    ))
    conn.commit()
    conn.close()

def update_status_prospeccao(prospeccao_id, novo_status, observacao=None, data_retorno=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    set_clause = 'status_prospeccao = ?'
    params = [novo_status]
    
    if observacao:
        set_clause += ', observacao = ?'
        params.append(observacao)
    if data_retorno:
        set_clause += ', data_retorno = ?'
        params.append(data_retorno)
    
    params.append(prospeccao_id)
    c.execute(f'UPDATE prospeccao_temp SET {set_clause} WHERE id = ?', params)
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
            SELECT * FROM prospeccao_temp 
            WHERE data_retorno IS NOT NULL 
              AND data_retorno >= ?
              AND status_prospeccao = 'Pediu para retornar'
              AND (arquivado = 0 OR arquivado IS NULL)
            ORDER BY data_retorno ASC
        ''', (data,))
    else:
        # Apenas retornos para data específica
        c.execute('''
            SELECT * FROM prospeccao_temp 
            WHERE data_retorno = ?
              AND status_prospeccao = 'Pediu para retornar'
              AND (arquivado = 0 OR arquivado IS NULL)
            ORDER BY data_criacao ASC
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
        SELECT * FROM prospeccao_temp 
        WHERE data_retorno < ?
          AND data_retorno IS NOT NULL
          AND status_prospeccao = 'Pediu para retornar'
          AND (arquivado = 0 OR arquivado IS NULL)
        ORDER BY data_retorno ASC
    ''', (hoje,))
    retornos = c.fetchall()
    conn.close()
    return retornos
