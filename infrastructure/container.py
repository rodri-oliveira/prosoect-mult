from __future__ import annotations

from functools import lru_cache

from domain.repositories.agendamentos_repository import AgendamentosRepository
from domain.repositories.lead_repository import LeadRepository
from domain.repositories.maps_existing_keys_repository import MapsExistingKeysRepository
from domain.repositories.prospeccao_repository import ProspeccaoRepository
from domain.repositories.prospeccao_temp_repository import ProspecctionTempRepository
from domain.repositories.relatorio_repository import RelatorioRepository
from domain.gateways.cnpj_gateway import CnpjGateway
from infrastructure.repositories.sqlite_agendamentos_repository import SqliteAgendamentosRepository
from infrastructure.repositories.sqlite_lead_repository import SqliteLeadRepository
from infrastructure.repositories.sqlite_maps_existing_keys_repository import SqliteMapsExistingKeysRepository
from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository
from infrastructure.repositories.sqlite_prospeccao_temp_repository import SqliteProspecctionTempRepository
from infrastructure.repositories.sqlite_relatorio_repository import SqliteRelatorioRepository
from infrastructure.gateways.brasil_api_cnpj_gateway import BrasilApiCnpjGateway


@lru_cache(maxsize=1)
def cnpj_gateway() -> CnpjGateway:
    return BrasilApiCnpjGateway()


@lru_cache(maxsize=1)
def maps_existing_keys_repository() -> MapsExistingKeysRepository:
    return SqliteMapsExistingKeysRepository()


@lru_cache(maxsize=1)
def prospeccao_temp_repository() -> ProspecctionTempRepository:
    return SqliteProspecctionTempRepository()


@lru_cache(maxsize=1)
def prospeccao_repository() -> ProspeccaoRepository:
    return SqliteProspeccaoRepository()


@lru_cache(maxsize=1)
def lead_repository() -> LeadRepository:
    return SqliteLeadRepository()


@lru_cache(maxsize=1)
def agendamentos_repository() -> AgendamentosRepository:
    return SqliteAgendamentosRepository()


@lru_cache(maxsize=1)
def relatorio_repository() -> RelatorioRepository:
    return SqliteRelatorioRepository()
