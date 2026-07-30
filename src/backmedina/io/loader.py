"""Detecção de formato e carregamento unificado de dados FWD."""

from __future__ import annotations

from pathlib import Path

from backmedina.io.csv_bacias import ler_csv_bacias
from backmedina.io.xlsx_kuab import e_planilha_kuab, ler_kuab_xlsx
from backmedina.io.xlsx_solocap import ler_solocap_xlsx
from backmedina.model.schema import DadosFWD


def carregar(caminho: str | Path) -> DadosFWD:
    """Carrega um arquivo FWD escolhendo o leitor pela extensão e pelo conteúdo.

    Suporta .xlsx (SOLOCAP ou KUAB), .csv (bacias) e .pdf (relatório SOLOCAP).
    Entre os .xlsx a escolha é por **conteúdo**: os layouts são incompatíveis
    (cabeçalho em linhas diferentes, outra nomenclatura de geofones e outra
    unidade), e ler um com o leitor do outro devolve uma tabela toda NaN.
    """
    caminho = Path(caminho)
    ext = caminho.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        if e_planilha_kuab(caminho):
            return ler_kuab_xlsx(caminho)
        return ler_solocap_xlsx(caminho)
    if ext == ".csv":
        return ler_csv_bacias(caminho)
    if ext == ".pdf":
        from backmedina.io.pdf_fwd import ler_pdf_fwd

        return ler_pdf_fwd(caminho)
    raise ValueError(f"Formato não suportado: {ext}")
