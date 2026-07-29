from pathlib import Path

import pandas as pd
import pytest

from backmedina.convert.backmedina_csv import (
    csvs_por_segmento,
    exportar_csv_backmedina,
    exportar_csv_backmedina_bytes,
    valores_estaca_do_arquivo,
)
from backmedina.segmentation.aashto_cumdiff import segmentar
from backmedina.convert.standardize import exportar_xlsx_bytes
from backmedina.io.xlsx_solocap import ler_solocap_xlsx
from backmedina.model.schema import BACKMEDINA_HEADER, SENSOR_LABELS

XLSX = Path(__file__).resolve().parents[1] / "z_docs" / "lwd" / "2-UFJF-VIA_LOCAL_FX1-FWD.xlsx"

pytestmark = pytest.mark.skipif(not XLSX.exists(), reason="arquivo UFJF ausente")


def test_ler_solocap_metadados_e_linhas():
    dados = ler_solocap_xlsx(XLSX)
    assert dados.metadados.cliente == "UNIVERSIDADE FEDERAL DE JUIZ DE FORA"
    # 105 estações (linhas 14..118).
    assert len(dados.tabela) == 105
    # Parsing BR aplicado.
    assert dados.tabela["Target Load (Kgf)"].iloc[0] == 4059.0
    assert abs(dados.tabela["Latitude"].iloc[0] - (-21.77314)) < 1e-6
    assert dados.tabela["D1"].iloc[0] == 44


def test_csv_backmedina_cabecalho():
    dados = ler_solocap_xlsx(XLSX)
    csv = exportar_csv_backmedina(dados)
    linhas = csv.splitlines()
    n = len(BACKMEDINA_HEADER)
    # Rótulo e valor em células separadas, linhas preenchidas até n colunas.
    assert linhas[0].split(";") == ["BACKMEDINA"] + [""] * (n - 1)
    assert linhas[1].split(";")[:2] == ["SEÇÃO:", "1984 VIA LOCAL - FAIXA 1 - PD"]
    assert linhas[2].split(";") == ["RAIO (cm):", "15"] + [""] * (n - 2)
    assert linhas[3].split(";") == list(BACKMEDINA_HEADER)
    assert all(len(l.split(";")) == n for l in linhas)
    # d0 da primeira estação = D1 = 44 (0,01 mm) -> 440 µm no BackMeDiNa.
    primeira = linhas[4].split(";")
    col = {name: i for i, name in enumerate(BACKMEDINA_HEADER)}
    assert primeira[col["d0"]] == "440"
    assert primeira[col["d180"]] == "30"  # D9 = 3 -> 30 µm
    assert primeira[col["d210"]] == "20"  # D10 = 2 -> 20 µm (só no CSV)
    assert primeira[col["Carga"]] == "4059"  # carga permanece em kgf


def test_csv_backmedina_formato_do_arquivo():
    """CRLF + CP1252: exigências do importador (ver z_docs/error/csv-backmedina)."""
    dados = ler_solocap_xlsx(XLSX)
    b = exportar_csv_backmedina_bytes(dados)
    assert b.startswith("BACKMEDINA;".encode("cp1252"))
    assert b"\r\n" in b
    assert b.replace(b"\r\n", b"").count(b"\n") == 0  # nenhum LF solto
    assert "Execução".encode("cp1252") in b  # acentuação ANSI, não UTF-8
    assert "Execução".encode("utf-8") not in b


def test_export_xlsx_bytes_valido():
    dados = ler_solocap_xlsx(XLSX)
    data = exportar_xlsx_bytes(dados)
    assert data[:2] == b"PK"  # assinatura de arquivo .xlsx (zip)


def test_sensor_labels_completos():
    assert SENSOR_LABELS == ("d0", "d20", "d30", "d45", "d60", "d90", "d120", "d150", "d180")


def test_faixa_e_trilha_da_ui_vao_para_todas_as_estacoes():
    """SOLOCAP não traz Faixa/Trilha: o valor da UI é aplicado a todas as linhas."""
    dados = ler_solocap_xlsx(XLSX)
    col = {name: i for i, name in enumerate(BACKMEDINA_HEADER)}

    # Sem informar nada -> 0/0 (comportamento anterior preservado).
    linhas = exportar_csv_backmedina(dados).splitlines()[4:]
    assert {l.split(";")[col["Estaca – Faixa"]] for l in linhas} == {"0"}
    assert {l.split(";")[col["Estaca – Trilha"]] for l in linhas} == {"0"}

    # Informando -> valor único em TODAS as estações.
    linhas = exportar_csv_backmedina(dados, faixa=1, trilha=2).splitlines()[4:]
    assert len(linhas) == 105
    assert {l.split(";")[col["Estaca – Faixa"]] for l in linhas} == {"1"}
    assert {l.split(";")[col["Estaca – Trilha"]] for l in linhas} == {"2"}


def test_faixa_e_trilha_chegam_aos_csvs_por_segmento():
    dados = ler_solocap_xlsx(XLSX)
    df_seg, _ = segmentar(dados.tabela)
    arquivos = csvs_por_segmento(dados, df_seg, faixa=3, trilha=1)
    col = {name: i for i, name in enumerate(BACKMEDINA_HEADER)}
    assert arquivos
    for nome, texto in arquivos.items():
        linhas = texto.splitlines()[4:]
        assert linhas, nome
        assert {l.split(";")[col["Estaca – Faixa"]] for l in linhas} == {"3"}, nome
        assert {l.split(";")[col["Estaca – Trilha"]] for l in linhas} == {"1"}, nome


def test_valores_estaca_do_arquivo_le_csv_de_bacias():
    """No CSV de bacias as colunas existem: viram o valor inicial da UI."""
    from backmedina.io.csv_bacias import ler_csv_bacias

    template = Path(__file__).resolve().parents[1] / "templates" / "Modelo_Arquivo_Bacias.csv"
    assert valores_estaca_do_arquivo(ler_csv_bacias(template)) == (0, 0)
    # SOLOCAP não tem as colunas -> 0/0 sem estourar.
    assert valores_estaca_do_arquivo(ler_solocap_xlsx(XLSX)) == (0, 0)
