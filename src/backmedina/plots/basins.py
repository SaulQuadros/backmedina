"""Gráficos de bacia de deflexão e da curva de diferenças acumuladas.

Usa matplotlib (sem dependência de Streamlit) e devolve objetos Figure,
prontos para `st.pyplot(fig)` ou salvamento.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # backend não-interativo (seguro em servidor)
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from backmedina.model.schema import D_TO_SENSOR, SENSOR_OFFSETS_CM  # noqa: E402


def plot_bacias(
    df: pd.DataFrame,
    max_linhas: int = 30,
    unidade_label: str = "0,01 mm",
    fator: float = 1.0,
):
    """Plota as bacias de deflexão (deflexão x distância radial).

    ``fator``/``unidade_label`` controlam apenas a EXIBIÇÃO (ex.: multiplicar por
    10 e rotular 'µm'); não alteram os dados nem os cálculos.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    dcols = [d for d in D_TO_SENSOR if d in df.columns]
    offsets = SENSOR_OFFSETS_CM[: len(dcols)]
    n = min(len(df), max_linhas)
    for i in range(n):
        y = [pd.to_numeric(df.iloc[i][d], errors="coerce") * fator for d in dcols]
        ax.plot(offsets, y, alpha=0.35, linewidth=1)
    ax.invert_yaxis()  # deflexão cresce para baixo
    ax.set_xlabel("Distância do centro da carga (cm)")
    ax.set_ylabel(f"Deflexão ({unidade_label})")
    ax.set_title("Bacias de deflexão")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def fig_para_png(fig, dpi: int = 200) -> bytes:
    """Serializa uma figura matplotlib em PNG (bytes) — para embutir em relatórios."""
    import io

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    return buf.getvalue()


def plot_curva_z(df_seg: pd.DataFrame, coluna_dist: str = "Metros"):
    """Plota a curva Z(x) das diferenças acumuladas colorida por segmento."""
    fig, ax = plt.subplots(figsize=(9, 4))
    x = pd.to_numeric(df_seg[coluna_dist], errors="coerce")
    ax.plot(x, df_seg["Z"], color="#37474F", linewidth=1.2)
    if "Segmento" in df_seg.columns:
        for seg, grupo in df_seg.groupby("Segmento"):
            gx = pd.to_numeric(grupo[coluna_dist], errors="coerce")
            ax.scatter(gx, grupo["Z"], s=14, label=f"Seg {seg}")
        ax.legend(fontsize=8, ncol=4)
    ax.set_xlabel("Distância (m)")
    ax.set_ylabel("Diferença acumulada Z")
    ax.set_title("Segmentação homogênea — diferenças acumuladas (AASHTO)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig
