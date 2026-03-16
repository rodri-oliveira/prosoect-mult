/**
 * Módulo de utilitários compartilhados
 */

/**
 * Pede data de retorno via prompt
 * @param {HTMLFormElement} form - Formulário
 * @returns {boolean}
 */
export function pedirDataRetorno(form) {
    const data = prompt('Nova data para retornar (AAAA-MM-DD):');
    if (!data) return false;
    const input = form.querySelector('.data-retorno-input');
    if (input) input.value = data;
    return true;
}

/**
 * Scroll suave para elemento com destaque
 * @param {string} hash - Seletor CSS (#id)
 */
export function scrollToHash(hash) {
    if (!hash) return;
    const el = document.querySelector(hash);
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    el.classList.add('ring-2', 'ring-brand-300');
    setTimeout(() => {
        el.classList.remove('ring-2', 'ring-brand-300');
    }, 1200);
}

/**
 * Inicializa botão back-to-top
 */
export function initBackToTop() {
    const btn = document.getElementById('back-to-top');
    if (!btn) return;

    btn.addEventListener('click', (e) => {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    const toggle = () => {
        if (window.scrollY > 200) btn.classList.remove('hidden');
        else btn.classList.add('hidden');
    };

    window.addEventListener('scroll', toggle, { passive: true });
    toggle();
}

/**
 * Inicializa scroll links
 */
export function initScrollLinks() {
    document.querySelectorAll('a.js-scroll[href^="#"]').forEach((a) => {
        a.addEventListener('click', (e) => {
            const hash = a.getAttribute('href');
            if (!hash) return;
            e.preventDefault();
            history.replaceState(null, '', hash);
            scrollToHash(hash);
        });
    });
}

// Expõe globalmente para compatibilidade
window.pedirDataRetorno = pedirDataRetorno;
