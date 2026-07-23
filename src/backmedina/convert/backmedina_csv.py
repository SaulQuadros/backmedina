"""Exportação para CSV compatível com o BackMeDiNa.

Formato (Franco et al., 2018; ver Machado, 2019, Fig. 2.14):
  linha 1: BACKMEDINA
  linha 2: SEÇÃO: <nome>
  linha 3: RAIO (cm): 15
  linha 4: cabeçalho das colunas
  linha 5+: dados (uma linha por estação)

Deflexões em 0,01 mm; carga em kgf. As colunas d0..d180 vêm de D1..D9 do
levantamento SOLOCAP (D10 é descartado).
"""

from __future__ import annotations

import csv
import io
import zipfile

import pandas as pd

from backmedina.model.schema import (
    BACKMEDINA_HEADER,
    BACKMEDINA_MARCADOR,
    D_TO_SENSOR,
    RAIO_PLACA_CM,
    SENSOR_LABELS,
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
    """Rótulo BackMeDiNa 'd0'..'d180' -> coluna SOLOCAP 'D1'..'D9'."""
    return {v: k for k, v in D_TO_SENSOR.items()}[label]


def _serie_ou_default(df: pd.DataFrame, col: str, default) -> pd.Series:
    n = len(df)
    if col in df.columns:
        return df[col].reset_index(drop=True)
    if callable(default):
        return pd.Series(default(n))
    return pd.Series([default] * n)


def montar_dataframe_backmedina(dados: DadosFWD) -> pd.DataFrame:
    """Constrói o DataFrame na ordem exata de BACKMEDINA_HEADER."""
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
        else _serie_ou_default(df, "Estaca – Deslocamento", 0)
    )

    saida = pd.DataFrame(
        {
            "Data de Execução": data_exec.reset_index(drop=True),
            "Temp. Do Ar": pd.Series(temp_ar).reset_index(drop=True),
            "Temp. Do Pavimento": pd.Series(temp_pav).reset_index(drop=True),
            "Carga": df.apply(_valor_carga_kgf, axis=1).reset_index(drop=True),
            "Estaca – Número": pd.Series(estaca_num).reset_index(drop=True),
            "Estaca – Deslocamento": pd.Series(estaca_desl).reset_index(drop=True),
            "Estaca – Faixa": _serie_ou_default(df, "Estaca – Faixa", 0),
            "Estaca – Trilha": _serie_ou_default(df, "Estaca – Trilha", 0),
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

    for label in SENSOR_LABELS:
        dcol = _sensor_para_d(label)
        if label in tem:
            saida[label] = df[label].map(_defl)
        elif dcol in tem:
            saida[label] = df[dcol].map(_defl)
        else:
            saida[label] = ""

    # Normaliza numéricos de temperatura/estaca.
    for col in ("Temp. Do Ar", "Temp. Do Pavimento", "Estaca – Deslocamento"):
        saida[col] = saida[col].map(_num)

    return saida[list(BACKMEDINA_HEADER)]


def exportar_csv_backmedina(dados: DadosFWD, secao: str | None = None) -> str:
    """Gera o texto do CSV BackMeDiNa (com cabeçalho de 3 linhas)."""
    df = montar_dataframe_backmedina(dados)
    nome_secao = secao or dados.metadados.secao()

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=",", lineterminator="\n")
    writer.writerow([BACKMEDINA_MARCADOR])
    writer.writerow([f"SEÇÃO: {nome_secao}"])
    writer.writerow([f"RAIO (cm): {RAIO_PLACA_CM}"])
    writer.writerow(list(BACKMEDINA_HEADER))
    for _, row in df.iterrows():
        writer.writerow(list(row.values))
    return buf.getvalue()


def csvs_por_segmento(
    dados: DadosFWD, df_segmentado: pd.DataFrame, coluna_segmento: str = "Segmento"
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
        arquivos[f"{nome}.csv"] = exportar_csv_backmedina(sub_dados, secao=nome)
    return arquivos


def zip_de_arquivos(arquivos: dict[str, str | bytes]) -> bytes:
    """Empacota ``{nome: conteúdo}`` num ZIP (bytes). Conteúdo str ou bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome, conteudo in arquivos.items():
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
