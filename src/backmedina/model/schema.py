"""Contratos de dados fixos do domínio FWD/BackMeDiNa.

Estas constantes são o "contrato" com o MeDiNa/BackMeDiNa e NÃO devem ser
alteradas sem autorização — mudá-las quebra a compatibilidade das saídas.

Referências: Rocha (2020), Machado (2019), manual do ConversorDadosFWD.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backmedina.model.units import UnidadeDeflexao

# --- Geometria do ensaio FWD ------------------------------------------------

# Raio da placa de carga (cm). Padrão brasileiro usado pelo BackMeDiNa.
RAIO_PLACA_CM: int = 15

# Distâncias radiais dos geofones em relação ao centro da carga (cm).
# Ordem = ordem física dos sensores da bacia de deflexão.
SENSOR_OFFSETS_CM: tuple[int, ...] = (0, 20, 30, 45, 60, 90, 120, 150, 180)

# Rótulos canônicos das deflexões (formato BackMeDiNa): d0, d20, ..., d180.
SENSOR_LABELS: tuple[str, ...] = tuple(f"d{o}" for o in SENSOR_OFFSETS_CM)

# Mapa autoritativo coluna SOLOCAP -> rótulo BackMeDiNa.
#   D1->d0, D2->d20, D3->d30, D4->d45, D5->d60,
#   D6->d90, D7->d120, D8->d150, D9->d180.
# D10 (geofone externo, ~210 cm) NÃO é usado pelo BackMeDiNa.
D_TO_SENSOR: dict[str, str] = {
    f"D{i + 1}": label for i, label in enumerate(SENSOR_LABELS)
}
SENSOR_TO_D: dict[str, str] = {v: k for k, v in D_TO_SENSOR.items()}

# Unidade das deflexões: 0,01 mm (= 10 micrômetros por unidade).
UNIDADE_DEFLEXAO: str = "x10⁻² mm"  # x10⁻² mm

# --- Layout da planilha SOLOCAP "Tabela" ------------------------------------

ABA_TABELA: str = "Tabela"
# Linhas (1-indexadas) do bloco de metadados: chave em col A, valor em col B.
LINHA_HEADER_COLUNAS: int = 13  # cabeçalho das colunas de dados
LINHA_PRIMEIRO_DADO: int = 14

# Chaves do bloco de metadados (col A), na ordem em que aparecem.
METADADOS_CHAVES: tuple[str, ...] = (
    "DATA",
    "RELATÓRIO N°",
    "OS Nº",
    "CLIENTE",
    "OBRA/TRECHO",
    "PISTA",
    "SENTIDO",
    "UNIDADE DAS LEITURAS",
)

# Cabeçalhos das colunas de dados da planilha SOLOCAP (ordem A->T).
COLUNAS_TABELA: tuple[str, ...] = (
    "Metros",
    "Target Load kN",
    "Target Load (Kgf)",
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10",
    "Temp Ar (°C)",
    "Temp Pav (°C)",
    "Latitude",
    "Longitude",
    "Raio",
    "Data e Hora",
    "Obs",
)

# Colunas numéricas que exigem parsing de número BR (vírgula decimal).
COLUNAS_NUMERICAS: tuple[str, ...] = (
    "Metros", "Target Load kN", "Target Load (Kgf)",
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10",
    "Temp Ar (°C)", "Temp Pav (°C)", "Latitude", "Longitude", "Raio",
)

# --- Layout do CSV de bacias (entrada B) ------------------------------------

CSV_BACIAS_SEP: str = ";"
CSV_BACIAS_ENCODING: str = "cp1252"
CSV_BACIAS_HEADER: tuple[str, ...] = (
    "Data de Execução",
    "Temp. Do Ar",
    "Temp. Do Pavimento",
    "Carga",
    "Estaca – Número",
    "Estaca – Descolamento",
    "Estaca – Faixa",
    "Estaca – Trilha",
    *SENSOR_LABELS,
)

# --- Layout do CSV BackMeDiNa (saída principal) -----------------------------
#
# Formato fiel ao arquivo aceito pelo BackMeDiNa (referência: Segmento_1.csv
# gerado pelo ConversorDadosFWD original). O importador é rígido: separador ';',
# encoding CP1252, fim de linha CRLF, rótulo e valor de `SEÇÃO:`/`RAIO (cm):`
# em CÉLULAS SEPARADAS e todas as linhas preenchidas até o nº total de colunas.

BACKMEDINA_MARCADOR: str = "BACKMEDINA"
BACKMEDINA_SEP: str = ";"
BACKMEDINA_ENCODING: str = "cp1252"
BACKMEDINA_EOL: str = "\r\n"

# O CSV do BackMeDiNa traz um 10º geofone (~210 cm) que NÃO entra nos cálculos
# (SENSOR_LABELS continua com os 9 sensores de Rocha). Vem de D10 do SOLOCAP.
SENSOR_LABEL_EXTRA: str = "d210"
BACKMEDINA_SENSOR_LABELS: tuple[str, ...] = (*SENSOR_LABELS, SENSOR_LABEL_EXTRA)

# Grafia real do template do BackMeDiNa: "Descolamento" (com "c") — igual a
# CSV_BACIAS_HEADER, o que permite reler a própria saída.
BACKMEDINA_COL_CHAINAGE: str = "Estaca – Descolamento"

BACKMEDINA_HEADER: tuple[str, ...] = (
    "Data de Execução",
    "Temp. Do Ar",
    "Temp. Do Pavimento",
    "Carga",
    "Estaca – Número",
    BACKMEDINA_COL_CHAINAGE,
    "Estaca – Faixa",
    "Estaca – Trilha",
    *BACKMEDINA_SENSOR_LABELS,
)


@dataclass
class MetadadosLevantamento:
    """Bloco de metadados do relatório FWD (cabeçalho da planilha)."""

    data: str = ""
    relatorio: str = ""
    os_numero: str = ""
    cliente: str = ""
    obra_trecho: str = ""
    pista: str = ""
    sentido: str = ""
    # Vazio por padrão: significa "o arquivo NÃO declarou a unidade". Um default
    # com 0,01 mm tornaria "não declarou" indistinguível de "declarou 0,01 mm",
    # e uma fonte em µm passaria a valer 10x. Quem decide o fallback é
    # `units.detectar_unidade`; a UI avisa quando a unidade foi presumida.
    unidade: str = ""

    def secao(self) -> str:
        """Nome da seção para o cabeçalho `SEÇÃO:` do CSV BackMeDiNa."""
        return self.pista or self.obra_trecho or "SEÇÃO"


@dataclass
class DadosFWD:
    """Resultado do parsing: metadados + tabela de bacias (DataFrame)."""

    metadados: MetadadosLevantamento
    # DataFrame com as colunas de COLUNAS_TABELA já convertidas para número.
    tabela: object  # pandas.DataFrame (evita import pesado no schema)
    origem: str = ""  # caminho/nome do arquivo de origem
    avisos: list[str] = field(default_factory=list)
    # Unidade em que as deflexões da tabela estão expressas (fonte).
    # SOLOCAP (xlsx/PDF) = 0,01 mm; CSV de bacias (BackMeDiNa) = µm.
    unidade_deflexao: UnidadeDeflexao = UnidadeDeflexao.DMM_001
