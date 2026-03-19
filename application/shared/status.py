"""
Status padronizados para prospecção e leads.
Centralização para facilitar manutenção e garantir consistência.
"""

# Status de Prospecção (tela de prospecção)
STATUS_PROSPECCAO = [
    "Não contatado",
    "Não atendeu",
    "Caixa postal",
    "Pediu para retornar",
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
    "Falou com responsável",
    "Apresentação feita",
    "Solicitou portfólio",
    "Interessado",
    "Em negociação",
    "Já tem consultor atendendo",
    "Cliente ativo",
    "Sem interesse",
    "Descartado",
]

# Resultados de interação (contatos)
RESULTADOS_INTERACAO = [
    "Não atendeu",
    "Caixa postal",
    "Sem contato",
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
    "Falou com responsável": "bg-green-100 text-green-800",
    "Apresentação feita": "bg-blue-100 text-blue-800",
    "Cliente ativo": "bg-green-200 text-green-900",
}

def get_status_color(status: str) -> str:
    """Retorna a classe CSS para o status."""
    return STATUS_COLORS.get(status, "bg-gray-100 text-gray-600")
