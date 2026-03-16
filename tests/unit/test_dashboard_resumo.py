"""
Testes unitários para use case de dashboard.
"""
import pytest
from dataclasses import dataclass

from application.relatorios.dashboard_resumo import (
    DashboardResumoResponse,
    get_dashboard_resumo_with_repo,
)


@dataclass
class MockRelatorioRepository:
    """Mock do repositório para testes."""
    _data: dict

    def get_resumo_hoje(self) -> dict:
        return self._data


class TestDashboardResumoResponse:
    """Testes para DTO DashboardResumoResponse."""

    def test_response_is_frozen(self):
        """DTO deve ser imutável (frozen=True)."""
        response = DashboardResumoResponse(
            ligacoes=10,
            whatsapp=5,
            efetivos=3,
            novos_leads=2,
            novas_prospeccoes=4,
            interessados=1,
            negociacoes=2,
        )
        with pytest.raises(AttributeError):
            response.ligacoes = 20

    def test_response_default_values(self):
        """DTO deve aceitar valores zero."""
        response = DashboardResumoResponse(
            ligacoes=0,
            whatsapp=0,
            efetivos=0,
            novos_leads=0,
            novas_prospeccoes=0,
            interessados=0,
            negociacoes=0,
        )
        assert response.ligacoes == 0
        assert response.whatsapp == 0


class TestGetDashboardResumoWithRepo:
    """Testes para use case de dashboard."""

    def test_returns_response_with_all_fields(self):
        """Deve retornar resposta com todos os campos preenchidos."""
        repo = MockRelatorioRepository({
            "ligacoes": 10,
            "whatsapp": 5,
            "efetivos": 3,
            "novos_leads": 2,
            "novas_prospeccoes": 4,
            "interessados": 1,
            "negociacoes": 2,
        })

        result = get_dashboard_resumo_with_repo(repo)

        assert isinstance(result, DashboardResumoResponse)
        assert result.ligacoes == 10
        assert result.whatsapp == 5
        assert result.efetivos == 3
        assert result.novos_leads == 2
        assert result.novas_prospeccoes == 4
        assert result.interessados == 1
        assert result.negociacoes == 2

    def test_handles_empty_data(self):
        """Deve lidar com dados vazios retornando zeros."""
        repo = MockRelatorioRepository({})

        result = get_dashboard_resumo_with_repo(repo)

        assert result.ligacoes == 0
        assert result.whatsapp == 0
        assert result.efetivos == 0

    def test_handles_missing_fields(self):
        """Deve lidar com campos faltantes retornando zeros."""
        repo = MockRelatorioRepository({
            "ligacoes": 10,
            # outros campos faltando
        })

        result = get_dashboard_resumo_with_repo(repo)

        assert result.ligacoes == 10
        assert result.whatsapp == 0
        assert result.efetivos == 0

    def test_handles_none_values(self):
        """Deve lidar com valores None retornando zeros."""
        repo = MockRelatorioRepository({
            "ligacoes": None,
            "whatsapp": None,
        })

        result = get_dashboard_resumo_with_repo(repo)

        assert result.ligacoes == 0
        assert result.whatsapp == 0
