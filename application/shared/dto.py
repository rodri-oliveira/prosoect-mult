"""
DTOs para entidades de domínio compartilhadas.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class LeadItem:
    """DTO para item de lead na listagem."""
    id: int
    nome_loja: str
    cnpj: str | None
    telefone: str | None
    whatsapp: str | None
    cidade: str | None
    estado: str | None
    segmentos: str | None
    status: str | None
    resultado: str | None
    site: str | None
    created_at: str | None
    # Campos de último contato
    ultimo_tipo_contato: str | None = None
    ultimo_resultado: str | None = None
    ultimo_observacao: str | None = None
    ultimo_contato_data: str | None = None
    # Alias para compatibilidade
    data_criacao: str | None = None


@dataclass(frozen=True)
class ProspeccaoItem:
    """DTO para item de prospecção."""
    id: int
    nome_loja: str
    cnpj: str | None
    telefone: str | None
    whatsapp: str | None
    endereco: str | None
    cidade: str | None
    estado: str | None
    segmento: str | None
    status_prospeccao: str | None
    data_prospeccao: str | None
    data_retorno: str | None
    hora_retorno: str | None
    observacao: str | None
    maps_url: str | None


@dataclass(frozen=True)
class EventoProspeccao:
    """DTO para evento de prospecção."""
    id: int
    prospeccao_id: int
    nome_loja: str
    cnpj: str | None
    cidade: str | None
    estado: str | None
    segmento: str | None
    tipo_evento: str
    data: str
    hora: str | None
    detalhe: str | None


@dataclass(frozen=True)
class MapsItem:
    """DTO para item do Maps."""
    nome: str
    endereco: str | None
    cidade: str | None
    estado: str | None
    telefone: str | None
    cnpj: str | None
    maps_url: str | None
    maps_place_id: str | None
    website: str | None
    segmentos: list[str] | None
    key: str | None
