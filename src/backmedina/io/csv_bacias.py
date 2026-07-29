"""Leitura do CSV de bacias (template Modelo_Arquivo_Bacias.csv) -> DadosFWD.

Formato: separado por ';', CP1252, com uma 1ª linha em branco (";;;..."),
depois o cabeçalho e as linhas de dados. Deflexões já vêm rotuladas d0..d180.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from backmedina.io.br_numbers import parse_br_series
from backmedina.model.schema import (
    BACKMEDINA_SENSOR_LABELS,
    CSV_BACIAS_ENCODING,
    CSV_BACIAS_SEP,
    SENSOR_LABELS,
    SENSOR_TO_D,
    MetadadosLevantamento,
    DadosFWD,
)
from backmedina.model.units import UnidadeDeflexao


def _achar_linha_header(linhas: list[str]) -> int:
    """Índice da linha de cabeçalho (a que contém 'd0' como campo)."""
    for i, linha in enumerate(linhas):
        campos = [c.strip().lower() for c in linha.split(CSV_BACIAS_SEP)]
        if "d0" in campos:
            return i
    return 0


def ler_csv_bacias(caminho: str | Path) -> DadosFWD:
    """Lê o CSV de bacias e devolve :class:`DadosFWD`.

    A tabela resultante usa os rótulos ``d0..d180`` como colunas de deflexão
    (mais as colunas de estaca/carga/temperatura do template).
    """
    caminho = Path(caminho)
    texto = caminho.read_text(encoding=CSV_BACIAS_ENCODING, errors="replace")
    linhas = [l for l in texto.splitlines()]
    inicio = _achar_linha_header(linhas)

    from io import StringIO

    conteudo = "\n".join(linhas[inicio:])
    df = pd.read_csv(
        StringIO(conteudo),
        sep=CSV_BACIAS_SEP,
        dtype=str,
        keep_default_na=False,
    )
    df.columns = [c.strip() for c in df.columns]

    # Normaliza colunas de deflexão para número. Inclui o d210 opcional, que
    # existe no CSV do BackMeDiNa mas não entra nos cálculos — sem isto ele
    # voltaria como texto e quebraria o round-trip (ler CSV -> exportar CSV).
    for label in BACKMEDINA_SENSOR_LABELS:
        if label in df.columns:
            df[label] = parse_br_series(df[label])
    for col in ("Temp. Do Ar", "Temp. Do Pavimento", "Carga"):
        if col in df.columns:
            df[col] = parse_br_series(df[col])

    # Deriva colunas D1..D10 a partir das deflexões d0..d180, para reaproveitar
    # os módulos de analytics/segmentação que trabalham com D1..D10.
    for label, dcol in ((l, SENSOR_TO_D[l]) for l in SENSOR_LABELS):
        if label in df.columns:
            df[dcol] = df[label]

    # A posição métrica (chainage) do levantamento vem de "Estaca – Descolamento"
    # (grafia real do template de bacias — com "c"). A segmentação e o export
    # esperam a coluna "Metros"; derivamos aqui para reaproveitar o mesmo pipeline
    # do SOLOCAP. Sem isto, a segmentação cai no fallback da 1ª coluna (a data) e
    # o export escreve "Estaca – Deslocamento" = 0.
    _COL_CHAINAGE = "Estaca – Descolamento"
    if _COL_CHAINAGE in df.columns and "Metros" not in df.columns:
        df["Metros"] = parse_br_series(df[_COL_CHAINAGE])

    metadados = MetadadosLevantamento(
        unidade=UnidadeDeflexao.MICROMETRO.rotulo
    )
    avisos: list[str] = []
    if df.empty:
        avisos.append("Nenhuma linha de dados encontrada no CSV de bacias.")

    # O CSV de bacias é o próprio formato do BackMeDiNa: deflexões já em µm.
    return DadosFWD(
        metadados=metadados,
        tabela=df,
        origem=caminho.name,
        avisos=avisos,
        unidade_deflexao=UnidadeDeflexao.MICROMETRO,
    )
