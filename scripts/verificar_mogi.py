#!/usr/bin/env python3
"""Verificar estrutura da tabela prospeccao_temp"""
import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

print("Prospecções em Mogi por segmento:")
c.execute("SELECT segmento, COUNT(*) FROM prospeccao_temp WHERE cidade LIKE '%Mogi%' GROUP BY segmento")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\nVerificando se ATA INFORMÁTICA existe:")
c.execute("SELECT nome_loja, maps_place_id, segmento FROM prospeccao_temp WHERE nome_loja LIKE '%ATA%' AND cidade LIKE '%Mogi%'")
for row in c.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]}")

print("\n" + "="*60)
print("Todas prospecções em Mogi:")
c.execute("""
    SELECT nome_loja, maps_place_id, segmento 
    FROM prospeccao_temp 
    WHERE cidade LIKE '%Mogi%'
    ORDER BY segmento
    LIMIT 20
""")
for row in c.fetchall():
    print(f"  • {row[0][:35]:<35} | {row[1][:30] if row[1] else 'N/A':<30} | {row[2]}")

conn.close()
