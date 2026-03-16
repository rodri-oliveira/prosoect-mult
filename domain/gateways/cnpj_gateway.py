from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CnpjInfo:
    """Informações de CNPJ retornadas pela API."""
    cnpj: str
    razao_social: str
    nome_fantasia: str | None
    situacao: str
    ativo: bool
    data_abertura: str | None
    endereco: str | None
    cidade: str | None
    estado: str | None
    cep: str | None
    telefone: str | None
    email: str | None
    atividade_principal: str | None


class CnpjGateway(Protocol):
    """Contrato para consulta de CNPJ (fonte externa)."""
    
    def consultar(self, cnpj: str) -> CnpjInfo | None:
        """Consulta CNPJ e retorna informações ou None se não encontrado."""
        ...
    
    def is_ativo(self, cnpj: str) -> bool:
        """Verifica se CNPJ está ativo na receita."""
        ...
