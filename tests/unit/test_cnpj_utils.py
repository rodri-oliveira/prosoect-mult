"""
Testes unitários para use cases de CNPJ.
"""
import pytest

from application.shared.cnpj_utils import (
    normalize_cnpj,
    is_valid_cnpj,
    validar_cnpj,
    ValidarCnpjResponse,
)


class TestNormalizeCnpj:
    """Testes para normalização de CNPJ."""

    def test_normalize_cnpj_with_formatting(self):
        """CNPJ com formatação deve retornar apenas dígitos."""
        assert normalize_cnpj("12.345.678/0001-90") == "12345678000190"

    def test_normalize_cnpj_with_letters(self):
        """CNPJ com letras deve retornar apenas dígitos."""
        assert normalize_cnpj("ABC12345678000190XYZ") == "12345678000190"

    def test_normalize_cnpj_clean(self):
        """CNPJ já limpo deve retornar igual."""
        assert normalize_cnpj("12345678000190") == "12345678000190"

    def test_normalize_cnpj_empty(self):
        """CNPJ vazio deve retornar None."""
        assert normalize_cnpj("") is None

    def test_normalize_cnpj_none(self):
        """CNPJ None deve retornar None."""
        assert normalize_cnpj(None) is None

    def test_normalize_cnpj_only_letters(self):
        """CNPJ apenas com letras deve retornar None."""
        assert normalize_cnpj("ABCDEF") is None


class TestIsValidCnpj:
    """Testes para validação de CNPJ."""

    def test_valid_cnpj(self):
        """CNPJ válido deve retornar True."""
        # CNPJ válido conhecido: 11.222.333/0001-81
        assert is_valid_cnpj("11222333000181") is True

    def test_valid_cnpj_with_formatting(self):
        """CNPJ válido com formatação deve retornar True."""
        assert is_valid_cnpj("11.222.333/0001-81") is True

    def test_invalid_cnpj_wrong_digits(self):
        """CNPJ com dígitos verificadores errados deve retornar False."""
        assert is_valid_cnpj("11222333000182") is False

    def test_invalid_cnpj_same_digits(self):
        """CNPJ com todos dígitos iguais deve retornar False."""
        assert is_valid_cnpj("11111111111111") is False

    def test_invalid_cnpj_short(self):
        """CNPJ com menos de 14 dígitos deve retornar False."""
        assert is_valid_cnpj("12345678") is False

    def test_invalid_cnpj_empty(self):
        """CNPJ vazio deve retornar False."""
        assert is_valid_cnpj("") is False

    def test_invalid_cnpj_none(self):
        """CNPJ None deve retornar False."""
        assert is_valid_cnpj(None) is False


class TestValidarCnpj:
    """Testes para função de validação completa."""

    def test_validar_cnpj_valid(self):
        """CNPJ válido deve retornar resposta com valido=True."""
        result = validar_cnpj("11.222.333/0001-81")
        assert isinstance(result, ValidarCnpjResponse)
        assert result.valido is True
        assert result.cnpj_normalizado == "11222333000181"

    def test_validar_cnpj_invalid(self):
        """CNPJ inválido deve retornar resposta com valido=False."""
        result = validar_cnpj("11222333000182")
        assert result.valido is False
        assert result.cnpj_normalizado is None

    def test_validar_cnpj_empty(self):
        """CNPJ vazio deve retornar resposta com valido=False."""
        result = validar_cnpj("")
        assert result.valido is False
        assert result.cnpj_normalizado is None
