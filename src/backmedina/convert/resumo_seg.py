"""Planilha-resumo da segmentação (Resumo_Seg.xlsx), no padrão ConversorDadosFWD.

Colunas: Segmento, Estacas (m), Comprimento (m), Dm, σ, Dc — com a legenda:
  Dm = Deflexão média · σ = Desvio padrão · Dc = Deflexão característica (Dm + σ).
Valores de deflexão em 0,01 mm (unidade dos cálculos / do MeDiNa).
"""

from __future__ import annotations

import io

from openpyxl import Workbook


def resumo_seg_xlsx_bytes(segmentos, desvio_label: str = "Amostral (n−1)") -> bytes:
    """Gera o Resumo_Seg.xlsx (bytes) a partir da lista de `Segmento`."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Resumo_Seg"

    ws.append(["RESUMO DA SEGMENTAÇÃO"])
    ws.append([f"Deflexões em 0,01 mm · σ: {desvio_label}"])
    ws.append([])
    ws.append(
        ["Segmento", "Estacas (m)", "Comprimento (m)", "Dm", "σ", "Dc"]
    )
    for s in segmentos:
        ws.append(
            [
                f"seg_{s.indice:02d}",
                f"{s.ini_m:g}–{s.fim_m:g}",
                round(s.comprimento_m, 2),
                round(s.d0_media, 2),
                round(s.d0_desvio, 2),
                round(s.d0_caracteristica, 2),
            ]
        )
    ws.append([])
    ws.append(["Dm = Deflexão média"])
    ws.append(["σ = Desvio padrão"])
    ws.append(["Dc = Deflexão característica (Dm + σ)"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
