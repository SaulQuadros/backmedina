"""Checagens de qualidade dos dados FWD antes da conversão.

Não interrompe o fluxo: devolve uma lista de avisos (strings) para exibição.
"""

from __future__ import annotations

import pandas as pd

from backmedina.model.schema import D_TO_SENSOR, DadosFWD


def validar(dados: DadosFWD) -> list[str]:
    """Valida a tabela e retorna avisos legíveis (pt-BR)."""
    df = dados.tabela
    avisos: list[str] = list(dados.avisos)

    if df.empty:
        avisos.append("Tabela vazia — nada a validar.")
        return avisos

    dcols = [d for d in D_TO_SENSOR if d in df.columns]

    # Monotonicidade da bacia: D1 >= D2 >= ... (deflexão decai com a distância).
    if len(dcols) >= 2:
        vals = df[dcols].apply(pd.to_numeric, errors="coerce")
        nao_monot = (vals.diff(axis=1).iloc[:, 1:] > 0).any(axis=1)
        q = int(nao_monot.sum())
        if q:
            avisos.append(
                f"{q} estação(ões) com bacia não monotônica "
                "(deflexão aumenta com a distância) — verificar leituras."
            )

    # Faixa de carga (kgf) plausível.
    for col in ("Target Load (Kgf)", "Carga"):
        if col in df.columns:
            carga = pd.to_numeric(df[col], errors="coerce")
            fora = ((carga < 2000) | (carga > 12000)).sum()
            if fora:
                avisos.append(
                    f"{int(fora)} estação(ões) com carga fora de 2000–12000 kgf."
                )
            break

    # Deflexão central (D0) não pode ser zero/negativa.
    if "D1" in df.columns:
        d0 = pd.to_numeric(df["D1"], errors="coerce")
        ruins = ((d0 <= 0) | d0.isna()).sum()
        if ruins:
            avisos.append(f"{int(ruins)} estação(ões) com D0 (D1) nula/ausente.")

    return avisos
