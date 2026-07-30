"""Extração da tabela de um relatório FWD em PDF (SOLOCAP/SWECO) -> DadosFWD.

Estratégia: usa o texto com layout preservado (`pdftotext -layout`, do poppler)
e faz um parsing posicional das linhas de dados. Cada linha de dados termina em
`dd/mm/yyyy HH:MM`, o que serve de âncora robusta para separar os 18 campos
numéricos (à esquerda) da coluna Obs (à direita).

Layout dos 18 campos numéricos (à esquerda da data/hora):
  Metros, Target Load kN, Target Load (Kgf), D1..D10, Temp Ar, Temp Pav,
  Latitude, Longitude, Raio.

Requisito de sistema: `pdftotext` (pacote poppler-utils). Em deploy, ver
`packages.txt` / `Dockerfile`.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd

from backmedina.io.br_numbers import parse_br_number
from backmedina.model.schema import (
    COLUNAS_NUMERICAS,
    COLUNAS_TABELA,
    MetadadosLevantamento,
    DadosFWD,
)
from backmedina.model.units import UnidadeDeflexao, detectar_unidade_explicita

# Âncora: data (dd/mm/aaaa) + hora (H:MM ou HH:MM) no fim da linha de dados.
_DATA_HORA = re.compile(r"(\d{2}/\d{2}/\d{4})\s+(\d{1,2}:\d{2})")

# Metadados: "CHAVE: valor" (o valor pode estar na mesma linha ou não).
_META_PATTERNS = {
    # No layout, um texto de título separa "DATA:" da data — busca a 1ª data
    # completa após "DATA:" (a data do relatório, ex.: 16/11/2023).
    "data": re.compile(r"DATA:.*?(\d{2}/\d{2}/\d{4})", re.S),
    "relatorio": re.compile(r"RELAT[ÓO]RIO\s*N[°º]:\s*([^\n]+?)\s*$", re.M),
    "os_numero": re.compile(r"OS\s*N[°º]:\s*([^\n]+?)\s*$", re.M),
    "cliente": re.compile(r"CLIENTE:\s*([^\n]+?)\s*$", re.M),
    "obra_trecho": re.compile(r"OBRA/TRECHO:\s*([^\n]+?)\s*$", re.M),
    "pista": re.compile(r"PISTA:\s*([^\n]+?)\s*$", re.M),
    "sentido": re.compile(r"SENTIDO:\s*([^\n]+?)\s*$", re.M),
}

# Ordem dos 18 campos numéricos à esquerda da data/hora.
_CAMPOS_NUM = (
    "Metros", "Target Load kN", "Target Load (Kgf)",
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10",
    "Temp Ar (°C)", "Temp Pav (°C)", "Latitude", "Longitude", "Raio",
)
_N_CAMPOS = len(_CAMPOS_NUM)  # 18


def extrair_texto_layout(caminho: str | Path) -> str:
    """Extrai o texto do PDF preservando o layout (via pdftotext -layout)."""
    if shutil.which("pdftotext") is None:
        raise RuntimeError(
            "pdftotext (poppler-utils) não encontrado. Instale poppler-utils "
            "(Linux: apt install poppler-utils) para ler PDFs FWD."
        )
    out = subprocess.run(
        ["pdftotext", "-layout", str(caminho), "-"],
        capture_output=True,
        check=True,
    )
    return out.stdout.decode("utf-8", errors="replace")


def _parse_metadados(texto: str) -> MetadadosLevantamento:
    meta = MetadadosLevantamento()
    for attr, pat in _META_PATTERNS.items():
        m = pat.search(texto)
        if m:
            setattr(meta, attr, m.group(1).strip())
    return meta


def parse_linhas_dados(texto: str) -> tuple[list[dict], list[str]]:
    """Percorre as linhas do texto e devolve (registros, avisos)."""
    registros: list[dict] = []
    avisos: list[str] = []
    for linha in texto.splitlines():
        if not linha.strip():
            continue
        m = _DATA_HORA.search(linha)
        if not m:
            continue
        prefixo = linha[: m.start()].split()
        # Primeiro token precisa ser numérico (Metros) — filtra cabeçalhos.
        if not prefixo:
            continue
        primeiro = parse_br_number(prefixo[0])
        if primeiro != primeiro:  # NaN -> não é linha de dados
            continue

        obs = linha[m.end():].strip()
        reg: dict[str, object] = {c: "" for c in COLUNAS_TABELA}
        reg["Data e Hora"] = f"{m.group(1)} {m.group(2)}"
        reg["Obs"] = obs

        if len(prefixo) == _N_CAMPOS:
            campos = prefixo
        elif len(prefixo) == _N_CAMPOS - 1:
            # Sem a coluna Raio: preenche Raio como vazio.
            campos = prefixo[:17] + [""]
            avisos.append(
                f"Linha em {prefixo[0]} sem coluna Raio — preenchida como vazia."
            )
        else:
            avisos.append(
                f"Linha ignorada (esperados {_N_CAMPOS} campos numéricos, "
                f"achados {len(prefixo)}): {linha.strip()[:60]}…"
            )
            continue

        for nome, token in zip(_CAMPOS_NUM, campos):
            reg[nome] = parse_br_number(token) if token != "" else float("nan")
        registros.append(reg)

    return registros, avisos


def ler_pdf_fwd(caminho: str | Path) -> DadosFWD:
    """Lê um relatório FWD em PDF e devolve :class:`DadosFWD`."""
    caminho = Path(caminho)
    texto = extrair_texto_layout(caminho)
    metadados = _parse_metadados(texto)
    registros, avisos = parse_linhas_dados(texto)

    df = pd.DataFrame(registros, columns=list(COLUNAS_TABELA))
    # Garante dtype numérico nas colunas numéricas (já são float/parse).
    for col in COLUNAS_NUMERICAS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if df.empty:
        avisos.append("Nenhuma linha de dados reconhecida no PDF.")

    # Só registra a unidade no metadado quando ela foi de fato DECLARADA no PDF;
    # preencher com o padrão faria a UI acreditar que o arquivo se identificou.
    declarada = detectar_unidade_explicita(texto)  # SOLOCAP traz "x10⁻² mm"
    unidade = declarada or UnidadeDeflexao.DMM_001
    if not metadados.unidade and declarada is not None:
        metadados.unidade = declarada.rotulo

    return DadosFWD(
        metadados=metadados,
        tabela=df,
        origem=caminho.name,
        avisos=avisos,
        unidade_deflexao=unidade,
    )
