import sqlite3

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 80)
print("1. BUSCANDO 'Ponto Com' em prospeccao_temp")
print("=" * 80)
c.execute("""
    SELECT id, nome_loja, cidade, estado, maps_place_id, maps_url, status_prospeccao, arquivado
    FROM prospeccao_temp
    WHERE nome_loja LIKE '%Ponto Com%' OR nome_loja LIKE '%ponto com%'
""")
rows = c.fetchall()
print(f"Encontrados: {len(rows)}")
for r in rows:
    print(dict(r))

print()
print("=" * 80)
print("2. BUSCANDO 'Ponto Com' em leads")
print("=" * 80)
c.execute("""
    SELECT id, nome_loja, cidade, estado, maps_place_id, maps_url, status
    FROM leads
    WHERE nome_loja LIKE '%Ponto Com%' OR nome_loja LIKE '%ponto com%'
""")
rows2 = c.fetchall()
print(f"Encontrados: {len(rows2)}")
for r in rows2:
    print(dict(r))

print()
print("=" * 80)
print("3. BUSCANDO 'Pindam' em prospeccao_temp")
print("=" * 80)
c.execute("""
    SELECT id, nome_loja, cidade, estado, maps_place_id, maps_url, status_prospeccao, arquivado
    FROM prospeccao_temp
    WHERE nome_loja LIKE '%Pindam%' OR cidade LIKE '%Pindam%'
""")
rows3 = c.fetchall()
print(f"Encontrados: {len(rows3)}")
for r in rows3:
    print(dict(r))

print()
print("=" * 80)
print("4. BUSCANDO 'Pindam' em leads")
print("=" * 80)
c.execute("""
    SELECT id, nome_loja, cidade, estado, maps_place_id, maps_url, status
    FROM leads
    WHERE nome_loja LIKE '%Pindam%' OR cidade LIKE '%Pindam%'
""")
rows4 = c.fetchall()
print(f"Encontrados: {len(rows4)}")
for r in rows4:
    print(dict(r))

print()
print("=" * 80)
print("5. TODAS AS CHAVES existentes no existing_keys (prospeccao + leads)")
print("=" * 80)

from services.maps_scrape_service import derive_maps_place_id

# Prospeccao
c.execute("""
    SELECT id, nome_loja, maps_place_id, maps_url, cidade
    FROM prospeccao_temp
    WHERE ((maps_place_id IS NOT NULL AND maps_place_id != '') OR (maps_url IS NOT NULL AND maps_url != ''))
      AND (arquivado = 0 OR arquivado IS NULL)
""")
prosp_rows = c.fetchall()
print(f"\nProspeccao_temp com chave (nao arquivados): {len(prosp_rows)}")

prosp_keys = set()
for r in prosp_rows:
    mpid = (r['maps_place_id'] or '').strip()
    mu = (r['maps_url'] or '').strip()
    if mpid:
        prosp_keys.add(mpid)
    if mu:
        dk = derive_maps_place_id(mu)
        if dk:
            prosp_keys.add(dk)

print(f"Total chaves unicas de prospeccao: {len(prosp_keys)}")

# Leads
c.execute("""
    SELECT id, nome_loja, maps_place_id, maps_url, cidade
    FROM leads
    WHERE (maps_place_id IS NOT NULL AND maps_place_id != '') OR (maps_url IS NOT NULL AND maps_url != '')
""")
lead_rows = c.fetchall()
print(f"Leads com chave: {len(lead_rows)}")

lead_keys = set()
for r in lead_rows:
    mpid = (r['maps_place_id'] or '').strip()
    mu = (r['maps_url'] or '').strip()
    if mpid:
        lead_keys.add(mpid)
    if mu:
        dk = derive_maps_place_id(mu)
        if dk:
            lead_keys.add(dk)

print(f"Total chaves unicas de leads: {len(lead_keys)}")

all_keys = prosp_keys | lead_keys
print(f"\nTotal de chaves COMBINADAS no banco: {len(all_keys)}")

# Agora vamos simular a chave que "Ponto Com Informática" teria
# Precisamos da maps_url ou maps_place_id desse item
print()
print("=" * 80)
print("6. Verificando se 'Ponto Com' tem uma chave que colide com outra loja")
print("=" * 80)

# Buscar TODOS os registros que tem maps_place_id duplicado ou vazio
c.execute("""
    SELECT id, nome_loja, cidade, maps_place_id, maps_url
    FROM prospeccao_temp
    WHERE (arquivado = 0 OR arquivado IS NULL)
    ORDER BY id DESC
    LIMIT 300
""")
all_prosp = c.fetchall()

# Verificar se alguma maps_place_id aparece mais de uma vez
from collections import Counter
key_counter = Counter()
key_to_names = {}
for r in all_prosp:
    mpid = (r['maps_place_id'] or '').strip()
    mu = (r['maps_url'] or '').strip()
    dk = ''
    if mu:
        dk = derive_maps_place_id(mu)
    
    effective_key = dk or mpid
    if effective_key:
        key_counter[effective_key] += 1
        if effective_key not in key_to_names:
            key_to_names[effective_key] = []
        key_to_names[effective_key].append(f"id={r['id']} | {r['nome_loja']} | {r['cidade']}")

duplicates = {k: v for k, v in key_counter.items() if v > 1}
if duplicates:
    print(f"\n⚠️  CHAVES DUPLICADAS ENCONTRADAS: {len(duplicates)}")
    for k, count in duplicates.items():
        print(f"\n  Chave: {k} (aparece {count}x)")
        for name in key_to_names[k]:
            print(f"    → {name}")
else:
    print("Nenhuma chave duplicada encontrada.")

# Verificar registros sem chave
no_key = [r for r in all_prosp if not (r['maps_place_id'] or '').strip() and not (r['maps_url'] or '').strip()]
print(f"\nRegistros SEM chave (maps_place_id e maps_url vazios): {len(no_key)}")
for r in no_key[:10]:
    print(f"  id={r['id']} | {r['nome_loja']} | {r['cidade']}")

conn.close()
