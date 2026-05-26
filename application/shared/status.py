"""
Status padronizados para prospecção e leads.
Centralização para facilitar manutenção e garantir consistência.
"""

# Status de Prospecção (tela de prospecção)
STATUS_PROSPECCAO = [
    "Não contatado",
    "Não atendeu",
    "Caixa postal",
    "Enviado Portfólio Whats",
    "Não analisou ainda o material",
    "Pediu para retornar",  # Exibido como "Agendamento" na UI
    "Solicitou portfólio",
    "Em negociação",
    "Interessado",
    "Já tem consultor atendendo",
    "Sem interesse",
    "Descartado",
    "Convertido em Lead",
]

# Status de Leads (tela de leads)
STATUS_LEADS = [
    "Novo Lead",
    "Sem contato",
    "Enviado Portfólio Whats",
    "Não analisou ainda o material",
    "Envio de documentação",
    "Em análise de documentação",
    "Envio de orçamento",
    "Falou com responsável",
    "Apresentação feita",
    "Solicitou portfólio",
    "Interessado",
    "Em negociação",
    "Já tem consultor atendendo",
    "Aguardando dados para cadastro",
    "Cliente ativo",
    "Sem interesse",
    "Descartado",
]

# Resultados de interação (contatos)
RESULTADOS_INTERACAO = [
    "Não atendeu",
    "Caixa postal",
    "Sem contato",
    "Enviado Portfólio Whats",
    "Não analisou ainda o material",
    "Envio de documentação",
    "Em análise de documentação",
    "Envio de orçamento",
    "Aguardando dados para cadastro",
    "Agendar retorno",
    "Pediu preço",
    "Solicitou portfólio",
    "Apresentação feita",
    "Em negociação",
    "Já tem consultor atendendo",
    "Sem interesse",
    "Descartado",
]

# Cores para status (CSS classes)
STATUS_COLORS = {
    # Prospecção
    "Não contatado": "bg-gray-100 text-gray-600",
    "Não atendeu": "bg-red-100 text-red-700",
    "Caixa postal": "bg-gray-200 text-gray-700",
    "Enviado Portfólio Whats": "bg-indigo-100 text-indigo-800",
    "Não analisou ainda o material": "bg-amber-100 text-amber-800",
    "Pediu para retornar": "bg-yellow-100 text-yellow-800",
    "Solicitou portfólio": "bg-blue-100 text-blue-800",
    "Em negociação": "bg-blue-100 text-blue-800",
    "Interessado": "bg-green-100 text-green-800",
    "Já tem consultor atendendo": "bg-orange-100 text-orange-800",
    "Sem interesse": "bg-gray-300 text-gray-700",
    "Descartado": "bg-red-50 text-red-600",
    "Convertido em Lead": "bg-purple-100 text-purple-800",
    # Leads
    "Novo Lead": "bg-blue-100 text-blue-800",
    "Tentativa 1": "bg-yellow-100 text-yellow-800",
    "Tentativa 2": "bg-yellow-100 text-yellow-800",
    "Tentativa 3": "bg-yellow-100 text-yellow-800",
    "Sem contato": "bg-gray-100 text-gray-600",
    "Enviado Portfólio Whats": "bg-indigo-100 text-indigo-800",
    "Envio de documentação": "bg-amber-100 text-amber-800",
    "Em análise de documentação": "bg-yellow-100 text-yellow-800",
    "Envio de orçamento": "bg-cyan-100 text-cyan-800",
    "Falou com responsável": "bg-green-100 text-green-800",
    "Apresentação feita": "bg-blue-100 text-blue-800",
    "Aguardando dados para cadastro": "bg-purple-100 text-purple-800",
    "Cliente ativo": "bg-green-200 text-green-900",
}

def get_status_color(status: str) -> str:
    """Retorna a classe CSS para o status."""
    return STATUS_COLORS.get(status, "bg-gray-100 text-gray-600")
