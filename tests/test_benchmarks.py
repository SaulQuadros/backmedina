import numpy as np
import pandas as pd

from backmedina.analytics.benchmarks import (
    classe_horak,
    classificar,
    fator_correcao_temperatura,
)


def test_classe_horak_limites_sci():
    # SCI (µm): <200 Sadio; 200–400 Alerta; >400 Crítico
    assert classe_horak(199.9, "SCI") == "Sadio"
    assert classe_horak(200.0, "SCI") == "Alerta"
    assert classe_horak(400.0, "SCI") == "Alerta"
    assert classe_horak(400.1, "SCI") == "Crítico"


def test_classe_horak_bdi_bci_e_nan():
    assert classe_horak(90, "BDI") == "Sadio"
    assert classe_horak(150, "BDI") == "Alerta"
    assert classe_horak(60, "BCI") == "Alerta"
    assert classe_horak(float("nan"), "SCI") == "n/d"


def test_fator_temperatura():
    # T_pav > T_ref -> reduz (fator < 1); T_pav = T_ref -> 1
    f = fator_correcao_temperatura(45.0, temp_ref=25.0, coef_por_grau=0.02)
    assert abs(float(f) - (1 + 0.02 * (25 - 45))) < 1e-9  # = 0,6
    assert abs(float(fator_correcao_temperatura(25.0, 25.0, 0.02)) - 1.0) < 1e-9
    # piso de 0,1 (não fica negativo em extremos)
    assert float(fator_correcao_temperatura(200.0, 25.0, 0.02)) == 0.1


def test_classificar_com_correcao():
    # SCI=30 (0,01 mm) = 300 µm -> Alerta cru; com T alta e correção, cai p/ Sadio.
    idx = pd.DataFrame({"Metros": [0.0], "SCI": [30.0], "BDI": [8.0], "BCI": [3.0]})
    # sem correção
    t0 = classificar(idx, corrigir=False)
    assert t0["SCI (µm)"].iloc[0] == 300.0
    assert t0["Classe SCI"].iloc[0] == "Alerta"
    assert t0["Classe BDI"].iloc[0] == "Sadio"  # 80 µm < 100
    assert t0["Classe BCI"].iloc[0] == "Sadio"  # 30 µm < 50
    # com correção: T=45, ref=25, coef=0,02 -> fator 0,6 -> 180 µm -> Sadio
    t1 = classificar(idx, temp_pav=[45.0], temp_ref=25.0, coef_por_grau=0.02, corrigir=True)
    assert "SCI corr (µm)" in t1.columns
    assert abs(t1["SCI corr (µm)"].iloc[0] - 180.0) < 1e-6
    assert t1["Classe SCI"].iloc[0] == "Sadio"


def test_presets_e_resumo():
    from backmedina.analytics.benchmarks import BENCHMARKS, resumo_por_classe
    assert set(BENCHMARKS) == {"Base granular", "Base cimentada", "Base betuminosa"}
    for nome, bench in BENCHMARKS.items():
        assert set(bench) == {"SCI", "BDI", "BCI"}
        for s, c in bench.values():
            assert 0 < s < c  # limiares crescentes e positivos
    # base cimentada tem limiar de SCI mais rígido (menor) que a granular
    assert BENCHMARKS["Base cimentada"]["SCI"][0] < BENCHMARKS["Base granular"]["SCI"][0]

    idx = pd.DataFrame({"SCI":[10.0,50.0], "BDI":[5.0,25.0], "BCI":[2.0,12.0]})
    tab = classificar(idx)  # 0,01 mm -> µm ×10
    r = resumo_por_classe(tab)
    assert list(r.columns) == ["Índice","Sadio","Alerta","Crítico","n/d"]
    assert set(r["Índice"]) == {"SCI","BDI","BCI"}
    # cada linha soma o nº de estações (2)
    assert (r[["Sadio","Alerta","Crítico","n/d"]].sum(axis=1) == 2).all()
