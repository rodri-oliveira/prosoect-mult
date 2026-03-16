from __future__ import annotations

import re
from dataclasses import dataclass

from domain.gateways.cnpj_gateway import CnpjGateway


@dataclass(frozen=True)
class ValidarCnpjResponse:
    cnpj_normalizado: str | None
    valido: bool


@dataclass(frozen=True)
class ConsultarCnpjResponse:
    cnpj: str
    razao_social: str
    nome_fantasia: str | None
    ativo: bool
    endereco: str | None
    cidade: str | None
    estado: str | None
    telefone: str | None
    email: str | None


def normalize_cnpj(value: str | None) -> str | None:
    """Normaliza CNPJ removendo caracteres não numéricos."""
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    return digits or None


def is_valid_cnpj(value: str | None) -> bool:
    """Valida CNPJ usando algoritmo de dígitos verificadores."""
    cnpj = normalize_cnpj(value)
    if not cnpj or len(cnpj) != 14:
        return False
    if cnpj == cnpj[0] * 14:
        return False

    def calc_digit(nums, weights):
        s = sum(int(n) * w for n, w in zip(nums, weights))
        r = s % 11
        return "0" if r < 2 else str(11 - r)

    d1 = calc_digit(cnpj[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = calc_digit(cnpj[:12] + d1, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return cnpj[-2:] == d1 + d2


def validar_cnpj(cnpj: str | None) -> ValidarCnpjResponse:
    """Valida e normaliza CNPJ."""
    cnpj_norm = normalize_cnpj(cnpj)
    valido = is_valid_cnpj(cnpj_norm) if cnpj_norm else False
    return ValidarCnpjResponse(
        cnpj_normalizado=cnpj_norm if valido else None,
        valido=valido,
    )


def consultar_cnpj_with_gateway(cnpj: str, gateway: CnpjGateway) -> ConsultarCnpjResponse | None:
    """Consulta CNPJ via gateway."""
    info = gateway.consultar(cnpj)
    if not info:
        return None
    
    return ConsultarCnpjResponse(
        cnpj=info.cnpj,
        razao_social=info.razao_social,
        nome_fantasia=info.nome_fantasia,
        ativo=info.ativo,
        endereco=info.endereco,
        cidade=info.cidade,
        estado=info.estado,
        telefone=info.telefone,
        email=info.email,
    )
