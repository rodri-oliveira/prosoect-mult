import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database import DB_PATH
from datetime import date

def get_resumo_hoje():
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Ligações realizadas hoje
    c.execute("SELECT COUNT(*) as qtd FROM contatos WHERE date(data) = ? AND tipo_contato = 'Ligação'", (hoje,))
    ligacoes = c.fetchone()['qtd']
    
    # WhatsApp enviados hoje
    c.execute("SELECT COUNT(*) as qtd FROM contatos WHERE date(data) = ? AND tipo_contato = 'WhatsApp'", (hoje,))
    whatsapp = c.fetchone()['qtd']
    
    # Contatos efetivos
    c.execute("SELECT COUNT(*) as qtd FROM contatos WHERE date(data) = ? AND resultado NOT IN ('Sem contato', 'Não atendeu')", (hoje,))
    efetivos = c.fetchone()['qtd']
    
    # Novos leads
    c.execute("SELECT COUNT(*) as qtd FROM leads WHERE date(data_criacao) = ?", (hoje,))
    novos_leads = c.fetchone()['qtd']

    c.execute("""
        SELECT COUNT(*) as qtd FROM prospeccao_temp
        WHERE data_prospeccao = ?
          AND (arquivado = 0 OR arquivado IS NULL)
    """, (hoje,))
    novas_prospeccoes = c.fetchone()['qtd']
    
    # Interessados e Negociações
    c.execute("SELECT COUNT(*) as qtd FROM leads WHERE status = 'Interessado'")
    interessados = c.fetchone()['qtd']
    
    c.execute("SELECT COUNT(*) as qtd FROM leads WHERE status = 'Negociação'")
    negociacoes = c.fetchone()['qtd']
    
    conn.close()
    
    return {
        'ligacoes': ligacoes,
        'whatsapp': whatsapp,
        'efetivos': efetivos,
        'novos_leads': novos_leads,
        'novas_prospeccoes': novas_prospeccoes,
        'interessados': interessados,
        'negociacoes': negociacoes
    }

def get_detalhes_relatorio_hoje():
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Pega detalhes de contatos feitos hoje
    c.execute('''
        SELECT c.resultado, c.observacao, l.nome_loja, l.status as status_final, l.cidade, l.estado
        FROM contatos c
        JOIN leads l ON c.lead_id = l.id
        WHERE date(c.data) = ?
        ORDER BY c.data DESC
    ''', (hoje,))
    detalhes = c.fetchall()
    conn.close()
    return detalhes

def get_relatorio_completo(data_inicio=None, data_fim=None):
    """Relatório completo para gestora: leads + prospecção"""
    if not data_inicio:
        data_inicio = date.today().isoformat()
    if not data_fim:
        data_fim = data_inicio
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # === DADOS DO CRM (LEADS) ===
    
    # Ligações realizadas no período
    c.execute("""
        SELECT COUNT(*) as qtd FROM contatos 
        WHERE date(data) BETWEEN ? AND ? AND tipo_contato = 'Ligação'
    """, (data_inicio, data_fim))
    ligacoes = c.fetchone()['qtd']
    
    # WhatsApp enviados no período
    c.execute("""
        SELECT COUNT(*) as qtd FROM contatos 
        WHERE date(data) BETWEEN ? AND ? AND tipo_contato = 'WhatsApp'
    """, (data_inicio, data_fim))
    whatsapp = c.fetchone()['qtd']
    
    # Contatos efetivos
    c.execute("""
        SELECT COUNT(*) as qtd FROM contatos 
        WHERE date(data) BETWEEN ? AND ? 
        AND resultado NOT IN ('Sem contato', 'Não atendeu', 'Pulado na fila')
    """, (data_inicio, data_fim))
    efetivos = c.fetchone()['qtd']
    
    # Novos leads no período
    c.execute("""
        SELECT COUNT(*) as qtd FROM leads 
        WHERE date(data_criacao) BETWEEN ? AND ?
    """, (data_inicio, data_fim))
    novos_leads = c.fetchone()['qtd']
    
    # Interessados e Negociações atuais
    c.execute("SELECT COUNT(*) as qtd FROM leads WHERE status = 'Interessado'")
    interessados = c.fetchone()['qtd']
    
    c.execute("SELECT COUNT(*) as qtd FROM leads WHERE status = 'Negociação'")
    negociacoes = c.fetchone()['qtd']
    
    # === DADOS DE PROSPECÇÃO (PRÉ-LISTA) ===
    
    # Total de prospecções no período
    c.execute("""
        SELECT COUNT(*) as qtd FROM prospeccao_temp 
        WHERE data_prospeccao BETWEEN ? AND ?
          AND (arquivado = 0 OR arquivado IS NULL)
    """, (data_inicio, data_fim))
    total_prospeccoes = c.fetchone()['qtd']
    
    # Tentativas de contato (tudo que não é 'Não contatado')
    c.execute("""
        SELECT COUNT(*) as qtd FROM prospeccao_temp 
        WHERE data_prospeccao BETWEEN ? AND ?
          AND (arquivado = 0 OR arquivado IS NULL)
        AND status_prospeccao != 'Não contatado'
    """, (data_inicio, data_fim))
    tentativas_prospeccao = c.fetchone()['qtd']
    
    # Por status da prospecção
    c.execute("""
        SELECT status_prospeccao, COUNT(*) as total
        FROM prospeccao_temp 
        WHERE data_prospeccao BETWEEN ? AND ?
          AND (arquivado = 0 OR arquivado IS NULL)
        GROUP BY status_prospeccao
    """, (data_inicio, data_fim))
    status_prospeccao = c.fetchall()
    
    # Convertidos em leads no período
    c.execute("""
        SELECT COUNT(*) as qtd FROM prospeccao_temp 
        WHERE data_prospeccao BETWEEN ? AND ?
          AND (arquivado = 0 OR arquivado IS NULL)
        AND convertido_lead_id IS NOT NULL
    """, (data_inicio, data_fim))
    convertidos = c.fetchone()['qtd']
    
    # Agendamentos de retorno
    c.execute("""
        SELECT COUNT(*) as qtd FROM prospeccao_temp 
        WHERE data_prospeccao BETWEEN ? AND ?
          AND (arquivado = 0 OR arquivado IS NULL)
        AND status_prospeccao = 'Pediu para retornar'
          AND data_retorno IS NOT NULL
    """, (data_inicio, data_fim))
    agendamentos = c.fetchone()['qtd']
    
    # Detalhes das prospecções do período
    c.execute("""
        SELECT * FROM prospeccao_temp 
        WHERE data_prospeccao BETWEEN ? AND ?
          AND (arquivado = 0 OR arquivado IS NULL)
        ORDER BY data_prospeccao DESC, data_criacao DESC
    """, (data_inicio, data_fim))
    detalhes_prospeccao = c.fetchall()
    
    # Detalhes dos leads do período (com CNPJ e Segmento)
    c.execute('''
        SELECT c.resultado, c.observacao, c.tipo_contato, 
               l.nome_loja, l.status as status_final, l.cidade, l.estado, 
               l.cnpj, date(c.data) as data,
               (SELECT GROUP_CONCAT(segmento, ', ') FROM segmentos_loja WHERE lead_id = l.id) as segmentos
        FROM contatos c
        JOIN leads l ON c.lead_id = l.id
        WHERE date(c.data) BETWEEN ? AND ?
        ORDER BY c.data DESC
    ''', (data_inicio, data_fim))
    detalhes_leads = c.fetchall()

    c.execute('''
        SELECT e.tipo_evento, e.detalhe,
               date(e.data_evento) as data,
               strftime('%H:%M', e.data_evento) as hora,
               e.data_retorno_antes, e.data_retorno_depois,
               p.nome_loja, p.cidade, p.estado, p.telefone, p.hora_retorno,
               p.segmento, p.cnpj
        FROM prospeccao_eventos e
        JOIN prospeccao_temp p ON p.id = e.prospeccao_id
        WHERE date(e.data_evento) BETWEEN ? AND ?
          AND e.tipo_evento IN ('RETORNO_TENTATIVA', 'RETORNO_REAGENDADO_AUTO', 'RETORNO_RESULTADO', 'STATUS_ATUALIZADO')
        ORDER BY e.data_evento DESC
    ''', (data_inicio, data_fim))
    detalhes_eventos_prospeccao = c.fetchall()

    c.execute('''
        SELECT COUNT(*) as qtd
        FROM prospeccao_eventos
        WHERE date(data_evento) BETWEEN ? AND ?
          AND tipo_evento = 'RETORNO_TENTATIVA'
    ''', (data_inicio, data_fim))
    tentativas_retorno_periodo = c.fetchone()['qtd']

    c.execute('''
        SELECT COUNT(*) as qtd
        FROM prospeccao_eventos
        WHERE date(data_evento) BETWEEN ? AND ?
          AND tipo_evento = 'RETORNO_REAGENDADO_AUTO'
    ''', (data_inicio, data_fim))
    reagendados_auto_periodo = c.fetchone()['qtd']
    
    conn.close()
    
    return {
        'periodo': {'inicio': data_inicio, 'fim': data_fim},
        # Métricas CRM
        'ligacoes': ligacoes,
        'whatsapp': whatsapp,
        'efetivos': efetivos,
        'novos_leads': novos_leads,
        'interessados': interessados,
        'negociacoes': negociacoes,
        # Métricas Prospecção
        'total_prospeccoes': total_prospeccoes,
        'tentativas_prospeccao': tentativas_prospeccao,
        'convertidos': convertidos,
        'agendamentos': agendamentos,
        'tentativas_retorno_periodo': tentativas_retorno_periodo,
        'reagendados_auto_periodo': reagendados_auto_periodo,
        'status_prospeccao': status_prospeccao,
        # Detalhes
        'detalhes_prospeccao': detalhes_prospeccao,
        'detalhes_leads': detalhes_leads,
        'detalhes_eventos_prospeccao': detalhes_eventos_prospeccao
    }
