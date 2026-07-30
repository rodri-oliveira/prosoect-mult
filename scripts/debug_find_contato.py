import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT id, nome_loja, status_prospeccao, data_retorno, hora_retorno, data_prospeccao, arquivado FROM prospeccao_temp WHERE id = 213")
row = c.fetchone()
if row:
    d = dict(row)
    print("=== Up Games Informática (ID=213) ===")
    for k, v in d.items():
        print(f"  {k}: {repr(v)}")
conn.close()
