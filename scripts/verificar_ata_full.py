#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect('database.db')
c = conn.cursor()

print("Verificando ATA INFORMÁTICA detalhes:")
c.execute("""
    SELECT nome_loja, maps_place_id, maps_url, cidade, segmento, arquivado 
    FROM prospeccao_temp 
    WHERE nome_loja LIKE '%ATA%' AND cidade LIKE '%Mogi%'
""")
for row in c.fetchall():
    print(f"  Nome: {row[0]}")
    print(f"  maps_place_id: {row[1]}")
    print(f"  maps_url: {row[2][:60]}..." if row[2] else "  maps_url: None")
    print(f"  Cidade: {row[3]}")
    print(f"  Segmento: {row[4]}")
    print(f"  Arquivado: {row[5]}")
    print()

# Verificar se há duplicata
print("\nTodas as entradas com nome similar:")
c.execute("""
    SELECT nome_loja, maps_place_id, segmento, arquivado 
    FROM prospeccao_temp 
    WHERE nome_loja LIKE '%ATA%'
""")
for row in c.fetchall():
    print(f"  {row[0]} | {row[1][:30] if row[1] else 'N/A':<30} | {row[2]} | arquivado={row[3]}")

conn.close()
