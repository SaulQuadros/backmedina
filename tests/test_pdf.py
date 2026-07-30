import shutil
from pathlib import Path

import pandas as pd
import pytest

from backmedina.io.pdf_fwd import ler_pdf_fwd, parse_linhas_dados
from backmedina.io.xlsx_solocap import ler_solocap_xlsx

RAIZ = Path(__file__).resolve().parents[1]
PDF = RAIZ / "z_docs" / "lwd" / "solocap" / "2-UFJF-VIA_LOCAL_FX1-FWD.pdf"
XLSX = RAIZ / "z_docs" / "lwd" / "solocap" / "2-UFJF-VIA_LOCAL_FX1-FWD.xlsx"

_sem_poppler = shutil.which("pdftotext") is None
pytestmark = pytest.mark.skipif(
    _sem_poppler or not PDF.exists(),
    reason="pdftotext (poppler) ausente ou PDF de exemplo ausente",
)

COLS = [
    "Metros", "Target Load kN", "Target Load (Kgf)",
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10",
    "Temp Ar (°C)", "Temp Pav (°C)", "Latitude", "Longitude", "Raio",
]


def test_pdf_bate_com_xlsx():
    pdf = ler_pdf_fwd(PDF)
    xls = ler_solocap_xlsx(XLSX)
    assert len(pdf.tabela) == len(xls.tabela) == 105
    a = pdf.tabela[COLS].reset_index(drop=True).astype(float)
    b = xls.tabela[COLS].reset_index(drop=True).astype(float)
    # Extração do PDF deve reproduzir exatamente os dados da planilha.
    assert (a - b).abs().max().max() == 0.0


def test_pdf_metadados():
    pdf = ler_pdf_fwd(PDF)
    assert pdf.metadados.cliente == "UNIVERSIDADE FEDERAL DE JUIZ DE FORA"
    assert pdf.metadados.data == "16/11/2023"
    assert pdf.metadados.os_numero == "500/23"


def test_pdf_data_hora_e_thousands():
    pdf = ler_pdf_fwd(PDF)
    # Estação com milhar no "Metros" (ex.: 2.080,00 -> 2080.0) parseada certo.
    assert pdf.tabela["Metros"].iloc[-1] == 2080.0
    assert pdf.tabela["Data e Hora"].iloc[0] == "11/09/2023 13:30"


def test_parse_linha_isolada():
    # Uma linha sintética no formato do relatório (18 numéricos + data/hora).
    linha = ("  0,00      40   4.059   44 29 21 13 9 6 4 3 3 2  "
             "36 41 -21,77314 -43,36878 162  11/09/2023 13:30")
    regs, avisos = parse_linhas_dados(linha)
    assert not avisos
    assert len(regs) == 1
    r = regs[0]
    assert r["D1"] == 44 and r["D9"] == 3 and r["Raio"] == 162
    assert r["Latitude"] == -21.77314
    assert r["Data e Hora"] == "11/09/2023 13:30"
