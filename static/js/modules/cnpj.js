/**
 * Módulo de consulta de CNPJ
 * Integração com API backend
 */

/**
 * Consulta CNPJ via API backend
 */
export async function consultarCNPJ() {
    const el = document.getElementById('f_cnpj');
    const status = document.getElementById('cnpjStatus');
    const cnpj = (el?.value || '').trim();

    if (!cnpj) {
        status.textContent = 'Informe o CNPJ';
        status.className = 'text-xs text-red-700';
        return;
    }

    status.textContent = 'Consultando...';
    status.className = 'text-xs text-gray-500';

    try {
        const resp = await fetch(`/api/cnpj/consultar?cnpj=${encodeURIComponent(cnpj)}`);
        const data = await resp.json();

        if (!resp.ok || !data.ok) {
            status.textContent = data.message || 'CNPJ inválido';
            status.className = 'text-xs text-red-700';
            return;
        }

        if (data.ativo === false) {
            const situ = (data.situacao || '').trim();
            status.textContent = situ ? `CNPJ NÃO ATIVO (${situ})` : 'CNPJ NÃO ATIVO';
            status.className = 'text-xs text-red-700';
            el.value = data.cnpj;
            return;
        }

        const razao = data.data?.razao_social || data.data?.nome_fantasia;
        const aberturaRaw = data.data?.data_inicio_atividade || data.data?.data_abertura;
        let msg = razao ? `OK: ${razao}` : 'OK';
        let cls = 'text-xs text-green-700';

        if (aberturaRaw) {
            const d = new Date(String(aberturaRaw).substring(0, 10) + 'T00:00:00');
            if (!isNaN(d.getTime())) {
                const now = new Date();
                const diffDays = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
                const aberturaFmt = String(aberturaRaw).substring(0, 10).split('-').reverse().join('/');
                msg += ` | Abertura: ${aberturaFmt}`;
                if (diffDays >= 0 && diffDays < 365) {
                    msg += ' | ATENÇÃO: empresa < 1 ano (pagamento à vista)';
                    cls = 'text-xs text-yellow-800';
                }
            }
        }

        status.textContent = msg;
        status.className = cls;
        el.value = data.cnpj;
    } catch (e) {
        status.textContent = 'Erro ao consultar';
        status.className = 'text-xs text-red-700';
    }
}

// Expõe globalmente para compatibilidade
window.consultarCNPJ = consultarCNPJ;
