"""Helpers puros de normalização e extração segura de dicionários aninhados."""

from typing import Any


def safe_dict(val: Any) -> dict:
    return val if isinstance(val, dict) else {}


def g(d: Any, key: str, default: Any = None) -> Any:
    if isinstance(d, dict):
        val = d.get(key)
        return val if val is not None else default
    return default


def normalizar_cpf_cnpj(val_bruto: Any) -> str | None:
    """Remove pontuação e zero-preenche para 11 (CPF) ou 14 (CNPJ) dígitos."""
    if not val_bruto:
        return None
    digitos = "".join(c for c in str(val_bruto).strip() if c.isdigit())
    n = len(digitos)
    if 1 <= n <= 11:
        return digitos.zfill(11)
    if 12 <= n <= 14:
        return digitos.zfill(14)
    return None
