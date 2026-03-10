import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database import DB_PATH

def get_leads(filtro_status=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if filtro_status:
        c.execute("SELECT * FROM leads WHERE status = ? ORDER BY id DESC", (filtro_status,))
    else:
        c.execute("SELECT * FROM leads ORDER BY id DESC")
    leads = c.fetchall()
    conn.close()
    return leads

def get_lead_by_id(lead_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    lead = c.fetchone()
    
    # get contatos
    c.execute("SELECT * FROM contatos WHERE lead_id = ? ORDER BY data DESC", (lead_id,))
    contatos = c.fetchall()
    
    # get segmentos
    c.execute("SELECT segmento FROM segmentos_loja WHERE lead_id = ?", (lead_id,))
    segmentos = [row['segmento'] for row in c.fetchall()]
    
    conn.close()
    return lead, contatos, segmentos

def create_lead(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO leads (nome_loja, telefone, whatsapp, cidade, estado, responsavel, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Novo Lead')
    ''', (data.get('nome_loja'), data.get('telefone'), data.get('whatsapp'), 
          data.get('cidade'), data.get('estado'), data.get('responsavel')))
    lead_id = c.lastrowid
    conn.commit()
    conn.close()
    return lead_id

def update_lead_status(lead_id, novo_status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE leads SET status = ? WHERE id = ?", (novo_status, lead_id))
    conn.commit()
    conn.close()

def add_contato(lead_id, data_contato):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO contatos (lead_id, tipo_contato, resultado, observacao)
        VALUES (?, ?, ?, ?)
    ''', (lead_id, data_contato.get('tipo_contato'), data_contato.get('resultado'), data_contato.get('observacao')))
    conn.commit()
    conn.close()
