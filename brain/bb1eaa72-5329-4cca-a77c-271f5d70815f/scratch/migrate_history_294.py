import sqlite3
import os

db_path = r'c:\projetos\prospect-mult\database.db'

def fix_history():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    lead_id = 4
    prospeccao_id = 294

    print(f"Migrando histórico para Lead {lead_id}...")

    # Limpar contatos existentes se houver (para evitar duplicidade do meu teste manual)
    c.execute("DELETE FROM contatos WHERE lead_id = ? AND tipo_contato = 'Prospecção'", (lead_id,))

    c.execute("SELECT * FROM prospeccao_eventos WHERE prospeccao_id = ?", (prospeccao_id,))
    eventos = c.fetchall()
    for ev in eventos:
        detalhe = ev['detalhe'] or ""
        if " | " in detalhe:
            res, obs = detalhe.split(" | ", 1)
        else:
            res, obs = detalhe, ""
            
        c.execute(
            """
            INSERT INTO contatos (lead_id, data, tipo_contato, resultado, observacao)
            VALUES (?, ?, ?, ?, ?)
        """,
            (lead_id, ev['data_evento'], "Prospecção", res, obs),
        )
    
    conn.commit()
    print(f"SUCESSO! {len(eventos)} eventos migrados.")
    conn.close()

if __name__ == "__main__":
    fix_history()
