import time
import hashlib
import re
import logging
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

_CACHE = {}


def _safe_text(v: str) -> str:
    return (v or '').strip()


def _clean_address(v: str) -> str:
    v = _safe_text(v)
    if not v:
        return ''
    v = v.replace('\n', ' ')
    v = re.sub(r'\s+', ' ', v).strip()
    v = re.sub(r'^[^0-9A-Za-zÀ-ÿ]+', '', v).strip()
    return v


def _clean_phone(v: str) -> str:
    v = _safe_text(v)
    if not v:
        return ''
    v = v.replace('\n', ' ')
    v = re.sub(r'\s+', ' ', v).strip()
    m = re.search(r'(\+?\d[\d\s().\-]{7,}\d)', v)
    if m:
        v = m.group(1).strip()

    # Normaliza telefones BR para evitar formatos quebrados como "19) 4042-5008"
    digits = re.sub(r'\D', '', v)
    if digits.startswith('55') and len(digits) in (12, 13):
        digits = digits[2:]
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"

    return re.sub(r'^[^0-9+]+', '', v).strip()


def _clean_website(v: str) -> str:
    v = _safe_text(v).replace('\n', ' ').strip()
    if not v:
        return ''
    v = re.sub(r'\s+', ' ', v).strip()

    m = re.search(r'(https?://[^\s]+)', v, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()

    m = re.search(r'([a-z0-9][a-z0-9\-\.]+\.[a-z]{2,})(/[^\s]*)?', v, flags=re.IGNORECASE)
    if m:
        return (m.group(1) + (m.group(2) or '')).strip()

    v = re.sub(r'^[^A-Za-z0-9]+', '', v).strip()
    return v


def derive_maps_place_id(maps_url: str) -> str:
    maps_url = _safe_text(maps_url)
    if not maps_url:
        return ''

    try:
        parsed = urlparse(maps_url)
        qs = parse_qs(parsed.query or '')
        cid = (qs.get('cid') or [''])[0]
        cid = _safe_text(cid)
        if cid and cid.isdigit():
            return f"cid:{cid}"
    except Exception:
        pass

    m = re.search(r'(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)', maps_url)
    if m:
        return f"ftid:{m.group(1).lower()}"

    return ''


def _get_first_text(loc) -> str:
    try:
        if loc.count() <= 0:
            return ''
        return _safe_text(loc.first.inner_text())
    except Exception:
        return ''


def _extract_labeled_button_value(page, data_item_id_contains: str) -> str:
    try:
        btn = page.locator(f'button[data-item-id*="{data_item_id_contains}"]')
        txt = _get_first_text(btn)
        if txt:
            return txt
    except Exception:
        pass
    return ''


def _extract_labeled_link_value(page, data_item_id_contains: str) -> str:
    try:
        a = page.locator(f'a[data-item-id*="{data_item_id_contains}"]')
        txt = _get_first_text(a)
        if txt:
            return txt
    except Exception:
        pass
    return ''


def _extract_external_website_fallback(page) -> str:
    try:
        anchors = page.locator('a[href^="http"]')
        n = anchors.count()
        for i in range(min(n, 60)):
            a = anchors.nth(i)
            href = _safe_text(a.get_attribute('href') or '')
            txt = _safe_text(a.inner_text() or '')
            if not href:
                continue
            href_l = href.lower()
            if 'google.' in href_l or '/maps' in href_l:
                continue
            if not txt or '.' not in txt:
                continue
            return txt
    except Exception:
        pass
    return ''


def scrape_maps_place_details(maps_url: str, headless: bool = True):
    maps_url = _safe_text(maps_url)
    if not maps_url:
        return {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(locale="pt-BR")
        page = context.new_page()

        try:
            page.goto(maps_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)

            html = page.content().lower()
            if "unusual traffic" in html or "detected unusual traffic" in html:
                raise RuntimeError("Google bloqueou a automação (unusual traffic).")

            endereco = _extract_labeled_button_value(page, "address")
            telefone = _extract_labeled_button_value(page, "phone")
            website = _extract_labeled_button_value(page, "authority")
            if not website:
                website = _extract_labeled_link_value(page, "authority")
            if not website:
                website = _extract_external_website_fallback(page)

            if not telefone:
                telefone = _extract_labeled_button_value(page, "phone:tel")

            return {
                "endereco": _clean_address(endereco),
                "telefone": _clean_phone(telefone),
                "website": _clean_website(website),
            }

        finally:
            context.close()
            browser.close()


def _cache_key(query: str, limit: int) -> str:
    return f"{query.strip().lower()}|{limit}"


def scrape_maps_results(query: str, limit: int = 20, headless: bool = False, cache_ttl_seconds: int = 300):
    query = (query or '').strip()
    if not query:
        return []

    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50

    now = time.time()
    key = _cache_key(query, limit)
    cached = _CACHE.get(key)
    if cached and (now - cached[0]) < cache_ttl_seconds:
        return cached[1]

    url = f"https://www.google.com/maps/search/{query.replace(' ', '%20')}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(locale="pt-BR")
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1500)

            html = page.content().lower()
            if "unusual traffic" in html or "detected unusual traffic" in html:
                raise RuntimeError("Google bloqueou a automação (unusual traffic).")

            feed = page.locator('div[role="feed"]')
            if feed.count() == 0:
                page.wait_for_timeout(1500)

            items = []
            seen = set()

            for _ in range(12):
                anchors = page.locator('a[href*="/maps/place/"]')
                count = anchors.count()
                for i in range(count):
                    a = anchors.nth(i)
                    href = (a.get_attribute("href") or "").strip()
                    if not href:
                        continue
                    if href.startswith("/"):
                        href = "https://www.google.com" + href
                    if href in seen:
                        continue

                    name = (a.get_attribute("aria-label") or "").strip()
                    if not name:
                        try:
                            name = (a.inner_text() or "").strip().split("\n")[0]
                        except Exception:
                            name = ""
                    
                    # Limpar o nome removendo ícones e caracteres especiais
                    if name:
                        name = re.sub(r'\[.*?\]', '', name)
                        name = re.sub(r'\(.*?\)', '', name)
                        name = re.sub(r'[^\w\s\-\.]', '', name)
                        name = name.strip()

                    if not name:
                        continue

                    # Extrair informações completas do cartão do Google Maps
                    endereco_completo = ""
                    cidade_extraida = ""
                    estado_extraido = ""
                    telefone_extraido = ""
                    whatsapp_extraido = ""
                    website_extraido = ""
                    raw_text = ""
                    card_text = ""

                    try:
                        # Estratégia 1: Subir na árvore DOM até encontrar o container do item
                        # O card do Maps geralmente tem role='article' ou é um div com dados do estabelecimento
                        try:
                            # Procura por ancestor que seja o container do resultado
                            card_container = a.locator('xpath=ancestor::div[@role="article"]')
                            if card_container.count() == 0:
                                # Fallback: procura container por estrutura de árvore
                                card_container = a.locator('xpath=ancestor::div[3]')
                            
                            if card_container.count() > 0:
                                card_text = (card_container.first.inner_text() or "").strip()
                        except Exception:
                            pass
                        
                        # Estratégia 2: Se ainda não conseguiu, tenta subir manualmente
                        if not card_text:
                            try:
                                card_text = (a.locator("xpath=../..").first.inner_text() or "").strip()
                            except Exception:
                                pass

                        # Estratégia 3: Último recurso - tenta subir mais na árvore
                        if not card_text:
                            try:
                                card_text = (a.locator("xpath=../../..").first.inner_text() or "").strip()
                            except Exception:
                                pass

                        # Filtra botões de ação conhecidos que poluem o texto
                        if card_text:
                            # Remove padrões comuns de botões do Maps
                            card_text = re.sub(r'\bRotas\b.*', '', card_text, flags=re.IGNORECASE)
                            card_text = re.sub(r'\bSalvar\b.*', '', card_text, flags=re.IGNORECASE)
                            card_text = re.sub(r'\bCompartilhar\b.*', '', card_text, flags=re.IGNORECASE)
                            card_text = re.sub(r'\bMais\b.*', '', card_text, flags=re.IGNORECASE)
                            card_text = re.sub(r'\bVocê chegou ao final\b.*', '', card_text, flags=re.IGNORECASE)
                            card_text = card_text.strip()

                            raw_text = card_text.replace("\n", " | ")

                            # Extrair endereço completo do card_text
                            # O endereço geralmente aparece após o nome e telefone, separado por | ou quebras de linha
                            lines = [l.strip() for l in card_text.split("\n") if l.strip()]
                            if len(lines) > 1:
                                # Tenta encontrar a linha que parece endereço (contém rua, av, etc.)
                                for line in lines:
                                    if line == name:
                                        continue
                                    line_lower = line.lower()
                                    # Se a linha contém padrões de endereço (Rua, Av, etc.) ou cidade-estado
                                    has_street_prefix = any(prefix in line_lower for prefix in ["rua", "avenida", "av.", "r.", "alameda", "travessa", "praça", "estrada", "rodovia"])
                                    has_city_state = re.search(r'[A-Za-zÀ-ÿ\s]+[-·,]\s*(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b', line, re.IGNORECASE)
                                    if has_street_prefix or has_city_state:
                                        endereco_completo = line
                                        break

                            # Extrair cidade e estado do endereço ou do card_text
                            full_text = endereco_completo if endereco_completo else card_text
                            city_state_match = re.search(r'([A-Za-zÀ-ÿ0-9\s\-]+?)\s*[,·\-]\s*(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b', full_text, re.IGNORECASE)
                            if city_state_match:
                                cidade_extraida = city_state_match.group(1).strip()
                                estado_extraido = city_state_match.group(2).strip().upper()
                                if not endereco_completo:
                                    endereco_completo = f"{cidade_extraida} - {estado_extraido}"

                            # Extrair telefone do card_text
                            phone_match = re.search(r'(\(?\d{2}\)?\s*\d{4,5}[-\s]?\d{4})', card_text)
                            if phone_match:
                                telefone_extraido = phone_match.group(1).strip()

                            # Extrair WhatsApp do card_text (procura por número após "WhatsApp" ou "WA")
                            whatsapp_match = re.search(r'(?:WhatsApp|WA)[:\s]*(\(?\d{2}\)?\s*\d{4,5}[-\s]?\d{4})', card_text, re.IGNORECASE)
                            if whatsapp_match:
                                whatsapp_extraido = whatsapp_match.group(1).strip()

                            # Extrair website do card_text
                            website_match = re.search(r'(https?://[^\s<>"]+|www\.[^\s<>"]+)', card_text, re.IGNORECASE)
                            if website_match:
                                website_extraido = website_match.group(1).strip()
                                
                        # Debug: log do texto extraído para verificação
                        if raw_text:
                            import logging
                            logging.getLogger(__name__).debug(f"[SCRAPER] nome={name} | raw={raw_text[:100]}... | cidade={cidade_extraida}")
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).debug(f"[SCRAPER] Erro ao extrair dados do cartão: {e}")

                    seen.add(href)
                    maps_place_id = derive_maps_place_id(href)
                    place_key = maps_place_id or hashlib.sha1(href.encode("utf-8")).hexdigest()[:16]
                    items.append({
                        "id": place_key,
                        "maps_place_id": maps_place_id or place_key,
                        "nome": name,
                        "endereco": _clean_address(endereco_completo),
                        "cidade": cidade_extraida,
                        "estado": estado_extraido,
                        "telefone": _clean_phone(telefone_extraido),
                        "whatsapp": _clean_phone(whatsapp_extraido),
                        "website": _clean_website(website_extraido),
                        "maps_url": href,
                        "__raw_text": raw_text,
                    })

                    if len(items) >= limit:
                        break

                if len(items) >= limit:
                    break

                try:
                    if feed.count() > 0:
                        feed.first.evaluate("(el) => { el.scrollTop = el.scrollTop + el.clientHeight * 2; }")
                    else:
                        page.mouse.wheel(0, 1400)
                except Exception:
                    pass

                page.wait_for_timeout(900)

            _CACHE[key] = (now, items)
            return items

        finally:
            context.close()
            browser.close()
