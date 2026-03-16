/**
 * Módulo do Drawer do Maps
 * Gerencia abertura/fechamento e estado do drawer
 */

let isDrawerOpen = false;

/**
 * Abre o drawer do Maps
 */
export function openDrawer() {
    const drawer = document.getElementById('mapsDrawer');
    const overlay = document.getElementById('mapsOverlay');
    if (!drawer || !overlay) return;

    // Remove hidden primeiro
    drawer.classList.remove('hidden');
    drawer.setAttribute('aria-hidden', 'false');
    
    // Depois anima
    drawer.classList.remove('translate-x-full');
    overlay.classList.remove('hidden');
    isDrawerOpen = true;

    // Renderiza cache existente (via window para evitar dependência circular)
    try {
        if (typeof window.__readMapsCache === 'function') {
            window.__readMapsCache();
        }
        const cached = window.__mapsResultsCache;
        if (Array.isArray(cached) && cached.length > 0 && typeof window.__renderMapsResults === 'function') {
            window.__renderMapsResults(cached);
        }
    } catch (e) {}

    // Foca no primeiro campo
    setTimeout(() => {
        const firstInput = drawer.querySelector('input:not([type="hidden"])');
        if (firstInput) firstInput.focus();
    }, 100);
}

/**
 * Fecha o drawer do Maps
 */
export function closeDrawer() {
    const drawer = document.getElementById('mapsDrawer');
    const overlay = document.getElementById('mapsOverlay');
    if (!drawer || !overlay) return;

    drawer.classList.add('translate-x-full');
    overlay.classList.add('hidden');
    isDrawerOpen = false;
}

/**
 * Verifica se o drawer está aberto
 * @returns {boolean}
 */
export function isDrawerOpenState() {
    return isDrawerOpen;
}

/**
 * Alterna estado do drawer
 */
export function toggleDrawer() {
    if (isDrawerOpen) {
        closeDrawer();
    } else {
        openDrawer();
    }
}

/**
 * Instala delegação de clique para o botão do drawer
 * Funciona com bfcache e navegação SPA
 */
export function installDrawerDelegation() {
    if (window.__MAPS_DRAWER_DELEGATION_INSTALLED) return;
    window.__MAPS_DRAWER_DELEGATION_INSTALLED = true;

    document.body.addEventListener('click', (e) => {
        const btn = e.target?.closest?.('#btnResultadosMaps');
        if (!btn) return;

        // Guard contra duplo clique
        if (window.__MAPS_DRAWER_OPEN_GUARD) return;
        window.__MAPS_DRAWER_OPEN_GUARD = true;
        setTimeout(() => { window.__MAPS_DRAWER_OPEN_GUARD = false; }, 0);

        e.preventDefault();
        e.stopPropagation();

        if (typeof window.__openMapsDrawer === 'function') {
            window.__openMapsDrawer();
        }
    });
}

/**
 * Instala listener para fechar drawer ao navegar para outra página
 */
export function installBeforeUnloadHandler() {
    if (window.__MAPS_BEFOREUNLOAD_INSTALLED) return;
    window.__MAPS_BEFOREUNLOAD_INSTALLED = true;

    window.addEventListener('beforeunload', () => {
        try {
            const drawer = document.getElementById('mapsDrawer');
            if (drawer && !drawer.classList.contains('hidden')) {
                drawer.classList.add('hidden');
                drawer.setAttribute('aria-hidden', 'true');
            }
        } catch (e) {}
    });
}

// Expõe funções globalmente para compatibilidade
window.__openMapsDrawer = openDrawer;
window.__closeMapsDrawer = closeDrawer;
window.__toggleMapsDrawer = toggleDrawer;
