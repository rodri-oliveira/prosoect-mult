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
    if limit > 50:
        limit = 50

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
            queries = _build_queries_for_segments(segs=segs, cidade=cidade, estado=estado, extra=query)
        else:
            queries = _build_queries_for_free_text(query=query, cidade=cidade, estado=estado)

        executed_queries = list(queries)

        try:
            from services.maps_scrape_service import scrape_maps_results

            merged: list[dict[str, Any]] = []
            per_query_limit = min(50, limit)
            for q in queries:
                t0 = time.time()
                got = scrape_maps_results(q, limit=per_query_limit, headless=True)
                dt_ms = int((time.time() - t0) * 1000)
                logger.warning("maps_query ms=%s limit=%s items=%s q=%s", dt_ms, per_query_limit, len(got or []), q)
                query_stats.append({"q": q, "ms": dt_ms, "items": len(got or [])})
                merged.extend(got)

            merged_before_dedupe = len(merged)

            merged = _dedupe_items(merged)
            merged_after_dedupe = len(merged)
            itens = merged[:limit]
            for it in itens:
                it["cidade"] = it.get("cidade") or cidade
                it["estado"] = it.get("estado") or estado
                it["segmentos"] = it.get("segmentos") or segs

            modo = "real"
            query_real = queries[0] if queries else ""
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


def _build_queries_for_segments(segs: list[str], cidade: str, estado: str, extra: str) -> list[str]:
    """Estratégia inteligente de multi-query baseada nas famílias Multilaser (Curva ABC).
    
    Divide as âncoras em grupos lógicos por família de produto para maximizar
    cobertura de lojas (B2B e varejo) sem tornar queries muito específicas.
    """
    local = ", ".join([p for p in [cidade, estado] if (p or "").strip()])
    if local:
        local = f" em {local}"

    extra_clean = _normalize_extra(extra=extra, cidade=cidade, estado=estado)
    extra_is_generic = extra_clean.lower() in {"lojas", "loja"}
    
    # Extrair extra útil (se não for igual ao segmento)
    extra_suffix = ""
    if extra_clean and not extra_is_generic:
        if _norm_key(extra_clean) != _norm_key(segs[0] if segs else ""):
            extra_suffix = f" {extra_clean}"

    # Termos B2B expandidos para máxima cobertura de revenda
    b2b_terms = ["distribuidor", "atacadista", "representante", "revenda", "fornecedor"]
    
    # Grupos de âncoras por família Multilaser (Curva ABC Fevereiro)
    # AC = Acessórios/Periféricos | ME = Mídia/Energia | PC = Computadores | IC = SSD/Memória
    anchor_groups: dict[str, list[str]] = {
        "Informática": [
            "mouse teclado",           # AC - periféricos básicos
            "headset webcam",          # AC - periféricos avançados  
            "carregador pilha",        # ME - energia
            "pendrive",                # ME - armazenamento
            "notebook",                # PC - computadores
            "ssd memória",             # IC - componentes
        ],
        "Celulares": [
            "celular",
            "smartphone acessórios",
            "carregador cabo",
        ],
        "Áudio e Vídeo": [
            "tv",
            "caixa de som",
            "fone soundbar",
        ],
        "Eletroportáteis": [
            "air fryer",
            "sanduicheira",
            "cafeteira chaleira",
        ],
        "Gamer": ["gamer"],
        "Brinquedos": ["brinquedos"],
        "Drones e Câmeras": ["drone dji", "câmera"],
        "Ortopédica": ["ortopedia"],
        "Fitness": ["fitness"],
        "Pet": ["pet shop"],
        "Redes": ["roteador switch", "cabo rede"],
        "Mobilidade Elétrica": ["patinete elétrico", "scooter"],
    }

    queries: list[str] = []
    
    for seg in segs:
        seg_clean = (seg or "").strip()
        if not seg_clean:
            continue

        anchor_lists = anchor_groups.get(seg_clean, [""])
        
        # Para cada grupo de âncoras, criar queries B2B
        for anchors in anchor_lists:
            anchors_part = f" {anchors}" if anchors else ""
            
            for b2b_term in b2b_terms:
                queries.append(f"{b2b_term} de {seg_clean}{anchors_part}{extra_suffix}{local}".strip())
        
        # Query varejo abrangente (sem âncoras específicas para capturar todas as lojas)
        queries.append(f"loja de {seg_clean}{extra_suffix}{local}".strip())
        
        # Query varejo com âncoras combinadas (primeiras 2 âncoras)
        first_anchors = " ".join(anchor_lists[:2]) if len(anchor_lists) >= 2 else (anchor_lists[0] if anchor_lists else "")
        if first_anchors:
            queries.append(f"loja de {seg_clean} {first_anchors}{extra_suffix}{local}".strip())

    # Remover duplicatas mantendo ordem
    seen = set()
    out: list[str] = []
    for q in queries:
        k = q.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(q)
    
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

    return extra_clean


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
