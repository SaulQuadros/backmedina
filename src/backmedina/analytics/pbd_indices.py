"""Parâmetros da Bacia Deflectométrica (PBD) — Rocha (2020).

Todas as deflexões em 0,01 mm. Entrada: DataFrame com colunas D1..D10
(SOLOCAP) OU d0..d180. Saída: DataFrame com os índices por estação.

Mapa: D0=D1, D20=D2, D30=D3, D45=D4, D60=D5, D90=D6, D120=D7, D150=D8, D180=D9.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backmedina.model.schema import D_TO_SENSOR
from backmedina.model.units import UnidadeDeflexao, fator_conversao


def _col(df: pd.DataFrame, offset_label: str) -> pd.Series:
    """Devolve a série de deflexão para um rótulo 'd0'..'d180'.

    Aceita DataFrames rotulados como D1..D10 (SOLOCAP) ou d0..d180.
    """
    if offset_label in df.columns:
        return pd.to_numeric(df[offset_label], errors="coerce")
    dcol = {v: k for k, v in D_TO_SENSOR.items()}[offset_label]  # d0->D1 ...
    return pd.to_numeric(df[dcol], errors="coerce")


def calcular_indices(
    df: pd.DataFrame,
    unidade: UnidadeDeflexao = UnidadeDeflexao.DMM_001,
) -> pd.DataFrame:
    """Calcula os índices PBD por estação.

    As fórmulas (em especial Rc, cuja constante 6250 embute a unidade) pressupõem
    deflexões em **0,01 mm**. Se os dados estiverem em outra unidade, informe
    ``unidade`` para que a normalização para 0,01 mm seja feita internamente.

    Retorna DataFrame com: Rc, AREA, SCI, BDI, BCI, CF, S (mesma ordem de linhas).
    """
    k = fator_conversao(unidade, UnidadeDeflexao.DMM_001)  # -> 0,01 mm
    d0 = _col(df, "d0") * k
    d20 = _col(df, "d20") * k
    d30 = _col(df, "d30") * k
    d60 = _col(df, "d60") * k
    d90 = _col(df, "d90") * k
    d120 = _col(df, "d120") * k

    # D25 interpolado (nenhum sensor a 25 cm).
    d25 = (d20 + d30) / 2.0

    # Rc (m): 6250 / [2*(D0 - D25)]. Evita divisão por zero.
    denom = 2.0 * (d0 - d25)
    rc = np.where(denom != 0, 6250.0 / denom, np.nan)

    # AREA (cm): 15 * [1 + 2*(D30/D0) + 2*(D60/D0) + (D90/D0)].
    with np.errstate(divide="ignore", invalid="ignore"):
        area = 15.0 * (1.0 + 2.0 * (d30 / d0) + 2.0 * (d60 / d0) + (d90 / d0))
        # S (%): média de (D0, D30, D60, D90, D120) normalizada por D0.
        s = (d0 + d30 + d60 + d90 + d120) / (5.0 * d0) * 100.0

    out = pd.DataFrame(
        {
            "Rc": rc,
            "AREA": area,
            "SCI": d0 - d30,
            "BDI": d30 - d60,
            "BCI": d60 - d90,
            "CF": d0 - d20,
            "S": s,
        }
    )
    return out


def indices_com_contexto(
    df: pd.DataFrame,
    unidade: UnidadeDeflexao = UnidadeDeflexao.DMM_001,
) -> pd.DataFrame:
    """Índices PBD concatenados à coluna 'Metros' (quando existir)."""
    idx = calcular_indices(df, unidade=unidade)
    if "Metros" in df.columns:
        return pd.concat([df[["Metros"]].reset_index(drop=True), idx], axis=1)
    return idx
