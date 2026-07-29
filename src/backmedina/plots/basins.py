"""Gráficos de bacia de deflexão e da curva de diferenças acumuladas.

Usa matplotlib (sem dependência de Streamlit) e devolve objetos Figure,
prontos para `st.pyplot(fig)` ou salvamento.
"""

from __future__ import annotations

import warnings

import matplotlib

matplotlib.use("Agg")  # backend não-interativo (seguro em servidor)
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402

from backmedina.model.schema import D_TO_SENSOR, SENSOR_OFFSETS_CM  # noqa: E402


def plot_bacias(
    df: pd.DataFrame,
    max_linhas: int = 30,
    unidade_label: str = "0,01 mm",
    fator: float = 1.0,
):
    """Plota as bacias de deflexão (deflexão x distância radial).

    Cada curva é a bacia de **uma estação** (os 9 geofones D1..D9 a
    0/20/30/45/60/90/120/150/180 cm). A cor identifica a **posição** da estação na
    via (coluna ``Metros``, ou a ordem se ela não existir), com barra de cores. A
    **bacia média** (todas as estações) é traçada em preto como referência.

    Quando há mais de ``max_linhas`` estações, amostra-se um subconjunto
    **distribuído por toda a via** (não apenas as primeiras) e o título informa
    quantas de quantas estão sendo exibidas.

    ``fator``/``unidade_label`` controlam apenas a EXIBIÇÃO (ex.: multiplicar por
    10 e rotular 'µm'); não alteram os dados nem os cálculos.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    dcols = [d for d in D_TO_SENSOR if d in df.columns]
    offsets = SENSOR_OFFSETS_CM[: len(dcols)]
    total = len(df)

    if total == 0 or not dcols:
        ax.set_title("Bacias de deflexão — sem dados")
        ax.set_xlabel("Distância do centro da carga (cm)")
        ax.set_ylabel(f"Deflexão ({unidade_label})")
        fig.tight_layout()
        return fig

    # Posição de cada estação (m) para colorir; cai para o índice se não houver "Metros".
    if "Metros" in df.columns:
        pos = pd.to_numeric(df["Metros"], errors="coerce").to_numpy(dtype=float)
        pos_label = "Posição na via (m)"
    else:
        pos = np.arange(total, dtype=float)
        pos_label = "Estação (ordem)"

    # Amostra estações distribuídas por TODA a via (não só as primeiras).
    if total > max_linhas:
        sel = np.unique(np.linspace(0, total - 1, max_linhas).round().astype(int))
    else:
        sel = np.arange(total)

    # Normalização de cor pela posição (ignora NaN).
    finito = pos[np.isfinite(pos)]
    norm = (
        Normalize(vmin=float(finito.min()), vmax=float(finito.max()))
        if finito.size and finito.min() != finito.max()
        else Normalize(0.0, 1.0)
    )
    cmap = plt.get_cmap("viridis")

    for i in sel:
        y = [pd.to_numeric(df.iloc[i][d], errors="coerce") * fator for d in dcols]
        cor = cmap(norm(pos[i])) if np.isfinite(pos[i]) else "0.6"
        ax.plot(offsets, y, color=cor, alpha=0.55, linewidth=1)

    # Bacia média (todas as estações) como referência destacada.
    vals = df[dcols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float) * fator
    with warnings.catch_warnings():  # "Mean of empty slice" se alguma coluna for toda NaN
        warnings.simplefilter("ignore", category=RuntimeWarning)
        media = np.nanmean(vals, axis=0)
    ax.plot(offsets, media, color="black", linewidth=2.2, label="Bacia média")

    ax.invert_yaxis()  # deflexão cresce para baixo
    ax.set_xlabel("Distância do centro da carga (cm)")
    ax.set_ylabel(f"Deflexão ({unidade_label})")
    ax.set_title(f"Bacias de deflexão — {len(sel)} de {total} estações")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=8)

    # Barra de cores: identifica cada curva pela posição na via (substitui a
    # legenda item-a-item, que seria ilegível com dezenas de curvas).
    sm = ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    fig.colorbar(sm, ax=ax, pad=0.02).set_label(pos_label)

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
