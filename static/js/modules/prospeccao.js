/**
 * Módulo principal de Prospecção
 * Inicializa todos os componentes e listeners
 */

import { segmentoSelector, cidadeAutocomplete, loadCidadesArray } from './autocomplete.js';
import { ProspeccaoState } from './state.js';
import { installDrawerDelegation, installBeforeUnloadHandler, openDrawer, closeDrawer } from './maps-drawer.js';
import { restoreMapFilters, installPageshowListener } from './filters.js';
import { searchMap, buscarCNPJNoGoogle, updateBtnBuscarCnpjGoogle } from './maps-search.js';
import { consultarCNPJ } from './cnpj.js';
import { initFormListeners, pedirDataRetorno, submitLeadFormAsJsonIfFromMaps } from './form.js';
import { readMapsCache, writeMapsCache, clearMapsCache } from './maps-cache.js';
import { renderResults, loadResults, initDrawerButtonListeners, initFormSubmitListener } from './maps-results.js';

// Expõe componentes Alpine globalmente
window.segmentoSelector = segmentoSelector;
window.cidadeAutocomplete = cidadeAutocomplete;
window.loadCidadesArray = loadCidadesArray;

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
 * Instala audit de localStorage para debug
 */
function installLocalStorageAudit() {
    try {
        if (!window.__MAPS_LS_AUDIT_INSTALLED) {
            window.__MAPS_LS_AUDIT_INSTALLED = true;
            const _setItem = localStorage.setItem.bind(localStorage);
            const _removeItem = localStorage.removeItem.bind(localStorage);
            const _clear = localStorage.clear.bind(localStorage);

            const shouldLogKey = (k) => {
                const key = String(k || '');
                return key === 'prospeccao_state_v1' || key === 'mapsResultsCache' || key === 'mapsLastPayloadCache' || key === 'mapsSearchPending' || key === 'mapsSearchPendingPayload' || key.startsWith('prospeccao_');
            };

            localStorage.setItem = function(k, v) {
                try {
                    if (window.MAPS_DEBUG && shouldLogKey(k)) {
                        const valStr = typeof v === 'string' ? v : String(v);
                        console.log('[MAPS_DEBUG] localStorage:setItem', {
                            key: String(k),
                            bytes: valStr.length,
                        });
                    }
                } catch (e) {}
                return _setItem(k, v);
            };

            localStorage.removeItem = function(k) {
                try {
                    if (window.MAPS_DEBUG && shouldLogKey(k)) {
                        console.log('[MAPS_DEBUG] localStorage:removeItem', { key: String(k) });
                    }
                } catch (e) {}
                return _removeItem(k);
            };

            localStorage.clear = function() {
                try {
                    if (window.MAPS_DEBUG) {
                        console.log('[MAPS_DEBUG] localStorage:clear', {});
                    }
                } catch (e) {}
                return _clear();
            };
        }
    } catch (e) {}
}

/**
 * Instala handlers globais de erro
 */
function installGlobalErrorHandlers() {
    try {
        if (!window.__MAPS_GLOBAL_ERR_INSTALLED) {
            window.__MAPS_GLOBAL_ERR_INSTALLED = true;
            window.addEventListener('error', (ev) => {
                try {
                    if (!window.MAPS_DEBUG) return;
                    console.log('[MAPS_DEBUG] window:error', {
                        message: ev?.message ? String(ev.message) : null,
                        filename: ev?.filename ? String(ev.filename) : null,
                        lineno: ev?.lineno || null,
                        colno: ev?.colno || null,
                    });
                } catch (e) {}
            });
            window.addEventListener('unhandledrejection', (ev) => {
                try {
                    if (!window.MAPS_DEBUG) return;
                    console.log('[MAPS_DEBUG] window:unhandledrejection', {
                        reason: ev?.reason ? String(ev.reason?.message || ev.reason) : null,
                    });
                } catch (e) {}
            });
        }
    } catch (e) {}
}

/**
 * Restaura drawer de sessionStorage
 */
function restorePendingDrawer() {
    let pendingRestore = null;
    try {
        const raw = sessionStorage.getItem('mapsDrawerRestore') || '';
        if (raw) {
            pendingRestore = JSON.parse(raw);
            sessionStorage.removeItem('mapsDrawerRestore');
        }
    } catch (e) {
        pendingRestore = null;
        try { sessionStorage.removeItem('mapsDrawerRestore'); } catch (err) {}
    }

    if (pendingRestore) {
        try {
            const restore = pendingRestore;
            
            readMapsCache();
            let items = window.__mapsResultsCache;
            let payload = window.__mapsLastPayloadCache;

            if (!items || items.length === 0) {
                if (restore?.items && Array.isArray(restore.items)) {
                    items = restore.items;
                }
            }

            if (!payload && restore?.payload) {
                payload = restore.payload;
            }

            if (restore?.remove_key) {
                const k = String(restore.remove_key).trim();
                if (k && Array.isArray(items)) {
                    items = items.filter((it) => String(it.maps_place_id || it.id || '').trim() !== k);
                }
            }

            window.__mapsResultsCache = items;
            window.__mapsLastPayloadCache = payload;
            writeMapsCache(items, payload);

            const statusEl = document.getElementById('mapsDrawerStatus');
            if (statusEl) statusEl.textContent = 'Clique em Buscar para nova pesquisa';
            renderResults(items);
        } catch (e) {
            console.error("Erro na restauração:", e);
        }
    }
}

/**
 * Inicializa módulos na carga da página
 */
function init() {
    // Debug mode
    try {
        window.MAPS_DEBUG = window.MAPS_DEBUG ?? true;
    } catch (e) {}

    // Instalar audit de localStorage
    installLocalStorageAudit();

    // Instalar handlers globais de erro
    installGlobalErrorHandlers();

    // Instalar delegação do drawer
    installDrawerDelegation();

    // Instalar listener para fechar drawer ao navegar
    installBeforeUnloadHandler();

    // Instalar listener de pageshow para bfcache
    installPageshowListener();

    // Restaurar filtros
    restoreMapFilters();

    // Inicializar listeners do formulário
    initFormListeners();

    // Inicializar listeners de botões do drawer
    initDrawerButtonListeners();

    // Inicializar listener de submit do formulário
    initFormSubmitListener();

    // Restaurar drawer pendente
    restorePendingDrawer();

    // Ler cache inicial
    readMapsCache();

    // Listener para mudança de estado (limpar cidade)
    const mapEstado = document.getElementById('mapEstado');
    if (mapEstado) {
        mapEstado.addEventListener('change', function(e) {
            const cidadeInput = document.getElementById('mapCidade');
            if (cidadeInput) cidadeInput.value = '';
        });
    }

    mapsLog('init:complete', {});
}

// Inicializa quando DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Exporta funções para uso externo
export {
    segmentoSelector,
    cidadeAutocomplete,
    loadCidadesArray,
    ProspeccaoState,
    installDrawerDelegation,
    installBeforeUnloadHandler,
    openDrawer,
    closeDrawer,
    restoreMapFilters,
    searchMap,
    buscarCNPJNoGoogle,
    updateBtnBuscarCnpjGoogle,
    consultarCNPJ,
    pedirDataRetorno,
    submitLeadFormAsJsonIfFromMaps,
    readMapsCache,
    writeMapsCache,
    clearMapsCache,
    renderResults,
    loadResults
};
