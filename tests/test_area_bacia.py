"""Área da bacia como variável alternativa de segmentação (usa todos os sensores)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backmedina.analytics.area_bacia import (
    COLUNA_AREA_BACIA,
    area_da_bacia,
    com_area_da_bacia,
)
from backmedina.model.units import UnidadeDeflexao
from backmedina.segmentation.aashto_cumdiff import (
    curva_zi_do_df,
    segmentar,
    segmentar_manual,
    tabela_zi,
)

XLSX = (
    Path(__file__).resolve().parents[1]
    / "z_docs" / "lwd" / "solocap" / "2-UFJF-VIA_LOCAL_FX1-FWD.xlsx"
)

DCOLS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]


def _linha(valores, metros=0.0):
    return {"Metros": metros, **dict(zip(DCOLS, valores))}


def test_area_e_a_integral_trapezoidal_sobre_0_180cm():
    """Bacia constante D=10: área = 10 × 180 cm = 1800."""
    df = pd.DataFrame([_linha([10] * 9)])
    assert area_da_bacia(df).iloc[0] == pytest.approx(1800.0)


def test_area_distingue_bacias_com_mesmo_d0():
    """O ponto do método: mesmo D0, formas diferentes -> áreas diferentes."""
    aguda = _linha([100, 40, 25, 15, 10, 6, 4, 3, 2])   # decai rápido
    aberta = _linha([100, 90, 85, 78, 70, 58, 48, 40, 34])  # decai devagar
    a = area_da_bacia(pd.DataFrame([aguda, aberta]))
    assert aguda["D1"] == aberta["D1"]      # mesmo D0
    assert a.iloc[1] > 3 * a.iloc[0]        # áreas muito diferentes


def test_area_nan_quando_faltam_geofones():
    df = pd.DataFrame([{"Metros": 0.0, "D1": 44}])  # só D1
    assert area_da_bacia(df).isna().all()


def test_com_area_nao_altera_o_df_original():
    df = pd.DataFrame([_linha([10] * 9)])
    out = com_area_da_bacia(df)
    assert COLUNA_AREA_BACIA in out.columns
    assert COLUNA_AREA_BACIA not in df.columns


def _df_sintetico():
    """Dois trechos: bacias abertas (0-200 m) e bacias agudas (220-400 m)."""
    linhas = []
    for i in range(11):
        linhas.append(_linha([100, 90, 85, 78, 70, 58, 48, 40, 34], metros=i * 20.0))
    for i in range(11, 21):
        linhas.append(_linha([100, 40, 25, 15, 10, 6, 4, 3, 2], metros=i * 20.0))
    return com_area_da_bacia(pd.DataFrame(linhas))


def test_estatisticas_ficam_em_d0_mesmo_segmentando_pela_area():
    """Dc é definido sobre D0 — não muda de significado com o método."""
    df = _df_sintetico()
    _, segs = segmentar(
        df, coluna_d0=COLUNA_AREA_BACIA, comprimento_min_m=100.0,
        unidade=UnidadeDeflexao.DMM_001, coluna_estat="D1",
    )
    assert segs
    for s in segs:
        # Todas as estações têm D0 = 100 -> Dm = 100 e σ = 0.
        assert s.d0_media == pytest.approx(100.0)
        assert s.d0_desvio == pytest.approx(0.0)
        assert s.d0_caracteristica == pytest.approx(100.0)


def test_sem_coluna_estat_preserva_o_comportamento_classico():
    """O padrão (coluna_estat=None) usa a própria variável de segmentação."""
    df = _df_sintetico()
    _, a = segmentar(df, unidade=UnidadeDeflexao.DMM_001)
    _, b = segmentar(df, unidade=UnidadeDeflexao.DMM_001, coluna_estat="D1")
    assert [s.d0_media for s in a] == [s.d0_media for s in b]
    assert [s.ini_m for s in a] == [s.ini_m for s in b]


def test_area_detecta_mudanca_que_d0_nao_ve():
    """D0 constante em toda a via: só a área encontra a troca de bacia."""
    df = _df_sintetico()
    _, por_d0 = segmentar(
        df, coluna_d0="D1", comprimento_min_m=100.0, unidade=UnidadeDeflexao.DMM_001
    )
    _, por_area = segmentar(
        df, coluna_d0=COLUNA_AREA_BACIA, comprimento_min_m=100.0,
        unidade=UnidadeDeflexao.DMM_001, coluna_estat="D1",
    )
    assert len(por_d0) == 1              # D0 não varia -> nenhum corte
    assert len(por_area) > 1             # a área enxerga a mudança de forma
    assert any(abs(s.ini_m - 220.0) < 40.0 for s in por_area)


def test_manual_tambem_aceita_coluna_estat():
    df = _df_sintetico()
    _, segs, viol = segmentar_manual(
        df, [220.0], coluna_d0=COLUNA_AREA_BACIA, comprimento_min_m=100.0,
        unidade=UnidadeDeflexao.DMM_001, coluna_estat="D1",
    )
    assert not viol
    assert all(s.d0_media == pytest.approx(100.0) for s in segs)


def test_tabela_zi_acompanha_o_rotulo_da_variavel():
    df = _df_sintetico()
    tab, _ = tabela_zi(
        df, coluna_d0=COLUNA_AREA_BACIA, unidade=UnidadeDeflexao.DMM_001,
        rotulo_var="Área da bacia (0,01 mm·cm)",
    )
    # O PDF lê a 2ª coluna pela posição — ela precisa ser a variável.
    assert list(tab.columns)[1] == "Área da bacia (0,01 mm·cm)"
    assert tab.columns[0] == "Metros"


@pytest.mark.skipif(not XLSX.exists(), reason="arquivo UFJF ausente")
def test_fechamento_z_em_zero_para_a_area():
    """Critério de verificação do método: Z fecha em 0 na última estação."""
    from backmedina.io.xlsx_solocap import ler_solocap_xlsx

    dados = ler_solocap_xlsx(XLSX)
    df = com_area_da_bacia(dados.tabela)
    _, z = curva_zi_do_df(
        df, coluna_d0=COLUNA_AREA_BACIA, unidade=dados.unidade_deflexao
    )
    amp = float(np.max(z) - np.min(z))
    assert abs(float(z[-1])) < amp * 1e-9
