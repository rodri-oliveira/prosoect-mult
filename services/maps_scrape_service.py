import time
import hashlib
import re
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
        return m.group(1).strip()
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

                    if not name:
                        continue

                    seen.add(href)
                    maps_place_id = derive_maps_place_id(href)
                    place_key = maps_place_id or hashlib.sha1(href.encode("utf-8")).hexdigest()[:16]
                    items.append({
                        "id": place_key,
                        "maps_place_id": maps_place_id or place_key,
                        "nome": name,
                        "endereco": "",
                        "telefone": "",
                        "whatsapp": "",
                        "website": "",
                        "maps_url": href,
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
