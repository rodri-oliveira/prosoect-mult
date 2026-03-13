import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("=== VERIFICANDO DUPLICIDADE ===\n")

# Verificar se há leads com maps_place_id
print("1. LEADS COM MAPS_PLACE_ID:")
c.execute("SELECT id, nome_loja, maps_place_id, maps_url FROM leads WHERE maps_place_id IS NOT NULL OR maps_url IS NOT NULL LIMIT 10")
leads = c.fetchall()
if leads:
    for row in leads:
        print(f"   Lead {row[0]}: {row[1]} | place_id={row[2]} | url={row[3]}")
else:
    print("   Nenhum lead encontrado com maps_place_id/url")

# Verificar prospeccoes convertidas
print("\n2. PROSPECÇÕES CONVERTIDAS:")
c.execute("SELECT id, nome_loja, maps_place_id, convertido_lead_id FROM prospeccao_temp WHERE convertido_lead_id IS NOT NULL LIMIT 10")
prospeccoes = c.fetchall()
if prospeccoes:
    for row in prospeccoes:
        print(f"   Prospecção {row[0]}: {row[1]} | place_id={row[2]} -> Lead {row[3]}")
else:
    print("   Nenhuma prospecção convertida encontrada")

# Verificar se há itens duplicados (mesmo place_id em prospeccao e lead)
print("\n3. VERIFICANDO POSSÍVEIS DUPLICADOS:")
c.execute("""
    SELECT p.id, p.nome_loja, p.maps_place_id, l.id, l.nome_loja 
    FROM prospeccao_temp p
    JOIN leads l ON p.maps_place_id = l.maps_place_id
    WHERE p.maps_place_id IS NOT NULL AND p.arquivado = 0
    LIMIT 5
""")
duplicados = c.fetchall()
if duplicados:
    for row in duplicados:
        print(f"   PlaceID {row[2]}: Prospecção {row[0]} ({row[1]}) -> Lead {row[3]} ({row[4]})")
else:
    print("   Nenhum duplicado encontrado (mesmo place_id em prospeccao ativa e lead)")

conn.close()
print("\n=== FIM ===")
