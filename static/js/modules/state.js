/**
 * Módulo de estado e persistência para Prospecção
 * Gerencia localStorage e estado do mapa
 */

const STATE_KEY = 'prospeccao_state_v1';

// Chaves legadas para fallback
const LEGACY_KEYS = {
    cidade: 'prospeccao_mapCidade',
    estado: 'prospeccao_mapEstado',
    segmentos: 'prospeccao_mapSegmentos',
    query: 'prospeccao_lastQuery'
};

/**
 * Objeto global de estado da prospecção
 */
export const ProspeccaoState = {
    KEY: STATE_KEY,

    /**
     * Carrega estado do localStorage
     * @returns {object} Estado salvo ou objeto vazio
     */
    load() {
        try {
            const raw = localStorage.getItem(this.KEY);
            if (raw) return JSON.parse(raw);
        } catch (e) {}
        return {};
    },

    /**
     * Salva estado no localStorage
     * @param {object} data - Dados a salvar
     */
    save(data) {
        try {
            localStorage.setItem(this.KEY, JSON.stringify(data));
        } catch (e) {}
    },

    /**
     * Salva filtros do mapa
     * @param {object} filters - { cidade, estado, segmentos, query }
     */
    saveMapFilters({ cidade, estado, segmentos, query }) {
        const state = this.load();
        state.mapCidade = cidade || '';
        state.mapEstado = estado || '';
        state.mapSegmentos = Array.isArray(segmentos) ? segmentos : [];
        state.mapQuery = query || '';
        this.save(state);

        // Fallback legado
        try {
            localStorage.setItem(LEGACY_KEYS.cidade, cidade || '');
            localStorage.setItem(LEGACY_KEYS.estado, estado || '');
            localStorage.setItem(LEGACY_KEYS.segmentos, JSON.stringify(segmentos || []));
            localStorage.setItem(LEGACY_KEYS.query, query || '');
        } catch (e) {}
    },

    /**
     * Carrega filtros do mapa
     * @returns {object} { cidade, estado, segmentos, query }
     */
    loadMapFilters() {
        const state = this.load();
        let cidade = state.mapCidade || '';
        let estado = state.mapEstado || '';
        let segmentos = Array.isArray(state.mapSegmentos) ? state.mapSegmentos : [];
        let query = state.mapQuery || '';

        // Fallback legado
        if (!cidade && !estado && !query) {
            try {
                cidade = localStorage.getItem(LEGACY_KEYS.cidade) || '';
                estado = localStorage.getItem(LEGACY_KEYS.estado) || '';
                const segRaw = localStorage.getItem(LEGACY_KEYS.segmentos) || '[]';
                query = localStorage.getItem(LEGACY_KEYS.query) || '';
                try { segmentos = JSON.parse(segRaw); } catch (e) { segmentos = []; }
                if (!Array.isArray(segmentos)) segmentos = [];
            } catch (e) {}
        }

        return { cidade, estado, segmentos, query };
    },

    /**
     * Marca busca como pendente
     */
    markSearchPending() {
        try {
            localStorage.setItem('mapsSearchPending', '1');
        } catch (e) {}
    },

    /**
     * Limpa flag de busca pendente
     */
    clearSearchPending() {
        try {
            localStorage.removeItem('mapsSearchPending');
        } catch (e) {}
    },

    /**
     * Verifica se há busca pendente
     * @returns {boolean}
     */
    isSearchPending() {
        try {
            return localStorage.getItem('mapsSearchPending') === '1';
        } catch (e) {
            return false;
        }
    }
};

// Expõe globalmente para compatibilidade
window.ProspeccaoState = ProspeccaoState;
