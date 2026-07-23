import numpy as np
import pandas as pd

from backmedina.analytics.deflexao_caracteristica import deflexao_caracteristica
from backmedina.segmentation.aashto_cumdiff import (
    curva_z,
    segmentar,
    segmentar_manual,
    validar_fronteiras_manuais,
)


def test_deflexao_caracteristica():
    # média + desvio amostral (ddof=1)
    vals = [40, 42, 44]
    dc = deflexao_caracteristica(vals)
    assert abs(dc - (42 + np.std(vals, ddof=1))) < 1e-9


def test_curva_z_dois_niveis():
    # Trecho 1 (baixo) depois trecho 2 (alto) => Z muda de inclinação.
    dist = np.arange(0, 200, 20.0)
    d0 = np.array([20, 20, 20, 20, 20, 60, 60, 60, 60, 60], dtype=float)
    z = curva_z(dist, d0)
    assert len(z) == len(dist)
    # Z deve atingir um mínimo perto da transição (índice ~5).
    assert 3 <= int(np.argmin(z)) <= 6


def test_segmentar_detecta_dois_segmentos():
    dist = np.arange(0, 400, 20.0)
    baixo = [20] * 10
    alto = [60] * 10
    df = pd.DataFrame({"Metros": dist, "D1": baixo + alto})
    _, segs = segmentar(df)
    assert len(segs) >= 2
    # Segmento com D0 alto tem deflexão característica maior.
    dcs = [s.d0_caracteristica for s in segs]
    assert max(dcs) > min(dcs)


def test_comprimento_dentro_dos_limites():
    # Via longa com dois patamares; todos os trechos devem ficar em [100, 2000].
    dist = np.arange(0, 3000, 20.0)  # 0..2980 m (150 estações)
    d0 = np.concatenate([np.full(75, 25.0), np.full(75, 70.0)])
    df = pd.DataFrame({"Metros": dist, "D1": d0})
    _, segs = segmentar(df, comprimento_min_m=100, comprimento_max_m=2000)
    assert len(segs) >= 2
    for s in segs:
        assert s.comprimento_m <= 2000.0 + 1e-6
        assert s.comprimento_m >= 100.0 - 1e-6


def test_divisao_forcada_sem_quebra_natural():
    # Perfil monotônico (sem vértices de Z) e longo -> divisão só por comprimento.
    dist = np.arange(0, 5000, 20.0)  # 0..4980 m
    d0 = 20 + 0.01 * dist  # cresce suavemente, sem troca de inclinação de Z
    df = pd.DataFrame({"Metros": dist, "D1": d0})
    _, segs = segmentar(df, comprimento_min_m=100, comprimento_max_m=2000)
    # 4980 m / 2000 -> pelo menos 3 trechos, nenhum acima de 2000 m.
    assert len(segs) >= 3
    assert all(s.comprimento_m <= 2000.0 + 1e-6 for s in segs)


def test_nao_cria_trecho_curto():
    # Um pico isolado não deve gerar um trecho < 100 m.
    dist = np.arange(0, 2000, 20.0)
    d0 = np.full(100, 30.0)
    d0[50] = 90.0  # spike de uma estação
    df = pd.DataFrame({"Metros": dist, "D1": d0})
    _, segs = segmentar(df, comprimento_min_m=100, comprimento_max_m=2000)
    assert all(s.comprimento_m >= 100.0 - 1e-6 for s in segs)


# --- Segmentação manual ---------------------------------------------------

def _via_2000():
    # 0..1980 m, 100 estações a cada 20 m.
    dist = np.arange(0, 2000, 20.0)
    d0 = np.full(100, 30.0)
    return pd.DataFrame({"Metros": dist, "D1": d0})


def test_manual_valido():
    df = _via_2000()
    # Fronteiras em estações válidas: 500 e 1200 m -> 3 trechos (500,700,780 m).
    out, segs, viol = segmentar_manual(df, [500.0, 1200.0])
    assert viol == []
    assert out is not None
    assert len(segs) == 3
    assert [round(s.ini_m) for s in segs] == [0, 500, 1200]
    assert all(100 <= s.comprimento_m <= 2000 for s in segs)


def test_manual_trecho_curto_rejeitado():
    df = _via_2000()
    # 500 e 560 m -> trecho do meio = 60 m (< 100). Deve falhar e NÃO segmentar.
    out, segs, viol = segmentar_manual(df, [500.0, 560.0])
    assert out is None and segs == []
    assert any("mínimo" in v for v in viol)


def test_manual_fronteira_fora_de_estacao():
    df = _via_2000()
    # 510 m não é estação (estações a cada 20 m).
    _, viol = validar_fronteiras_manuais(df["Metros"].to_numpy(), [510.0])
    assert any("não coincide com uma estação" in v for v in viol)


def test_manual_selecao_vazia():
    # Modo manual sem fronteiras -> "Seleção vazia" (espelha o .exe).
    df = _via_2000()
    out, segs, viol = segmentar_manual(df, [])
    assert out is None and segs == []
    assert any("Seleção vazia" in v for v in viol)


def test_manual_circuito_fechado_valido():
    # Circuito fechado: trecho circular = (fim-c_last) + (c_first-início).
    df = _via_2000()  # 0..1980 m
    # Marcadores 600 e 1200 m: interno [600,1200)=600 m; circular=(1980-1200)+600=1380 m.
    out, segs, viol = segmentar_manual(df, [600.0, 1200.0], circuito_fechado=True)
    assert viol == [], viol
    assert out is not None
    # 2 trechos: 1 interno + 1 circular.
    assert len(segs) == 2
    comps = sorted(round(s.comprimento_m) for s in segs)
    assert comps == [600, 1380]


def test_manual_circular_curto_rejeitado():
    df = _via_2000()
    # 100 e 1900 -> circular=(1980-1900)+100=180... interno[100,1900)=1800>máx? não (máx 2000).
    # Ajuste: 100 e 300 -> interno 200 m ok; circular=(1980-300)+100=1780 ok.
    # Para violar o mínimo circular: 100 e 1960 -> circular=(1980-1960)+100=120 ok...
    # Usar 20 e 1960: circular=(1980-1960)+20=40 m < 100.
    _, viol = validar_fronteiras_manuais(
        df["Metros"].to_numpy(), [20.0, 1960.0], circuito_fechado=True
    )
    assert any("segmento circular" in v and "mínimo" in v for v in viol)


def test_ddof_populacional_vs_amostral():
    df = _via_2000().copy()
    df.loc[:, "D1"] = list(range(100))  # variabilidade real
    _, segs_amostral, _ = segmentar_manual(df, [500.0], ddof=1)
    _, segs_pop, _ = segmentar_manual(df, [500.0], ddof=0)
    # Populacional (n) < amostral (n-1) para o mesmo conjunto.
    assert segs_pop[0].d0_desvio < segs_amostral[0].d0_desvio


def test_tabela_zi():
    from backmedina.segmentation.aashto_cumdiff import tabela_zi
    dist = np.arange(0, 200, 20.0)
    d0 = np.array([44, 40, 43, 39, 28, 28, 33, 30, 30, 28], dtype=float)
    df = pd.DataFrame({"Metros": dist, "D1": d0})
    tab, tot = tabela_zi(df)
    assert list(tab.columns) == ["Metros","D0 (0,01 mm)","D_media","Delta_l (m)","A_i","Soma_A","Soma_L","Zi"]
    # 1ª estação sem intervalo -> D_media NaN; A_i idem
    assert np.isnan(tab["D_media"].iloc[0]) and np.isnan(tab["A_i"].iloc[0])
    # linha 1 (20 m): D̄=(44+40)/2=42; A=42*20=840; ΣA=840
    assert tab["D_media"].iloc[1] == 42.0
    assert tab["A_i"].iloc[1] == 840.0
    assert tab["Soma_A"].iloc[1] == 840.0
    # totais consistentes: Zi = ΣA - tanα·ΣL, e Zi[fim] ≈ 0
    assert abs(tot["tan_alpha"] - tot["A_c"]/tot["L_c"]) < 1e-9
    assert abs(tab["Zi"].iloc[-1]) < 1e-6
