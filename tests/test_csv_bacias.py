"""Regressão do caminho de entrada CSV de bacias.

Cobre o bug em que o loader não derivava a coluna "Metros" a partir de
"Estaca – Descolamento" (grafia real do template, com "c"), fazendo a
segmentação cair na 1ª coluna (a data) e o export zerar o deslocamento.
"""

from pathlib import Path

from backmedina.convert.backmedina_csv import exportar_csv_backmedina
from backmedina.io.csv_bacias import ler_csv_bacias
from backmedina.model.schema import (
    BACKMEDINA_HEADER,
    CSV_BACIAS_ENCODING,
    CSV_BACIAS_HEADER,
    CSV_BACIAS_SEP,
)
from backmedina.model.units import UnidadeDeflexao
from backmedina.segmentation.aashto_cumdiff import segmentar

TEMPLATE = (
    Path(__file__).resolve().parents[1] / "templates" / "Modelo_Arquivo_Bacias.csv"
)


def test_csv_bacias_deriva_metros():
    # O loader deve criar "Metros" a partir de "Estaca – Descolamento".
    dados = ler_csv_bacias(TEMPLATE)
    assert "Metros" in dados.tabela.columns
    assert list(dados.tabela["Metros"]) == [0.0, 20.0]
    # CSV de bacias já está em µm (nenhuma conversão de unidade na exportação).
    assert dados.unidade_deflexao is UnidadeDeflexao.MICROMETRO


def test_csv_bacias_export_preserva_deslocamento():
    # "Estaca – Deslocamento" no CSV BackMeDiNa não pode ser zerado pela
    # diferença de grafia Descolamento (entrada) vs Deslocamento (saída).
    dados = ler_csv_bacias(TEMPLATE)
    linhas = exportar_csv_backmedina(dados).splitlines()
    col = {name: i for i, name in enumerate(BACKMEDINA_HEADER)}
    assert linhas[3].split(",") == list(BACKMEDINA_HEADER)  # cabeçalho de colunas
    est2 = linhas[5].split(",")                             # 2ª estação de dados
    assert est2[col["Estaca – Deslocamento"]] == "20"       # antes vinha "0"
    # Bacias já em µm -> sem ×10 (d0 da 2ª estação permanece 712).
    assert est2[col["d0"]] == "712"


def _escrever_csv_bacias(tmp_path, n=20):
    """Gera um CSV de bacias sintético com degrau de deflexão (dois segmentos)."""
    linhas = [CSV_BACIAS_SEP * (len(CSV_BACIAS_HEADER) - 1)]  # 1ª linha em branco
    linhas.append(CSV_BACIAS_SEP.join(CSV_BACIAS_HEADER))
    for i in range(n):
        desl = i * 20
        base = 500 if i < n // 2 else 800  # degrau na metade -> troca de patamar
        bacia = [base, base - 100, base - 200, base - 300, base - 350,
                 base - 400, base - 450, base - 480, base - 500]
        campos = ["04/04/2018", "28", "55", "4000", str(i + 1), str(desl), "0", "0",
                  *[str(v) for v in bacia]]
        linhas.append(CSV_BACIAS_SEP.join(campos))
    caminho = tmp_path / "bacias.csv"
    caminho.write_text("\n".join(linhas), encoding=CSV_BACIAS_ENCODING)
    return caminho


def test_csv_bacias_segmentavel_por_metros(tmp_path):
    # Com "Metros" derivado, a segmentação usa a distância real (0..380 m),
    # não a 1ª coluna (a data). O degrau deve render >= 2 segmentos.
    dados = ler_csv_bacias(_escrever_csv_bacias(tmp_path, n=20))
    assert "Metros" in dados.tabela.columns
    _df_seg, segs = segmentar(
        dados.tabela, coluna_dist="Metros", coluna_d0="D1",
        unidade=dados.unidade_deflexao,
    )
    assert len(segs) >= 2
    assert max(s.fim_m for s in segs) >= 300  # cobre a via real, não uma data
