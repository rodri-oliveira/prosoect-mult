import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Tabela leads
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_loja TEXT NOT NULL,
            cnpj TEXT,
            telefone TEXT,
            whatsapp TEXT,
            email TEXT,
            cidade TEXT,
            estado TEXT,
            endereco TEXT,
            responsavel TEXT,
            status TEXT DEFAULT 'Novo Lead',
            observacoes TEXT,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela segmentos_loja
    c.execute('''
        CREATE TABLE IF NOT EXISTS segmentos_loja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            segmento TEXT NOT NULL,
            FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela contatos
    c.execute('''
        CREATE TABLE IF NOT EXISTS contatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            data DATETIME DEFAULT CURRENT_TIMESTAMP,
            tipo_contato TEXT NOT NULL,
            resultado TEXT,
            observacao TEXT,
            FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela prospeccao_temp - rascunho de prospecção (mantém histórico permanente)
    c.execute('''
        CREATE TABLE IF NOT EXISTS prospeccao_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_loja TEXT NOT NULL,
            telefone TEXT,
            whatsapp TEXT,
            endereco TEXT,
            cidade TEXT,
            estado TEXT,
            segmento TEXT,
            status_prospeccao TEXT DEFAULT 'Não contatado',
            observacao TEXT,
            data_retorno DATE,
            data_prospeccao DATE DEFAULT CURRENT_DATE,
            arquivado BOOLEAN DEFAULT 0,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            convertido_lead_id INTEGER,
            FOREIGN KEY(convertido_lead_id) REFERENCES leads(id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Banco de dados inicializado com sucesso.")
