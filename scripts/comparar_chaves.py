#!/usr/bin/env python3
import sys
sys.path.insert(0, 'c:\\projetos\\prospect-mult')

import sqlite3
from services.maps_scrape_service import derive_maps_place_id

conn = sqlite3.connect('database.db')
c = conn.cursor()

print("Comparando chaves do banco vs derivadas da URL:")
c.execute("""
    SELECT nome_loja, maps_place_id, maps_url
    FROM prospeccao_temp 
    WHERE cidade LIKE '%Mogi%' AND segmento = 'Informática'
    LIMIT 5
""")

for row in c.fetchall():
    nome = row[0]
    db_key = row[1] or 'N/A'
    url = row[2] or ''
    
    # Derivar chave da URL
    derived_key = derive_maps_place_id(url)
    
    print(f"\nNome: {nome}")
    print(f"  DB key:     {db_key}")
    print(f"  Derived:    {derived_key or 'N/A'}")
    print(f"  Match:      {'✅' if db_key == derived_key else '❌'}")
    if url:
        print(f"  URL:        {url[:80]}...")

conn.close()
