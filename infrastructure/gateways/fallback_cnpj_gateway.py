from __future__ import annotations

import logging

from domain.gateways.cnpj_gateway import CnpjGateway, CnpjInfo
from infrastructure.gateways.brasil_api_cnpj_gateway import BrasilApiCnpjGateway
from infrastructure.gateways.receitaws_cnpj_gateway import ReceitaWsCnpjGateway


class FallbackCnpjGateway(CnpjGateway):
    """Gateway composto que tenta BrasilAPI primeiro, e se falhar usa ReceitaWS."""

    def __init__(self, timeout_seconds: int = 8):
        self._brasil_api = BrasilApiCnpjGateway(timeout_seconds=timeout_seconds)
        self._receitaws = ReceitaWsCnpjGateway(timeout_seconds=timeout_seconds + 2)
        self._logger = logging.getLogger(__name__)

    def consultar(self, cnpj: str) -> CnpjInfo | None:
        info = self._brasil_api.consultar(cnpj)
        if info:
            self._logger.debug("CNPJ %s encontrado via BrasilAPI", cnpj)
            return info

        self._logger.warning("BrasilAPI falhou para CNPJ %s, tentando ReceitaWS", cnpj)
        info = self._receitaws.consultar(cnpj)
        if info:
            self._logger.debug("CNPJ %s encontrado via ReceitaWS", cnpj)
            return info

        self._logger.error("Todas as APIs de CNPJ falharam para %s", cnpj)
        return None

    def is_ativo(self, cnpj: str) -> bool:
        info = self.consultar(cnpj)
        return info.ativo if info else False
