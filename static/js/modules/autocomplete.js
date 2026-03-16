/**
 * Módulo de autocomplete de cidades via API IBGE
 * Componente Alpine.js para seleção de cidade com busca
 */

export const SEGMENTOS = [
    'Informática', 'Celulares', 'Áudio e Vídeo', 'Eletroportáteis', 'Gamer',
    'Brinquedos', 'Drones e Câmeras', 'Ortopédica',
    'Fitness', 'Pet', 'Redes', 'Mobilidade Elétrica'
];

/**
 * Componente Alpine.js para seleção de segmentos
 */
export function segmentoSelector() {
    return {
        open: false,
        segmentos: SEGMENTOS,
        selecionados: [],
        toggle(seg) {
            if (this.selecionados.includes(seg)) {
                this.selecionados = this.selecionados.filter(s => s !== seg);
            } else {
                this.selecionados.push(seg);
            }
        }
    };
}

/**
 * Carrega lista de cidades do IBGE
 * @param {string} uf - Sigla do estado
 * @returns {Promise<string[]>} Lista de cidades ordenadas
 */
export async function loadCidadesArray(uf) {
    if (!uf) return [];
    try {
        const response = await fetch(
            `https://servicodados.ibge.gov.br/api/v1/localidades/estados/${uf}/municipios`
        );
        const cidades = await response.json();
        return cidades.map(c => c.nome).sort();
    } catch (e) {
        console.error("Erro ao carregar cidades", e);
        return [];
    }
}

/**
 * Componente Alpine.js para autocomplete de cidades
 */
export function cidadeAutocomplete() {
    return {
        open: false,
        search: '',
        cidades: [],
        highlightedIndex: -1,
        loading: false,
        get filteredCidades() {
            if (!this.search) return this.cidades;
            const term = this.search.toLowerCase();
            return this.cidades.filter(c => c.toLowerCase().includes(term));
        },
        async ensureLoaded() {
            // Sempre carrega ao focar
            const uf = (document.getElementById('mapEstado')?.value || 'SP').toUpperCase();
            if (!uf) return;
            
            this.loading = true;
            try {
                this.cidades = await loadCidadesArray(uf);
                // Reabrir dropdown após carregar se ainda está focado
                const input = document.getElementById('mapCidade');
                if (input && document.activeElement === input) {
                    this.open = true;
                }
            } catch (e) {
                console.error('Erro ao carregar cidades:', e);
            }
            this.loading = false;
        },
        select(cidade) {
            this.search = cidade;
            this.open = false;
            this.highlightedIndex = -1;
        },
        moveDown() {
            if (this.filteredCidades.length === 0) return;
            this.highlightedIndex = (this.highlightedIndex + 1) % this.filteredCidades.length;
        },
        moveUp() {
            if (this.filteredCidades.length === 0) return;
            this.highlightedIndex = this.highlightedIndex <= 0 
                ? this.filteredCidades.length - 1 
                : this.highlightedIndex - 1;
        },
        selectHighlighted() {
            if (this.highlightedIndex >= 0 && this.highlightedIndex < this.filteredCidades.length) {
                this.select(this.filteredCidades[this.highlightedIndex]);
            }
        }
    };
}
