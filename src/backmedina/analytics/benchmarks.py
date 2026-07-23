"""Classificação estrutural por benchmarks de bacia (Horak, 2008) + correção de
temperatura.

Horak propôs faixas de condição para os índices da bacia em **pavimentos de base
granular**, com carga padrão de **40 kN** e deflexões em **µm**:

  SCI (D0−D30):  Sadio < 200 · Alerta 200–400 · Crítico > 400
  BDI (D30−D60): Sadio < 100 · Alerta 100–200 · Crítico > 200
  BCI (D60−D90): Sadio <  50 · Alerta  50–100 · Crítico > 100

Ressalvas: valem para base granular; SCI/BDI/BCI escalam com a carga (normalizar a
40 kN); SCI é sensível à temperatura (correção abaixo). Os índices do app estão em
0,01 mm — convertem-se para µm multiplicando por 10.
"""

from __future__ import annotations

import math

import numpy as np

# Limiares (µm): (limite Sadio/Alerta, limite Alerta/Crítico).
BENCHMARK_HORAK_GRANULAR: dict[str, tuple[float, float]] = {
    "SCI": (200.0, 400.0),
    "BDI": (100.0, 200.0),
    "BCI": (50.0, 100.0),
}

# Presets por tipo de base (Horak, 2008). O de BASE GRANULAR é o mais consolidado;
# os de base cimentada e betuminosa são valores de referência que devem ser
# CONFERIDOS com a fonte para o caso específico (limiares em µm).
BENCHMARKS: dict[str, dict[str, tuple[float, float]]] = {
    "Base granular": BENCHMARK_HORAK_GRANULAR,
    "Base cimentada": {
        "SCI": (150.0, 400.0),
        "BDI": (80.0, 150.0),
        "BCI": (40.0, 80.0),
    },
    "Base betuminosa": {
        "SCI": (100.0, 300.0),
        "BDI": (50.0, 100.0),
        "BCI": (40.0, 80.0),
    },
}

# Cores (fundo claro) por classe — para destacar em tabelas HTML/relatórios.
CLASSE_CORES = {
    "Sadio": "#C8E6C9",   # verde claro
    "Alerta": "#FFF9C4",  # amarelo claro
    "Crítico": "#FFCDD2",  # vermelho claro
    "n/d": "#EEEEEE",
}

# Indicador por emoji (para exibição em tabelas sem estilização/CSS).
CLASSE_EMOJI = {
    "Sadio": "🟢 Sadio",
    "Alerta": "🟡 Alerta",
    "Crítico": "🔴 Crítico",
    "n/d": "— n/d",
}

# Só o índice raso (SCI) é corrigido por temperatura; BDI/BCI (camadas profundas)
# não são governados pelo asfalto.
INDICE_CORRIGIVEL_TEMP = "SCI"


def classe_horak(
    valor_um: float, indice: str,
    benchmark: dict = BENCHMARK_HORAK_GRANULAR,
) -> str:
    """Classifica um valor (em µm) em Sadio / Alerta / Crítico."""
    if valor_um is None or (isinstance(valor_um, float) and math.isnan(valor_um)):
        return "n/d"
    s, c = benchmark[indice]
    if valor_um < s:
        return "Sadio"
    if valor_um <= c:
        return "Alerta"
    return "Crítico"


def fator_correcao_temperatura(
    temp_pav, temp_ref: float = 25.0, coef_por_grau: float = 0.02
):
    """Fator multiplicativo para levar a deflexão à temperatura de referência.

    Modelo linear e transparente: ``f = 1 + coef·(T_ref − T_pav)`` (limitado a
    ≥ 0,1). Com T_pav > T_ref e coef > 0, f < 1 (reduz a deflexão inflada pelo
    calor). ``coef`` é a sensibilidade (fração por °C) e **deve ser calibrado** à
    espessura do revestimento (ex.: 0,02 = 2 %/°C).
    """
    f = 1.0 + coef_por_grau * (temp_ref - np.asarray(temp_pav, dtype=float))
    return np.clip(f, 0.1, None)


def classificar(
    indices_df,
    temp_pav=None,
    temp_ref: float = 25.0,
    coef_por_grau: float = 0.02,
    corrigir: bool = False,
    benchmark: dict = BENCHMARK_HORAK_GRANULAR,
):
    """Tabela de classificação estrutural (Horak) por estação.

    ``indices_df`` deve ter SCI, BDI, BCI (em 0,01 mm) e, opcionalmente, Metros.
    Retorna DataFrame com valores em µm e a classe de cada índice. Se ``corrigir``
    e ``temp_pav`` forem dados, o **SCI** é corrigido para ``temp_ref`` antes de
    classificar (BDI/BCI não são corrigidos).
    """
    import pandas as pd

    n = len(indices_df)
    out = pd.DataFrame()
    if "Metros" in indices_df.columns:
        out["Metros"] = indices_df["Metros"].to_numpy()

    def um(col):  # 0,01 mm -> µm
        return pd.to_numeric(indices_df[col], errors="coerce").to_numpy(float) * 10.0

    sci, bdi, bci = um("SCI"), um("BDI"), um("BCI")

    sci_base = sci
    if corrigir and temp_pav is not None:
        f = fator_correcao_temperatura(temp_pav, temp_ref, coef_por_grau)
        sci_base = sci * f
        out["SCI (µm)"] = np.round(sci, 1)
        out["SCI corr (µm)"] = np.round(sci_base, 1)
    else:
        out["SCI (µm)"] = np.round(sci, 1)

    out["Classe SCI"] = [classe_horak(v, "SCI", benchmark) for v in sci_base]
    out["BDI (µm)"] = np.round(bdi, 1)
    out["Classe BDI"] = [classe_horak(v, "BDI", benchmark) for v in bdi]
    out["BCI (µm)"] = np.round(bci, 1)
    out["Classe BCI"] = [classe_horak(v, "BCI", benchmark) for v in bci]
    return out


def resumo_por_classe(tab_class):
    """Resumo: nº de estações por classe (Sadio/Alerta/Crítico/n/d) por índice."""
    import pandas as pd

    ordem = ["Sadio", "Alerta", "Crítico", "n/d"]
    linhas = []
    for col in [c for c in tab_class.columns if c.startswith("Classe")]:
        vc = tab_class[col].value_counts()
        linha = {"Índice": col.replace("Classe ", "")}
        linha.update({k: int(vc.get(k, 0)) for k in ordem})
        linhas.append(linha)
    return pd.DataFrame(linhas, columns=["Índice", *ordem])
