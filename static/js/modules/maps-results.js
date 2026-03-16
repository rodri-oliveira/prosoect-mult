/**
 * Módulo de resultados do Maps
 * Gerencia renderização e carregamento de resultados da API
 */

import { writeMapsCache, readMapsCache, clearMapsCache, buildQueryPayload, getLastMapsItems, setLastMapsItems, removeItemByKey } from './maps-cache.js';
import { closeDrawer } from './maps-drawer.js';
import { submitLeadFormAsJsonIfFromMaps } from './form.js';
import { updateBtnBuscarCnpjGoogle } from './maps-search.js';

/**
 * Log de debug
 */
const mapsLog = (event, data) => {
    try {
        if (!window.MAPS_DEBUG) return;
        console.log(`[MAPS_DEBUG] ${event}`, data || {});
    } catch (e) {}
};

/**
 * Renderiza resultados no drawer
 */
export const renderResults = (items) => {
    const resultsNow = document.getElementById('mapsResults');
    const emptyNow = document.getElementById('mapsEmpty');
    if (!resultsNow || !emptyNow) {
        mapsLog('renderResults:missing_elements', { hasResultsEl: !!resultsNow, hasEmptyEl: !!emptyNow });
        return;
    }
    resultsNow.innerHTML = '';
    const list = Array.isArray(items) ? items : [];
    const normalized = list.map((it) => {
        const key = String(it.maps_place_id || it.id || '').trim();
        const already = !!it.already_added;
        return { ...it, __key: key, __already: already };
    });

    setLastMapsItems(normalized);
    if (normalized.length === 0) {
        emptyNow.classList.remove('hidden');
        return;
    }
    emptyNow.classList.add('hidden');

    normalized.forEach((it) => {
        const card = document.createElement('div');
        card.className = 'border border-gray-200 rounded-lg p-3 bg-white hover:bg-gray-50';
        card.dataset.id = it.id || '';

        const nome = it.nome || '';
        const endereco = it.endereco || '';
        const telefone = it.telefone || '';
        const website = it.website || '';
        const mapsUrl = it.maps_url || '';
        const already = !!it.__already;

        const websiteHref = (website && (website.startsWith('http://') || website.startsWith('https://')))
            ? website
            : (website ? `https://${website}` : '');

        card.innerHTML = `
            <div class="flex items-start justify-between gap-3">
                <label class="flex items-start gap-2 flex-1">
                    <input type="checkbox" name="mapsPick" value="${(it.id || '').replace(/"/g, '')}" class="mt-1 rounded border-gray-300 text-brand-600 focus:ring-brand-500" ${already ? 'disabled' : ''}>
                    <div class="min-w-0">
                        <div class="text-sm font-semibold text-gray-900 truncate">${nome}</div>
                        <div class="text-xs text-gray-500 mt-0.5">${endereco || '-'}</div>
                        <div class="text-xs text-gray-500 mt-0.5">${telefone ? '📞 ' + telefone : ''}${website ? (telefone ? ' • ' : '') + `<a href="${websiteHref}" target="_blank" class="hover:underline text-brand-700">${website}</a>` : ''}</div>
                        ${already ? '<div class="text-[11px] text-green-700 mt-1">Já adicionado</div>' : ''}
                    </div>
                </label>
                <div class="flex flex-col gap-2 items-end">
                    ${mapsUrl ? `<a href="${mapsUrl}" target="_blank" class="text-xs text-brand-700 hover:underline">Maps</a>` : ''}
                    <button type="button" class="btnUseOne text-xs px-3 py-1.5 rounded-md bg-gray-800 text-white hover:bg-gray-900">Usar</button>
                </div>
            </div>
        `;

        const useBtn = card.querySelector('.btnUseOne');
        if (useBtn) {
            useBtn.addEventListener('click', () => {
                useItem(it);
            });
        }

        resultsNow.appendChild(card);
    });
};

/**
 * Usa um item (preenche formulário)
 */
const useItem = async (it) => {
    const form = document.getElementById('formLead');
    if (!form) return;

    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val || '';
        if (id === 'f_site') {
            try { updateSiteLink(); } catch (e) {}
        }
    };

    const updateSiteLink = () => {
        const input = document.getElementById('f_site');
        const btn = document.getElementById('f_site_btn');
        if (!input || !btn) return;

        const normalizeWebsite = (value) => {
            const raw = String(value || '').trim();
            if (!raw) return '';
            const cleaned = raw.replace(/\s+/g, ' ').trim();
            const urlMatch = cleaned.match(/(https?:\/\/[^\s]+)/i);
            if (urlMatch && urlMatch[1]) return urlMatch[1].trim();
            const domainMatch = cleaned.match(/([a-z0-9][a-z0-9\-.]+\.[a-z]{2,})(\/[^\s]*)?/i);
            if (domainMatch && domainMatch[0]) return domainMatch[0].trim();
            return cleaned.replace(/^[^a-z0-9]+/i, '').trim();
        };

        const normalized = normalizeWebsite(input.value);
        if (!normalized) {
            btn.classList.add('hidden');
            btn.onclick = null;
            return;
        }

        const href = (normalized.startsWith('http://') || normalized.startsWith('https://')) ? normalized : `https://${normalized}`;
        btn.classList.remove('hidden');
        btn.onclick = () => {
            // Usar globalThis.open para evitar conflito com sandbox/extensões
            const opener = typeof globalThis !== 'undefined' ? globalThis.open : window.open;
            if (typeof opener === 'function') {
                opener(href, '_blank', 'noopener,noreferrer');
            } else {
                // Fallback: criar link e clicar
                const a = document.createElement('a');
                a.href = href;
                a.target = '_blank';
                a.rel = 'noopener,noreferrer';
                a.click();
            }
        };
    };

    const currentKey = String(it.maps_place_id || it.id || '').trim();
    window.__mapsUseCurrentKey = currentKey;

    let enriched = it;
    setVal('f_nome', enriched.nome || '');
    setVal('f_endereco', enriched.endereco || '');
    setVal('f_telefone', enriched.telefone || '');
    setVal('f_whatsapp', enriched.whatsapp || enriched.telefone || '');
    setVal('f_site', enriched.website || enriched.site || '');
    setVal('f_maps_place_id', enriched.maps_place_id || enriched.id || '');
    setVal('f_maps_url', enriched.maps_url || '');
    setVal('f_cidade', it.cidade || (document.getElementById('mapCidade')?.value || ''));
    setVal('f_estado', it.estado || (document.getElementById('mapEstado')?.value || ''));

    try {
        const inputSite = document.getElementById('f_site');
        if (inputSite) inputSite.addEventListener('input', updateSiteLink);
        updateSiteLink();
    } catch (e) {}

    try { updateBtnBuscarCnpjGoogle(); } catch (e) {}

    const checks = form.querySelectorAll('input[name="segmento"]');
    if (checks && enriched.segmentos && Array.isArray(enriched.segmentos)) {
        checks.forEach((el) => {
            el.checked = enriched.segmentos.includes(el.value);
        });
    }

    const statusEl = document.getElementById('mapsDrawerStatus');
    const needsDetails = (!enriched.website) && !!enriched.maps_url;
    if (needsDetails) {
        try {
            if (statusEl) statusEl.textContent = 'Buscando detalhes...';
            fetch('/api/maps/detalhe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ maps_url: enriched.maps_url })
            })
                .then(async (resp) => ({ ok: resp.ok, data: await resp.json().catch(() => null) }))
                .then(({ ok, data }) => {
                    if (window.__mapsUseCurrentKey !== currentKey) return;
                    if (!ok || !data || !data.ok || !data.item) return;
                    const d = data.item;
                    if (d.endereco) setVal('f_endereco', d.endereco);
                    if (d.telefone) {
                        setVal('f_telefone', d.telefone);
                        const curWa = (document.getElementById('f_whatsapp')?.value || '').trim();
                        if (!curWa) setVal('f_whatsapp', d.telefone);
                    }
                    if (d.website) setVal('f_site', d.website);
                    if (statusEl) statusEl.textContent = 'OK';
                    try { updateBtnBuscarCnpjGoogle(); } catch (e) {}
                })
                .catch(() => {});
        } catch (e) {}
    }

    // Fecha o drawer para revelar o formulário
    try {
        window.__mapsResultsCache = Array.isArray(getLastMapsItems()) ? getLastMapsItems() : [];
        window.__mapsLastPayloadCache = buildQueryPayload();
    } catch (e) {}
    closeDrawer();
};

/**
 * Carrega resultados da API
 */
export const loadResults = async () => {
    const statusEl = document.getElementById('mapsDrawerStatus');
    const subEl = document.getElementById('mapsDrawerSub');
    if (!statusEl || !subEl) return;

    const { segmentosSelecionados, cidade, estado, query } = buildQueryPayload();
    subEl.textContent = query ? query : '';

    mapsLog('loadResults:start', { query, cidade, estado, segmentosSelecionados });

    statusEl.textContent = 'Carregando...';
    try {
        const params = new URLSearchParams();
        if (query) params.set('query', query);
        if (cidade) params.set('cidade', cidade);
        if (estado) params.set('estado', estado);
        params.set('limit', '50');
        (segmentosSelecionados || []).forEach((s) => params.append('segmentos', s));
        const resp = await fetch(`/api/maps/resultados?${params.toString()}`);
        const data = await resp.json();
        if (!resp.ok || !data.ok) throw new Error(data.message || 'Erro');
        statusEl.textContent = data.modo === 'mock' ? 'Modo: mock' : 'OK';
        mapsLog('loadResults:success', { modo: data.modo, items: (data.items || []).length, existing_keys: (data.existing_keys || []).length });
        const nextItems = Array.isArray(data.items) ? data.items : [];
        const currentCached = (window.ProspeccaoState && typeof window.ProspeccaoState.getMapItems === 'function')
            ? window.ProspeccaoState.getMapItems()
            : (Array.isArray(window.__mapsResultsCache) ? window.__mapsResultsCache : []);
        const shouldPreserve = nextItems.length === 0 && Array.isArray(currentCached) && currentCached.length > 0;
        if (!shouldPreserve) {
            writeMapsCache(nextItems, buildQueryPayload());
            renderResults(nextItems);
        } else {
            try { readMapsCache(); } catch (e) {}
            statusEl.textContent = '0 resultados. Mantendo últimos resultados.';
            renderResults(currentCached);
        }
        try {
            if (window.ProspeccaoState && typeof window.ProspeccaoState.save === 'function') {
                window.ProspeccaoState.save({ mapsSearchPending: false });
            } else {
                localStorage.setItem('mapsSearchPending', '0');
            }
        } catch (e) {}
    } catch (e) {
        mapsLog('loadResults:error', { error: String(e && e.message ? e.message : e) });
        try {
            const cached = Array.isArray(window.__mapsResultsCache) ? window.__mapsResultsCache : [];
            if (cached.length > 0) {
                statusEl.textContent = 'Erro ao buscar. Mantendo últimos resultados.';
                renderResults(cached);
                return;
            }
        } catch (err) {}
        statusEl.textContent = 'Erro ao carregar resultados.';
        renderResults([]);
    }
};

/**
 * Inicializa listeners de botões do drawer
 */
export function initDrawerButtonListeners() {
    const statusEl = document.getElementById('mapsDrawerStatus');
    const useSelectedBtn = document.getElementById('mapsUseSelected');
    const addSelectedBtn = document.getElementById('mapsAddSelected');

    // Botão Atualizar
    if (!window.__MAPS_RELOAD_DELEGATION_INSTALLED) {
        window.__MAPS_RELOAD_DELEGATION_INSTALLED = true;
        document.body.addEventListener('click', (e) => {
            const btn = e.target?.closest?.('#mapsDrawerReload');
            if (!btn) return;
            e.preventDefault();
            e.stopPropagation();
            mapsLog('reload:click', {});
            clearMapsCache();
            loadResults();
        });
    }

    // Botão Fechar
    if (!window.__MAPS_CLOSE_DELEGATION_INSTALLED) {
        window.__MAPS_CLOSE_DELEGATION_INSTALLED = true;
        document.body.addEventListener('click', (e) => {
            const btn = e.target?.closest?.('#mapsDrawerClose');
            if (!btn) return;
            e.preventDefault();
            e.stopPropagation();
            mapsLog('close:click', {});
            closeDrawer();
        });
    }

    // Overlay
    if (!window.__MAPS_OVERLAY_DELEGATION_INSTALLED) {
        window.__MAPS_OVERLAY_DELEGATION_INSTALLED = true;
        document.body.addEventListener('click', (e) => {
            const el = e.target?.closest?.('#mapsDrawerOverlay');
            if (!el) return;
            mapsLog('overlay:click', {});
            closeDrawer();
        });
    }

    // Botão Usar selecionado
    if (useSelectedBtn) {
        useSelectedBtn.addEventListener('click', () => {
            const picked = document.querySelector('input[name="mapsPick"]:checked');
            if (!picked) return;
            const id = picked.value;
            const it = (getLastMapsItems() || []).find((x) => String(x.id || '') === String(id));
            if (!it) return;
            useItem(it);
        });
    }

    // Botão Adicionar selecionados
    if (addSelectedBtn) {
        addSelectedBtn.addEventListener('click', async () => {
            const items = getPickedItems();
            if (!items || items.length === 0) return;

            if (statusEl) statusEl.textContent = 'Adicionando...';
            try {
                const resp = await fetch('/api/maps/adicionar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ items })
                });
                const data = await resp.json();
                if (!resp.ok || !data.ok) throw new Error(data.message || 'Erro');

                if (statusEl) statusEl.textContent = `Adicionados: ${data.added_count} | Já existiam: ${data.duplicate_count}`;

                const addedKeySet = new Set([].concat(data.added_keys || [], data.duplicate_keys || []).map((k) => String(k || '').trim()).filter(Boolean));
                const updatedItems = (getLastMapsItems() || []).map((it) => {
                    const key = String(it.maps_place_id || it.id || '').trim();
                    if (key && addedKeySet.has(key)) return { ...it, already_added: true };
                    return it;
                });
                setLastMapsItems(updatedItems);
                renderResults(updatedItems);
            } catch (e) {
                if (statusEl) statusEl.textContent = 'Erro ao adicionar selecionados.';
            }
        });
    }
}

/**
 * Obtém itens selecionados
 */
const getPickedItems = () => {
    const picked = Array.from(document.querySelectorAll('input[name="mapsPick"]:checked'));
    const ids = picked.map((el) => String(el.value || '')).filter(Boolean);
    const items = (getLastMapsItems() || []).filter((x) => ids.includes(String(x.id || '')));
    return items;
};

/**
 * Inicializa listener de submit do formulário
 */
export function initFormSubmitListener() {
    const formLead = document.getElementById('formLead');
    const statusEl = document.getElementById('mapsDrawerStatus');
    if (!formLead) return;

    formLead.addEventListener('submit', async (e) => {
        try {
            const mapsPlaceId = (document.getElementById('f_maps_place_id')?.value || '').trim();
            const mapsUrl = (document.getElementById('f_maps_url')?.value || '').trim();
            const fromMaps = !!mapsPlaceId || !!mapsUrl;
            mapsLog('form:submit', { fromMaps, mapsPlaceId: mapsPlaceId || null, hasMapsUrl: !!mapsUrl });
            if (!fromMaps) return;

            e.preventDefault();
            const res = await submitLeadFormAsJsonIfFromMaps();
            if (!res || !res.handled) return;

            mapsLog('form:submit:api_done', { created: res.data ? res.data.created : null, maps_place_id: res.data ? res.data.maps_place_id : null });

            if (res.data && res.data.created === false) {
                if (statusEl) statusEl.textContent = 'Já existia na sua lista.';
                alert('Este item já existe na sua lista de prospecção.');
                return;
            }

            const mpid = (res.data && res.data.maps_place_id) ? String(res.data.maps_place_id).trim() : '';
            if (mpid) removeItemByKey(mpid);

            mapsLog('form:submit:remove_item', { mpid: mpid || null, remaining: Array.isArray(getLastMapsItems()) ? getLastMapsItems().length : null });

            const elMpid = document.getElementById('f_maps_place_id');
            const elMurl = document.getElementById('f_maps_url');
            const elCnpj = document.getElementById('f_cnpj');
            const elCnpjStatus = document.getElementById('cnpjStatus');
            if (elMpid) elMpid.value = '';
            if (elMurl) elMurl.value = '';
            if (elCnpj) elCnpj.value = '';
            if (elCnpjStatus) elCnpjStatus.textContent = '';

            try {
                const restore = {
                    items: Array.isArray(getLastMapsItems()) ? getLastMapsItems() : [],
                    payload: buildQueryPayload(),
                    remove_key: mpid,
                };
                sessionStorage.setItem('mapsDrawerRestore', JSON.stringify(restore));
                mapsLog('restore:write_sessionStorage', { items: restore.items.length, hasPayload: !!restore.payload, remove_key: restore.remove_key || null });
            } catch (e) {}

            try {
                formLead.reset();
                if (elMpid) elMpid.value = '';
                if (elMurl) elMurl.value = '';
                if (elCnpjStatus) elCnpjStatus.textContent = '';
            } catch (e) {}

            if (statusEl) statusEl.textContent = 'Adicionado.';
            
            // Limpa cache do drawer e fecha
            try {
                clearMapsCache();
            } catch (e) {}
            closeDrawer();
            
            // Recarrega apenas a lista de prospecção
            window.location.reload();
        } catch (err) {
            e.preventDefault();
            mapsLog('form:submit:error', { error: String(err && err.message ? err.message : err) });
            alert(err && err.message ? err.message : 'Erro ao adicionar');
        }
    });
}

// Expõe loadResults globalmente para maps-drawer (evitar dependência circular)
window.__loadMapsResults = loadResults;
window.__renderMapsResults = renderResults;
