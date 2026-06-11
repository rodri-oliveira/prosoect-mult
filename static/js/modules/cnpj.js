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
            const msg = data.message || '';
            if (resp.status === 502 || msg.includes('indisponíveis') || msg.includes('Falha')) {
                status.textContent = 'Serviço de consulta temporariamente indisponível. Tente novamente em alguns segundos.';
            } else if (msg.includes('inválido')) {
                status.textContent = 'CNPJ inválido. Verifique o número digitado.';
            } else if (msg.includes('não encontrado')) {
                status.textContent = 'CNPJ não encontrado na base de dados.';
            } else {
                status.textContent = msg || 'Erro ao consultar CNPJ';
            }
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
        const aberturaRaw = data.data?.data_abertura || data.data?.data_inicio_atividade;
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
                    const meses = Math.floor(diffDays / 30);
                    msg += ` | ATENÇÃO: CNPJ com ${meses} meses (Multilaser exige 12+ meses para faturado)`;
                    cls = 'text-xs text-red-700 font-bold';
                } else {
                    const anos = Math.floor(diffDays / 365);
                    const meses = Math.floor((diffDays % 365) / 30);
                    if (anos >= 1) {
                        msg += ` | OK: ${anos} ano${anos > 1 ? 's' : ''} e ${meses} meses (aprovado para faturado)`;
                    }
                }
            }
        }

        status.textContent = msg;
        status.className = cls;
        el.value = data.cnpj;
    } catch (e) {
        status.textContent = 'Erro de conexão. Verifique sua internet e tente novamente.';
        status.className = 'text-xs text-red-700';
    }
}

/**
 * Consulta o CNPJ digitado e preenche o formulario com os dados oficiais.
 */
export async function preencherDadosCNPJ() {
    const el = document.getElementById('f_cnpj');
    const status = document.getElementById('cnpjStatus');
    const cnpj = (el?.value || '').trim();

    if (!cnpj) {
        status.textContent = 'Informe o CNPJ';
        status.className = 'text-xs text-red-700';
        return;
    }

    status.textContent = 'Buscando dados...';
    status.className = 'text-xs text-gray-500';

    try {
        const resp = await fetch(`/api/cnpj/consultar?cnpj=${encodeURIComponent(cnpj)}`);
        const data = await resp.json();

        if (!resp.ok || !data.ok) {
            status.textContent = data.message || 'Erro ao buscar dados do CNPJ';
            status.className = 'text-xs text-red-700';
            return;
        }

        const d = data.data || {};
        setValue('f_cnpj', data.cnpj);
        setValue('f_nome', d.nome_fantasia || d.razao_social || '');
        setValue('f_endereco', buildEnderecoComCep(d.endereco, d.cep));
        setValue('f_cidade', d.cidade || '');
        setValue('f_estado', d.estado || '');
        setValue('f_telefone', formatPhoneBR(d.telefone || ''));
        setValue('f_whatsapp', formatPhoneBR(d.telefone || ''));
        setValue('f_email', d.email || '');

        const razao = d.razao_social || d.nome_fantasia || 'CNPJ encontrado';
        status.textContent = data.ativo === false
            ? `Dados preenchidos | CNPJ NAO ATIVO (${data.situacao || 'situacao desconhecida'})`
            : `Dados preenchidos: ${razao}`;
        status.className = data.ativo === false
            ? 'text-xs text-red-700 font-bold'
            : 'text-xs text-green-700';
    } catch (e) {
        status.textContent = 'Erro de conexao. Verifique sua internet e tente novamente.';
        status.className = 'text-xs text-red-700';
    }
}

function setValue(id, value) {
    const el = document.getElementById(id);
    if (!el || value == null || String(value).trim() === '') return;
    el.value = String(value).trim();
    el.dispatchEvent(new Event('input', { bubbles: true }));
}

function formatPhoneBR(value) {
    const raw = String(value || '').trim();
    if (!raw) return '';

    let digits = raw.replace(/\D/g, '');
    if (!digits) return raw;

    if (digits.startsWith('55') && (digits.length === 12 || digits.length === 13)) {
        digits = digits.substring(2);
    }

    if (digits.length === 8) return `${digits.substring(0, 4)}-${digits.substring(4)}`;
    if (digits.length === 9) return `${digits.substring(0, 5)}-${digits.substring(5)}`;
    if (digits.length === 10) return `(${digits.substring(0, 2)}) ${digits.substring(2, 6)}-${digits.substring(6)}`;
    if (digits.length === 11) return `(${digits.substring(0, 2)}) ${digits.substring(2, 7)}-${digits.substring(7)}`;

    return raw;
}

function buildEnderecoComCep(endereco, cep) {
    const end = String(endereco || '').trim();
    const cepClean = String(cep || '').trim();
    if (!end) return '';
    if (!cepClean || end.includes(cepClean)) return end;
    return `${end}, ${cepClean}`;
}

// Expõe globalmente para compatibilidade
window.consultarCNPJ = consultarCNPJ;
window.preencherDadosCNPJ = preencherDadosCNPJ;
