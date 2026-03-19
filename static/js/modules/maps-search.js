/**
 * Módulo de busca do Google Maps
 * Gerencia integração com Google Maps embed
 */

import { ProspeccaoState } from './state.js';

/**
 * Realiza busca no Google Maps
 * Agora sincronizado com o backend via /api/maps/queries
 */
export async function searchMap() {
    const cidade = (document.getElementById('mapCidade')?.value || '').trim();
    const estado = (document.getElementById('mapEstado')?.value || '').trim();
    const segWrapper = document.getElementById('segmentoSelector');

    let segmentos = [];
    try {
        const alpineData = Alpine.$data(segWrapper);
        segmentos = alpineData?.selecionados || [];
    } catch (e) {}

    if (!cidade && !estado) {
        alert('Informe cidade ou estado para buscar.');
        return;
    }

    let effectiveQuery = '';
    
    // Se temos segmentos, buscar queries do backend (sincronizado)
    if (segmentos.length > 0) {
        try {
            const params = new URLSearchParams();
            if (cidade) params.set('cidade', cidade);
            if (estado) params.set('estado', estado);
            segmentos.forEach((s) => params.append('segmentos', s));
            
            const resp = await fetch(`/api/maps/queries?${params.toString()}`);
            const data = await resp.json();
            
            if (data.ok && data.primary_query) {
                effectiveQuery = data.primary_query;
                
                // Salvar queries geradas para o drawer usar depois
                window.__generatedQueries = data.queries || [];
                window.__generatedQueriesTimestamp = Date.now();
                
                // Salvar no localStorage para persistência
                try {
                    localStorage.setItem('mapsGeneratedQueries', JSON.stringify({
                        queries: data.queries,
                        primary_query: data.primary_query,
                        cidade,
                        estado,
                        segmentos,
                        timestamp: Date.now(),
                    }));
                } catch (e) {}
            }
        } catch (e) {
            console.error('Erro ao buscar queries:', e);
            // Fallback: query simples
            effectiveQuery = `${segmentos.join(' ')} ${cidade} ${estado}`.trim();
        }
    } else {
        // Sem segmentos: query genérica
        const parts = ['atacadista', 'distribuidor', 'loja'];
        if (cidade) parts.push(cidade);
        if (estado) parts.push(estado);
        effectiveQuery = parts.join(' ');
    }

    window.lastQuery = effectiveQuery;
    
    // Disponibilizar globalmente para o botão "Abrir no Google Maps"
    window.__mapsPrimaryQuery = effectiveQuery;

    // Salvar filtros
    ProspeccaoState.saveMapFilters({
        cidade,
        estado,
        segmentos,
        query: effectiveQuery
    });

    // Atualizar iframe
    const mapFrame = document.getElementById('mapFrame');
    const openGoogleMaps = document.getElementById('openGoogleMaps');

    if (mapFrame) {
        mapFrame.src = `https://www.google.com/maps?q=${encodeURIComponent(effectiveQuery)}&output=embed`;
    }
    if (openGoogleMaps) {
        openGoogleMaps.href = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(effectiveQuery)}`;
    }
}

/**
 * Retorna queries geradas pelo backend (se disponíveis)
 */
export function getGeneratedQueries() {
    try {
        const raw = localStorage.getItem('mapsGeneratedQueries');
        if (!raw) return null;
        const data = JSON.parse(raw);
        // Cache válido por 5 minutos
        if (Date.now() - (data.timestamp || 0) < 5 * 60 * 1000) {
            return data;
        }
    } catch (e) {}
    return null;
}

/**
 * Busca CNPJ no Google
 */
export function buscarCNPJNoGoogle() {
    const nome = (document.getElementById('f_nome')?.value || '').trim();
    const cidade = (document.getElementById('f_cidade')?.value || '').trim();
    const uf = (document.getElementById('f_estado')?.value || '').trim();
    const endereco = (document.getElementById('f_endereco')?.value || '').trim();

    if (!nome || (!cidade && !uf)) return;

    const parts = ['CNPJ', nome];
    if (endereco) parts.push(endereco);
    if (cidade) parts.push(cidade);
    if (uf) parts.push(uf);

    const query = parts.join(' ');
    const url = `https://www.google.com/search?hl=pt-BR&nfpr=1&q=${encodeURIComponent(query)}`;
    // Usar globalThis.open para evitar conflito com sandbox/extensões
    const opener = typeof globalThis !== 'undefined' ? globalThis.open : window.open;
    if (typeof opener === 'function') {
        opener(url, '_blank', 'noopener,noreferrer');
    } else {
        // Fallback: criar link e clicar
        const a = document.createElement('a');
        a.href = url;
        a.target = '_blank';
        a.rel = 'noopener,noreferrer';
        a.click();
    }
}

/**
 * Atualiza estado do botão de buscar CNPJ
 */
export function updateBtnBuscarCnpjGoogle() {
    const btn = document.getElementById('btnBuscarCnpjGoogle');
    if (!btn) return;

    const nome = (document.getElementById('f_nome')?.value || '').trim();
    const cidade = (document.getElementById('f_cidade')?.value || '').trim();
    const uf = (document.getElementById('f_estado')?.value || '').trim();

    const ok = !!nome && (!!cidade || !!uf);
    btn.disabled = !ok;
    btn.className = ok
        ? 'px-3 py-1.5 rounded-md bg-white text-gray-800 text-xs font-medium border border-gray-300 hover:bg-gray-50'
        : 'px-3 py-1.5 rounded-md bg-gray-100 text-gray-500 text-xs font-medium disabled:opacity-60 disabled:cursor-not-allowed hover:bg-gray-200';
}

// Expõe globalmente para compatibilidade
window.searchMap = searchMap;
window.buscarCNPJNoGoogle = buscarCNPJNoGoogle;
window.updateBtnBuscarCnpjGoogle = updateBtnBuscarCnpjGoogle;
