#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect('database.db')
c = conn.cursor()
print("ATA INFORMÁTICA no banco:")
c.execute("SELECT nome_loja, maps_place_id, maps_url, segmento FROM prospeccao_temp WHERE nome_loja LIKE '%ATA%' AND cidade LIKE '%Mogi%'")
for row in c.fetchall():
    print(f"  Nome: {row[0]}")
    print(f"  maps_place_id: {row[1]}")
    print(f"  maps_url: {row[2]}")
    print(f"  segmento: {row[3]}")
    print()
conn.close()
