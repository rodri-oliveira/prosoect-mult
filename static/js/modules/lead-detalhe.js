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
    return v === 'agendar retorno';
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
    console.log("Lead-detalhe: Inicializando módulo...");
    const resultado = document.getElementById('resultado');
    if (resultado) {
        resultado.addEventListener('change', updateFields);
        updateFields();
    }

    // Configuração do modo Edição de Informações (In-place)
    const btnEditar = document.getElementById('btn-editar-lead');
    const btnSalvar = document.getElementById('btn-salvar-lead');
    const btnCancelar = document.getElementById('btn-cancelar-edit');
    const fieldContainer = document.getElementById('lead-fields-container');

    console.log("Lead-detalhe IDs encontrados:", {
        btnEditar: !!btnEditar,
        btnSalvar: !!btnSalvar,
        btnCancelar: !!btnCancelar,
        fieldContainer: !!fieldContainer
    });

    if (btnEditar && fieldContainer) {
        const toggleEdit = (active) => {
            fieldContainer.querySelectorAll('.view-val').forEach(el => el.classList.toggle('hidden', active));
            fieldContainer.querySelectorAll('.edit-input').forEach(el => el.classList.toggle('hidden', !active));
            
            btnEditar.classList.toggle('hidden', active);
            btnSalvar.classList.toggle('hidden', !active);
            btnCancelar.classList.toggle('hidden', !active);

            if (active) {
                const firstInput = fieldContainer.querySelector('.edit-input');
                if (firstInput) {
                    setTimeout(() => firstInput.focus(), 50); // Delay para transição suave
                }
            }
        };

        btnEditar.addEventListener('click', () => toggleEdit(true));
        btnCancelar.addEventListener('click', () => toggleEdit(false));
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
