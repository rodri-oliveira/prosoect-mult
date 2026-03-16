"""
Testes unitários para gateway CNPJ.
"""
import pytest
from unittest.mock import MagicMock, patch

from domain.gateways.cnpj_gateway import CnpjInfo
from infrastructure.gateways.brasil_api_cnpj_gateway import BrasilApiCnpjGateway


class TestCnpjInfo:
    """Testes para DTO CnpjInfo."""

    def test_cnpj_info_is_frozen(self):
        """DTO deve ser imutável."""
        info = CnpjInfo(
            cnpj="12345678000190",
            razao_social="Empresa Teste",
            nome_fantasia="Teste",
            situacao="ATIVA",
            ativo=True,
            data_abertura="2000-01-01",
            endereco="Rua A, 123",
            cidade="São Paulo",
            estado="SP",
            cep="01234567",
            telefone="11999999999",
            email="teste@email.com",
            atividade_principal="Comércio",
        )
        with pytest.raises(AttributeError):
            info.cnpj = "novo_cnpj"

    def test_cnpj_info_optional_fields(self):
        """Campos opcionais devem aceitar None."""
        info = CnpjInfo(
            cnpj="12345678000190",
            razao_social="Empresa Teste",
            nome_fantasia=None,
            situacao="ATIVA",
            ativo=True,
            data_abertura=None,
            endereco=None,
            cidade=None,
            estado=None,
            cep=None,
            telefone=None,
            email=None,
            atividade_principal=None,
        )
        assert info.nome_fantasia is None
        assert info.endereco is None


class TestBrasilApiCnpjGateway:
    """Testes para gateway BrasilAPI."""

    def test_consultar_invalid_cnpj_returns_none(self):
        """CNPJ inválido deve retornar None."""
        gateway = BrasilApiCnpjGateway()
        result = gateway.consultar("123")
        assert result is None

    def test_consultar_none_cnpj_returns_none(self):
        """CNPJ None deve retornar None."""
        gateway = BrasilApiCnpjGateway()
        result = gateway.consultar(None)
        assert result is None

    def test_consultar_same_digits_cnpj_returns_none(self):
        """CNPJ com todos dígitos iguais deve retornar None."""
        gateway = BrasilApiCnpjGateway()
        result = gateway.consultar("11111111111111")
        assert result is None

    @patch('infrastructure.gateways.brasil_api_cnpj_gateway.urlopen')
    def test_consultar_valid_cnpj_returns_info(self, mock_urlopen):
        """CNPJ válido deve retornar CnpjInfo."""
        # CNPJ válido conhecido para teste
        valid_cnpj = "11222333000181"
        
        mock_response = MagicMock()
        json_data = '{"cnpj":"' + valid_cnpj + '","razao_social":"Empresa Teste LTDA","nome_fantasia":"Teste","descricao_situacao_cadastral":"ATIVA","logradouro":"Rua A","numero":"123","bairro":"Centro","municipio":"Sao Paulo","uf":"SP","cep":"01234567","ddd_telefone_1":"11999999999","email":"teste@email.com","cnae_fiscal_descricao":"Comercio varejista"}'
        mock_response.read.return_value = json_data.encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        gateway = BrasilApiCnpjGateway()
        result = gateway.consultar(valid_cnpj)

        assert result is not None
        assert result.cnpj == valid_cnpj
        assert result.razao_social == "Empresa Teste LTDA"
        assert result.ativo is True

    @patch('infrastructure.gateways.brasil_api_cnpj_gateway.urlopen')
    def test_consultar_inactive_cnpj_returns_ativo_false(self, mock_urlopen):
        """CNPJ inativo deve retornar ativo=False."""
        valid_cnpj = "11222333000181"
        
        mock_response = MagicMock()
        json_data = '{"cnpj":"' + valid_cnpj + '","razao_social":"Empresa Teste","descricao_situacao_cadastral":"BAIXADA"}'
        mock_response.read.return_value = json_data.encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        gateway = BrasilApiCnpjGateway()
        result = gateway.consultar(valid_cnpj)

        assert result is not None
        assert result.ativo is False

    def test_is_ativo_returns_false_for_none(self):
        """is_ativo deve retornar False para CNPJ não encontrado."""
        gateway = BrasilApiCnpjGateway()
        result = gateway.is_ativo("invalido")
        assert result is False
