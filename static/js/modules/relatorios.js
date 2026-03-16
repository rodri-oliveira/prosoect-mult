/**
 * Módulo de Relatórios
 */

/**
 * Copia relatório completo para WhatsApp
 * @param {string} periodo - Período do relatório
 * @param {object} relatorio - Dados do relatório
 */
export function copyToWhatsApp(periodo, relatorio) {
    const periodoTexto = periodo === 'hoje' ? 'Hoje' : periodo === 'ontem' ? 'Ontem' : relatorio.data_inicio;
    
    const text = `🚀 *RELATÓRIO - ${periodoTexto}*

*📊 PROSPECÇÃO:*
Total: ${relatorio.total_prospeccoes} | Tentativas: ${relatorio.tentativas_prospeccao} | Convertidos: ${relatorio.convertidos}

*👤 CRM:*
Ligações: ${relatorio.ligacoes} | Whats: ${relatorio.whatsapp} | Efetivos: ${relatorio.efetivos} | Novos: ${relatorio.novos_leads}

_CRM Prospecção_`;

    navigator.clipboard.writeText(text).then(() => alert('Relatório copiado!'));
}

/**
 * Copia relatório de prospecção
 * @param {string} dataInicio - Data início
 * @param {string} dataFim - Data fim
 * @param {object} relatorio - Dados do relatório
 */
export function copiarRelatorioProspeccao(dataInicio, dataFim, relatorio) {
    const resumoLinhas = relatorio.resumo.map(([status, total]) => `- ${status}: ${total}`).join('\n');
    const detalheLinhas = relatorio.items.map(item => {
        let linha = `- ${item.data_prospeccao} | ${item.nome_loja} | ${item.status_prospeccao}`;
        if (item.observacao) linha += ` | ${item.observacao}`;
        return linha;
    }).join('\n');

    const texto = `RELATÓRIO DE PROSPECÇÃO
Período: ${dataInicio} a ${dataFim}

RESUMO:
- Total de Prospecções: ${relatorio.total_geral}
- Tentativas de Contato: ${relatorio.total_tentativas}
- Convertidos em Leads: ${relatorio.total_convertidos}

POR STATUS:
${resumoLinhas}

DETALHAMENTO:
${detalheLinhas}`;

    navigator.clipboard.writeText(texto).then(() => {
        alert('Relatório copiado para clipboard!');
    });
}

// Expõe globalmente
window.copyToWhatsApp = copyToWhatsApp;
window.copiarRelatorioProspeccao = copiarRelatorioProspeccao;
