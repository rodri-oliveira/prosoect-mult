import sqlite3
import re
from urllib.parse import urlparse, parse_qs

def derive_maps_place_id(maps_url):
    maps_url = (maps_url or '').strip()
    if not maps_url:
        return ''
    try:
        parsed = urlparse(maps_url)
        qs = parse_qs(parsed.query or '')
        cid = (qs.get('cid') or [''])[0].strip()
        if cid and cid.isdigit():
            return f"cid:{cid}"
    except:
        pass
    m = re.search(r'(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)', maps_url)
    if m:
        return f"ftid:{m.group(1).lower()}"
    return ''

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# O FLUXO REAL:
# 1. Scraper retorna item com maps_place_id = "ftid:0xABC:0xDEF" (derivado da URL)
# 2. Frontend faz: setVal('f_maps_place_id', enriched.maps_place_id || enriched.id || '')
# 3. Frontend submete: payload.maps_place_id = valor do campo f_maps_place_id
# 4. Backend: api_rascunho_novo -> data["maps_place_id"] = (data.get("maps_place_id") or "").strip()
# 5. Backend: repo.add() -> WHERE maps_place_id = ?

# MAS ESPERA! Olhando o maps-results.js linha 277:
# setVal('f_maps_place_id', enriched.maps_place_id || enriched.id || '');
#
# E o scraper (maps_scrape_service.py linha 351-355):
# maps_place_id = derive_maps_place_id(href)  -> "ftid:0x..."
# place_key = maps_place_id or hashlib.sha1(href).hexdigest()[:16]
# "id": place_key,
# "maps_place_id": maps_place_id or place_key,
#
# Entao:
# - Se derive retorna algo -> maps_place_id = "ftid:0x...", id = "ftid:0x..."
# - Se derive retorna vazio -> maps_place_id = SHA1[:16], id = SHA1[:16]
#
# O backend repo.add() busca: WHERE maps_place_id = "ftid:0x..."
# Isso so bate se EXATAMENTE esse ftid ja existe no banco

# VAMOS VERIFICAR: Tem alguma loja no banco cuja maps_url aponte para o MESMO maps_place_id
# que "Ponto Com Informatica Pindamonhangaba" teria?

# Nao temos a URL do Ponto Com, mas podemos verificar se algum maps_place_id
# no banco pertence a uma loja de outra cidade que NAO eh "ponto com"
# -> Isso indicaria que o scraper esta retornando URLs erradas

# HIPOTESE NOVA: E se o problema nao eh colisao de chave, mas sim que o
# frontend NAO esta usando a chave derivada corretamente?
# 
# Olhando api_rascunho_novo (interfaces/api/routes.py linhas 169-170):
#   data["maps_place_id"] = (data.get("maps_place_id") or "").strip()
#   data["maps_url"] = (data.get("maps_url") or "").strip()
#
# E o create_draft.py recebe maps_place_id e maps_url do form
# E o repo.add() faz:
#   maps_place_id = (dados.get("maps_place_id") or "").strip() or None
#   -> busca WHERE maps_place_id = ? com esse valor DIRETO
#
# MAS NO REPO DE EXISTING KEYS (sqlite_maps_existing_keys_repository.py):
#   -> Ele busca maps_place_id E TAMBEM derive_maps_place_id(maps_url)
#   -> Ou seja, o existing_keys pode ter DUAS chaves por registro
#
# ENTAO: No repo.add(), so verifica maps_place_id DIRETO
# Mas e se o maps_place_id do item novo != maps_place_id salvo,
# POREM o derive(maps_url) do novo == derive(maps_url) do salvo?

# ISSO NAO IMPORTA AQUI porque o add() so faz WHERE maps_place_id = ?
# Se nao bater exato, vai para verificacao 2 (CNPJ) e depois 3 (nome)

# ENTAO A QUESTAO REAL: se "Ponto Com" nao existe no banco com nenhum maps_place_id,
# e nao existe com nenhum CNPJ, e nao existe com nome+cidade+estado...
# POR QUE O BACKEND RETORNA created=False?

# VAMOS LOGAR O QUE REALMENTE ACONTECE!
# Adicionar logging temporario ao repo.add()

print("CONCLUSAO DA INVESTIGACAO:")
print()
print("O item 'Ponto Com Informatica Pindam' NAO existe no banco de NENHUMA forma:")
print("  - Nao encontrado por maps_place_id")
print("  - Nao encontrado por CNPJ")
print("  - Nao encontrado por nome+cidade+estado")
print()
print("POSSIBILIDADES RESTANTES:")
print()
print("  1. O maps_place_id enviado pelo form COLIDE com outra loja")
print("     (mesmo ftid para lojas diferentes - bug do Google Maps)")
print()
print("  2. O frontend esta enviando maps_place_id de OUTRA loja")
print("     (bug de cache/estado no JS)")
print()
print("  3. O frontend nao esta limpando o campo f_maps_place_id")
print("     entre usos do botao 'Usar'")
print()

# Vamos verificar se o maps_place_id enviado pertence a outra loja
# Para isso, precisamos ver os logs do servidor
# Mas podemos tambem verificar uma coisa: o formulario LIMPA o maps_place_id?

# Em maps-results.js, apos submit bem-sucedido (linha 659-664):
# const elMpid = document.getElementById('f_maps_place_id');
# if (elMpid) elMpid.value = '';
# 
# Mas se o submit FALHA (created=false), o campo NAO eh limpo!
# E da proxima vez que o usuario clicar "Usar" em outro item,
# o maps_place_id sera SUBSTITUIDO pelo novo item.

# POREM: O useItem() (linha 267-268) faz:
# const currentKey = String(it.maps_place_id || it.id || '').trim();
# window.__mapsUseCurrentKey = currentKey;
# E na linha 277:
# setVal('f_maps_place_id', enriched.maps_place_id || enriched.id || '');
# Entao o campo sempre eh atualizado com o novo item.

# ENTAO O BUG PRECISA SER UM DESTES:
# A) O maps_place_id da "Ponto Com" eh identico ao de outra loja no banco
# B) Algo no fluxo JS esta misturando dados

# Para descobrir qual, preciso adicionar logging ao backend
print("ACAO RECOMENDADA:")
print("Adicionar logging ao repo.add() para ver EXATAMENTE qual")
print("maps_place_id esta sendo enviado e qual registro esta batendo")

conn.close()
