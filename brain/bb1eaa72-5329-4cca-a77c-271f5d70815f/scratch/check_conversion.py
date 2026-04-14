import sqlite3
import os

db_path = r'c:\projetos\prospect-mult\database.db'

def check_db():
    if not os.path.exists(db_path):
        print(f"Banco não encontrado em {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    print("--- ÚLTIMOS 5 LEADS ---")
    c.execute("SELECT id, nome_loja, status, data_criacao FROM leads ORDER BY id DESC LIMIT 5")
    for row in c.fetchall():
        print(f"ID: {row['id']} | Loja: {row['nome_loja']} | Status: {row['status']} | Criado em: {row['data_criacao']}")

    print("\n--- ÚLTIMAS 5 PROSPECÇÕES ---")
    c.execute("SELECT id, nome_loja, status_prospeccao, arquivado, convertido_lead_id FROM prospeccao_temp ORDER BY id DESC LIMIT 5")
    for row in c.fetchall():
        print(f"ID: {row['id']} | Loja: {row['nome_loja']} | Status: {row['status_prospeccao']} | Arquivado: {row['arquivado']} | Lead ID: {row['convertido_lead_id']}")

    conn.close()

if __name__ == "__main__":
    check_db()
