import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database import DB_PATH


def _normalize_segmentos(segmentos):
    if not segmentos:
        return []
    if isinstance(segmentos, (list, tuple)):
        values = segmentos
    else:
        values = str(segmentos).split(',')
    cleaned = []
    for s in values:
        s2 = str(s).strip()
        if s2:
            cleaned.append(s2)
    return cleaned

def get_leads(filtro_status=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if filtro_status:
        c.execute('''
            SELECT
                l.*,
                c2.tipo_contato as ultimo_tipo_contato,
                c2.resultado as ultimo_resultado,
                c2.observacao as ultimo_observacao,
                c2.data as ultimo_contato_data
            FROM leads l
            LEFT JOIN contatos c2 ON c2.id = (
                SELECT id FROM contatos
                WHERE lead_id = l.id
                ORDER BY data DESC
                LIMIT 1
            )
            WHERE l.status = ?
            ORDER BY l.id DESC
        ''', (filtro_status,))
    else:
        c.execute('''
            SELECT
                l.*,
                c2.tipo_contato as ultimo_tipo_contato,
                c2.resultado as ultimo_resultado,
                c2.observacao as ultimo_observacao,
                c2.data as ultimo_contato_data
            FROM leads l
            LEFT JOIN contatos c2 ON c2.id = (
                SELECT id FROM contatos
                WHERE lead_id = l.id
                ORDER BY data DESC
                LIMIT 1
            )
            ORDER BY l.id DESC
        ''')
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

    status = data.get('status') or 'Novo Lead'
    c.execute('''
        INSERT INTO leads (
            nome_loja, cnpj, telefone, whatsapp, email, cidade, estado, endereco, responsavel, status, observacoes, maps_place_id, maps_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('nome_loja'),
        data.get('cnpj'),
        data.get('telefone'),
        data.get('whatsapp'),
        data.get('email'),
        data.get('cidade'),
        data.get('estado'),
        data.get('endereco'),
        data.get('responsavel'),
        status,
        data.get('observacoes') or data.get('observacao'),
        (data.get('maps_place_id') or '').strip() or None,
        (data.get('maps_url') or '').strip() or None,
    ))
    lead_id = c.lastrowid

    segmentos = _normalize_segmentos(data.get('segmentos'))
    for seg in segmentos:
        c.execute('INSERT INTO segmentos_loja (lead_id, segmento) VALUES (?, ?)', (lead_id, seg))

    conn.commit()
    conn.close()

    return lead_id

def get_retornos_leads(data=None, mostrar_todos=False):
    from datetime import date as _date
    if not data:
        data = _date.today().isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if mostrar_todos:
        c.execute('''
            SELECT
                l.*,
                c2.data_retorno as data_retorno,
                c2.hora_retorno as hora_retorno,
                c2.tipo_contato as ultimo_tipo_contato,
                c2.resultado as ultimo_resultado,
                c2.observacao as ultimo_observacao,
                c2.data as ultimo_contato_data
            FROM leads l
            JOIN contatos c2 ON c2.id = (
                SELECT id FROM contatos
                WHERE lead_id = l.id AND data_retorno IS NOT NULL
                ORDER BY data DESC
                LIMIT 1
            )
            WHERE date(c2.data_retorno) >= date(?)
            ORDER BY date(c2.data_retorno) ASC
        ''', (data,))
    else:
        c.execute('''
            SELECT
                l.*,
                c2.data_retorno as data_retorno,
                c2.hora_retorno as hora_retorno,
                c2.tipo_contato as ultimo_tipo_contato,
                c2.resultado as ultimo_resultado,
                c2.observacao as ultimo_observacao,
                c2.data as ultimo_contato_data
            FROM leads l
            JOIN contatos c2 ON c2.id = (
                SELECT id FROM contatos
                WHERE lead_id = l.id AND data_retorno IS NOT NULL
                ORDER BY data DESC
                LIMIT 1
            )
            WHERE date(c2.data_retorno) = date(?)
            ORDER BY (c2.hora_retorno IS NULL) ASC, c2.hora_retorno ASC, c2.data DESC
        ''', (data,))

    rows = c.fetchall()
    conn.close()
    return rows

def get_retornos_leads_atrasados(data=None):
    from datetime import date as _date
    if not data:
        data = _date.today().isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('''
        SELECT
            l.*,
            c2.data_retorno as data_retorno,
            c2.hora_retorno as hora_retorno,
            c2.tipo_contato as ultimo_tipo_contato,
            c2.resultado as ultimo_resultado,
            c2.observacao as ultimo_observacao,
            c2.data as ultimo_contato_data
        FROM leads l
        JOIN contatos c2 ON c2.id = (
            SELECT id FROM contatos
            WHERE lead_id = l.id AND data_retorno IS NOT NULL
            ORDER BY data DESC
            LIMIT 1
        )
        WHERE date(c2.data_retorno) < date(?)
        ORDER BY date(c2.data_retorno) ASC
    ''', (data,))

    rows = c.fetchall()
    conn.close()
    return rows

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
        INSERT INTO contatos (lead_id, tipo_contato, resultado, observacao, data_retorno, hora_retorno)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        lead_id,
        data_contato.get('tipo_contato'),
        data_contato.get('resultado'),
        data_contato.get('observacao'),
        data_contato.get('data_retorno'),
        data_contato.get('hora_retorno'),
    ))
    conn.commit()
    conn.close()
