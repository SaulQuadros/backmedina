"""Deflexão característica de um trecho homogêneo (procedimento MeDiNa).

D_c = Dm + σ, onde Dm = deflexão média (D0) e σ = desvio-padrão. O desvio pode
ser **amostral** (ddof=1, n−1) ou **populacional** (ddof=0, n) — o
ConversorDadosFWD oferece as duas opções. Referência: Machado (2019), §4.2.3.
"""

from __future__ import annotations

import numpy as np


def deflexao_caracteristica(d0_valores, ddof: int = 1) -> float:
    """Retorna D_c = média + desvio-padrão das deflexões máximas.

    ``ddof=1`` (padrão) usa desvio amostral (n−1); ``ddof=0`` usa populacional (n).
    """
    arr = np.asarray(d0_valores, dtype=float)
    arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        return float("nan")
    media = float(np.mean(arr))
    desvio = float(np.std(arr, ddof=ddof)) if arr.size > ddof else 0.0
    return media + desvio
