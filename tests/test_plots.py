"""Gráficos (matplotlib, backend Agg) — conteúdo dos dados plotados."""

import numpy as np
import pandas as pd

from backmedina.plots.basins import plot_d0_por_estaca


def _linhas_h(ax):
    """Valores y das linhas de referência (as tracejadas: D̄ e Dc)."""
    return sorted(
        float(l.get_ydata()[0]) for l in ax.lines if l.get_linestyle() == "--"
    )


def test_d0_por_estaca_usa_metros_e_d1():
    df = pd.DataFrame({"Metros": [0, 20, 40, 60], "D1": [40, 50, 60, 50]})
    ax = plot_d0_por_estaca(df).axes[0]
    serie = ax.lines[0]
    assert list(serie.get_xdata()) == [0, 20, 40, 60]
    assert list(serie.get_ydata()) == [40, 50, 60, 50]
    assert ax.get_xlabel() == "Distância (m)"
    assert "0,01 mm" in ax.get_ylabel()

    # Referências: D̄ = 50 e Dc = D̄ + σ (amostral, ddof=1) = 50 + 8,165.
    media, sigma = 50.0, float(np.std([40, 50, 60, 50], ddof=1))
    assert _linhas_h(ax) == [media, media + sigma]


def test_d0_por_estaca_cai_para_d0_e_ordem():
    """CSV de bacias: coluna 'd0' e sem 'Metros' -> eixo x pela ordem."""
    df = pd.DataFrame({"d0": [400.0, 500.0]})
    ax = plot_d0_por_estaca(df, unidade_label="µm").axes[0]
    assert list(ax.lines[0].get_xdata()) == [0, 1]
    assert list(ax.lines[0].get_ydata()) == [400.0, 500.0]
    assert ax.get_xlabel() == "Estação (ordem)"
    assert "µm" in ax.get_ylabel()


def test_d0_por_estaca_fator_e_apenas_exibicao():
    df = pd.DataFrame({"Metros": [0, 20], "D1": [40, 60]})
    ax = plot_d0_por_estaca(df, fator=10.0, unidade_label="µm").axes[0]
    assert list(ax.lines[0].get_ydata()) == [400.0, 600.0]
    assert list(df["D1"]) == [40, 60]  # dados de origem intactos


def test_d0_por_estaca_sem_dados_nao_estoura():
    assert plot_d0_por_estaca(pd.DataFrame()) is not None
    assert plot_d0_por_estaca(pd.DataFrame({"D1": []})) is not None
    # Estação única: σ indefinido (n <= ddof) -> não estoura, Dc = D̄.
    ax = plot_d0_por_estaca(pd.DataFrame({"Metros": [0], "D1": [44]})).axes[0]
    assert _linhas_h(ax) == [44.0, 44.0]
