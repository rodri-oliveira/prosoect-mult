import json
import re
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


def normalize_cnpj(value):
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    return digits or None


def is_valid_cnpj(value):
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


def consultar_cnpj_brasilapi(value, timeout_seconds=8):
    cnpj = normalize_cnpj(value)
    if not cnpj:
        return None

    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    req = Request(url, headers={"User-Agent": "prospect-mult"})

    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except HTTPError as e:
        try:
            raw = e.read().decode("utf-8")
            return {"error": raw, "status": e.code}
        except Exception:
            return {"error": str(e), "status": getattr(e, "code", None)}
    except URLError as e:
        return {"error": str(e), "status": None}
    except Exception as e:
        return {"error": str(e), "status": None}


def is_cnpj_ativo_brasilapi(data: dict) -> bool:
    if not isinstance(data, dict):
        return False

    desc = data.get('descricao_situacao_cadastral')
    if isinstance(desc, str) and desc.strip():
        return desc.strip().upper() == 'ATIVA'

    situ = data.get('situacao_cadastral')
    if isinstance(situ, str) and situ.strip():
        return situ.strip().upper() == 'ATIVA'

    return False
