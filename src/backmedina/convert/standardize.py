"""Geração da planilha padronizada "Tabela" (formato Modelo.xlsx).

Reproduz o layout SOLOCAP: bloco de metadados (linhas 1-10) + cabeçalho das
colunas (linha 13) + dados (linha 14+). Serve como saída fiel ao .exe original.
"""

from __future__ import annotations

import io

import pandas as pd
from openpyxl import Workbook

from backmedina.model.schema import (
    ABA_TABELA,
    COLUNAS_TABELA,
    UNIDADE_DEFLEXAO,
    DadosFWD,
)


def _linhas_metadados(dados: DadosFWD) -> list[tuple[str, str]]:
    m = dados.metadados
    return [
        ("DATA", m.data),
        ("RELATÓRIO N°", m.relatorio),
        ("OS Nº", m.os_numero),
        ("CLIENTE", m.cliente),
        ("OBRA/TRECHO", m.obra_trecho),
        ("PISTA", m.pista),
        ("SENTIDO", m.sentido),
        ("UNIDADE DAS LEITURAS", f"UNIDADE DAS LEITURAS ({UNIDADE_DEFLEXAO})"),
    ]


def montar_workbook(dados: DadosFWD) -> Workbook:
    """Monta o Workbook openpyxl com a aba "Tabela" padronizada."""
    wb = Workbook()
    ws = wb.active
    ws.title = ABA_TABELA

    ws.cell(1, 1, "LEVANTAMENTO DEFLECTOMÉTRICO (FWD) — Tabela extraída do PDF")
    for i, (chave, valor) in enumerate(_linhas_metadados(dados), start=3):
        ws.cell(i, 1, chave)
        ws.cell(i, 2, valor)

    # Cabeçalho das colunas na linha 13.
    for c, nome in enumerate(COLUNAS_TABELA, start=1):
        ws.cell(13, c, nome)

    # Dados a partir da linha 14, respeitando a ordem de COLUNAS_TABELA.
    df: pd.DataFrame = dados.tabela
    for r, (_, row) in enumerate(df.iterrows(), start=14):
        for c, nome in enumerate(COLUNAS_TABELA, start=1):
            valor = row[nome] if nome in df.columns else ""
            if pd.isna(valor):
                valor = ""
            ws.cell(r, c, valor)
    return wb


def exportar_xlsx_bytes(dados: DadosFWD) -> bytes:
    """Serializa a planilha padronizada em bytes (para download no Streamlit)."""
    wb = montar_workbook(dados)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
