/**
 * Módulo da página de Agendamentos
 */

import { pedirDataRetorno, scrollToHash, initBackToTop, initScrollLinks } from './utils.js';

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
    const seg = cardEl.getAttribute('data-segmento') || '';
    const next = cardEl.getAttribute('data-next') || '/agendamentos';

    document.getElementById('modalTitle').textContent = nome;
    document.getElementById('modalPhone').textContent = tel ? `📞 ${tel}` : '📞 Sem telefone';
    document.getElementById('modalNext').value = next;
    document.getElementById('modalSegmento').value = seg;
    document.getElementById('modalResultado').value = '';
    document.getElementById('modalObs').value = '';
    document.getElementById('modalDataRetorno').value = '';
    const hr = document.getElementById('modalHoraRetorno');
    if (hr) hr.value = '';

    form.action = `/agendamentos/${id}/registrar-tentativa`;
    modal.classList.remove('hidden');
    updateModalRequirements();
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
    const needsObs = v === 'em negociação' || v === 'agendar retorno' || v === 'pediu preço';
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
        obs.required = needsObs;
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
