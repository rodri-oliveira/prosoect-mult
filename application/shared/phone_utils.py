from __future__ import annotations

import re


def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    digits = re.sub(r"\D", "", raw)
    if not digits:
        return raw

    if digits.startswith("55") and len(digits) in (12, 13):
        digits = digits[2:]

    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:]}"
    if len(digits) == 9:
        return f"{digits[:5]}-{digits[5:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"

    return raw
