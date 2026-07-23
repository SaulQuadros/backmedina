"""Detecção de formato e carregamento unificado de dados FWD."""

from __future__ import annotations

from pathlib import Path

from backmedina.io.csv_bacias import ler_csv_bacias
from backmedina.io.xlsx_solocap import ler_solocap_xlsx
from backmedina.model.schema import DadosFWD


def carregar(caminho: str | Path) -> DadosFWD:
    """Carrega um arquivo FWD escolhendo o leitor pela extensão.

    Suporta .xlsx (SOLOCAP) e .csv (bacias). PDF será adicionado na Fase 2.
    """
    caminho = Path(caminho)
    ext = caminho.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        return ler_solocap_xlsx(caminho)
    if ext == ".csv":
        return ler_csv_bacias(caminho)
    if ext == ".pdf":
        from backmedina.io.pdf_fwd import ler_pdf_fwd

        return ler_pdf_fwd(caminho)
    raise ValueError(f"Formato não suportado: {ext}")
