"""
Utilitários e DTOs compartilhados da camada Application.
"""
from __future__ import annotations

from application.shared.cnpj_utils import (
    ConsultarCnpjResponse,
    ValidarCnpjResponse,
    consultar_cnpj_with_gateway,
    is_valid_cnpj,
    normalize_cnpj,
    validar_cnpj,
)
from application.shared.dto import (
    LeadItem,
    ProspeccaoItem,
    EventoProspeccao,
    MapsItem,
)

__all__ = [
    # CNPJ
    "ConsultarCnpjResponse",
    "ValidarCnpjResponse",
    "consultar_cnpj_with_gateway",
    "is_valid_cnpj",
    "normalize_cnpj",
    "validar_cnpj",
    # DTOs
    "LeadItem",
    "ProspeccaoItem",
    "EventoProspeccao",
    "MapsItem",
]
