"""Área da bacia de deflexão — variável alternativa para a segmentação.

Integral trapezoidal das deflexões sobre as distâncias radiais dos geofones
(0 a 180 cm, D1..D9 do mapa de sensores):

    A_bacia(x) = ∫ D(r) dr

Serve como variável de segmentação que usa **todos os sensores**, no lugar da
deflexão máxima D0 isolada. Duas estações com o mesmo D0 e bacias diferentes
produzem áreas diferentes — é essa a informação que D0 sozinho não carrega.

**Não confundir com o índice `AREA`** de `pbd_indices`: aquele é a área
normalizada de Hoffman/AASHTO (dividida por D0, em cm), que descreve só a FORMA
da bacia; esta aqui preserva também o NÍVEL das deflexões.

Por que a integral e não a média dos 9 sensores: os geofones não são
equiespaçados (0, 20, 30, 45, 60, 90, 120, 150, 180 cm) — quatro deles nos
primeiros 45 cm. Uma média simples superponderaria a região próxima da carga; a
regra do trapézio pondera pelo espaçamento real.

Unidade: a função **não normaliza** as deflexões. A área sai na unidade da
fonte multiplicada por cm (µm·cm ou 0,01 mm·cm). Como a área é linear nas
deflexões, o mesmo `unidade` que a segmentação usa para normalizar D0 também
normaliza a área corretamente.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backmedina.model.schema import D_TO_SENSOR, SENSOR_OFFSETS_CM

COLUNA_AREA_BACIA: str = "Area_bacia"


def area_da_bacia(df: pd.DataFrame) -> pd.Series:
    """Área sob a bacia de deflexão de cada estação (unidade da fonte × cm).

    Usa os sensores presentes em ``df`` (D1..D9). Estações com qualquer geofone
    ausente resultam em NaN — a segmentação já descarta esses pontos.
    """
    colunas = [d for d in D_TO_SENSOR if d in df.columns]
    if len(colunas) < 2:
        return pd.Series(np.full(len(df), np.nan), index=df.index)

    offsets = np.array(
        [SENSOR_OFFSETS_CM[list(D_TO_SENSOR).index(c)] for c in colunas], dtype=float
    )
    valores = df[colunas].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    return pd.Series(np.trapezoid(valores, offsets, axis=1), index=df.index)


def com_area_da_bacia(df: pd.DataFrame) -> pd.DataFrame:
    """Cópia de ``df`` com a coluna :data:`COLUNA_AREA_BACIA` acrescentada."""
    out = df.copy()
    out[COLUNA_AREA_BACIA] = area_da_bacia(df)
    return out
