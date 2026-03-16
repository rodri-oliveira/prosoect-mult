from __future__ import annotations

import json
import re
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from domain.gateways.cnpj_gateway import CnpjGateway, CnpjInfo


class BrasilApiCnpjGateway(CnpjGateway):
    """Implementação do gateway CNPJ usando BrasilAPI."""
    
    def __init__(self, timeout_seconds: int = 8):
        self._timeout = timeout_seconds
    
    def _normalize_cnpj(self, value: str | None) -> str | None:
        if value is None:
            return None
        digits = re.sub(r"\D", "", str(value))
        return digits or None
    
    def _is_valid_cnpj(self, value: str) -> bool:
        cnpj = self._normalize_cnpj(value)
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
    
    def consultar(self, cnpj: str) -> CnpjInfo | None:
        cnpj_norm = self._normalize_cnpj(cnpj)
        if not cnpj_norm or not self._is_valid_cnpj(cnpj_norm):
            return None

        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_norm}"
        req = Request(url, headers={"User-Agent": "prospect-mult"})

        try:
            with urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
                return self._parse_response(cnpj_norm, data)
        except HTTPError:
            return None
        except URLError:
            return None
        except Exception:
            return None
    
    def _parse_response(self, cnpj: str, data: dict) -> CnpjInfo:
        """Converte resposta da API para CnpjInfo."""
        situacao = data.get("descricao_situacao_cadastral") or data.get("situacao_cadastral") or ""
        ativo = situacao.strip().upper() == "ATIVA"
        
        endereco_parts = []
        if data.get("logradouro"):
            endereco_parts.append(data["logradouro"])
        if data.get("numero"):
            endereco_parts.append(data["numero"])
        if data.get("bairro"):
            endereco_parts.append(data["bairro"])
        endereco = ", ".join(endereco_parts) if endereco_parts else None
        
        return CnpjInfo(
            cnpj=cnpj,
            razao_social=data.get("razao_social") or "",
            nome_fantasia=data.get("nome_fantasia"),
            situacao=situacao,
            ativo=ativo,
            data_abertura=data.get("data_inicio_atividade"),
            endereco=endereco,
            cidade=data.get("municipio"),
            estado=data.get("uf"),
            cep=data.get("cep"),
            telefone=data.get("ddd_telefone_1"),
            email=data.get("email"),
            atividade_principal=data.get("cnae_fiscal_descricao"),
        )
    
    def is_ativo(self, cnpj: str) -> bool:
        info = self.consultar(cnpj)
        return info.ativo if info else False
