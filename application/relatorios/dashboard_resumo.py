from __future__ import annotations

from dataclasses import dataclass

from domain.repositories.relatorio_repository import RelatorioRepository


@dataclass(frozen=True)
class DashboardResumoResponse:
    ligacoes: int
    whatsapp: int
    efetivos: int
    novos_leads: int
    novas_prospeccoes: int
    interessados: int
    negociacoes: int


def _safe_int(value) -> int:
    """Converte valor para int, tratando None e tipos inválidos."""
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def get_dashboard_resumo_with_repo(repo: RelatorioRepository) -> DashboardResumoResponse:
    """Use case: obter resumo do dashboard para o dia atual."""
    try:
        dados = repo.get_resumo_hoje() or {}
    except Exception:
        dados = {}
    
    return DashboardResumoResponse(
        ligacoes=_safe_int(dados.get("ligacoes")),
        whatsapp=_safe_int(dados.get("whatsapp")),
        efetivos=_safe_int(dados.get("efetivos")),
        novos_leads=_safe_int(dados.get("novos_leads")),
        novas_prospeccoes=_safe_int(dados.get("novas_prospeccoes")),
        interessados=_safe_int(dados.get("interessados")),
        negociacoes=_safe_int(dados.get("negociacoes")),
    )
