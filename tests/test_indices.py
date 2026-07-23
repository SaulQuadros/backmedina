import pandas as pd

from backmedina.analytics.pbd_indices import calcular_indices


def _linha_estacao_0():
    # Estação 0,00 m do arquivo real UFJF:
    # D1=44 D2=29 D3=21 D4=13 D5=9 D6=6 D7=4 D8=3 D9=3 (D10=2 descartado)
    return pd.DataFrame(
        [{"D1": 44, "D2": 29, "D3": 21, "D4": 13, "D5": 9,
          "D6": 6, "D7": 4, "D8": 3, "D9": 3, "D10": 2}]
    )


def test_indices_estacao_0():
    idx = calcular_indices(_linha_estacao_0()).iloc[0]
    # SCI = D0 - D30 = 44 - 21 = 23
    assert idx["SCI"] == 23
    # BDI = D30 - D60 = 21 - 9 = 12
    assert idx["BDI"] == 12
    # BCI = D60 - D90 = 9 - 6 = 3
    assert idx["BCI"] == 3
    # CF = D0 - D20 = 44 - 29 = 15
    assert idx["CF"] == 15


def test_area_e_s():
    idx = calcular_indices(_linha_estacao_0()).iloc[0]
    # AREA = 15*(1 + 2*21/44 + 2*9/44 + 6/44)
    esperado_area = 15 * (1 + 2 * 21 / 44 + 2 * 9 / 44 + 6 / 44)
    assert abs(idx["AREA"] - esperado_area) < 1e-9
    # S = (44 + 21 + 9 + 6 + 4) / (5*44) * 100
    esperado_s = (44 + 21 + 9 + 6 + 4) / (5 * 44) * 100
    assert abs(idx["S"] - esperado_s) < 1e-9


def test_rc():
    idx = calcular_indices(_linha_estacao_0()).iloc[0]
    # D25 = (29 + 21)/2 = 25 ; Rc = 6250 / (2*(44-25)) = 6250/38
    assert abs(idx["Rc"] - 6250 / 38) < 1e-9
