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

    limit = req.limit or 20
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

            if any((s or "").strip() == "Sennheiser" for s in segs):
                merged.sort(
                    key=lambda it: (
                        -int(it.get("sennheiser_fit_score") or 0),
                        _get_sort_priority(it),
                    )
                )
            elif any("varej" in (s or "").lower() for s in segs):
                merged.sort(
                    key=lambda it: (
                        -int(it.get("varejo_medio_fit_score") or 0),
                        _get_sort_priority(it),
                    )
                )
            elif any("inform" in (s or "").lower() for s in segs):
                merged.sort(
                    key=lambda it: (
                        -int(it.get("informatica_medio_fit_score") or it.get("informatica_fit_score") or 0),
                        _get_sort_priority(it),
                    )
                )
            elif any("mobilidade" in (s or "").lower() for s in segs):
                merged.sort(
                    key=lambda it: (
                        -int(it.get("mobilidade_fit_score") or 0),
                        _get_sort_priority(it),
                    )
                )
            else:
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
        merged_before_dedupe=merged_before_dedupe,
        merged_after_dedupe=merged_after_dedupe,
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

    if "brinquedo" in seg_clean:
        return _filter_noise_brinquedos(results)

    if "gamer" in seg_clean:
        return _filter_noise_gamer(results)

    if "varej" in seg_clean:
        return _filter_noise_varejo_medio(results)

    if "mobilidade" in seg_clean:
        return _filter_noise_mobilidade_eletrica(results)

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
    "provedor",
    "internet service provider",
    "software company",
    "data recovery service",
    "telecom",
    "telecomunicacoes",
    "telecomunicações",
    "fibra",
    "provedor de internet",
    "telecommunications service provider",
    "cftv",
    "segurança",
    "seguranca",
    "security system supplier",
    "cerca eletrica",
    "portão",
]

_BRINQUEDOS_POSITIVE_TERMS = [
    "brinquedo",
    "brinquedos",
    "toy store",
    "loja de brinquedos",
    "distribuidor de brinquedos",
    "atacadista de brinquedos",
    "atacado de brinquedos",
    "revenda de brinquedos",
    "importadora de brinquedos",
    "brinquedos educativos",
    "jogos educativos",
    "jogos infantis",
    "artigos infantis",
    "loja infantil",
    "loja kids",
    "baby store",
    "bebe e brinquedos",
    "crianca e brinquedos",
]

_BRINQUEDOS_NOISE_NAMES = [
    "buffet",
    "festa",
    "festas",
    "decoracao",
    "decoracoes",
    "locacao",
    "locadora",
    "aluguel",
    "aluga",
    "recreacao",
    "animacao",
    "animador",
    "playground",
    "parque",
    "brinquedoteca",
    "escola",
    "creche",
    "bercario",
    "curso",
    "terapia",
    "clinica",
    "odontopediatria",
    "fotografia",
    "estudio fotografico",
    "roupa infantil",
    "moda infantil",
    "calcados infantis",
    "enxoval",
    "maternidade",
    "fralda",
    "fraldas",
    "salao infantil",
    "cabelo infantil",
]

_GAMER_NOISE_NAMES = [
    "lan house",
    "lanhouse",
    "cyber cafe",
    "cybercafe",
    "arena e-sports",
    "arena esports",
    "arena gamer",
    "salao de jogos",
    "salao de games",
    "clube de jogos",
    "clube de games",
    "fliperama",
    "fliperamas",
    "sinuca",
    "bilhar",
    "boliche",
    "escape room",
    "casa de jogos",
    "cassino",
    "poker",
    "baralho",
    "jogos de azar",
]


_SENNHEISER_NOISE_NAMES = [
    "som automotivo",
    "audio automotivo",
    "audio car",
    "acessorios para carro",
    "acessorios automotivos",
    "central multimidia",
    "dvd automotivo",
    "som residencial",
    "home theater",
    "home cinema",
    "conserto de tv",
    "conserto de radio",
    "assistencia tecnica",
    "assistencia eletronica",
    "reparo eletronico",
    "manutencao eletronica",
    "eletronica de bairro",
    "alto falante de carro",
    "alto falante automotivo",
    "alarme automotivo",
    "insulfilm",
    "pelicula",
    "envelopamento",
    "sound e film",
    "sound & film",
    "som e film",
    "som & film",
    "auto som",
    "sound car",
]

_SENNHEISER_BUYER_PROFILE_TERMS = [
    "audio profissional",
    "pro audio",
    "loja de audio",
    "instrumentos musicais",
    "microfone",
    "microfones",
    "fone profissional",
    "equipamentos de som",
    "estudio",
    "gravacao",
    "podcast",
    "produtora",
    "audiovisual",
    "radio",
    "tv",
    "broadcast",
    "igreja",
    "templo",
    "auditorio",
    "teatro",
    "casa de show",
    "centro de convencoes",
    "casa de eventos",
    "hotel",
    "universidade",
    "escola de musica",
    "sonorizacao",
    "locacao de som",
    "locadora de som",
    "eventos",
    "integrador",
    "audio e video",
    "videoconferencia",
    "conferencia",
    "corporativo",
]

_SENNHEISER_STRONG_QUERY_TERMS = [
    "broadcast audio",
    "emissora de radio",
    "emissora de tv",
    "estudio de gravacao",
    "estudio de podcast",
    "produtora audiovisual",
    "produtora de video",
    "som para igreja",
    "sonorizacao para igrejas",
    "sonorizacao de eventos",
    "locadora de som",
    "locacao de som para eventos",
    "loja de instrumentos musicais",
    "loja de audio profissional",
    "revenda de audio profissional",
    "distribuidor de instrumentos musicais",
    "revenda de instrumentos musicais",
    "integrador audio e video",
    "integrador av",
    "audio corporativo",
    "sistemas de conferencia",
]

_SENNHEISER_HIGH_INTENT_TERMS = [
    "podcast",
    "estudio",
    "gravacao",
    "radio",
    "emissora",
    "broadcast",
    "loja de audio",
    "audio profissional",
    "instrumentos musicais",
    "escola de musica",
    "conservatorio",
    "microfone",
    "microfones",
    "sonorizacao",
    "locadora de som",
    "locacao de som",
    "integrador audio",
    "integrador av",
]

_SENNHEISER_MEDIUM_INTENT_TERMS = [
    "produtora",
    "audiovisual",
    "foto video",
    "film",
    "eventos",
    "casa de eventos",
    "centro de convencoes",
    "anfiteatro",
    "auditorio",
    "teatro",
    "casa de show",
    "igreja",
    "templo",
    "hotel",
    "universidade",
    "videoconferencia",
    "conferencia",
    "corporativo",
]

_SENNHEISER_LOW_CONFIDENCE_TERMS = [
    "recanto",
    "chacara",
    "sitio",
    "espaco",
    "salao de festas",
    "festa infantil",
    "buffet infantil",
    "casa da alegria",
]

_SENNHEISER_BUSINESS_HINTS = [
    "radio",
    "fm",
    "studio",
    "estudio",
    "podcast",
    "music",
    "musical",
    "som",
    "sound",
    "audio",
    "video",
    "film",
    "eventos",
    "producoes",
    "produtora",
    "igreja",
    "conservatorio",
    "instituto",
    "escola",
    "teatro",
    "anfiteatro",
    "eventos",
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


_INFO_POSITIVE_TERMS = [
    "informatica", "informática", "perifericos", "periféricos", "hardware",
    "suprimentos", "computador", "computadores", "notebook", "notebooks",
    "laptop", "laptops", "nobreak", "nobreaks", "cabos", "conectores",
    "mouse", "mouses", "teclado", "teclados", "pendrive", "ssd",
    "memoria", "memória", "componentes", "papelaria", "eletronicos", "eletrônicos",
    "computer", "electronics", "office supply", "tech", "technology",
]

_PERSONAL_FIRST_NAMES = {
    "joao", "joão", "pedro", "carlos", "paulo", "jose", "josé", "maria",
    "lucas", "gabriel", "matheus", "marcos", "andre", "andré", "felipe",
    "rafael", "luiz", "luis", "rodrigo", "diego", "bruno", "eduardo",
    "guilherme", "renato", "marcelo", "alexandre", "fernando", "ricardo",
    "vitor", "victor", "tiago", "thiago", "claudio", "cláudio", "sergio",
    "sérgio", "antonio", "antônio", "francisco", "mario", "mário"
}

_BUSINESS_INDICATORS = [
    "distribuidora", "distribuidor", "revenda", "atacado", "atacadista",
    "suprimentos", "comercio", "comércio", "comercial", "loja", "store",
    "milenio", "milênio", "alpha", "beta", "tech", "pc", "eletronica",
    "eletrônica", "eletronicos", "eletrônicos", "papelaria"
]


def _score_informatica_fit(texto: str, nome: str) -> int:
    score = 20  # Base
    nome_norm = _norm_key(nome)
    texto_norm = _norm_key(texto)

    # Tier 1 (+80): Canal B2B Direto (Distribuidora, Revenda, Atacado)
    if any(t in nome_norm or t in texto_norm for t in ["distribuidora", "distribuidor", "atacadista", "atacado", "revenda"]):
        score += 80
    # Tier 2 (+50): Suprimentos / TI Especializada
    elif any(t in nome_norm or t in texto_norm for t in ["suprimentos", "computadores e perifericos", "hardware", "componentes"]):
        score += 50
    # Tier 3 (+30): Comércio/Loja de TI ou Papelaria + TI
    elif any(t in nome_norm or t in texto_norm for t in ["loja de informatica", "comercio de informatica", "papelaria"]):
        score += 30

    return score


def _filter_noise_informatica(results: list[dict]) -> list[dict]:
    """Filtro para o segmento de Informática.
    Lógica:
      - Remove escolas, cursos e baterias (automotivas)
      - Remove empresas de serviço puro (Software, Nuvem, Consultoria, ISPs, Segurança)
      - Remove autônomos e pessoas físicas sem indicativo comercial
      - Remove lojas genéricas sem correlação com TI
      - Mantém lojas de TI e revendas mesmo que prestem assistência técnica secundária
      - Calcula e atribui Fit Score B2B (informatica_medio_fit_score)
    """
    filtered = []
    for item in results:
        nome_raw = item.get("nome") or ""
        nome = _norm_key(nome_raw)
        raw_text = _norm_key(item.get("__raw_text") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])
        query_sources = " ".join([_norm_key(str(qs)) for qs in (item.get("query_sources") or [])])
        
        texto_loja = f"{nome} {raw_text} {categorias_str}"
        texto_para_busca = f"{texto_loja} {query_sources}"

        # 1. Filtro de termos e categorias de ruído no texto da LOJA
        is_noise = any(t in texto_loja for t in _INFO_NOISE_NAMES)
        
        # Exceção: Se o NOME da loja tiver "informatica", "eletronico" ou "suprimentos", mantemos
        tem_nome_comercial_ti = any(b in nome for b in ["informatica", "informática", "eletronico", "eletrônico", "suprimentos", "distribuidora", "revenda", "componentes"])
        if tem_nome_comercial_ti:
            is_noise = False

        # Descartar assistências técnicas puras (sem indicação de loja/revenda/distribuidora no nome)
        termos_reparo = ["assistencia tecnica", "assistência técnica", "computer repair service", "conserto", "reparo"]
        tem_termo_reparo = any(r in texto_loja for r in termos_reparo)
        if tem_termo_reparo:
            tem_canal_loja = any(c in nome for c in ["loja", "store", "distribuidora", "distribuidor", "revenda", "atacadista", "atacado", "suprimentos", "comercio", "comércio", "comercial"])
            if not tem_canal_loja:
                continue

        if is_noise:
            continue

        # 2. Filtro de Pessoas Físicas / Autônomos (Ex: "João da Silva Informática")
        primeira_palavra = nome.split()[0] if nome.split() else ""
        if primeira_palavra in _PERSONAL_FIRST_NAMES:
            tem_indicativo_comercial = any(b in nome for b in _BUSINESS_INDICATORS)
            if not tem_indicativo_comercial:
                continue

        # 3. Filtro de lojas genéricas sem termo de confirmação de TI no texto da LOJA
        tem_termo_positivo = any(p in texto_loja for p in _INFO_POSITIVE_TERMS)
        if not tem_termo_positivo:
            continue

        # Calcular Fit Score B2B
        fit_score = _score_informatica_fit(texto_para_busca, nome_raw)
        item["informatica_medio_fit_score"] = fit_score
        item["informatica_fit_score"] = fit_score

        filtered.append(item)

    # Ordenar por fit score decrescente
    filtered.sort(key=lambda it: int(it.get("informatica_medio_fit_score") or 0), reverse=True)
    return filtered


def _filter_noise_brinquedos(results: list[dict]) -> list[dict]:
    """Filtro para Brinquedos B2B/revenda.

    Mantem lojas, distribuidores e varejos correlatos com sinal claro de
    brinquedos; remove servicos infantis como buffet, locacao e escolas.
    """
    filtered = []
    for item in results:
        nome = _norm_key(item.get("nome") or "")
        raw_text = _norm_key(item.get("__raw_text") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])

        texto_para_busca = f"{nome} {raw_text} {categorias_str}"

        if any(t in texto_para_busca for t in _BRINQUEDOS_NOISE_NAMES):
            continue

        if any(t in texto_para_busca for t in _BRINQUEDOS_POSITIVE_TERMS):
            filtered.append(item)

    return filtered


def _filter_noise_gamer(results: list[dict]) -> list[dict]:
    """Filtro para segmento Gamer B2B.
    Descarta negócios voltados para consumo final (lan houses, cyber cafés, arenas de e-sports, fliperamas, etc.).
    """
    filtered = []
    for item in results:
        nome = _norm_key(item.get("nome") or "")
        raw_text = _norm_key(item.get("__raw_text") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])

        texto_para_busca = f"{nome} {raw_text} {categorias_str}"

        # Se contiver qualquer termo de ruído gamer, descarta
        if any(t in texto_para_busca for t in _GAMER_NOISE_NAMES):
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
        raw_text = _norm_key(item.get("__raw_text") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])
        query_sources = item.get("query_sources") or []
        query_sources_str = " ".join([_norm_key(str(q)) for q in query_sources])
        
        texto_para_bloqueio = f"{nome} {raw_text} {categorias_str}"
        texto_para_score = f"{texto_para_bloqueio} {query_sources_str}"

        is_noise = any(t in texto_para_bloqueio for t in _SENNHEISER_NOISE_NAMES)
        
        if is_noise:
            continue

        item["sennheiser_fit_score"] = _score_sennheiser_fit(texto_para_score, nome)
        filtered.append(item)

    return sorted(filtered, key=lambda it: int(it.get("sennheiser_fit_score") or 0), reverse=True)


def _score_sennheiser_fit(texto: str, nome: str = "") -> int:
    texto_norm = _norm_key(texto or "")
    nome_norm = _norm_key(nome or "")
    profile_score = sum(1 for term in _SENNHEISER_BUYER_PROFILE_TERMS if term in texto_norm)
    source_score = sum(2 for term in _SENNHEISER_STRONG_QUERY_TERMS if term in texto_norm)
    high_score = sum(5 for term in _SENNHEISER_HIGH_INTENT_TERMS if term in texto_norm)
    medium_score = sum(2 for term in _SENNHEISER_MEDIUM_INTENT_TERMS if term in texto_norm)
    low_penalty = sum(3 for term in _SENNHEISER_LOW_CONFIDENCE_TERMS if term in texto_norm)
    person_penalty = 5 if _looks_like_person_name(nome_norm) else 0
    return profile_score + source_score + high_score + medium_score - low_penalty - person_penalty


def _looks_like_person_name(nome_norm: str) -> bool:
    parts = [p for p in (nome_norm or "").split() if p]
    if len(parts) < 2 or len(parts) > 4:
        return False
    if any(term in nome_norm for term in _SENNHEISER_BUSINESS_HINTS):
        return False
    return True


_VAREJO_MEDIO_NOISE_NAMES = [
    # Mercados municipais / Órgãos públicos
    "mercado municipal", "mercadão municipal", "mercadao municipal", "feira livre",
    # Usados / Brechós / Segunda mão / Antiguidades
    "usados", "usado", "segunda mão", "segunda mao", "brechó", "brecho", "móveis usados", "moveis usados", "eletros usados", "antiguidades", "bazar beneficente",
    # Saúde / Farmácias puras / Óticas / Clínicas
    "farmacia", "farmácia", "drogaria", "drogarias", "drogasil", "droga raia",
    "otica", "ótica", "optica", "óptica", "laboratorio", "laboratório",
    "clinica", "clínica", "hospital", "consultorio", "consultório", "odontologia", "dentista", "ortodontia",
    # Automotivo / Postos / Mecânica
    "auto pecas", "auto peças", "autopeças", "autopecas", "mecanica", "mecânica",
    "funilaria", "borracharia", "pneus", "posto de gasolina", "posto de combustivel", "lava rapido", "lava rápido", "centro automotivo",
    # Construção civil pesada
    "material de construcao", "material de construção", "tintas", "madeireira", "marmoraria", "vidracaria", "vidraçaria", "serralheria", "cimento", "areia",
    # Serviços administrativos e profissionais
    "imobiliaria", "imobiliária", "advocacia", "advogado", "contabilidade", "contabil", "despachante",
    # Estética / Beleza / Fitness
    "academia", "pilates", "crossfit", "barbearia", "salao de beleza", "salão de beleza", "estetica", "estética", "manicure",
    # Pets / Veterinária
    "pet shop", "veterinaria", "veterinária", "agropecuaria", "agropecuária",
    # Alimentação consumo imediato (Restaurantes/Bares/Padarias)
    "restaurante", "lanchonete", "pizzaria", "hamburgueria", "padaria", "confeitaria", "bar ", "churrascaria", "sorveteria",
]

_VAREJO_MEDIO_POSITIVE_TERMS = [
    "supermercado", "supermercados", "hipermercado", "hipermercados", "mercado", "mercados",
    "atacarejo", "atacarejos", "mercearia", "comercial de alimentos", "rede de supermercados",
    "moveis", "móveis", "eletro", "eletromoveis", "eletromóveis", "eletrodomesticos", "eletrodomésticos",
    "eletroportateis", "eletroportáteis", "departamento", "departamentos", "loja de departamentos",
    "utilidades", "utilidade", "variedades", "variedade", "bazar", "presentes", "artigos para o lar",
    "loja", "magazine", "comercio", "comércio", "comercial", "varejo", "varejista",
]


def _score_varejo_medio_fit(texto: str, nome: str) -> int:
    score = 20  # Base
    nome_norm = _norm_key(nome)
    texto_norm = _norm_key(texto)

    # Tier 1 (+80): Supermercados / Hipermercados / Atacarejos regionais / Redes alimentícias
    if any(t in nome_norm or t in texto_norm for t in ["supermercado", "supermercados", "hipermercado", "hipermercados", "atacarejo", "atacarejos", "rede de supermercados", "comercial de alimentos"]):
        score += 80
    # Tier 2 (+50): Móveis e Eletro / Eletromóveis / Lojas de Departamentos regionais
    elif any(t in nome_norm or t in texto_norm for t in ["moveis e eletro", "móveis e eletro", "eletromoveis", "eletromóveis", "eletrodomesticos", "eletrodomésticos", "departamento", "departamentos", "loja de departamentos", "eletroportateis", "eletroportáteis"]):
        score += 50
    # Tier 3 (+30): Utilidades Domésticas / Variedades / Bazar
    elif any(t in nome_norm or t in texto_norm for t in ["utilidades", "variedades", "bazar", "artigos para o lar", "presentes"]):
        score += 30

    return score


def _filter_noise_varejo_medio(results: list[dict]) -> list[dict]:
    """Filtro para Varejistas de Médio Porte (Tier 3).
    
    Lógica:
      - Remove serviços puros, autopeças, clínicas, drogarias, construção pesada e restaurantes
      - Mantém supermercados, hipermercados locais, lojas de móveis e eletro, utilidades e departamentos
      - Calcula e atribui Fit Score B2B (varejo_medio_fit_score)
    """
    filtered = []
    for item in results:
        nome_raw = item.get("nome") or ""
        nome = _norm_key(nome_raw)
        raw_text = _norm_key(item.get("__raw_text") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])
        query_sources = " ".join([_norm_key(str(qs)) for qs in (item.get("query_sources") or [])])

        texto_loja = f"{nome} {raw_text} {categorias_str}"
        texto_para_busca = f"{texto_loja} {query_sources}"

        # 1. Filtro de ruídos óbvios
        is_noise = any(t in texto_loja for t in _VAREJO_MEDIO_NOISE_NAMES)

        # Bloqueios absolutos (itens usados, brechós e mercados municipais sempre são descartados)
        termos_bloqueio_absoluto = ["usado", "usados", "segunda mao", "segunda mão", "brecho", "brechó", "mercado municipal", "mercadao municipal", "mercadão municipal", "feira livre", "antiguidades"]
        tem_bloqueio_absoluto = any(u in texto_loja for u in termos_bloqueio_absoluto)

        if tem_bloqueio_absoluto:
            is_noise = True
        elif is_noise:
            # Exceção de ruído para nomes fortes de redes (ex: Supermercado do Povo)
            tem_indicativo_forte = any(b in nome for b in ["supermercado", "hipermercado", "atacarejo", "eletromoveis", "eletromóveis", "moveis e eletro", "móveis e eletro"])
            if tem_indicativo_forte:
                is_noise = False

        if is_noise:
            continue

        # 2. Filtro de negócios genéricos sem qualquer sinal positivo de varejo/médio porte
        tem_positivo = any(p in texto_loja for p in _VAREJO_MEDIO_POSITIVE_TERMS)
        if not tem_positivo:
            continue

        # Calcular Fit Score Tier 3
        fit_score = _score_varejo_medio_fit(texto_para_busca, nome_raw)
        item["varejo_medio_fit_score"] = fit_score

        filtered.append(item)

    filtered.sort(key=lambda it: int(it.get("varejo_medio_fit_score") or 0), reverse=True)
    return filtered


_MOBILIDADE_NOISE_NAMES = [
    # Eletropostos / Estações de Carga (não vendem veículos)
    "eletroposto",
    "estacao de recarga",
    "estação de recarga",
    "ponto de recarga",
    "posto de recarga",
    "chargestation",
    "ev charging",
    "carregador eletrico",
    "carregador elétrico",
    # Locação pública por app / Compartilhamento
    "bike itau",
    "bike sampa",
    "yellow bike",
    "grin",
    "ciclofaixa",
    "aluguel de bike",
    "aluguel de bicicleta",
    "locacao de patinete",
    "locação de patinete",
    # Oficinas mecânicas a combustão / Carros
    "troca de oleo",
    "troca de óleo",
    "funilaria",
    "pintura automotiva",
    "centro automotivo",
    "auto center",
    "mecanica automotiva",
    "mecânica automotiva",
    "retifica",
    "retífica",
    "oficina mecanica",
    "oficina mecânica",
    "alinhamento e balanceamento",
    "borracharia",
    "posto de combustivel",
    "posto de combustível",
    "conveniencia",
    "conveniência",
    # Auto Elétrica de carros a combustão (baterias/alternadores de automóveis)
    "auto eletrica",
    "auto elétrica",
    "eletrica automotiva",
    "elétrica automotiva",
    "auto eletrico",
    "auto elétrico",
    # Ortopedia / Cadeira de rodas motorizada
    "cadeira de rodas",
    "ortopedia",
    "ortopedica",
    "ortopédica",
]

_MOBILIDADE_POSITIVE_TERMS = [
    "moto eletrica", "moto elétrica", "motos eletricas", "motos elétricas",
    "bicicleta eletrica", "bicicleta elétrica", "bicicletas eletricas", "bicicletas elétricas",
    "bicicletaria eletrica", "bicicletaria elétrica", "bicicletaria e-bike", "bicicletaria ebike",
    "e-bike", "ebike", "scooter eletrica", "scooter elétrica", "scooters eletricas", "scooters elétricas",
    "patinete eletrico", "patinete elétrico", "patinetes eletricos", "patinetes elétricos",
    "veiculo eletrico", "veículo elétrico", "veiculos eletricos", "veículos elétricos",
    "mobilidade eletrica", "mobilidade elétrica", "mobilidade leve",
    "watts", "voltz", "shineray eletrica", "shineray elétrica", "niu", "super soco", "bee eletrica", "lev", "nxt", "muv", "two dogs",
    "concessionaria", "concessionária", "revenda de motos", "revenda de ebike", "revenda de bicicletas eletricas", "revenda de bicicletas elétricas",
]

_MOBILIDADE_B2B_HIGH_INTENT = [
    "distribuidor", "distribuidora", "atacadista", "atacado", "revenda", "importadora", "fornecedor", "concessionaria", "concessionária",
]

_MOBILIDADE_B2B_MEDIUM_INTENT = [
    "loja de motos eletricas", "loja de motos elétricas", "loja de bicicletas eletricas", "loja de bicicletas elétricas",
    "loja de e-bikes", "ebike shop", "loja de scooters", "veiculos eletricos", "veículos elétricos", "mobilidade eletrica", "mobilidade elétrica",
    "bicicletaria eletrica", "bicicletaria elétrica",
]

_MOBILIDADE_BUSINESS_HINTS = [
    "eletrica", "elétrica", "ebike", "e-bike", "scooter", "moto", "motos", "bike", "bikes",
    "bicicleta", "bicicletas", "mobilidade", "veiculos", "veículos", "motors", "ev",
    "distribuidora", "revenda", "loja", "concessionaria", "concessionária", "ltda", "me", "epp", "s.a",
]


def _score_mobilidade_fit(texto: str, nome: str) -> int:
    score = 20  # Base
    nome_norm = _norm_key(nome)
    texto_norm = _norm_key(texto)

    # Tier 1 (+80): Canal B2B Direto (Distribuidor, Revenda, Atacado, Concessionária)
    if any(t in nome_norm or t in texto_norm for t in _MOBILIDADE_B2B_HIGH_INTENT):
        score += 80

    # Tier 2 (+50): Produto e Loja Especializada (Moto Elétrica, E-bike, Scooter, Mobilidade Elétrica)
    if any(t in nome_norm or t in texto_norm for t in _MOBILIDADE_B2B_MEDIUM_INTENT):
        score += 50

    # Tier 3 (+30): Termos positivos de mobilidade elétrica
    if any(t in nome_norm or t in texto_norm for t in _MOBILIDADE_POSITIVE_TERMS):
        score += 30

    # Penalidade (-30): Se parecer nome de pessoa física sem indicador comercial
    if _looks_like_mobilidade_person_name(nome_norm):
        score -= 30

    return max(0, score)


def _looks_like_mobilidade_person_name(nome_norm: str) -> bool:
    parts = [p for p in (nome_norm or "").split() if p]
    if len(parts) < 2 or len(parts) > 5:
        return False
    if any(term in nome_norm for term in _MOBILIDADE_BUSINESS_HINTS):
        return False
    return True


def _filter_noise_mobilidade_eletrica(results: list[dict]) -> list[dict]:
    """Filtro semântico e B2B em memória para o segmento 'Mobilidade Elétrica'.

    Lógica:
      - Remove eletropostos, estações de carga, oficinas a combustão, aluguel público e bicicletarias tradicionais sem e-bike
      - Mantém lojas, concessionárias e distribuidores de motos, e-bikes e scooters elétricas
      - Calcula e atribui Fit Score B2B (mobilidade_fit_score)
    """
    filtered = []
    for item in results:
        nome_raw = item.get("nome") or ""
        nome = _norm_key(nome_raw)
        raw_text = _norm_key(item.get("__raw_text") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])
        query_sources = " ".join([_norm_key(str(qs)) for qs in (item.get("query_sources") or [])])

        texto_loja = f"{nome} {raw_text} {categorias_str}"
        texto_para_busca = f"{texto_loja} {query_sources}"

        # 1. Filtro de ruídos óbvios
        is_noise = any(t in texto_loja for t in _MOBILIDADE_NOISE_NAMES)
        if is_noise:
            continue

        # 2. Descarte de bicicletarias e oficinas tradicionais de bicicletas a pedal sem sinal elétrico/e-bike
        termos_bicicletaria_tradicional = ["bicicletaria", "casa das bicicletas", "oficina de bicicletas", "conserto de bicicletas", "loja de bicicletas", "bicicletas"]
        eh_bicicletaria_tradicional = any(b in texto_loja for b in termos_bicicletaria_tradicional)
        if eh_bicicletaria_tradicional:
            tem_sinal_eletrico = any(e in texto_loja for e in ["eletrica", "elétrica", "e-bike", "ebike", "scooter", "moto", "watts", "voltz", "shineray", "niu", "lev", "nxt", "mobilidade"])
            if not tem_sinal_eletrico:
                continue

        # 3. Filtro de negócios genéricos sem qualquer sinal positivo de mobilidade elétrica no texto próprio da loja
        tem_positivo = any(p in texto_loja for p in _MOBILIDADE_POSITIVE_TERMS)
        if not tem_positivo:
            continue

        # Calcular Fit Score B2B
        fit_score = _score_mobilidade_fit(texto_para_busca, nome_raw)
        item["mobilidade_fit_score"] = fit_score

        filtered.append(item)

    filtered.sort(key=lambda it: int(it.get("mobilidade_fit_score") or 0), reverse=True)
    return filtered


def _filter_large_retail(results: list[dict]) -> list[dict]:
    """Filtra grandes redes de varejo e serviços puramente técnicos dos resultados."""
    server_exclusions = [
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
        "lojas cem",
        "loja cem",
        "pernambucanas",
        "marabraz",
        "lojas colombo",
        "gazin",
        "novo mundo",
        "assaí",
        "assai",
        "atacadão",
        "atacadao",
        "sam's club",
        "sams club",
        "pão de açúcar",
        "pao de acucar",
        "mercado livre",
        "ponto de coleta",
        "agência mercado livre",
        
        "refrigeração",
        "refrigeracao",
        "lavadora",
        "lavadoras",
        "oficina",
        
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

    repair_exclusions = [
        "assistência técnica",
        "assistencia tecnica",
        "conserto",
        "reparo",
        "manutenção",
        "manutencao",
    ]

    commercial_exceptions = [
        "informática",
        "informatica",
        "distribuidor",
        "distribuidora",
        "revenda",
        "atacadista",
        "atacado",
        "loja",
        "suprimentos",
        "periféricos",
        "perifericos",
        "eletrônicos",
        "eletronicos",
        "gamer",
        "tecnologia",
        "componentes",
    ]
    
    filtered = []
    for item in results:
        nome = (item.get("nome", "") or "").lower()
        # Verificar grandes redes e exclusões absolutas
        if any(excl in nome for excl in server_exclusions):
            continue

        # Verificar se é assistência técnica pura (sem termos comerciais de TI)
        has_repair = any(rep in nome for rep in repair_exclusions)
        if has_repair:
            has_commercial = any(comm in nome for comm in commercial_exceptions)
            if not has_commercial:
                continue

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

    Ex: ao buscar em "Altair", remove "Shineray Suzano", "Shineray Ferraz de Vasconcelos" ou "Loja Zema - Casa Branca".
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

        norm_nome = _norm_key(nome_raw)

        # 1. Checa separadores " - Cidade", " / Cidade", " (Cidade)" ou palavra isolada de cidade no final
        m = re.search(r"[\s\-/\(]\s*([A-Za-zÀ-ÿ0-9\s]{2,40})[\)]?$", nome_raw)
        if m:
            declared_city = _norm_key(m.group(1))
            if declared_city and declared_city != target_city and target_city not in norm_nome:
                # Se declarou explicitamente outra cidade no nome e a cidade alvo não está no nome, descarte
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
    # Detecta "Cidade - UF" ou "Cidade, UF"
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
            if norm_cidade_extraida and norm_cidade_extraida != target_city and target_city not in norm_cidade_extraida:
                # Cidade extraída é diferente da cidade alvo - descarta
                continue

        # 3. Fallback: Verifica se o texto bruto do card do Maps acusa uma cidade diferente
        raw_text = str(item.get("__raw_text") or "")
        if raw_text:
            matches = city_state_re.findall(raw_text)
            if matches:
                found_wrong_city = False
                for match_city in reversed(matches):
                    candidate = match_city.split("·")[-1].split("|")[-1].split("-")[-1].strip()
                    candidate = _norm_key(candidate)

                    if candidate and candidate != target_city and candidate not in target_city:
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
    
    # Termos leves de exclusão para a query do Google Maps (para não estourar limite de tamanho da busca)
    # O descarte pesado de grandes redes e assistências técnicas é feito 100% em memória no Python (_filter_large_retail)
    exclude_terms = [
        "fechado",
        "extinto",
        "falência",
    ]
    
    # Grupos de âncoras por família Multilaser (Curva ABC Fevereiro)
    # AC = Acessórios/Periféricos | ME = Mídia/Energia | PC = Computadores | IC = SSD/Memória
    anchor_groups: dict[str, list[str]] = {
        "Informática": [
            # Núcleo de Alta Performance B2B e Varejo Especializado
            "distribuidor informática",
            "revenda informática",
            "atacadista informática",
            "loja de informática",
            "comércio de acessórios de informática",
            "loja de eletrônicos e informática",
            "suprimentos de informática",
            "loja de laptops",
            "loja de tablets",
            "papelaria e informática",
            "comércio de informática",
            "distribuidor de componentes de computador",
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
        "Gamer": [
            # TIER 1: Compra em volume e revenda B2B
            "distribuidor gamer",
            "distribuidor de games",
            "distribuidor de jogos",
            "atacadista gamer",
            "atacadista de games",
            "revenda gamer",
            "revenda de games",
            "fornecedor gamer",
            "fornecedor de games",
            "importadora gamer",
            "atacado gamer",
            
            # TIER 2: Varejo especializado com foco em comércio (físico/online)
            "loja gamer",
            "loja de games",
            "loja de jogos",
            "loja de informática gamer",
            
            # TIER 3: Periféricos e Acessórios
            "acessórios gamer",
            "periféricos gamer",
            "cadeira gamer",
            "pc gamer",
        ],
        "Brinquedos": [
            # TIER 1: compra em volume e revenda
            "distribuidor de brinquedos",
            "atacadista de brinquedos",
            "atacado de brinquedos",
            "revenda de brinquedos",
            "fornecedor de brinquedos",
            "importadora de brinquedos",
            "brinquedos atacado e varejo",
            # TIER 2: varejo especializado com giro
            "loja de brinquedos",
            "lojas de brinquedos",
            "brinquedos educativos",
            "jogos educativos",
            "jogos infantis",
            "loja infantil brinquedos",
            "loja kids brinquedos",
            # TIER 3: correlatos que costumam revender brinquedos
            "papelaria e brinquedos",
            "bazar e brinquedos",
            "loja de presentes e brinquedos",
            "loja de variedades brinquedos",
            "loja de 1.99 brinquedos",
        ],
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
        "Mobilidade Elétrica": [
            # TIER 0: Termos naturais diretos de busca no Maps
            "mobilidade elétrica",
            "lojas de mobilidade elétrica",

            # TIER 1: B2B - Atacadistas e Distribuidores
            "distribuidor de mobilidade elétrica",
            "distribuidor de motos elétricas",
            "distribuidor de bicicletas elétricas",
            "atacadista de mobilidade elétrica",
            "revenda de mobilidade elétrica",
            "revenda de motos elétricas",
            "revenda de bicicletas elétricas",

            # TIER 2: Motos e Scooter Elétricas (Concessionárias e Lojas Especializadas)
            "loja de motos elétricas",
            "concessionária de motos elétricas",
            "loja de scooters elétricas",
            "scooter elétrica",
            "motos elétricas",

            # TIER 3: Bicicletas Elétricas (e-bikes)
            "loja de bicicletas elétricas",
            "loja de e-bikes",
            "ebike shop",
            "bicicletaria elétrica",
            "bicicletas elétricas",

            # TIER 4: Patinetes e Veículos Leves Elétricos
            "loja de patinetes elétricos",
            "veículos elétricos",
            "assistência e venda de moto elétrica",
        ],
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

    # Sennheiser: CNPJ com necessidade profissional de audio, mesmo quando for
    # consumidor final empresarial, e nao apenas revenda em volume.
    anchor_groups["Sennheiser"] = [
        "loja de audio profissional",
        "audio profissional",
        "revenda de audio profissional",
        "equipamentos de audio profissional",
        "loja de instrumentos musicais",
        "distribuidor de instrumentos musicais",
        "revenda de instrumentos musicais",
        "instrumentos musicais e audio profissional",
        "microfones profissionais",
        "sistemas de microfone sem fio",
        "estudio de gravacao",
        "estudio de podcast",
        "podcast studio",
        "produtora audiovisual",
        "produtora de video",
        "integrador audiovisual",
        "solucoes av",
        "emissora de radio",
        "emissora de tv",
        "broadcast audio",
        "equipamentos para radio e tv",
        "sonorizacao profissional",
        "sonorizacao de eventos",
        "equipamentos para eventos",
        "locadora de som",
        "locacao de som para eventos",
        "locacao de audio",
        "som para igreja",
        "sonorizacao para igrejas",
        "audio para auditorio",
        "teatro e auditorio",
        "casa de show",
        "casa de eventos",
        "centro de convencoes",
        "hotel eventos",
        "universidade auditorio",
        "escola de musica",
        "audio corporativo",
        "integrador audio e video",
        "integrador av",
        "videoconferencia corporativa",
        "sistemas de conferencia",
    ]

    anchor_groups["Informática (Médio Porte)"] = [
        "distribuidora de informática",
        "revenda de informática",
        "atacadista de informática",
        "atacado de informática",
        "suprimentos de informática",
        "loja de informática atacado",
        "distribuidor de informática",
        "computadores e periféricos",
    ]

    anchor_groups["Varejistas de Médio Porte"] = [
        "supermercado",
        "supermercados",
        "supermercado regional",
        "rede de supermercados",
        "hipermercado",
        "atacarejo",
        "loja de móveis e eletro",
        "móveis e eletrodomésticos",
        "loja de eletrodomésticos",
        "loja de departamentos",
        "loja de utilidades domésticas",
        "loja de utilidades",
        "loja de variedades",
        "bazar e presentes",
        "eletromóveis",
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
            "Informática (Médio Porte)",
            "Varejistas de Médio Porte",
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
                    "atacado", "distribuidora", "fornecedor", "revenda", "outlet", "saldão", "bazar", "shopping", "papelaria",
                    "locadora", "equipamento", "drone", "câmera", "estabilizador",
                    "acessório", "clube", "produtora", "estúdio", "importadora",
                    "concessionária", "concessionaria", "ebike", "bicicletaria", "veículos", "veiculos", "assistência", "assistencia",
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
            # Drones: Inserir "DJI"
            # Mobilidade Elétrica: Inserir marcas do setor ("Watts", "Voltz", "Shineray")
            if "drone" in seg_clean.lower():
                seg_brands = ["DJI"]
            elif "mobilidade" in seg_clean.lower():
                seg_brands = ["Watts", "Voltz", "Shineray"]
            else:
                seg_brands = brand_terms[:2]
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
        if seg == "Sennheiser":
            all_excludes = exclude_terms + _SENNHEISER_NOISE_NAMES
        if seg == "Brinquedos":
            all_excludes = exclude_terms + _BRINQUEDOS_NOISE_NAMES
        if seg == "Gamer":
            all_excludes = exclude_terms + _GAMER_NOISE_NAMES
        if "varej" in seg.lower():
            all_excludes = exclude_terms + ["magazine luiza", "casas bahia", "lojas cem", "pernambucanas", "marabraz", "farmacia", "drogaria", "oficina", "mecanica"]
        if "inform" in seg.lower():
            all_excludes = exclude_terms + ["assistencia tecnica", "software", "provedor", "consultoria"]
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
