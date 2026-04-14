/**
 * Módulo da página de Agendamentos
 */

import { pedirDataRetorno } from './form.js';
import { scrollToHash, initBackToTop, initScrollLinks } from './utils.js';

const historicoCache = new Map();

/**
 * Converte hora HH:MM para minutos
 */
const toMinutes = (hhmm) => {
    if (!hhmm) return null;
    const parts = String(hhmm).split(':');
    if (parts.length < 2) return null;
    const h = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    if (Number.isNaN(h) || Number.isNaN(m)) return null;
    return h * 60 + m;
};

/**
 * Destaca itens por horário
 */
function highlightByTime() {
    const now = new Date();
    const nowMinutes = now.getHours() * 60 + now.getMinutes();

    document.querySelectorAll('[data-hora-retorno]').forEach((el) => {
        const hhmm = el.getAttribute('data-hora-retorno');
        const mins = toMinutes(hhmm);
        if (mins === null) return;
        const diff = mins - nowMinutes;

        const badge = el.querySelector('.js-time-badge');
        const setBadge = (text, cls) => {
            if (!badge) return;
            badge.textContent = text;
            badge.className = `js-time-badge px-2 py-1 rounded-full text-xs font-bold ${cls}`;
        };

        if (diff < 0) {
            el.classList.add('bg-red-50', 'ring-1', 'ring-red-200');
            setBadge(`Atrasado ${Math.abs(diff)} min`, 'bg-red-100 text-red-800');
            return;
        }

        if (diff <= 30) {
            el.classList.add('bg-yellow-50', 'ring-2', 'ring-brand-300');
            setBadge(`Vence em ${diff} min`, 'bg-yellow-100 text-yellow-800');
        }
    });
}

function formatEventoDate(value) {
    if (!value) return '';
    const str = String(value);
    return str.replace('T', ' ').slice(0, 16);
}

function renderHistoricoItens(itens) {
    const wrap = document.getElementById('modalHistoricoWrap');
    const list = document.getElementById('modalHistorico');
    if (!wrap || !list) return;

    list.innerHTML = '';
    wrap.classList.remove('hidden');

    if (!itens || itens.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'text-xs text-gray-500';
        empty.textContent = 'Sem histórico registrado.';
        list.appendChild(empty);
        return;
    }

    itens.forEach((ev) => {
        const row = document.createElement('div');
        row.className = 'border-b border-gray-200 last:border-b-0 pb-2 last:pb-0';

        const line = document.createElement('div');
        line.className = 'text-xs text-gray-700';
        const when = formatEventoDate(ev.data_evento);
        const tipo = ev.tipo_evento ? String(ev.tipo_evento).replace(/_/g, ' ') : 'Evento';
        const detalhe = ev.detalhe ? String(ev.detalhe) : '';
        line.textContent = `${when ? when + ' • ' : ''}${tipo}${detalhe ? ': ' + detalhe : ''}`;
        row.appendChild(line);

        if (ev.data_retorno_antes || ev.data_retorno_depois) {
            const extra = document.createElement('div');
            extra.className = 'text-[11px] text-gray-500 mt-0.5';
            const antes = ev.data_retorno_antes || '-';
            const depois = ev.data_retorno_depois || '-';
            extra.textContent = `Retorno: ${antes} → ${depois}`;
            row.appendChild(extra);
        }

        list.appendChild(row);
    });
}

async function loadHistorico(prospeccaoId) {
    const wrap = document.getElementById('modalHistoricoWrap');
    const list = document.getElementById('modalHistorico');
    if (!wrap || !list) return;

    wrap.classList.remove('hidden');
    list.innerHTML = '';
    const loading = document.createElement('div');
    loading.className = 'text-xs text-gray-500';
    loading.textContent = 'Carregando histórico...';
    list.appendChild(loading);

    if (historicoCache.has(prospeccaoId)) {
        renderHistoricoItens(historicoCache.get(prospeccaoId));
        return;
    }

    try {
        const resp = await fetch(`/api/prospeccao/${prospeccaoId}/eventos`);
        const data = await resp.json().catch(() => null);
        if (!resp.ok || !data || !data.ok) {
            throw new Error((data && data.message) || 'Erro ao carregar histórico');
        }
        historicoCache.set(prospeccaoId, data.eventos || []);
        renderHistoricoItens(data.eventos || []);
    } catch (err) {
        list.innerHTML = '';
        const fail = document.createElement('div');
        fail.className = 'text-xs text-red-600';
        fail.textContent = 'Não foi possível carregar o histórico.';
        list.appendChild(fail);
    }
}

/**
 * Abre modal de registro
 */
function openRegistrarModal(cardEl) {
    if (!cardEl) return;
    const modal = document.getElementById('registrarModal');
    const form = document.getElementById('registrarForm');
    const id = cardEl.getAttribute('data-prospeccao-id');
    const nome = cardEl.getAttribute('data-nome-loja') || '-';
    const tel = cardEl.getAttribute('data-telefone') || '';
    const wa = cardEl.getAttribute('data-whatsapp') || '';
    const seg = cardEl.getAttribute('data-segmento') || '';
    const obsAtual = cardEl.getAttribute('data-observacao') || '';
    const resp = cardEl.getAttribute('data-responsavel') || '';
    const mapsUrl = cardEl.getAttribute('data-maps-url') || '';
    const next = cardEl.getAttribute('data-next') || '/agendamentos';

    const titleEl = document.getElementById('modalTitle');
    if (titleEl) {
        if (mapsUrl) {
            titleEl.innerHTML = `${nome} <a href="${mapsUrl}" target="_blank" class="ml-1 text-brand-500 hover:text-brand-700" title="Ver no Google Maps">📍</a>`;
        } else {
            titleEl.textContent = nome;
        }
    }
    document.getElementById('modalPhone').textContent = tel ? `📞 ${tel}` : '📞 Sem telefone';
    const waEl = document.getElementById('modalWhatsapp');
    if (waEl) waEl.textContent = wa ? `WhatsApp: ${wa}` : 'WhatsApp: Sem WhatsApp';
    
    const respEl = document.getElementById('modalResponsavel');
    if (respEl) {
        respEl.textContent = resp ? `👤 ${resp}` : '👤 Responsável Não Informado';
        respEl.classList.toggle('text-gray-400', !resp);
        respEl.classList.toggle('text-brand-600', !!resp);
    }
    document.getElementById('modalNext').value = next;
    document.getElementById('modalSegmento').value = seg;
    document.getElementById('modalResultado').value = '';
    document.getElementById('modalObs').value = '';
    document.getElementById('modalDataRetorno').value = '';
    const hr = document.getElementById('modalHoraRetorno');
    if (hr) hr.value = '';

    const obsWrap = document.getElementById('modalObsAtualWrap');
    const obsEl = document.getElementById('modalObsAtual');
    if (obsWrap && obsEl) {
        if (obsAtual) {
            obsEl.textContent = obsAtual;
            obsWrap.classList.remove('hidden');
        } else {
            obsEl.textContent = '';
            obsWrap.classList.add('hidden');
        }
    }

    form.action = `/agendamentos/${id}/registrar-tentativa`;
    modal.classList.remove('hidden');
    updateModalRequirements();
    loadHistorico(id);
}

/**
 * Fecha modal de registro
 */
function closeRegistrarModal() {
    const modal = document.getElementById('registrarModal');
    if (modal) modal.classList.add('hidden');
}

/**
 * Atualiza requisitos do modal baseado no resultado
 */
function updateModalRequirements() {
    const resultado = document.getElementById('modalResultado');
    const segWrap = document.getElementById('modalSegmentoWrap');
    const seg = document.getElementById('modalSegmento');
    const dateWrap = document.getElementById('modalDataRetornoWrap');
    const date = document.getElementById('modalDataRetorno');
    const timeWrap = document.getElementById('modalHoraRetornoWrap');
    const time = document.getElementById('modalHoraRetorno');
    const obs = document.getElementById('modalObs');
    const v = (resultado.value || '').toLowerCase();

    const needsDate = v === 'em negociação' || v === 'agendar retorno';
    const needsTime = needsDate;
    const needsSeg = v === 'em negociação';
    const needsObs = false; // Tornar observação sempre opcional
    const shouldShowConverter = v === 'interessado';

    if (dateWrap && date) {
        dateWrap.classList.toggle('hidden', !needsDate);
        date.required = needsDate;
        if (!needsDate) date.value = '';
    }
    if (timeWrap && time) {
        timeWrap.classList.toggle('hidden', !needsTime);
        time.required = needsTime;
        if (!needsTime) time.value = '';
    }
    if (segWrap && seg) {
        segWrap.classList.toggle('hidden', !needsSeg);
        seg.required = needsSeg;
    }
    if (obs) {
        obs.required = false;
    }

    const btnConv = document.getElementById('btnSalvarConverter');
    if (btnConv) {
        btnConv.classList.toggle('hidden', !shouldShowConverter);
    }
}

/**
 * Inicializa página de agendamentos
 */
function init() {
    initScrollLinks();
    initBackToTop();
    scrollToHash(window.location.hash);
    highlightByTime();

    const r = document.getElementById('modalResultado');
    if (r) r.addEventListener('change', updateModalRequirements);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Expõe globalmente para onclick no HTML
window.pedirDataRetorno = pedirDataRetorno;
window.openRegistrarModal = openRegistrarModal;
window.closeRegistrarModal = closeRegistrarModal;
window.scrollToHash = scrollToHash;
