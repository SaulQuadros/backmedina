"""PDF autocontido do cálculo de Zi (para NotebookLM/apresentação).

Inclui: método, exemplo passo a passo, o gráfico Zi embutido, a tabela completa
do cálculo (todas as estações) e o resumo dos trechos. Compilado com LuaLaTeX +
TeX Gyre Pagella (CID Type 0C, sem Type 1) — ver skill `gerar-documentos`.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np

from backmedina.report.comum import RESUMO_CABECALHO, linhas_resumo
from backmedina.report.relatorio_pdf import _preambulo, esc, lualatex_disponivel
from backmedina.segmentation.aashto_cumdiff import _extremos_z


def _br(v, casas: int = 1) -> str:
    """Número BR (vírgula) ou '—' para vazio/NaN."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "—"
    if f != f:  # NaN
        return "—"
    if casas == 0:
        return f"{f:.0f}"
    return f"{f:.{casas}f}".replace(".", ",")


def _linha_calc(row) -> str:
    return " & ".join(
        [
            _br(row["Metros"], 0),
            _br(row["D0 (0,01 mm)"], 0),
            _br(row["D_media"], 1),
            _br(row["Delta_l (m)"], 0),
            _br(row["A_i"], 0),
            _br(row["Soma_A"], 0),
            _br(row["Soma_L"], 0),
            _br(row["Zi"], 1),
        ]
    ) + r" \\"


def _tex(tab, totais, segmentos, img_nome: str) -> str:
    p: list[str] = [_preambulo(), "\\begin{document}\n"]
    p.append(
        "\\begin{center}\\Large\\bfseries "
        "Cálculo de $Z_i$ (Diferenças Acumuladas) — SOLOCAP/UFJF"
        "\\end{center}\n\\vspace{4pt}\n"
    )

    p.append("\\section*{Método (AASHTO 1993)}\n")
    p.append(
        "Sobre a deflexão máxima $D_0$ (0,01 mm), com $\\Delta l$ entre estações:\n"
        "\\begin{itemize}\\setlength{\\itemsep}{1pt}\n"
        "\\item $\\bar D_i = (D_{i-1}+D_i)/2$ \\quad $A_i = \\bar D_i\\,\\Delta l_i$\n"
        "\\item $A_c=\\sum A_i$;\\ $L_c=\\sum \\Delta l_i$;\\ "
        "$\\tan\\alpha = A_c/L_c$\n"
        "\\item $Z_i = \\sum A_i - \\tan\\alpha \\cdot \\sum \\Delta l_i$ "
        "(vértices $\\Rightarrow$ fronteiras)\n"
        "\\end{itemize}\n"
    )
    p.append(
        "\\textbf{Totais:} "
        f"$A_c={_br(totais['A_c'],0)}$, $L_c={_br(totais['L_c'],0)}$ m, "
        f"$\\tan\\alpha={_br(totais['tan_alpha'],4)}$. "
        "$Z$ fecha em 0 na última estação.\n"
    )

    # Nº de vértices candidatos (crus) vs fronteiras adotadas.
    z = tab["Zi"].to_numpy()
    amp = float(z.max() - z.min()) if len(z) else 0.0
    tol = max(amp * 0.001, 1e-9)
    n_vert = len(_extremos_z(z, tol))
    n_seg = len(segmentos)
    n_bound = max(n_seg - 1, 0)

    p.append("\\section*{Critério de fronteira (como o app decide)}\n")
    p.append(
        "\\textbf{Nem todo vértice de $Z_i$ vira fronteira.} A seleção tem 3 passos:\n"
        "\\begin{enumerate}\\setlength{\\itemsep}{1pt}\n"
        "\\item \\textbf{Candidatos}: os vértices de $Z_i$ (troca de sinal da inclinação).\n"
        "\\item \\textbf{Nitidez + piso de 100 m}: aceitam-se os vértices mais nítidos "
        "(2ª diferença de $Z_i$) desde que \\emph{ambos os lados} fiquem $\\ge 100$ m "
        "(e $\\ge 2$ estações). É isso que descarta a maioria dos vértices.\n"
        "\\item \\textbf{Divisão forçada}: qualquer trecho $> 2000$ m é subdividido.\n"
        "\\end{enumerate}\n"
        f"No exemplo: \\textbf{{{n_vert} vértices candidatos}} $\\to$ "
        f"\\textbf{{{n_bound} fronteiras}} ({n_seg} trechos).\n"
    )

    p.append("\\section*{Convenção de fronteira e comprimento}\n")
    p.append(
        "A fronteira é a estação onde \\textbf{começa} o novo trecho (o anterior "
        "termina na estação imediatamente antes). O comprimento é medido "
        "\\textbf{fronteira-a-fronteira} — por isso a soma dos comprimentos é a "
        "extensão total da via.\n"
    )

    p.append("\\section*{Gráfico $Z_i \\times$ distância}\n")
    p.append(
        f"\\begin{{center}}\\includegraphics[width=\\linewidth]{{{img_nome}}}\\end{{center}}\n"
    )

    p.append("\\section*{Modo manual}\n")
    p.append(
        "Além do automático, o engenheiro pode marcar as fronteiras "
        "\\textbf{clicando na própria curva $Z_i$}. Ao acionar \"Segmentar Trechos\", "
        "valem as \\textbf{mesmas regras} (cada trecho em [100; 2000] m, $\\ge 2$ "
        "estações; e o trecho circular, se \"Circuito fechado\"). Se as regras forem "
        "violadas, o app \\textbf{não segmenta} e avisa (ex.: \"Seleção vazia\"; "
        "\"distância menor/maior que o comprimento mínimo/máximo\"). Se forem "
        "atendidas, a segmentação manual passa a valer.\n"
    )

    p.append("\\section*{Deflexão característica}\n")
    p.append(
        "Por trecho: $D_c = D_m + \\sigma$ (em 0,01 mm), com $\\sigma$ "
        "\\textbf{amostral (n$-$1) por padrão} (populacional, n, opcional). "
        "É a entrada por segmento no MeDiNa (Modo Reforço).\n"
    )

    # Resumo dos trechos
    p.append("\\section*{Trechos homogêneos}\n")
    p.append("\\footnotesize\n\\begin{longtable}{@{}l l r r r r@{}}\\toprule\n")
    p.append(
        " & ".join(r"$\sigma$" if h == "σ" else esc(h) for h in RESUMO_CABECALHO)
        + r" \\ \midrule" + "\n"
    )
    for linha in linhas_resumo(segmentos):
        p.append(" & ".join(esc(c) for c in linha) + r" \\" + "\n")
    p.append("\\bottomrule\\end{longtable}\\normalsize\n")

    p.append("\\section*{Unidades — por que 0,01 mm}\n")
    p.append(
        "Os cálculos são em \\textbf{0,01 mm} porque o raio de curvatura "
        "$R_c = 6250/[2(D_0-D_{25})]$ tem a constante 6250 \\textbf{embutindo essa "
        "unidade}, e o campo $D_c$ do MeDiNa também é em 0,01 mm. O $Z_i$ é "
        "\\textbf{invariante à escala} (em µm tudo $\\times 10$; as fronteiras não "
        "mudam). Para o \\textbf{BackMeDiNa}, a saída das deflexões vai em µm.\n"
    )

    # Tabela completa do cálculo
    p.append("\\section*{Cálculo completo ($D_0$, $\\bar D_i$, $A_i$, $Z_i$)}\n")
    p.append(
        "\\scriptsize\n\\begin{longtable}{@{}r r r r r r r r@{}}\\toprule\n"
        "Metros & $D_0$ & $\\bar D_i$ & $\\Delta l$ & $A_i$ & "
        "$\\sum A_i$ & $\\sum \\Delta l$ & $Z_i$ \\\\ \\midrule\n"
        "\\endhead\n"
    )
    for _, row in tab.iterrows():
        p.append(_linha_calc(row) + "\n")
    p.append("\\bottomrule\\end{longtable}\\normalsize\n")

    p.append("\\end{document}\n")
    return "".join(p)


def gerar_pdf_zi(tab, totais: dict, segmentos, zi_png: bytes) -> bytes:
    """Compila o PDF do cálculo de Zi (14×21, Pagella, sem Type 1)."""
    if not lualatex_disponivel():
        raise RuntimeError("lualatex não encontrado (necessário para o PDF).")
    with tempfile.TemporaryDirectory() as d:
        dp = Path(d)
        (dp / "zi.png").write_bytes(zi_png)
        (dp / "ap.tex").write_text(_tex(tab, totais, segmentos, "zi.png"), "utf-8")
        for _ in range(2):
            proc = subprocess.run(
                ["lualatex", "-interaction=nonstopmode", "-halt-on-error", "ap.tex"],
                cwd=d, capture_output=True, text=True,
            )
        pdf = dp / "ap.pdf"
        if not pdf.exists():
            log = (dp / "ap.log")
            raise RuntimeError(
                "Falha ao compilar PDF Zi:\n"
                + (log.read_text(errors="replace")[-1500:] if log.exists() else proc.stdout)
            )
        return pdf.read_bytes()
