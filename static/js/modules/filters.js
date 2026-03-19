/**
 * Módulo de restauração de filtros do Maps
 * Gerencia persistência e restauração após navegação bfcache
 */

import { ProspeccaoState } from './state.js';
import { installDrawerDelegation } from './maps-drawer.js';

/**
 * Restaura filtros do mapa após navegação ou reload
 */
export function restoreMapFilters() {
    try {
        const { cidade, estado, segmentos, query } = ProspeccaoState.loadMapFilters();

        // Aplicar aos campos de texto
        const mapCidade = document.getElementById('mapCidade');
        const mapEstado = document.getElementById('mapEstado');

        if (mapCidade) mapCidade.value = cidade;
        if (mapEstado) mapEstado.value = estado;

        // Restaurar segmentos no Alpine com retry
        const segWrapper = document.getElementById('segmentoSelector');

        if (segWrapper && Array.isArray(segmentos) && segmentos.length > 0) {
            const maxAttempts = 30;
            const attemptInterval = 100;

            const tryRestore = (attempt) => {
                try {
                    const alpineData = Alpine.$data(segWrapper);
                    if (alpineData) {
                        const currentSelected = alpineData.selecionados || [];
                        const needsRestore = currentSelected.length === 0 ||
                            JSON.stringify(currentSelected.sort()) !== JSON.stringify(segmentos.sort());

                        if (needsRestore) {
                            alpineData.selecionados = segmentos;
                        }

                        if (attempt < maxAttempts) {
                            setTimeout(() => tryRestore(attempt + 1), attemptInterval);
                        }
                    } else if (attempt < maxAttempts) {
                        setTimeout(() => tryRestore(attempt + 1), attemptInterval);
                    }
                } catch (e) {
                    if (attempt < maxAttempts) {
                        setTimeout(() => tryRestore(attempt + 1), attemptInterval);
                    }
                }
            };
            tryRestore(0);
        }

        // Restaurar query do mapa
        let effectiveQuery = query;
        try {
            const rawQ = localStorage.getItem('mapsPrimaryQuery') || '';
            const rawP = localStorage.getItem('mapsPrimaryPayload') || '';
            if (rawQ && rawP) {
                const payload = JSON.parse(rawP);
                const sameCidade = String(payload?.cidade || '').trim() === String(cidade || '').trim();
                const sameEstado = String(payload?.estado || '').trim() === String(estado || '').trim();
                const segKey = (arr) => (Array.isArray(arr) ? arr.map((s) => String(s || '').trim().toLowerCase()).filter(Boolean).sort().join('|') : '');
                const sameSegs = segKey(payload?.segmentos) === segKey(segmentos);
                if (sameCidade && sameEstado && sameSegs) {
                    effectiveQuery = String(rawQ || '').trim();
                }
            }
        } catch (e) {}

        if (effectiveQuery && cidade) {
            window.lastQuery = effectiveQuery;
            const mapFrame = document.getElementById('mapFrame');
            const openGoogleMaps = document.getElementById('openGoogleMaps');
            if (mapFrame) {
                mapFrame.src = `https://www.google.com/maps?q=${encodeURIComponent(effectiveQuery)}&output=embed`;
            }
            if (openGoogleMaps) {
                openGoogleMaps.href = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(effectiveQuery)}`;
            }
        }
    } catch (e) {
        if (window.MAPS_DEBUG) {
            console.log('[MAPS_DEBUG] filters:restore_error', { error: String(e.message || e) });
        }
    }
}

/**
 * Instala listener de pageshow para bfcache
 * Re-instala delegação do drawer e restaura filtros
 */
export function installPageshowListener() {
    if (window.__MAPS_PAGESHOW_INSTALLED) return;
    window.__MAPS_PAGESHOW_INSTALLED = true;

    window.addEventListener('pageshow', (ev) => {
        // Re-instalar delegação do drawer (crítico para bfcache)
        installDrawerDelegation();
        // Restaurar filtros
        restoreMapFilters();
    });
}

// Expõe globalmente para compatibilidade
window.__restoreMapFilters = restoreMapFilters;
