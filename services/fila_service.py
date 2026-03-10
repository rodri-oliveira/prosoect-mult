import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database import DB_PATH

def get_proximo_lead():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # Pega o lead com base nos status focos que estão há mais tempo sem interação
    c.execute('''
        SELECT leads.*, 
               IFNULL((SELECT MAX(data) FROM contatos WHERE lead_id = leads.id), '0000-00-00') as ultimo_contato
        FROM leads 
        WHERE status IN ('Novo Lead', 'Tentativa 1', 'Tentativa 2', 'Tentativa 3', 'Sem contato')
        ORDER BY ultimo_contato ASC, id ASC
        LIMIT 1
    ''')
    lead = c.fetchone()
    conn.close()
    return lead

def processa_acao_fila(lead_id, acao, observacao=''):
    from services.lead_service import add_contato, update_lead_status
    if acao == 'Ligar':
        add_contato(lead_id, {'tipo_contato': 'Ligação', 'resultado': 'Tentativa (Fila)', 'observacao': observacao})
    elif acao == 'WhatsApp':
        add_contato(lead_id, {'tipo_contato': 'WhatsApp', 'resultado': 'Mensagem Enviada (Fila)', 'observacao': observacao})
    elif acao == 'Sem contato':
        add_contato(lead_id, {'tipo_contato': 'Ligação', 'resultado': 'Sem contato', 'observacao': observacao})
        update_lead_status(lead_id, 'Sem contato')
    elif acao == 'Interessado':
        add_contato(lead_id, {'tipo_contato': 'Ligação', 'resultado': 'Interessado', 'observacao': observacao or 'Marcado via Fila'})
        update_lead_status(lead_id, 'Interessado')

def get_total_fila():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM leads 
        WHERE status IN ('Novo Lead', 'Tentativa 1', 'Tentativa 2', 'Tentativa 3', 'Sem contato')
    ''')
    total = c.fetchone()[0]
    conn.close()
    return total

