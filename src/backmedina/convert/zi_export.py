"""Exportação da tabela de cálculo de Zi (diferenças acumuladas) para XLSX."""

from __future__ import annotations

import io
import math

from openpyxl import Workbook


def _cel(v):
    """Converte NaN -> None (célula vazia); mantém números/texto."""
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):  # numpy scalar
        v = v.item()
    return v


def zi_xlsx_bytes(tabela, totais: dict) -> bytes:
    """Serializa a tabela de Zi + totais (A_c, L_c, tan_alpha) em XLSX (bytes)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Calculo_Zi"

    ws.append(list(tabela.columns))
    for _, row in tabela.iterrows():
        ws.append([_cel(v) for v in row])

    ws.append([])
    ws.append(["A_c (área acumulada total)", round(totais["A_c"], 2)])
    ws.append(["L_c (comprimento total, m)", round(totais["L_c"], 2)])
    ws.append(["tan α = A_c / L_c", round(totais["tan_alpha"], 4)])
    ws.append([])
    ws.append([
        "D0 em 0,01 mm. Zi = ΣAᵢ − tanα·ΣΔlᵢ (unidade de área: 0,01 mm·m). "
        "Vértices de Zi = fronteiras de trechos homogêneos."
    ])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
