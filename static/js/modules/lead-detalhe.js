/**
 * Módulo da página de Detalhe do Lead
 */

/**
 * Verifica se resultado requer observação
 */
function shouldRequireObs(value) {
    if (!value) return false;
    const v = value.toLowerCase();
    return v.includes('agendar retorno') || v.includes('em negociação') || v.includes('pediu') || v.includes('preço');
}

/**
 * Verifica se resultado requer data de retorno
 */
function shouldRequireReturnDate(value) {
    if (!value) return false;
    const v = value.toLowerCase();
    return v === 'em negociação' || v === 'agendar retorno';
}

/**
 * Atualiza campos baseado no resultado selecionado
 */
function updateFields() {
    const resultado = document.getElementById('resultado');
    const obs = document.getElementById('observacao');
    const campoDataRetorno = document.getElementById('campo-data-retorno');
    const dataRetorno = document.getElementById('data_retorno');
    const campoHoraRetorno = document.getElementById('campo-hora-retorno');
    const horaRetorno = document.getElementById('hora_retorno');

    if (!resultado || !obs) return;

    const v = resultado.value || '';
    obs.required = shouldRequireObs(v);
    const needsDate = shouldRequireReturnDate(v);
    const needsTime = needsDate;

    if (campoDataRetorno && dataRetorno) {
        campoDataRetorno.classList.toggle('hidden', !needsDate);
        dataRetorno.required = needsDate;
    }

    if (campoHoraRetorno && horaRetorno) {
        campoHoraRetorno.classList.toggle('hidden', !needsTime);
        horaRetorno.required = needsTime;
    }

    if (obs.required) {
        obs.placeholder = 'Obrigatório: descreva o próximo passo (ex: enviar catálogo hoje, retornar sexta 15h)';
    } else {
        obs.placeholder = 'Ex: Pediu para ligar sexta à tarde';
    }
}

/**
 * Inicializa página de detalhe do lead
 */
function init() {
    const resultado = document.getElementById('resultado');
    if (resultado) {
        resultado.addEventListener('change', updateFields);
        updateFields();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
