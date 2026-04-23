from __future__ import annotations

from dataclasses import dataclass
import logging
import time
import unicodedata
from typing import Any

from domain.repositories.maps_existing_keys_repository import MapsExistingKeysRepository
from infrastructure.repositories.sqlite_maps_existing_keys_repository import SqliteMapsExistingKeysRepository


@dataclass(frozen=True)
class SearchMapsResultsRequest:
    query: str
    cidade: str
    estado: str
    segmentos: list[str]
    limit: int


@dataclass(frozen=True)
class SearchMapsResultsResponse:
    ok: bool
    modo: str
    query: str
    message: str | None
    existing_keys: list[str]
    items: list[dict[str, Any]]
    executed_queries: list[str]
    query_stats: list[dict[str, Any]]
    merged_before_dedupe: int
    merged_after_dedupe: int


@dataclass(frozen=True)
class GenerateQueriesResponse:
    ok: bool
    queries: list[dict[str, str]]  # [{"q": "...", "segmento": "..."}]
    primary_query: str  # Query principal para iframe
    total_queries: int


def generate_queries_for_segments(
    segmentos: list[str],
    cidade: str,
    estado: str,
    extra: str = "",
) -> GenerateQueriesResponse:
    """Gera lista de queries para segmentos sem executar scraper.
    
    Usado para sincronizar o botão Buscar com o Resultado Beta.
    Retorna a query principal para o iframe e todas as queries para o drawer.
    """
    segs = [s for s in (segmentos or []) if (s or "").strip()]
    
    if not segs:
        # Fallback: query genérica
        local = ", ".join([p for p in [cidade, estado] if (p or "").strip()])
        if local:
            local = f" em {local}"
        q = f"{extra}{local}".strip() if extra else f"lojas{local}".strip()
        return GenerateQueriesResponse(
            ok=True,
            queries=[{"q": q, "segmento": ""}],
            primary_query=q,
            total_queries=1,
        )
    
    queries = _build_queries_for_segments(segs=segs, cidade=cidade, estado=estado, extra=extra)
    
    # Query principal: primeira query (mais genérica/relevante)
    primary_query = queries[0]["q"] if queries else ""
    
    return GenerateQueriesResponse(
        ok=True,
        queries=queries,
        primary_query=primary_query,
        total_queries=len(queries),
    )


def search_maps_results(req: SearchMapsResultsRequest) -> SearchMapsResultsResponse:
    return search_maps_results_with_repo(req, SqliteMapsExistingKeysRepository())


def search_maps_results_with_repo(
    req: SearchMapsResultsRequest,
    existing_keys_repo: MapsExistingKeysRepository,
) -> SearchMapsResultsResponse:
    logger = logging.getLogger(__name__)
    query = (req.query or "").strip()
    cidade = (req.cidade or "").strip()
    estado = (req.estado or "").strip()
    segmentos = req.segmentos or []

    limit = int(req.limit or 20)
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200

    itens: list[dict[str, Any]] = []
    modo = "mock"
    message: str | None = None
    executed_queries: list[str] = []
    query_stats: list[dict[str, Any]] = []
    merged_before_dedupe = 0
    merged_after_dedupe = 0

    segs = [s for s in (segmentos or []) if (s or "").strip()]
    endereco_base = cidade + (f"/{estado}" if estado else "")

    if query:
        query_real = ""
        if segs:
            query_specs = _build_queries_for_segments(segs=segs, cidade=cidade, estado=estado, extra=query)
        else:
            query_specs = [{"q": q, "segmento": ""} for q in _build_queries_for_free_text(query=query, cidade=cidade, estado=estado)]

        executed_queries = []

        try:
            from services.maps_scrape_service import scrape_maps_results

            merged: list[dict[str, Any]] = []
            per_query_limit = min(50, limit)
            
            # Rastrear lojas únicas por query para análise de overlap
            seen_keys_total: set[str] = set()
            
            for spec in query_specs:
                q = (spec.get("q") or "").strip()
                seg = (spec.get("segmento") or "").strip()
                if not q:
                    continue
                executed_queries.append(q)
                t0 = time.time()
                got = scrape_maps_results(q, limit=per_query_limit, headless=True)
                dt_ms = int((time.time() - t0) * 1000)
                
                # Enriquecer itens com segmento e fonte da query (antes dos filtros)
                for it in (got or []):
                    if seg:
                        cur = it.get("segmentos")
                        if not isinstance(cur, list):
                            cur = []
                        if seg not in cur:
                            cur.append(seg)
                        it["segmentos"] = cur
                    src = it.get("query_sources")
                    if not isinstance(src, list):
                        src = []
                    if q not in src:
                        src.append(q)
                    it["query_sources"] = src

                # Filtrar varejo grande dos resultados (Google Maps não respeita exclusão)
                got = _filter_large_retail(got or [])

                # Filtro: remover a própria cidade retornada como se fosse um negócio
                if cidade:
                    got = _filter_city_page_results(got or [], cidade=cidade)

                # Filtro semântico por segmento
                # Para drones: filtro leve (só remove aluguel/locação, não bloqueia lojas genéricas)
                got = _filter_segment_noise(got or [], seg=seg)

                # Filtro conservador: remover itens que declaram outra cidade no nome
                # Ex: "Loja Zema - Casa Branca" quando o alvo é "Aguaí"
                if cidade:
                    got = _filter_items_with_other_city_in_name(got or [], cidade=cidade)
                
                # Filtro geográfico estrito: remove itens que o scraper identificou como estando em outra cidade
                if cidade:
                    got = _filter_strict_city(got or [], cidade=cidade)

                # Calcular new_unique APÓS filtros → stats refletem o que realmente entra
                new_keys: set[str] = set()
                for it in (got or []):
                    k = _key_from_item(it)
                    if k and k not in seen_keys_total:
                        new_keys.add(k)

                # Atualizar total de lojas únicas
                seen_keys_total.update(new_keys)

                # Log detalhado com estatísticas e nomes das lojas
                lojas_nomes = [it.get("nome", "?")[:30] for it in (got or [])[:5]]
                logger.warning(
                    "maps_query ms=%s items=%s new_unique=%s total_unique=%s segmento=%s q=%s lojas=%s",
                    dt_ms,
                    len(got or []),
                    len(new_keys),
                    len(seen_keys_total),
                    seg or "-",
                    q,
                    lojas_nomes,
                )

                query_stats.append({
                    "q": q,
                    "segmento": seg or None,
                    "ms": dt_ms,
                    "items": len(got or []),
                    "new_unique": len(new_keys),
                    "total_unique": len(seen_keys_total),
                })
                merged.extend(got)
                
                # Evita gastar queries quando jÃ¡ atingiu o limite Ãºnico desejado
                if limit and len(seen_keys_total) >= limit:
                    logger.warning(
                        "maps_early_stop reason=limit_reached total_unique=%s limit=%s",
                        len(seen_keys_total),
                        limit,
                    )
                    break

            merged_before_dedupe = len(merged)
            merged = _dedupe_items(merged)
            merged_after_dedupe = len(merged)

            # Log final com resumo (valores reais do retorno)
            logger.warning(
                "maps_summary total_queries=%s before_dedupe=%s after_dedupe=%s total_unique_keys=%s",
                len(executed_queries),
                merged_before_dedupe,
                merged_after_dedupe,
                len(seen_keys_total),
            )
            # Ordenação Estratégica: Fixo > Celular > Outros
            def _get_sort_priority(it: dict[str, Any]) -> int:
                tel = str(it.get("telefone") or "").strip()
                # Limpa apenas dígitos
                clean = "".join(ch for ch in tel if ch.isdigit())
                # Se tem DDD (10 ou 11 dígitos), o 3º dígito é o definidor
                if len(clean) >= 10:
                    first = clean[2]
                    if first in ('2', '3', '4', '5'): return 1 # Fixo
                    if first == '9': return 2 # Celular
                elif len(clean) > 0:
                    # Sem DDD, pega o 1º dígito
                    first = clean[0]
                    if first in ('2', '3', '4', '5'): return 1 
                    if first == '9': return 2
                return 3 # Outros/Sem tel

            merged.sort(key=_get_sort_priority)
            
            itens = merged[:limit]
            for it in itens:
                it["cidade"] = it.get("cidade") or cidade
                it["estado"] = it.get("estado") or estado
                if segs:
                    it["segmentos"] = it.get("segmentos") or []
                else:
                    it["segmentos"] = it.get("segmentos") or segs

            modo = "real"
            query_real = executed_queries[0] if executed_queries else ""
        except Exception as e:
            message = str(e)
            itens = []
            for i in range(1, limit + 1):
                itens.append(
                    {
                        "id": f"mock-{i}",
                        "nome": f"Resultado Exemplo {i} ({query})",
                        "endereco": endereco_base,
                        "telefone": f"(11) 9000{i:02d}-000{i%10}",
                        "whatsapp": f"(11) 9000{i:02d}-000{i%10}",
                        "website": "",
                        "maps_url": f"https://www.google.com/maps/search/{query}",
                        "cidade": cidade,
                        "estado": estado,
                        "segmentos": segs,
                    }
                )
            modo = "mock"
            merged_before_dedupe = len(itens)
            merged_after_dedupe = len(itens)

    existing_data = existing_keys_repo.get_existing_maps_keys()
    existing_keys = _find_existing_keys(itens, existing_keys_repo)
    
    # DEBUG: Log detalhado de chaves
    if existing_keys:
        logger.warning("[DEBUG] Total existing_keys encontradas: %s", len(existing_keys))
        logger.warning("[DEBUG] Amostra existing_keys: %s", existing_keys[:5])
    
    # DEBUG: Verificar chaves dos primeiros itens
    for idx, it in enumerate(itens[:3]):
        k = _key_from_item(it)
        nome = it.get("nome", "?")
        logger.warning("[DEBUG] Item %s: nome=%s | key=%s | in_existing=%s", 
                      idx, nome, k, k in existing_keys if existing_keys else False)

    if existing_keys:
        existing_set = set(existing_keys)
        for it in itens or []:
            k = _key_from_item(it)
            if k and k in existing_set:
                it["already_added"] = True
                it["existing_status"] = existing_data.key_status_map.get(k) if existing_data.key_status_map else None
                logger.warning("[DEBUG] Marcado already_added: nome=%s | key=%s | status=%s", 
                              it.get("nome", "?"), k, it["existing_status"])

    return SearchMapsResultsResponse(
        ok=True,
        modo=modo,
        query=query,
        message=message,
        existing_keys=existing_keys,
        items=itens,
        executed_queries=executed_queries,
        query_stats=query_stats,
        merged_before_dedupe=int(merged_before_dedupe),
        merged_after_dedupe=int(merged_after_dedupe),
    )


def _key_from_item(it: dict[str, Any]) -> str:
    try:
        from services.maps_scrape_service import derive_maps_place_id
    except Exception:
        derive_maps_place_id = None

    u = str(it.get("maps_url") or "").strip()
    if u and derive_maps_place_id:
        try:
            dk = derive_maps_place_id(u)
            if dk:
                return dk
        except Exception:
            pass
    k = str(it.get("maps_place_id") or it.get("id") or "").strip()
    if k:
        return k
    return ""


def _find_existing_keys(
    items: list[dict[str, Any]],
    existing_keys_repo: MapsExistingKeysRepository,
) -> list[str]:
    incoming_keys = []
    for it in items or []:
        k = _key_from_item(it)
        if k:
            incoming_keys.append(k)

    incoming_set = set(incoming_keys)
    if not incoming_set:
        return []

    existing = existing_keys_repo.get_existing_maps_keys()
    existing_set = set(existing.prospeccao_keys or set()).union(set(existing.lead_keys or set()))

    matched = incoming_set.intersection(existing_set)
    return sorted(matched)


def _build_queries_for_free_text(query: str, cidade: str, estado: str) -> list[str]:
    base = (query or "").strip()
    if not base:
        return []
    
    cidade_clean = (cidade or "").strip()
    estado_clean = (estado or "").strip()
    local_parts = []
    if cidade_clean:
        local_parts.append(f'"{cidade_clean}"')
    if estado_clean:
        local_parts.append(estado_clean)
        
    local = ", ".join(local_parts)
    if local:
        return [f"{base} em {local}"]
    return [base]


def _filter_segment_noise(results: list[dict], seg: str) -> list[dict]:
    """Filtro semântico por segmento: descarta estabelecimentos que claramente
    não vendem os produtos do segmento alvo, mesmo que tenham aparecido na busca.
    """
    seg_clean = (seg or "").strip().lower()

    if "drone" in seg_clean:
        return _filter_noise_drones(results)

    if "inform" in seg_clean:
        return _filter_noise_informatica(results)

    if "sennheiser" in seg_clean:
        return _filter_noise_sennheiser(results)

    return results


# Termos que CONFIRMAM que é um negócio de drones/aeromodelismo
_DRONE_POSITIVE_TERMS = [
    "drone", "dji", "fpv", "aeromodel", "radiocontrol", "rádio controle",
    "radio controle", "radiocontrol", "multirotor", "quadcopter",
    "parrot", "autel", "skydio", "hubsan", "syma",
    "aeromod", "planador", "helicóptero rc", "helicoptero rc",
]

# Categorias Google Maps que indicam negócio genérico (não drone)
_DRONE_NEGATIVE_CATEGORIES = [
    "photography studio", "estúdio fotográfico", "fotógrafo", "photographer",
    "sound equipment supplier", "áudio e vídeo", "audio e video",
    "sporting goods store", "artigos esportivos",
    "electronics store",   # sozinho é genérico demais; só bloqueado se sem positivo
    "security system supplier", "sistema de segurança", "cftv", "alarme",
    "musical instrument store", "instrumentos musicais",
    "rental service", "locadora",
    "video production", "produtora de vídeo",
]


_DRONE_NOISE_NAMES = [
    "aluguel", "alugação", "locação", "locação", "aluga drone",
    "piloto de drone", "serviço de drone", "filmagem", "filmagens", "fotografia aerea",
    "foto aerea", "aerial", "ceubô drone", "voo de drone",
    # Segurança / CFTV / Alarmes (não vendem drones)
    "cftv", "alarme", "alarmes", "segurança", "seguranca",
    "cerca eletrica", "cerca elétrica", "portão", "portao",
    "cabeamento estruturado", "intelbras", "câmera de segurança", "camera de seguranca",
    "monitoramento", "vigilância", "vigilancia",
    # Material elétrico / Utilidades / Auto peças (lixo genérico)
    "auto peças", "auto pecas", "autopeças", "autopecas",
    "material eletrico", "material elétrico", "eletromax",
    "utilidade", "utilidades", "presentes",
    "papelaria", "bazar",
    # Limpeza / Produtos não relacionados
    "limpeza", "produtos de limpeza", "distribuidora de limpeza",
    "distribuidora de produtos", "atacado",
    # Imagens / Serviços (não vendem drones)
    "imagens aereas", "imagem aerea", "imagens aéreas", "imagem aérea",
    "drone show", "drone light show",
    # Shows / Entretenimento
    "magic show", "espetaculo", "entretenimento",
]


# Termos que indicam ruído para Informática (escolas, baterias, serviços puros, etc)
_INFO_NOISE_NAMES = [
    "escola de",
    "curso",
    "treinamento",
    "baterias",
    "bateria",
    "automotiva",
    "centro automotivo",
    "nuvem",
    "cloud",
    "software",
    "sistemas",
    "consultoria",
    "material eletrico",
    "eletrica",
    "hidraulica",
    "moveis para escritorio",
    "servicos de ti",
    "desentupidora",
]

_SENNHEISER_NOISE_NAMES = [
    "som automotivo",
    "acessorios para carro",
    "central multimidia",
    "som residencial",
    "home theater",
    "conserto de tv",
    "conserto de radio",
    "eletronica de bairro",
    "alto falante de carro",
]


def _filter_noise_drones(results: list[dict]) -> list[dict]:
    """Remove estabelecimentos que não têm relação com VENDA de drones.

    Lógica:
      - Remove nomes com termos de serviço puro (locação, filmagem)
      - Remove CFTV, alarmes, segurança, auto peças, material elétrico, limpeza
      - Verifica nome + categorias do Maps
      - Mantém apenas lojas/revendas de drones, aeromodelismo e FPV
    """
    filtered = []
    for item in results:
        nome = _norm_key(item.get("nome") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])
        texto_para_busca = f"{nome} {categorias_str}"

        # Remove locadoras, prestadores de serviço e lojas irrelevantes
        is_noise = any(t in texto_para_busca for t in _DRONE_NOISE_NAMES)
        if is_noise:
            continue

        filtered.append(item)

    return filtered


def _filter_noise_informatica(results: list[dict]) -> list[dict]:
    """Filtro para o segmento de Informática.
    Lógica:
      - Remove escolas, cursos e baterias (automotivas)
      - Remove empresas de serviço puro (Software, Nuvem, Consultoria)
      - Verifica tanto o NOME quanto as CATEGORIAS retornadas pelo Maps
    """
    filtered = []
    for item in results:
        nome = _norm_key(item.get("nome") or "")
        # Pega as categorias (segmentos) que o scraper achou
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])
        
        texto_para_busca = f"{nome} {categorias_str}"

        is_noise = any(t in texto_para_busca for t in _INFO_NOISE_NAMES)
        
        # Exceção: Se for "Bateria" mas também tiver "Informatica" no nome, 
        # pode ser nobreak, então mantemos (ex: "Real Baterias e Informatica")
        if "bateria" in texto_para_busca and "inform" in texto_para_busca:
            is_noise = False

        if is_noise:
            continue

        filtered.append(item)

    return filtered


def _filter_noise_sennheiser(results: list[dict]) -> list[dict]:
    """Filtro para Sennheiser (Pro Audio).
    Lógica:
      - Remove som automotivo (maior poluição)
      - Remove home theater e eletrônicas de conserto
      - Foca em Pro Audio, Broadcast e Rental
    """
    filtered = []
    for item in results:
        nome = _norm_key(item.get("nome") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])
        
        texto_para_busca = f"{nome} {categorias_str}"

        is_noise = any(t in texto_para_busca for t in _SENNHEISER_NOISE_NAMES)
        
        if is_noise:
            continue

        filtered.append(item)

    return filtered


def _filter_large_retail(results: list[dict]) -> list[dict]:
    """Filtra grandes redes de varejo e serviços puramente técnicos dos resultados."""
    server_exclusions = [
        # Grandes redes B2C globais e regionais
        "magazine luiza",
        "magalu",
        "americanas",
        "casas bahia",
        "ponto frio",
        "carrefour",
        "extra",
        "walmart",
        "leroy merlin",
        "camicado",
        "madeiramadeira",
        "havan",
        "kalunga",
        "fast shop",
        "kabum",
        "bumerang",
        "pichau",
        "terabyte",
        "mercado livre",
        "ponto de coleta",
        "agência mercado livre",
        
        "refrigeração",
        "refrigeracao",
        "lavadora",
        "lavadoras",
        "oficina",
        
        # Filtros de Assistência Técnica
        "assistência técnica",
        "assistencia tecnica",
        "assistência",
        "assistencia",
        "conserto",
        "reparo",
        "manutenção",
        "manutencao",
        
        # Lojas irrelevantes para Informática (varal, parafusos, metalurgia, ferragens)
        "varal",
        "varais",
        "parafuso",
        "parafusos",
        "metalurgia",
        "metalúrgica",
        "metalurgica",
        "ferragem",
        "ferragens",
        "ferramenta",
        "ferramentas",
        "serralheria",
        "solda",
        "soldas",
        "máquinas",
        "maquinas",
        "industrial",
        "industriais",
        # Hardware industrial específico
        "spiralock",
        "aço",
        "açoforti",
        "acoforti",
        "afiação",
        "afiacao",
        "pro-lar",
        "prolar",
        "trava",
        "travas",
        "fixação",
        "fixacao",
        "porca",
        "porcas",
        "buchas",
        "arruela",
    ]
    
    filtered = []
    for item in results:
        nome = (item.get("nome", "") or "").lower()
        # Verificar se o nome contém algum dos termos proibidos
        excluded = any(excl in nome for excl in server_exclusions)
        if not excluded:
            filtered.append(item)
    
    return filtered


def _filter_city_page_results(results: list[dict], cidade: str) -> list[dict]:
    """Remove resultados onde o nome É a própria cidade.

    Acontece quando o Google Maps retorna a página da cidade/região (ex: 'Adamantina')
    em vez de um negócio real. Filtro exato + variações comuns.
    """
    if not cidade:
        return results

    target = _norm_key(cidade)
    if not target:
        return results

    out: list[dict] = []
    for item in results or []:
        nome = _norm_key(str(item.get("nome") or ""))
        if not nome:
            out.append(item)
            continue
        # Nome IDÊNTICO à cidade → lixo (página da cidade no Maps)
        if nome == target:
            continue
        # Nome é a cidade + sufixo genérico (ex: "Adamantina - SP", "Adamantina SP")
        if nome.startswith(target) and len(nome) - len(target) < 5:
            continue
        out.append(item)

    return out


def _filter_items_with_other_city_in_name(results: list[dict], cidade: str) -> list[dict]:
    """Remove itens que declaram explicitamente outra cidade no nome.

    Ex: ao buscar em "Aguaí", remove "Loja Zema - Casa Branca".
    Filtro conservador: só remove quando o nome termina com " - <texto>" e esse
    <texto> não bate com a cidade alvo normalizada.
    """

    import re

    target_city = _norm_key(cidade)
    if not target_city:
        return results

    out: list[dict] = []
    for item in results or []:
        nome_raw = str(item.get("nome") or "").strip()
        if not nome_raw:
            out.append(item)
            continue

        m = re.search(r"\s-\s([^\d]{2,40})$", nome_raw)
        if not m:
            out.append(item)
            continue

        declared_city = _norm_key(m.group(1))
        if not declared_city:
            out.append(item)
            continue

        # Se declarou explicitamente outra cidade, remover.
        # Se declarou a própria cidade (ou variação), manter.
        if declared_city != target_city:
            continue

        out.append(item)

    return out


def _filter_strict_city(results: list[dict], cidade: str) -> list[dict]:
    """Remove itens que são explícitos sobre estarem em outra cidade,
    ou quando o resultado é apenas o marcador da própria cidade.
    """
    import re

    target_city = _norm_key(cidade)
    if not target_city:
        return results

    out: list[dict] = []

    # Lista de siglas de estados para o regex
    estados = "AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO"

    # Regex melhorado:
    # 1. Suporta separadores , ou · ou - antes da sigla do estado
    # 2. Suporta siglas em maiúsculo ou minúsculo
    # 3. Detecta "Cidade - UF" ou "Cidade, UF"
    city_state_re = re.compile(
        rf'([A-Za-zÀ-ÿ0-9\s\-]+)\s*[,·\-]\s*(?:{estados})\b', 
        re.IGNORECASE
    )

    for item in results or []:
        nome_raw = str(item.get("nome") or "").strip()
        if not nome_raw:
            out.append(item)
            continue

        # 1. Bloqueia o marcador genérico da cidade (Ex: name="Americana")
        norm_nome = _norm_key(nome_raw)
        if norm_nome == target_city:
            continue

        # 2. Verifica se o campo cidade extraído do scraper está diferente da cidade alvo
        cidade_extraida = str(item.get("cidade") or "").strip()
        if cidade_extraida:
            norm_cidade_extraida = _norm_key(cidade_extraida)
            if norm_cidade_extraida and norm_cidade_extraida != target_city:
                # Cidade extraída é diferente da cidade alvo - descarta
                continue

        # 3. Fallback: Verifica se o texto bruto do card do Maps acusa uma cidade diferente
        raw_text = str(item.get("__raw_text") or "")
        if raw_text and not cidade_extraida:
            # Tenta encontrar correspondências de "Cidade, UF"
            # O Maps costuma colocar o endereço no final ou perto do final separados por | ou ponto
            matches = city_state_re.findall(raw_text)
            if matches:
                # Vamos verificar de trás para frente, pois o endereço completo costuma estar no final
                found_wrong_city = False
                for match_city in reversed(matches):
                    # Limpa a "cidade" encontrada
                    candidate = match_city.split("·")[-1].split("|")[-1].split("-")[-1].strip()
                    candidate = _norm_key(candidate)

                    if candidate and candidate != target_city:
                        # Se achamos uma cidade explícita diferente, é lixo geográfico
                        found_wrong_city = True
                        break

                if found_wrong_city:
                    continue

        # Se passou pelos filtros, mantém
        out.append(item)

    return out


def _build_queries_for_segments(segs: list[str], cidade: str, estado: str, extra: str) -> list[dict[str, str]]:
    """Estratégia inteligente de multi-query baseada nas famílias Multilaser (Curva ABC).
    
    Divide as âncoras em grupos lógicos por família de produto para maximizar
    cobertura de lojas (B2B e varejo) sem tornar queries muito específicas.
    
    Otimização para múltiplos segmentos:
    - 1 segmento: estratégia detalhada (~16 queries)
    - 2-3 segmentos: combinar com OR (~20 queries)
    - 4+ segmentos: estratégia genérica + priorização (~25 queries)
    """
    cidade_clean = (cidade or "").strip()
    estado_clean = (estado or "").strip()
    local_parts = []
    if cidade_clean:
        local_parts.append(f'"{cidade_clean}"')
    if estado_clean:
        local_parts.append(estado_clean)
        
    local = ", ".join(local_parts)
    if local:
        local = f" em {local}"

    extra_clean = _normalize_extra(extra=extra, cidade=cidade, estado=estado)
    if _looks_like_segment_or_query(extra_clean=extra_clean, segs=segs, cidade=cidade, estado=estado):
        extra_clean = ""
    extra_is_generic = extra_clean.lower() in {"lojas", "loja"}
    
    # Se temos segmentos selecionados, ignorar extra (evita duplicação de segmentos na query)
    # O extra contém a query do frontend com OR que não deve ser adicionada novamente
    if segs:
        extra_suffix = ""
    else:
        # Extrair extra útil (se não for igual ao segmento)
        extra_suffix = ""
        if extra_clean and not extra_is_generic:
            extra_suffix = f" {extra_clean}"

    # Termos B2B otimizados baseados em análise de logs
    # "distribuidor" traz 86% das lojas únicas
    # "loja" captura varejo (7%)
    # Removidos: atacadista, revenda, fornecedor (redundantes, <8% combinados)
    b2b_terms = ["distribuidor", "loja"]
    
    # Marcas relevantes para capturar revendedores específicos
    # Multilaser + marcas complementares que indicam potencial B2B
    brand_terms = ["Multilaser", "Lenovo", "Dell", "Samsung", "LG", "Positivo"]
    
    # Termos de exclusão para evitar resultados irrelevantes
    # Serão usados como "-fechado" na query do Google
    exclude_terms = [
        "fechado",
        "extinto",
        "falência",
        # Varejo grande e agências - não interessam para revenda CNPJ
        "Magazine Luiza",
        "Magalu",
        "Americanas",
        "Casas Bahia",
        "Ponto Frio",
        "Carrefour",
        "Extra",
        "Walmart",
        "Leroy Merlin",
        "Camicado",
        "MadeiraMadeira",
        "Havan",
        "Kalunga",
        "Fast Shop",
        "Kabum",
        "Agência Mercado Livre",
        "Ponto de Coleta",
        "Assistência Técnica",
        "Assistencia Tecnica",
        "Conserto",
        "Reparo",
        "Manutenção",
        "Manutencao",
    ]
    
    # Grupos de âncoras por família Multilaser (Curva ABC Fevereiro)
    # AC = Acessórios/Periféricos | ME = Mídia/Energia | PC = Computadores | IC = SSD/Memória
    anchor_groups: dict[str, list[str]] = {
        "Informática": [
            # Foco B2B - O Alto Volume
            "atacadista informática",
            "distribuidor informática",
            "revenda informática",
            "atacadista de periféricos",
            "distribuidor de periféricos",
            "atacado e varejo informática",
            
            # Produtos Específicos e Acessórios
            "loja de mouses e teclados",
            "loja de cabos",
            "loja de cabos e conectores",
            "pendrive e cartões de memória",
            "venda de periféricos",
            "comércio de acessórios de informática",
            
            # Equipamentos Maiores (O Médio Comércio)
            "loja de tablets",
            "loja de laptops",
            "venda de notebooks e laptops",
            "loja de nobreaks",
            
            # Varejo e Centro da Cidade (Giro Rápido)
            "loja de informática",
            "comércio de informática",
            "varejo informática",
            "loja de acessórios informática",
            "loja de eletrônicos e informática",
            "suprimentos de informática",
            "loja de informática centro",
            
            # Componentes
            "atacadista de componentes de computador",
            "distribuidor de componentes de computador",
            "atacadista de hardware",
            "distribuidor de hardware",
        ],
        "Celulares": [
            # O Alto Volume
            "atacadista acessórios celular",
            "distribuidor acessórios celular",
            "revenda acessórios celular",
            # O Médio Comércio e Revendedores de Acessórios
            "loja de capinhas de celular",
            "acessórios para celular",
            "comércio de eletrônicos",
            "loja de eletrônicos",
            "loja de celulares centro",
            "venda de celular flip",
            "celular para idoso loja",
            "assistência e venda de celular",
        ],
        "Áudio e Vídeo": [
            # O Alto Volume B2B
            "distribuidor áudio profissional",
            "loja de instrumentos musicais", # Lojas de música revendem muitas caixas de som e fones pesados
            "distribuidor som automotivo",
            # O Médio Comércio
            "loja de som e acessórios",
            "loja de eletrônicos",
            "acústica e som",
            "equipamentos de áudio",
            "instalação de som automotivo", # Compram centrais multimídia aos montes
        ],
        "Utilidades e Variedades": [
            # O Pote de Ouro para produtos de curva B e C Multimarcas (Limpo de alimentos)
            "loja de utilidades",
            "loja de variedades",
            "bazar e presentes",
            "comercial importadora",
            "loja de utilidades domésticas",
        ],
        "Eletroportáteis": [
            # O Alto Volume (Atacadistas e distribuidores regionais)
            "atacadista eletrodomésticos",
            "distribuidor eletrodomésticos",
            "revenda eletrodomésticos",
            # O Médio Comércio (Lojistas de Utensílios e Médio Varejo)
            "loja de eletrodomésticos",
            "loja de eletroportáteis",
            "comércio de eletroportáteis",
            # Vendas Correlatas e Giro Rápido (Lojas menores/bairro e móveis)
            "loja de utilidades domésticas",
            "loja de artigos para o lar",
            "loja de presentes",
            "loja de móveis e eletro",
            # O Novo Nicho (Giro Rápido / Outlets / Saldo)
            "outlet eletrodomésticos",
            "saldão eletrodomésticos",
        ],
        "Gamer": ["gamer"],
        "Brinquedos": ["brinquedos"],
        "Drones e Câmeras": [
            # TIER 1: Revenda B2B / Distribuidores
            "distribuidor de drones",
            "revenda de drones",
            "importadora de drones",
            "revenda DJI",
            "assistência DJI",
            
            # TIER 2: Varejo Especializado / Lojas Físicas
            "loja de drones",
            "loja de drones e câmeras",
            "drone shop",
            "drone store",
            
            # TIER 3: Hobby e FPV (Pequenas revendas especializadas)
            "loja de aeromodelismo",
            "loja fpv",
            "loja de radiocontrole",
        ],
        "Ortopédica": ["ortopedia"],
        "Fitness": ["fitness"],
        "Pet": ["pet shop"],
        "Redes": ["roteador switch", "cabo rede"],
        "Mobilidade Elétrica": ["patinete elétrico", "scooter"],
        "Health Care": [
            # Atacadistas e distribuidores (foco CNPJ)
            "atacadista equipamentos médicos",
            "distribuidor equipamentos médicos",
            "loja de equipamentos médicos atacado",
            "revenda equipamentos médicos",
        ],
        "Tablets Kids": [
            "loja de tablets",
            "tablet infantil",
            "tablet educativo",
            "acessórios tablet",
            "papelaria digital",
            "brinquedo educativo",
            "loja de eletrônicos",
        ],
        # Multikids - linha infantil completa
        "Multikids": [
            "boneca", "boneca bebê",
            "pelúcia", "ursinho",
            "Disney", "Marvel", "Barbie", "Frozen",
            "carrinho brinquedo", "hot wheels",
            "faz de conta", "kit cozinha", "kit médico",
        ],
        "Sennheiser": [
            # TIER 1: O "Coração" do B2B Pro Audio
            "áudio profissional",
            "equipamentos para estúdio de som",
            "loja de áudio profissional",
            "locaçao de som para eventos",
            "locação de microfones profissionais",
            "sistemas de áudio sem fio",
            
            # TIER 2: Segmentos Verticais (Broadcast e Touring)
            "revenda broadcast áudio",
            "integrador de sistemas de áudio",
            "sonorização profissional",
            "loja de instrumentos musicais especializada",
            
            # TIER 3: Nichos Específicos
            "equipamentos para rádio e tv",
            "conferência e áudio corporativo",
            "fones de ouvido audiófilo",
        ],
    }

    # Override Multikids anchors with the updated list
    # Termos genéricos de varejo infantil + marcas/licenciados
    anchor_groups["Multikids"] = [
        # Varejo genérico infantil
        "loja de brinquedos",
        "loja kids",
        "shopping infantil",
        "shopping das crianças",
        "loja de 1.99",
        "jogos para crianças",
        "brinquedos",
        # Marcas/licenciados populares
        "disney",
        "barbie",
        "hot wheels",
        "boneca",
    ]

    queries: list[dict[str, str]] = []
    num_segs = len(segs)
    
    # Estratégia baseada no número de segmentos
    if num_segs == 0:
        return []
    
    # Para cada segmento, usar estratégia detalhada completa
    # Não importa se são 1, 3 ou 5 segmentos - cada um merece atenção
    for seg in segs:
        seg_clean = (seg or "").strip()
        if not seg_clean:
            continue

        anchor_lists = anchor_groups.get(seg_clean, [""])

        # Segmentos especiais que são marcas/linhas (não tipos de loja)
        # Para esses, usar apenas âncoras, não o nome do segmento na query
        is_brand_segment = seg_clean in [
            "Multikids",
            "Health Care",
            "Sennheiser",
        ]

        if is_brand_segment:
            # Para segmentos de marca/linha, usar queries com âncoras diretamente
            for anchors in anchor_lists:
                if not anchors:
                    continue
                # Usar a âncora diretamente sem adicionar prefixos
                q = f"{anchors}{local}".strip()
                queries.append({"q": q, "segmento": seg_clean})
        else:
            # Para segmentos normais, usar estratégia mais limpa
            # Query principal do segmento
            q = f"loja de {seg_clean}{local}".strip()
            queries.append({"q": q, "segmento": seg_clean})
            
            # Queries com âncoras específicas (sem repetir o segmento)
            for anchors in anchor_lists:
                if not anchors:
                    continue
                anchor_lower = anchors.lower()
                
                # Palavras que indicam que a âncora já possui seu próprio prefixo estrutural
                prefixes_to_ignore = (
                    "loja", "comércio", "comercial", "atacadista", "distribuidor",
                    "revenda", "outlet", "saldão", "bazar", "shopping", "papelaria",
                    "locadora", "equipamento", "drone", "câmera", "estabilizador",
                    "acessório", "clube", "produtora", "estúdio", "importadora",
                )
                
                if anchor_lower.startswith(prefixes_to_ignore):
                    q = f"{anchors}{local}".strip()
                else:
                    q = f"loja de {anchors}{local}".strip()
                
                queries.append({"q": q, "segmento": seg_clean})
            
            # Query B2B do segmento
            q = f"distribuidor de {seg_clean}{local}".strip()
            queries.append({"q": q, "segmento": seg_clean})
            
            # Queries com marcas relevantes
            # Drones: Inserir "DJI" para focar em profissionais e revendas
            seg_brands = brand_terms[:2] if "drone" not in seg_clean.lower() else ["DJI"]
            for brand in seg_brands:
                queries.append({"q": f"{brand} {seg_clean}{local}".strip(), "segmento": seg_clean})
    
    # Remover duplicatas mantendo ordem
    seen = set()
    out: list[dict[str, str]] = []
    for spec in queries:
        q = (spec.get("q") or "").strip()
        k = q.lower()
        if k and k not in seen:
            seen.add(k)
            out.append({"q": q, "segmento": spec.get("segmento") or ""})
    
    # Adicionar termos de exclusão a todas as queries
    for spec in out:
        seg = spec.get("segmento") or ""
        all_excludes = exclude_terms
        exclude_suffix = " " + " ".join([f'-"{term}"' for term in all_excludes])
        spec["q"] = f"{spec['q']}{exclude_suffix}".strip()
    
    return out


def _normalize_extra(extra: str, cidade: str, estado: str) -> str:
    extra_clean = (extra or "").strip()
    if not extra_clean:
        return ""

    cidade_clean = (cidade or "").strip()
    estado_clean = (estado or "").strip()
    if not cidade_clean and not estado_clean:
        return extra_clean

    extra_clean = " ".join(extra_clean.split())

    if cidade_clean and estado_clean:
        import re

        pat = rf"\s+em\s+{re.escape(cidade_clean)}\s*,\s*{re.escape(estado_clean)}\s*$"
        cleaned = _re_sub_ignoring_case(pat, "", extra_clean).strip()
        if cleaned != extra_clean:
            return cleaned

    if cidade_clean:
        import re

        pat = rf"\s+em\s+{re.escape(cidade_clean)}\s*$"
        cleaned = _re_sub_ignoring_case(pat, "", extra_clean).strip()
        if cleaned != extra_clean:
            return cleaned

    if cidade_clean and estado_clean:
        import re

        pat = rf"\s+{re.escape(cidade_clean)}\s*,?\s*{re.escape(estado_clean)}\s*$"
        cleaned = _re_sub_ignoring_case(pat, "", extra_clean).strip()
        if cleaned != extra_clean:
            return cleaned

    if cidade_clean:
        import re

        pat = rf"\s+{re.escape(cidade_clean)}\s*$"
        cleaned = _re_sub_ignoring_case(pat, "", extra_clean).strip()
        if cleaned != extra_clean:
            return cleaned

    return extra_clean


def _looks_like_segment_or_query(extra_clean: str, segs: list[str], cidade: str, estado: str) -> bool:
    """Detecta query do frontend (segmentos com OR + local) para evitar sufixo lixo."""
    if not extra_clean or not segs:
        return False

    extra_norm = _norm_key(extra_clean)
    if " or " not in extra_norm:
        return False

    cidade_clean = (cidade or "").strip()
    estado_clean = (estado or "").strip()
    if cidade_clean and estado_clean:
        loc_norm = _norm_key(f"{cidade_clean} {estado_clean}")
        if extra_norm.endswith(loc_norm):
            extra_norm = extra_norm[: -len(loc_norm)].strip()
    elif cidade_clean:
        loc_norm = _norm_key(cidade_clean)
        if extra_norm.endswith(loc_norm):
            extra_norm = extra_norm[: -len(loc_norm)].strip()

    seg_norms = [_norm_key(s) for s in segs if (s or "").strip()]
    return bool(seg_norms) and all(sn in extra_norm for sn in seg_norms)


def _norm_key(v: str) -> str:
    s = (v or "").strip().casefold()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.split())


def _re_sub_ignoring_case(pattern: str, repl: str, text: str) -> str:
    import re

    return re.sub(pattern, repl, text, flags=re.IGNORECASE)


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen = set()
    for it in items or []:
        k = _key_from_item(it)
        if not k:
            continue
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out
