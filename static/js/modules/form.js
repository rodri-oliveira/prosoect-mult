/**
 * Módulo de formulário de Prospecção
 * Gerencia submit, modal de retorno e integração com Maps
 */

import { buscarCNPJNoGoogle, updateBtnBuscarCnpjGoogle } from './maps-search.js';

/**
 * Abre modal para definir data de retorno
 * @param {HTMLFormElement} form - Formulário de prospecção
 * @returns {boolean} False para prevenir submit, true para continuar
 */
export function pedirDataRetorno(form) {
    const modal = document.getElementById('modalRetorno');
    const inputData = document.getElementById('retornoData');
    const inputHora = document.getElementById('retornoHora');
    const btnCancelar = document.getElementById('retornoCancelar');
    const btnSalvar = document.getElementById('retornoSalvar');
    if (!modal || !inputData || !inputHora || !btnCancelar || !btnSalvar) return true;

    const agora = new Date();
    const yyyy = agora.getFullYear();
    const mm = String(agora.getMonth() + 1).padStart(2, '0');
    const dd = String(agora.getDate()).padStart(2, '0');
    const hh = String(agora.getHours()).padStart(2, '0');
    const mi = String(agora.getMinutes()).padStart(2, '0');
    if (!inputData.value) inputData.value = `${yyyy}-${mm}-${dd}`;
    if (!inputHora.value) inputHora.value = `${hh}:${mi}`;

    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');

    const close = () => {
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
    };

    const cleanup = () => {
        btnCancelar.removeEventListener('click', onCancel);
        btnSalvar.removeEventListener('click', onSave);
        document.removeEventListener('keydown', onKeyDown);
    };

    const onCancel = () => {
        cleanup();
        close();
    };

    const onSave = () => {
        const data = (inputData.value || '').trim();
        const hora = (inputHora.value || '').trim();
        const obs = (document.getElementById('retornoObs')?.value || '').trim();
        
        if (!data || !hora) return;
        
        const d = form.querySelector('.data-retorno-input');
        const h = form.querySelector('.hora-retorno-input');
        const o = form.querySelector('.observacao-retorno-input');
        
        if (d) d.value = data;
        if (h) h.value = hora;
        if (o) o.value = obs;
        
        cleanup();
        close();
        form.submit();
    };

    const onKeyDown = (e) => {
        if (e.key === 'Escape') onCancel();
    };

    btnCancelar.addEventListener('click', onCancel);
    btnSalvar.addEventListener('click', onSave);
    document.addEventListener('keydown', onKeyDown);
    setTimeout(() => inputData.focus(), 0);
    return false;
}

/**
 * Submete formulário como JSON quando vem do Maps
 * @returns {Promise<{handled: boolean, data?: object}>}
 */
export async function submitLeadFormAsJsonIfFromMaps() {
    const form = document.getElementById('formLead');
    if (!form) return { handled: false };

    const mapsPlaceId = (document.getElementById('f_maps_place_id')?.value || '').trim();
    const mapsUrl = (document.getElementById('f_maps_url')?.value || '').trim();
    if (!mapsPlaceId && !mapsUrl) return { handled: false };

    const fd = new FormData(form);
    const payload = {};
    for (const [k, v] of fd.entries()) {
        if (k === 'segmento') {
            if (!payload.segmento) payload.segmento = [];
            payload.segmento.push(String(v || '').trim());
        } else {
            payload[k] = typeof v === 'string' ? v.trim() : v;
        }
    }

    const resp = await fetch('/api/prospeccao/rascunho/novo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const data = await resp.json().catch(() => null);
    if (!resp.ok || !data || !data.ok) {
        throw new Error((data && data.message) ? data.message : 'Erro ao adicionar');
    }
    return { handled: true, data };
}

/**
 * Inicializa listeners do formulário
 */
function statusNeedsReturnFields(value) {
    const v = String(value || '').trim().toLowerCase();
    return v === 'pediu para retornar'
        || v === 'agendamento'
        || v === 'agendar retorno'
        || v === 'em negociação'
        || v === 'não analisou ainda o material';
}

function syncReturnFieldsVisibility(statusSelect) {
    if (!statusSelect) return;

    const needsDate = statusNeedsReturnFields(statusSelect.value);
    const campoData = document.getElementById('campo-data-retorno');
    const campoHora = document.getElementById('campo-hora-retorno');

    if (needsDate) {
        if (campoData) campoData.classList.remove('hidden');
        if (campoHora) campoHora.classList.remove('hidden');
    } else {
        if (campoData) campoData.classList.add('hidden');
        if (campoHora) campoHora.classList.add('hidden');
        const d = document.querySelector('input[name="data_retorno"]');
        if (d) d.value = '';
        const h = document.querySelector('input[name="hora_retorno"]');
        if (h) h.value = '';
    }
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

function installPhoneFormatting(id) {
    const el = document.getElementById(id);
    if (!el) return;

    const apply = () => {
        const formatted = formatPhoneBR(el.value);
        if (formatted && formatted !== el.value) el.value = formatted;
    };

    el.addEventListener('blur', apply);
    el.addEventListener('change', apply);
}

export function initFormListeners() {
    // Atualizar botão de buscar CNPJ no Google e limpar vinculo com Maps se editar manualmente
    ['f_nome', 'f_cidade', 'f_estado', 'f_endereco'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', (e) => {
                updateBtnBuscarCnpjGoogle();
                
                // Se o usuário editar manualmente os dados vitais da loja (nome, cidade),
                // devemos remover o vínculo com o Google Maps do item anterior para evitar colisão.
                // Mas permitimos pequenas correções apenas no nome sem apagar?
                // O mais seguro é: se ele digitar (isTrusted), limpar as chaves do maps.
                if (e.isTrusted && (id === 'f_nome' || id === 'f_cidade')) {
                    const mpid = document.getElementById('f_maps_place_id');
                    const murl = document.getElementById('f_maps_url');
                    if (mpid && mpid.value) mpid.value = '';
                    if (murl && murl.value) murl.value = '';
                }
            });
        }
    });
    updateBtnBuscarCnpjGoogle();
    installPhoneFormatting('f_telefone');
    installPhoneFormatting('f_whatsapp');

    // Status select - mostrar/esconder campo de data de retorno
    const statusSelect = document.querySelector('select[name="status_prospeccao"]');
    if (statusSelect) {
        statusSelect.addEventListener('change', function() {
            syncReturnFieldsVisibility(this);
        });
        syncReturnFieldsVisibility(statusSelect);
    }
}

// Expõe globalmente para compatibilidade
window.pedirDataRetorno = pedirDataRetorno;
window.submitLeadFormAsJsonIfFromMaps = submitLeadFormAsJsonIfFromMaps;
