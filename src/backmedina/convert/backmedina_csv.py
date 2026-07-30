"""Exportação para CSV compatível com o BackMeDiNa.

Formato (Franco et al., 2018; ver Machado, 2019, Fig. 2.14), fiel ao arquivo
que o BackMeDiNa aceita — separador ';', CP1252, CRLF, todas as linhas
preenchidas até o nº total de colunas:

  linha 1: BACKMEDINA;;;…
  linha 2: SEÇÃO:;<nome>;;;…      <- rótulo e valor em células separadas
  linha 3: RAIO (cm):;15;;;…      <- idem
  linha 4: cabeçalho das colunas
  linha 5+: dados (uma linha por estação)

Deflexões em µm; carga em kgf. As colunas d0..d180 vêm de D1..D9 do
levantamento SOLOCAP e d210 de D10 (presente no CSV, fora dos cálculos).
"""

from __future__ import annotations

import csv
import io
import zipfile

import pandas as pd

from backmedina.model.schema import (
    BACKMEDINA_COL_CHAINAGE,
    BACKMEDINA_ENCODING,
    BACKMEDINA_EOL,
    BACKMEDINA_HEADER,
    BACKMEDINA_MARCADOR,
    BACKMEDINA_SENSOR_LABELS,
    BACKMEDINA_SEP,
    D_TO_SENSOR,
    RAIO_PLACA_CM,
    SENSOR_LABEL_EXTRA,
    DadosFWD,
)


def _valor_carga_kgf(row: pd.Series) -> object:
    """Carga em kgf: usa 'Target Load (Kgf)' se houver, senão 'Carga'."""
    for col in ("Target Load (Kgf)", "Carga"):
        if col in row and pd.notna(row[col]):
            return _num(row[col])
    return ""


def _num(v: object) -> object:
    """Formata número sem casas decimais espúrias (deflexões são inteiras)."""
    if v == "" or pd.isna(v):
        return ""
    f = float(v)
    return int(round(f)) if abs(f - round(f)) < 1e-9 else f


def _sensor_para_d(label: str) -> str:
    """Rótulo BackMeDiNa 'd0'..'d210' -> coluna SOLOCAP 'D1'..'D10'."""
    if label == SENSOR_LABEL_EXTRA:
        return "D10"  # geofone externo: só existe na saída CSV
    return {v: k for k, v in D_TO_SENSOR.items()}[label]


def _serie_ou_default(df: pd.DataFrame, col: str, default) -> pd.Series:
    n = len(df)
    if col in df.columns:
        return df[col].reset_index(drop=True)
    if callable(default):
        return pd.Series(default(n))
    return pd.Series([default] * n)


def _coluna_estaca(df: pd.DataFrame, col: str, valor: int | None) -> pd.Series:
    """Faixa/Trilha: valor informado pelo usuário vence; senão o do arquivo; senão 0.

    A planilha SOLOCAP não traz essas colunas — só o CSV de bacias traz. Quando
    nenhuma das duas fontes existe, o BackMeDiNa aceita 0.
    """
    if valor is not None:
        return pd.Series([valor] * len(df))
    return _serie_ou_default(df, col, 0)


def valores_estaca_do_arquivo(dados: DadosFWD) -> tuple[int, int]:
    """(faixa, trilha) lidos do arquivo de entrada — 0 quando ausentes.

    Serve de valor inicial para os campos da UI. Se a coluna existir mas variar
    entre estações, devolve o valor da primeira (a UI aplica um valor único).
    """
    df = dados.tabela
    out = []
    for col in ("Estaca – Faixa", "Estaca – Trilha"):
        if col in df.columns and len(df):
            try:
                out.append(int(float(df[col].iloc[0])))
                continue
            except (TypeError, ValueError):
                pass
        out.append(0)
    return out[0], out[1]


def montar_dataframe_backmedina(
    dados: DadosFWD, faixa: int | None = None, trilha: int | None = None
) -> pd.DataFrame:
    """Constrói o DataFrame na ordem exata de BACKMEDINA_HEADER.

    ``faixa``/``trilha``: valor único aplicado a todas as estações (vem da UI).
    ``None`` mantém o que houver no arquivo de entrada.
    """
    df = dados.tabela.reset_index(drop=True)
    n = len(df)
    tem = set(df.columns)

    # Data de Execução: da coluna SOLOCAP "Data e Hora" (só a data) ou direta.
    if "Data e Hora" in tem:
        data_exec = df["Data e Hora"].map(
            lambda v: str(v).split(" ")[0] if v not in ("", None) else ""
        )
    else:
        data_exec = _serie_ou_default(df, "Data de Execução", "")

    temp_ar = (
        df["Temp Ar (°C)"] if "Temp Ar (°C)" in tem
        else _serie_ou_default(df, "Temp. Do Ar", "")
    )
    temp_pav = (
        df["Temp Pav (°C)"] if "Temp Pav (°C)" in tem
        else _serie_ou_default(df, "Temp. Do Pavimento", "")
    )
    estaca_num = (
        df["Estaca – Número"] if "Estaca – Número" in tem
        else pd.Series(range(1, n + 1))
    )
    estaca_desl = (
        df["Metros"] if "Metros" in tem
        else _serie_ou_default(df, BACKMEDINA_COL_CHAINAGE, 0)
    )

    saida = pd.DataFrame(
        {
            "Data de Execução": data_exec.reset_index(drop=True),
            "Temp. Do Ar": pd.Series(temp_ar).reset_index(drop=True),
            "Temp. Do Pavimento": pd.Series(temp_pav).reset_index(drop=True),
            "Carga": df.apply(_valor_carga_kgf, axis=1).reset_index(drop=True),
            "Estaca – Número": pd.Series(estaca_num).reset_index(drop=True),
            BACKMEDINA_COL_CHAINAGE: pd.Series(estaca_desl).reset_index(drop=True),
            "Estaca – Faixa": _coluna_estaca(df, "Estaca – Faixa", faixa),
            "Estaca – Trilha": _coluna_estaca(df, "Estaca – Trilha", trilha),
        }
    )

    # Deflexões d0..d180 a partir de D1..D9 (ou já rotuladas d0..d180),
    # CONVERTIDAS para µm (exigência do BackMeDiNa). Origem 0,01 mm -> ×10;
    # origem já em µm -> ×1.
    fator = dados.unidade_deflexao.fator_para_micrometro

    def _defl(v):
        if v == "" or pd.isna(v):
            return ""
        return _num(float(v) * fator)

    for label in BACKMEDINA_SENSOR_LABELS:
        dcol = _sensor_para_d(label)
        if label in tem:
            serie = df[label].map(_defl)
        elif dcol in tem:
            serie = df[dcol].map(_defl)
        else:
            serie = pd.Series([""] * n)
        if label == SENSOR_LABEL_EXTRA:
            # Equipamentos sem o 10º geofone (KUAB) deixariam d210 vazio. No
            # arquivo de referência nenhuma célula numérica vem vazia, e d210
            # não entra em cálculo algum — 0 é inerte e não arrisca o "ERRO 1".
            serie = serie.replace("", "0")
        saida[label] = serie

    # Normaliza numéricos de temperatura/estaca. "Estaca – Número" entra aqui
    # porque fontes que a trazem (KUAB, CSV de bacias) a entregam como float, e
    # sairia "0.0" onde o importador espera "0".
    for col in (
        "Temp. Do Ar",
        "Temp. Do Pavimento",
        "Estaca – Número",
        BACKMEDINA_COL_CHAINAGE,
        "Estaca – Faixa",
        "Estaca – Trilha",
    ):
        saida[col] = saida[col].map(_num)

    return saida[list(BACKMEDINA_HEADER)]


def _preencher(campos: list, n: int) -> list:
    """Completa a linha com células vazias até `n` colunas.

    O importador do BackMeDiNa exige que TODAS as linhas — inclusive as três de
    cabeçalho — tenham o mesmo número de campos.
    """
    return list(campos) + [""] * (n - len(campos))


def exportar_csv_backmedina(
    dados: DadosFWD,
    secao: str | None = None,
    faixa: int | None = None,
    trilha: int | None = None,
) -> str:
    """Gera o texto do CSV BackMeDiNa (com cabeçalho de 3 linhas)."""
    df = montar_dataframe_backmedina(dados, faixa=faixa, trilha=trilha)
    nome_secao = secao or dados.metadados.secao()
    n = len(BACKMEDINA_HEADER)

    buf = io.StringIO()
    writer = csv.writer(
        buf, delimiter=BACKMEDINA_SEP, lineterminator=BACKMEDINA_EOL
    )
    writer.writerow(_preencher([BACKMEDINA_MARCADOR], n))
    writer.writerow(_preencher(["SEÇÃO:", nome_secao], n))
    writer.writerow(_preencher(["RAIO (cm):", RAIO_PLACA_CM], n))
    writer.writerow(list(BACKMEDINA_HEADER))
    for _, row in df.iterrows():
        writer.writerow(list(row.values))
    return buf.getvalue()


def exportar_csv_backmedina_bytes(
    dados: DadosFWD,
    secao: str | None = None,
    faixa: int | None = None,
    trilha: int | None = None,
) -> bytes:
    """CSV BackMeDiNa já codificado em CP1252 — use isto para gravar/baixar.

    O importador do BackMeDiNa (Windows/ANSI) não lê UTF-8: acentos de
    "Execução"/"Número" e o travessão "–" das colunas chegam corrompidos e o
    arquivo é rejeitado com "ERRO 1 — Problemas ao abrir o arquivo".
    """
    return codificar_backmedina(
        exportar_csv_backmedina(dados, secao=secao, faixa=faixa, trilha=trilha)
    )


def codificar_backmedina(texto: str) -> bytes:
    """Codifica o texto do CSV em CP1252 (ANSI Windows), como espera o app."""
    return texto.encode(BACKMEDINA_ENCODING, errors="replace")


def csvs_por_segmento(
    dados: DadosFWD,
    df_segmentado: pd.DataFrame,
    coluna_segmento: str = "Segmento",
    faixa: int | None = None,
    trilha: int | None = None,
) -> dict[str, str]:
    """Gera um CSV BackMeDiNa por segmento adotado.

    ``df_segmentado`` é o DataFrame produzido pela segmentação (contém a coluna
    ``Segmento`` além das colunas originais do levantamento). Retorna um dicionário
    ``{"seg_01.csv": texto, "seg_02.csv": texto, ...}`` — cada CSV com as estações
    daquele trecho, deflexões em **µm** e cabeçalho `SEÇÃO: seg_NN`.
    """
    from backmedina.model.schema import DadosFWD as _DadosFWD

    arquivos: dict[str, str] = {}
    labels = sorted(
        int(s) for s in pd.unique(df_segmentado[coluna_segmento]) if int(s) > 0
    )
    for s in labels:
        sub = df_segmentado[df_segmentado[coluna_segmento] == s].reset_index(
            drop=True
        )
        nome = f"seg_{s:02d}"
        sub_dados = _DadosFWD(
            metadados=dados.metadados,
            tabela=sub,
            origem=dados.origem,
            unidade_deflexao=dados.unidade_deflexao,
        )
        arquivos[f"{nome}.csv"] = exportar_csv_backmedina(
            sub_dados, secao=nome, faixa=faixa, trilha=trilha
        )
    return arquivos


def zip_de_arquivos(arquivos: dict[str, str | bytes]) -> bytes:
    """Empacota ``{nome: conteúdo}`` num ZIP (bytes). Conteúdo str ou bytes.

    Conteúdo em ``str`` é codificado em CP1252 — ``zipfile.writestr`` usaria
    UTF-8 por padrão, o que quebraria os CSVs no BackMeDiNa.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome, conteudo in arquivos.items():
            if isinstance(conteudo, str):
                conteudo = codificar_backmedina(conteudo)
            zf.writestr(nome, conteudo)
    return buf.getvalue()


def descricao_conversao_micrometro(dados: DadosFWD) -> str:
    """Texto legível (pt-BR) da conversão de unidade aplicada na exportação."""
    fator = dados.unidade_deflexao.fator_para_micrometro
    origem = dados.unidade_deflexao.rotulo
    if fator == 1.0:
        return f"Unidade detectada: {origem} — já em µm, sem conversão."
    return (
        f"Unidade detectada: {origem} → CSV BackMeDiNa em µm "
        f"(deflexões × {fator:g})."
    )
