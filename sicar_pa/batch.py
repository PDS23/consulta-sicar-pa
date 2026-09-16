"""Processamento em lote: roda a mesma busca individual por linha de planilha."""

from typing import Any, Callable

import pandas as pd
import time

from .client import buscar_sicar_completo
from .config import BLOCOS_CAMPOS

ProgressCallback = Callable[[int, int, str], None]


def processar_lote_planilha(
    df_input: pd.DataFrame,
    coluna_busca: str,
    var_payload: str,
    campos_selecionados: list[str],
    token: str,
    url: str,
    progress_callback: ProgressCallback | None = None,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    df_resultado = df_input.copy()
    mapa_chaves_nomes = {k: v for b in BLOCOS_CAMPOS.values() for k, v in b.items()}
    cols_add = [mapa_chaves_nomes[c] for c in campos_selecionados if c in mapa_chaves_nomes]
    for c in cols_add:
        df_resultado[c] = None

    novas_linhas: list[dict[str, Any]] = []
    todos_brutos: list[dict[str, Any]] = []
    total = len(df_input)

    for idx, row in df_input.iterrows():
        valor_pesquisa = row.get(coluna_busca)
        if progress_callback:
            progress_callback(idx + 1, total, str(valor_pesquisa))

        if pd.isna(valor_pesquisa) or str(valor_pesquisa).strip() == "":
            l = row.to_dict()
            l.update({c: "VAZIO" for c in cols_add})
            novas_linhas.append(l)
            continue

        regs = buscar_sicar_completo(var_payload, valor_pesquisa, token, url)

        if not regs:
            l = row.to_dict()
            l.update({c: "NAO ENCONTRADO" for c in cols_add})
            novas_linhas.append(l)
        else:
            todos_brutos.extend(regs)
            for reg in regs:
                l = row.to_dict()
                for c_raw in campos_selecionados:
                    if c_raw in mapa_chaves_nomes:
                        l[mapa_chaves_nomes[c_raw]] = reg.get(c_raw, "N/A")
                novas_linhas.append(l)
        time.sleep(0.3)

    return pd.DataFrame(novas_linhas), todos_brutos
