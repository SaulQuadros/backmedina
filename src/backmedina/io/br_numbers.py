"""Parsing de números em formato brasileiro (vírgula decimal, ponto de milhar).

Nos arquivos SOLOCAP os números vêm como texto:
  "4.059"     -> 4059.0    (ponto = separador de milhar)
  "-21,77314" -> -21.77314 (vírgula = separador decimal)
  "0,00"      -> 0.0
  "2.080,00"  -> 2080.0
"""

from __future__ import annotations

import math
import re

import pandas as pd

_NUM_RE = re.compile(r"^[+-]?[\d.]*\d(?:,\d+)?$")


def parse_br_number(value: object) -> float:
    """Converte um valor em formato numérico BR para float.

    Aceita já-numéricos (int/float) e strings BR. Retorna ``math.nan`` para
    vazios/inválidos, de forma a não interromper o processamento em lote.
    """
    if value is None:
        return math.nan
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    if not s:
        return math.nan

    # Caso comum: "1.234,56" -> remove pontos de milhar, vírgula vira ponto.
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        # Sem vírgula: pontos são milhar SE seguirem o padrão de 3 dígitos
        # ("4.059", "2.080"); caso contrário assume ponto decimal ("162.0").
        if re.fullmatch(r"[+-]?\d{1,3}(\.\d{3})+", s):
            s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return math.nan


def parse_br_series(series: pd.Series) -> pd.Series:
    """Aplica :func:`parse_br_number` a uma coluna inteira do pandas."""
    return series.map(parse_br_number).astype("float64")
