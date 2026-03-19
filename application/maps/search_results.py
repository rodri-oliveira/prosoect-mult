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
                
                # Calcular lojas únicas desta query
                new_keys: set[str] = set()
                for it in (got or []):
                    k = _key_from_item(it)
                    if k and k not in seen_keys_total:
                        new_keys.add(k)
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
            
            # Log final com resumo
            logger.warning(
                "maps_summary total_queries=%s before_dedupe=%s after_dedupe=%s total_unique_keys=%s",
                len(executed_queries),
                merged_before_dedupe,
                len(seen_keys_total),
                len(seen_keys_total)
            )

            merged = _dedupe_items(merged)
            merged_after_dedupe = len(merged)
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

    existing_keys = _find_existing_keys(itens, existing_keys_repo)

    if existing_keys:
        existing_set = set(existing_keys)
        for it in itens or []:
            k = _key_from_item(it)
            if k and k in existing_set:
                it["already_added"] = True

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

    k = str(it.get("maps_place_id") or it.get("id") or "").strip()
    if k:
        return k
    u = str(it.get("maps_url") or "").strip()
    if u and derive_maps_place_id:
        try:
            return derive_maps_place_id(u)
        except Exception:
            return ""
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
    local = ", ".join([p for p in [cidade, estado] if (p or "").strip()])
    if local:
        return [f"{base} em {local}"]
    return [base]


def _build_queries_for_segments(segs: list[str], cidade: str, estado: str, extra: str) -> list[dict[str, str]]:
    """Estratégia inteligente de multi-query baseada nas famílias Multilaser (Curva ABC).
    
    Divide as âncoras em grupos lógicos por família de produto para maximizar
    cobertura de lojas (B2B e varejo) sem tornar queries muito específicas.
    
    Otimização para múltiplos segmentos:
    - 1 segmento: estratégia detalhada (~16 queries)
    - 2-3 segmentos: combinar com OR (~20 queries)
    - 4+ segmentos: estratégia genérica + priorização (~25 queries)
    """
    local = ", ".join([p for p in [cidade, estado] if (p or "").strip()])
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
    exclude_terms = ["fechado", "extinto", "falência"]
    
    # Grupos de âncoras por família Multilaser (Curva ABC Fevereiro)
    # AC = Acessórios/Periféricos | ME = Mídia/Energia | PC = Computadores | IC = SSD/Memória
    anchor_groups: dict[str, list[str]] = {
        "Informática": [
            "loja de informática",
            "informática",
            "mouse teclado",
            "headset webcam",  
            "notebook",
            "pendrive",
            "ssd memória",
        ],
        "Celulares": [
            "celular",
            "smartphone acessórios",
            "carregador cabo",
        ],
        "Áudio e Vídeo": [
            "loja de eletrônicos",
            "caixa de som",
            "soundbar",
            "vitrola",
            "microfone",
            "smartwatch",
            "amplificador",
            "som automotivo",
        ],
        "Eletroportáteis": [
            "loja de eletrodomésticos",
            "air fryer",
            "sanduicheira grill",
            "cafeteira",
            "chaleira elétrica",
            "liquidificador mixer",
            "secador prancha",
            "aspirador de pó",
            "ferro de passar",
            "climatizador",
        ],
        "Gamer": ["gamer"],
        "Brinquedos": ["brinquedos"],
        "Drones e Câmeras": [
            "loja de drones",
            "drone dji",
            "drone mini mavic",
            "drone fpv",
            "câmera de ação",
            "estabilizador gimbal",
            "osmo pocket",
            "filmadora câmera",
            "microfone sem fio",
        ],
        "Ortopédica": ["ortopedia"],
        "Fitness": ["fitness"],
        "Pet": ["pet shop"],
        "Redes": ["roteador switch", "cabo rede"],
        "Mobilidade Elétrica": ["patinete elétrico", "scooter"],
        "Health Care": [
            "loja de produtos médicos",
            "farmácia",
            "umidificador",
            "inalador nebulizador",
            "monitor de pressão",
            "oxímetro",
            "termômetro",
            "escova elétrica dental",
            "óleo essencial",
            "fita kinesio",
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
        is_brand_segment = seg_clean in ["Multikids"]
        
        if is_brand_segment:
            # Para segmentos de marca/linha, usar queries com âncoras diretamente
            for anchors in anchor_lists:
                if not anchors:
                    continue
                # Evitar duplicação se âncora já contém "loja" ou "distribuidor"
                anchor_lower = anchors.lower()
                has_loja = anchor_lower.startswith("loja de ") or anchor_lower.startswith("loja ") or " loja " in anchor_lower
                has_distribuidor = anchor_lower.startswith("distribuidor ")
                
                # Query B2B com âncora
                if has_distribuidor or has_loja:
                    q = f"{anchors}{local}".strip()
                else:
                    q = f"distribuidor de {anchors}{local}".strip()
                queries.append({"q": q, "segmento": seg_clean})
                
                # Query varejo com âncora
                if has_loja:
                    q = f"{anchors}{local}".strip()
                else:
                    q = f"loja de {anchors}{local}".strip()
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
                has_loja = anchor_lower.startswith("loja de ") or anchor_lower.startswith("loja ")
                
                # Query varejo com âncora
                if has_loja:
                    q = f"{anchors}{local}".strip()
                else:
                    q = f"loja de {anchors}{local}".strip()
                queries.append({"q": q, "segmento": seg_clean})
            
            # Query B2B do segmento
            q = f"distribuidor de {seg_clean}{local}".strip()
            queries.append({"q": q, "segmento": seg_clean})
            
            # Queries com marcas relevantes (captura revendedores autorizados)
            for brand in brand_terms[:2]:  # Limitar a 2 marcas por segmento
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
    
    # Adicionar query com exclusão apenas para a mais genérica (após deduplicação)
    if out:
        out[0]["q"] = f"{out[0]['q']} -fechado"
    
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
