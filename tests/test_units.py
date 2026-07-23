import pandas as pd

from backmedina.analytics.pbd_indices import calcular_indices
from backmedina.convert.backmedina_csv import exportar_csv_backmedina
from backmedina.model.schema import BACKMEDINA_HEADER, MetadadosLevantamento, DadosFWD
from backmedina.model.units import (
    UnidadeDeflexao,
    detectar_unidade,
    fator_conversao,
)


def test_detectar_unidade():
    assert detectar_unidade("UNIDADE DAS LEITURAS (x10⁻² mm)") is UnidadeDeflexao.DMM_001
    assert detectar_unidade("Deflexões em µm") is UnidadeDeflexao.MICROMETRO
    assert detectar_unidade("micrômetro") is UnidadeDeflexao.MICROMETRO
    # Sem marcador reconhecível -> default.
    assert detectar_unidade("texto qualquer") is UnidadeDeflexao.DMM_001


def test_fatores():
    assert UnidadeDeflexao.DMM_001.fator_para_micrometro == 10.0
    assert UnidadeDeflexao.MICROMETRO.fator_para_micrometro == 1.0
    assert fator_conversao(UnidadeDeflexao.DMM_001, UnidadeDeflexao.MICROMETRO) == 10.0
    assert fator_conversao(UnidadeDeflexao.MICROMETRO, UnidadeDeflexao.DMM_001) == 0.1


def _dados(unidade):
    tab = pd.DataFrame(
        [{"Metros": 0.0, "Target Load (Kgf)": 4000,
          "D1": 44, "D2": 29, "D3": 21, "D4": 13, "D5": 9,
          "D6": 6, "D7": 4, "D8": 3, "D9": 3, "D10": 2,
          "Data e Hora": "11/09/2023 13:30"}]
    )
    return DadosFWD(MetadadosLevantamento(), tab, unidade_deflexao=unidade)


def test_csv_converte_0p01mm_para_micrometro():
    csv = exportar_csv_backmedina(_dados(UnidadeDeflexao.DMM_001))
    col = {n: i for i, n in enumerate(BACKMEDINA_HEADER)}
    linha = csv.splitlines()[4].split(",")
    assert linha[col["d0"]] == "440"   # 44 * 10
    assert linha[col["d180"]] == "30"  # 3 * 10


def test_csv_nao_converte_quando_ja_micrometro():
    csv = exportar_csv_backmedina(_dados(UnidadeDeflexao.MICROMETRO))
    col = {n: i for i, n in enumerate(BACKMEDINA_HEADER)}
    linha = csv.splitlines()[4].split(",")
    assert linha[col["d0"]] == "44"  # sem conversão
    assert linha[col["d180"]] == "3"


def test_indices_invariantes_a_unidade():
    # Mesma bacia física expressa em 0,01 mm e em µm -> índices idênticos.
    base = {"D1": 44, "D2": 29, "D3": 21, "D4": 13, "D5": 9,
            "D6": 6, "D7": 4, "D8": 3, "D9": 3, "D10": 2}
    df_dmm = pd.DataFrame([base])
    df_um = pd.DataFrame([{k: v * 10 for k, v in base.items()}])
    a = calcular_indices(df_dmm, unidade=UnidadeDeflexao.DMM_001).iloc[0]
    b = calcular_indices(df_um, unidade=UnidadeDeflexao.MICROMETRO).iloc[0]
    for col in ("Rc", "AREA", "SCI", "BDI", "BCI", "CF", "S"):
        assert abs(a[col] - b[col]) < 1e-6, col


def test_csvs_por_segmento_zip():
    import io as _io
    import zipfile
    from backmedina.convert.backmedina_csv import (
        csvs_por_segmento, zip_de_arquivos,
    )
    from backmedina.io.xlsx_solocap import ler_solocap_xlsx
    from backmedina.segmentation.aashto_cumdiff import segmentar
    from pathlib import Path

    xlsx = Path(__file__).resolve().parents[1] / "z_docs" / "lwd" / "2-UFJF-VIA_LOCAL_FX1-FWD.xlsx"
    if not xlsx.exists():
        import pytest; pytest.skip("arquivo UFJF ausente")

    dados = ler_solocap_xlsx(xlsx)
    df_seg, segs = segmentar(dados.tabela, unidade=dados.unidade_deflexao)
    arquivos = csvs_por_segmento(dados, df_seg)

    # Um CSV por segmento, nomeados seg_01, seg_02, ...
    assert len(arquivos) == len(segs)
    assert "seg_01.csv" in arquivos
    esperado = {f"seg_{i:02d}.csv" for i in range(1, len(segs) + 1)}
    assert set(arquivos) == esperado

    # Cada CSV: cabeçalho correto, SEÇÃO seg_NN, deflexões em µm (D1*10).
    csv1 = arquivos["seg_01.csv"].splitlines()
    assert csv1[0] == "BACKMEDINA"
    assert csv1[1] == "SEÇÃO: seg_01"
    assert csv1[2] == "RAIO (cm): 15"
    d0_primeira = int(csv1[4].split(",")[8])   # coluna d0
    d0_bruto = int(dados.tabela["D1"].iloc[0])
    assert d0_primeira == d0_bruto * 10

    # Nº de estações no seg_01 == nº de linhas de dados do CSV (linhas - 4).
    assert len(csv1) - 4 == segs[0].n_pontos

    # ZIP contém todos os arquivos.
    zb = zip_de_arquivos(arquivos)
    with zipfile.ZipFile(_io.BytesIO(zb)) as zf:
        assert set(zf.namelist()) == esperado


def test_resumo_seg_xlsx_e_zip_com_resumo():
    import io as _io
    import zipfile
    from pathlib import Path
    from openpyxl import load_workbook
    from backmedina.convert.backmedina_csv import csvs_por_segmento, zip_de_arquivos
    from backmedina.convert.resumo_seg import resumo_seg_xlsx_bytes
    from backmedina.io.xlsx_solocap import ler_solocap_xlsx
    from backmedina.segmentation.aashto_cumdiff import segmentar

    xlsx = Path(__file__).resolve().parents[1] / "z_docs" / "lwd" / "2-UFJF-VIA_LOCAL_FX1-FWD.xlsx"
    if not xlsx.exists():
        import pytest; pytest.skip("arquivo UFJF ausente")

    dados = ler_solocap_xlsx(xlsx)
    df_seg, segs = segmentar(dados.tabela, unidade=dados.unidade_deflexao)

    # Resumo_Seg.xlsx válido, com uma linha por segmento.
    data = resumo_seg_xlsx_bytes(segs)
    assert data[:2] == b"PK"
    wb = load_workbook(_io.BytesIO(data))
    ws = wb["Resumo_Seg"]
    header = [c.value for c in ws[4]]
    assert header == ["Segmento", "Estacas (m)", "Comprimento (m)", "Dm", "σ", "Dc"]
    # primeira linha de dados = seg_01
    assert ws.cell(5, 1).value == "seg_01"

    # ZIP contém os CSVs + o Resumo_Seg.xlsx.
    arquivos = csvs_por_segmento(dados, df_seg)
    arquivos["Resumo_Seg.xlsx"] = data
    zb = zip_de_arquivos(arquivos)
    with zipfile.ZipFile(_io.BytesIO(zb)) as zf:
        nomes = set(zf.namelist())
    assert "Resumo_Seg.xlsx" in nomes
    assert "seg_01.csv" in nomes
    assert len([n for n in nomes if n.endswith(".csv")]) == len(segs)


def test_glossario_cobre_todas_as_colunas():
    import pandas as pd
    from backmedina.analytics.pbd_glossario import GLOSSARIO_PBD
    from backmedina.analytics.pbd_indices import indices_com_contexto
    df = pd.DataFrame([{"D1":44,"D2":29,"D3":21,"D4":13,"D5":9,"D6":6,"D7":4,"D8":3,"D9":3,"D10":2,"Metros":0.0}])
    colunas = set(indices_com_contexto(df).columns)  # Metros, Rc, AREA, SCI, BDI, BCI, CF, S
    siglas = {g["sigla"] for g in GLOSSARIO_PBD}
    assert colunas <= siglas, f"faltam no glossário: {colunas - siglas}"
    # cada item tem os campos essenciais preenchidos
    for g in GLOSSARIO_PBD:
        for campo in ("nome","unidade","formula","o_que_e","para_que_serve"):
            assert g[campo], f"{g['sigla']} sem {campo}"
