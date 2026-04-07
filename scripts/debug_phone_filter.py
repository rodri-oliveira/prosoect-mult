
import sqlite3
import os

DB_PATH = 'database.db'

def debug_phone_search(phone_number):
    if not os.path.exists(DB_PATH):
        print(f"Erro: Banco de dados não encontrado em {DB_PATH}")
        return

    tel_clean = "".join(filter(str.isdigit, phone_number))
    print(f"Buscando por números limpos: {tel_clean}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Buscar todos para ver o que temos
    print("\n--- Amostra de Prospecções (Top 5) ---")
    c.execute("SELECT id, nome_loja, telefone, whatsapp FROM prospeccao_temp LIMIT 5")
    for row in c.fetchall():
        print(f"ID: {row['id']} | Nome: {row['nome_loja']} | Tel: {row['telefone']} | Whats: {row['whatsapp']}")

    # 2. Testar a query exata usada no repositório
    print(f"\n--- Testando Query do Repositório para: {phone_number} ---")
    query = """
        SELECT id, nome_loja, telefone, whatsapp 
        FROM prospeccao_temp 
        WHERE (replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', '') LIKE ? 
           OR replace(replace(replace(replace(whatsapp, '(', ''), ')', ''), '-', ''), ' ', '') LIKE ?)
    """
    params = (f"%{tel_clean}%", f"%{tel_clean}%")
    c.execute(query, params)
    results = c.fetchall()
    
    if results:
        print(f"Encontrados {len(results)} resultados:")
        for row in results:
            print(f"ID: {row['id']} | Nome: {row['nome_loja']} | Tel: {row['telefone']} | Whats: {row['whatsapp']}")
    else:
        print("Nenhum resultado encontrado com a query do repositório.")

    # 3. Busca por nome aproximado se falhar o telefone (para ver se o registro existe)
    print("\n--- Busca por qualquer registro com '11942153458' no texto ---")
    c.execute("SELECT id, nome_loja, telefone, whatsapp FROM prospeccao_temp WHERE telefone LIKE ? OR whatsapp LIKE ?", (f"%{tel_clean}%", f"%{tel_clean}%"))
    results = c.fetchall()
    for row in results:
        print(f"ID: {row['id']} | Nome: {row['nome_loja']} | Tel: {row['telefone']} | Whats: {row['whatsapp']}")

    conn.close()

if __name__ == "__main__":
    debug_phone_search("1194215-3458")
