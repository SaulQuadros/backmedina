"""Geração do relatório em PDF via lualatex + fontspec + TeX Gyre Pagella.

REGRA DE FONTES (crítica): usar SOMENTE lualatex/xelatex + fontspec — nunca
pdflatex+lmodern, que embute Type 1 (descontinuada pela Adobe em jan/2023, quebra
em leitores modernos). A Pagella (OpenType/CFF) é embutida como CID Type 0C.
Após compilar, `verificar_sem_type1` confirma que nenhuma fonte Type 1 entrou.
Formato 14×21 cm (miolo de livro).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from backmedina.report.comum import (
    RESUMO_CABECALHO,
    TITULO,
    legenda_resumo,
    linhas_rastreabilidade,
    linhas_resumo,
)

_ESPECIAIS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def esc(s) -> str:
    """Escapa caracteres especiais do LaTeX em texto dinâmico."""
    return "".join(_ESPECIAIS.get(ch, ch) for ch in str(s))


def _sigma(cel: str) -> str:
    """σ vira modo matemático (garante o glifo independente da fonte de texto)."""
    return r"$\sigma$" if cel.strip() == "σ" else esc(cel)


def _preambulo() -> str:
    return (
        "\\documentclass{article}\n"
        "\\usepackage[paperwidth=14cm,paperheight=21cm,margin=1.8cm]{geometry}\n"
        "\\usepackage{fontspec}\n"
        "\\usepackage{unicode-math}\n"
        "\\setmainfont{TeX Gyre Pagella}\n"
        # Fonte matemática OpenType (evita CMMI10 Type 1 em símbolos como σ).
        "\\setmathfont{TeX Gyre Pagella Math}\n"
        "\\usepackage{booktabs}\n"
        "\\usepackage{longtable}\n"
        "\\usepackage{graphicx}\n"
        "\\usepackage{array}\n"
        "\\setlength{\\parindent}{0pt}\n"
        "\\pagestyle{empty}\n"
    )


def _build_tex(
    projeto, metadados, segmentos, img_nome: str, desvio_label: str,
    classificacao: dict | None = None,
) -> str:
    partes: list[str] = [_preambulo(), "\\begin{document}\n"]

    partes.append(f"\\begin{{center}}\\Large\\bfseries {esc(TITULO)}\\end{{center}}\n")
    nome = (projeto or {}).get("nome", "")
    if nome:
        partes.append(f"\\begin{{center}}\\itshape {esc(nome)}\\end{{center}}\n")
    partes.append("\\vspace{4pt}\n")

    # Rastreabilidade
    partes.append("\\section*{Dados do Projeto (Rastreabilidade)}\n")
    partes.append("\\begin{longtable}{@{}>{\\bfseries}p{4.4cm}p{5.4cm}@{}}\\toprule\n")
    for rotulo, valor in linhas_rastreabilidade(projeto, metadados):
        partes.append(f"{esc(rotulo)} & {esc(valor)} \\\\\n")
    partes.append("\\bottomrule\\end{longtable}\n")

    # Segmentação: imagem + resumo
    partes.append("\\section*{Segmentação Homogênea}\n")
    partes.append(
        f"\\begin{{center}}\\includegraphics[width=\\linewidth]{{{img_nome}}}\\end{{center}}\n"
    )
    ncols = len(RESUMO_CABECALHO)
    partes.append(
        "\\begin{longtable}{@{}l l r r r r@{}}\\toprule\n"
        if ncols == 6
        else "\\begin{longtable}{@{}" + "l" * ncols + "@{}}\\toprule\n"
    )
    partes.append(
        " & ".join(_sigma(h) for h in RESUMO_CABECALHO) + " \\\\\n\\midrule\n"
    )
    for linha in linhas_resumo(segmentos):
        partes.append(" & ".join(esc(c) for c in linha) + " \\\\\n")
    partes.append("\\bottomrule\\end{longtable}\n")
    partes.append(f"\\vspace{{2pt}}\\footnotesize {esc(legenda_resumo(desvio_label))}\n")

    # Classificação estrutural (Horak) — opcional.
    if classificacao and classificacao.get("resumo") is not None:
        resumo = classificacao["resumo"]
        partes.append("\\normalsize\\section*{Classificação estrutural (Horak)}\n")
        if classificacao.get("nota"):
            partes.append(f"\\footnotesize {esc(classificacao['nota'])}\\normalsize\n\n")
        cols = list(resumo.columns)
        partes.append(
            "\\begin{longtable}{@{}l" + "r" * (len(cols) - 1) + "@{}}\\toprule\n"
        )
        partes.append(" & ".join(esc(c) for c in cols) + " \\\\\n\\midrule\n")
        for _, row in resumo.iterrows():
            partes.append(" & ".join(esc(v) for v in row.values) + " \\\\\n")
        partes.append("\\bottomrule\\end{longtable}\n")
        partes.append(
            "\\footnotesize SCI = camadas superiores · BDI = base · BCI = subleito. "
            "Faixas de Horak em µm (índices ×10). SCI/BDI/BCI escalam com a carga "
            "(40 kN).\\normalsize\n"
        )

    partes.append("\\end{document}\n")
    return "".join(partes)


def lualatex_disponivel() -> bool:
    return shutil.which("lualatex") is not None


def gerar_pdf(
    projeto: dict | None,
    metadados,
    segmentos,
    zi_png: bytes,
    desvio_label: str = "Amostral (n−1)",
    classificacao: dict | None = None,
) -> bytes:
    """Compila o relatório PDF (14×21, Pagella/CID Type 0C) e devolve os bytes."""
    if not lualatex_disponivel():
        raise RuntimeError(
            "lualatex não encontrado. Instale um TeX com LuaLaTeX e a família "
            "tex-gyre (Linux: texlive-luatex + texlive-fonts-extra)."
        )
    with tempfile.TemporaryDirectory() as d:
        dpath = Path(d)
        (dpath / "zi.png").write_bytes(zi_png)
        tex = _build_tex(
            projeto, metadados, segmentos, "zi.png", desvio_label, classificacao
        )
        (dpath / "rel.tex").write_text(tex, encoding="utf-8")
        for _ in range(2):  # 2 passes (longtable)
            proc = subprocess.run(
                ["lualatex", "-interaction=nonstopmode", "-halt-on-error", "rel.tex"],
                cwd=d, capture_output=True, text=True,
            )
        pdf = dpath / "rel.pdf"
        if not pdf.exists():
            log = (dpath / "rel.log").read_text(errors="replace") if (dpath / "rel.log").exists() else proc.stdout
            raise RuntimeError("Falha na compilação do PDF:\n" + log[-1500:])
        return pdf.read_bytes()


def verificar_sem_type1(pdf_bytes: bytes) -> tuple[bool, list[str]]:
    """Roda pdffonts e retorna (ok, tipos). ok=False se houver qualquer Type 1."""
    if shutil.which("pdffonts") is None:
        return True, ["(pdffonts indisponível — verificação pulada)"]
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(pdf_bytes)
        f.flush()
        out = subprocess.run(
            ["pdffonts", f.name], capture_output=True, text=True
        ).stdout
    tipos: list[str] = []
    tem_type1 = False
    for linha in out.splitlines()[2:]:
        if not linha.strip():
            continue
        # a coluna "type" é o 2º campo; "Type 1" contém espaço -> checa substring
        if "Type 1" in linha and "Type 1C" not in linha:
            tem_type1 = True
        tipos.append(linha.split()[0])
    return (not tem_type1), tipos
