from pathlib import Path

import pandas as pd
import pytest

from backmedina.convert.backmedina_csv import exportar_csv_backmedina
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
    assert linhas[0] == "BACKMEDINA"
    assert linhas[1].startswith("SEÇÃO:")
    assert linhas[2] == "RAIO (cm): 15"
    assert linhas[3].split(",") == list(BACKMEDINA_HEADER)
    # d0 da primeira estação = D1 = 44 (0,01 mm) -> 440 µm no BackMeDiNa.
    primeira = linhas[4].split(",")
    col = {name: i for i, name in enumerate(BACKMEDINA_HEADER)}
    assert primeira[col["d0"]] == "440"
    assert primeira[col["d180"]] == "30"  # D9 = 3 -> 30 µm
    assert primeira[col["Carga"]] == "4059"  # carga permanece em kgf


def test_export_xlsx_bytes_valido():
    dados = ler_solocap_xlsx(XLSX)
    data = exportar_xlsx_bytes(dados)
    assert data[:2] == b"PK"  # assinatura de arquivo .xlsx (zip)


def test_sensor_labels_completos():
    assert SENSOR_LABELS == ("d0", "d20", "d30", "d45", "d60", "d90", "d120", "d150", "d180")
