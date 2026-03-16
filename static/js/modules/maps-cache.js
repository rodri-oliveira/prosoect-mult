/**
 * Módulo de cache do Maps
 * Gerencia persistência de resultados e payload no localStorage
 */

import { ProspeccaoState } from './state.js';

let lastMapsItems = [];

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
 * Atualiza status do cache na UI
 */
const updateMapsCacheStatus = (prefix) => {
    try {
        let n = 0;
        try {
            const parsed = (window.ProspeccaoState && typeof window.ProspeccaoState.getMapItems === 'function')
                ? window.ProspeccaoState.getMapItems()
                : (() => {
                    const rawItems = localStorage.getItem('mapsResultsCache') || '';
                    return rawItems ? JSON.parse(rawItems) : [];
                })();
            n = Array.isArray(parsed) ? parsed.length : 0;
        } catch (e) {
            n = 0;
        }
        const hasPayload = (window.ProspeccaoState && typeof window.ProspeccaoState.getMapPayload === 'function')
            ? !!window.ProspeccaoState.getMapPayload()
            : !!(localStorage.getItem('mapsLastPayloadCache') || '');
        const statusNow = document.getElementById('mapsDrawerStatus');
        if (statusNow) statusNow.textContent = `${prefix || 'Cache'}: ${n} item(s)${hasPayload ? '' : ' (sem payload)'}`;
        mapsLog('cache:status', { prefix: prefix || 'Cache', items: n, hasPayload });
    } catch (e) {
        const statusNow = document.getElementById('mapsDrawerStatus');
        if (statusNow) statusNow.textContent = `${prefix || 'Cache'}: erro ao ler`;
        mapsLog('cache:status_error', { prefix: prefix || 'Cache', error: String(e && e.message ? e.message : e) });
    }
};

/**
 * Escreve cache de resultados
 */
export const writeMapsCache = (items, payload) => {
    mapsLog('cache:write:start', { items: Array.isArray(items) ? items.length : null, hasPayload: !!payload });
    try {
        window.__mapsResultsCache = Array.isArray(items) ? items : [];
        window.__mapsLastPayloadCache = payload || null;
    } catch (e) {}
    try {
        if (window.ProspeccaoState && typeof window.ProspeccaoState.saveMapResults === 'function') {
            window.ProspeccaoState.saveMapResults(Array.isArray(items) ? items : [], payload || null);
        } else {
            localStorage.setItem('mapsResultsCache', JSON.stringify(Array.isArray(items) ? items : []));
            localStorage.setItem('mapsLastPayloadCache', JSON.stringify(payload || null));
        }
    } catch (e) {}
    updateMapsCacheStatus('Cache salvo');
    mapsLog('cache:write:done', { memItems: Array.isArray(window.__mapsResultsCache) ? window.__mapsResultsCache.length : null });
};

/**
 * Limpa cache de resultados
 */
export const clearMapsCache = () => {
    mapsLog('cache:clear', {});
    try {
        window.__mapsResultsCache = [];
        window.__mapsLastPayloadCache = null;
    } catch (e) {}
    try {
        if (window.ProspeccaoState && typeof window.ProspeccaoState.clearMapResults === 'function') {
            window.ProspeccaoState.clearMapResults();
        } else {
            localStorage.removeItem('mapsResultsCache');
            localStorage.removeItem('mapsLastPayloadCache');
        }
    } catch (e) {}
    updateMapsCacheStatus('Cache limpo');
};

/**
 * Lê cache de resultados
 */
export const readMapsCache = () => {
    mapsLog('cache:read:start', {});
    try {
        let items = [];
        let payload = null;
        try {
            if (window.MAPS_DEBUG) {
                const rawState = localStorage.getItem('prospeccao_state_v1');
                console.log('[MAPS_DEBUG] state:raw_snapshot', {
                    exists: rawState !== null,
                    bytes: rawState ? String(rawState).length : 0,
                });
            }
        } catch (e) {}
        if (window.ProspeccaoState && typeof window.ProspeccaoState.getMapItems === 'function') {
            items = window.ProspeccaoState.getMapItems();
            payload = (typeof window.ProspeccaoState.getMapPayload === 'function') ? window.ProspeccaoState.getMapPayload() : null;
        } else {
            const rawItems = localStorage.getItem('mapsResultsCache') || '';
            const rawPayload = localStorage.getItem('mapsLastPayloadCache') || '';
            items = rawItems ? JSON.parse(rawItems) : [];
            payload = rawPayload ? JSON.parse(rawPayload) : null;
        }
        
        window.__mapsResultsCache = Array.isArray(items) ? items : [];
        window.__mapsLastPayloadCache = payload || null;
    } catch (e) {}
    updateMapsCacheStatus('Cache lido');
    mapsLog('cache:read:done', { items: Array.isArray(window.__mapsResultsCache) ? window.__mapsResultsCache.length : null, hasPayload: !!window.__mapsLastPayloadCache });
};

/**
 * Remove item do cache por chave
 */
export const removeItemByKey = (key) => {
    const k = String(key || '').trim();
    if (!k) return;
    lastMapsItems = (lastMapsItems || []).filter((it) => {
        const itKey = String(it.maps_place_id || it.id || '').trim();
        return itKey !== k;
    });
    writeMapsCache(lastMapsItems, buildQueryPayload());
};

/**
 * Constrói payload de query
 */
export const buildQueryPayload = () => {
    const segWrapper = document.getElementById('segmentoSelector');
    const segmentosSelecionados = segWrapper ? (Alpine.$data(segWrapper).selecionados || []) : [];
    const cidade = (document.getElementById('mapCidade')?.value || '').trim();
    const estado = (document.getElementById('mapEstado')?.value || '').trim();
    const query = (window.lastQuery || '').trim();
    return { segmentosSelecionados, cidade, estado, query };
};

/**
 * Getter para lastMapsItems
 */
export const getLastMapsItems = () => lastMapsItems;

/**
 * Setter para lastMapsItems
 */
export const setLastMapsItems = (items) => {
    lastMapsItems = Array.isArray(items) ? items : [];
};

// Expõe globalmente para compatibilidade
window.__clearMapsCache = clearMapsCache;
window.__readMapsCache = readMapsCache;
window.__mapsResultsCache = [];
window.__mapsLastPayloadCache = null;
