"""Unidades de deflexão e conversões.

Convenções do domínio:
- **0,01 mm** (`x10⁻² mm`): unidade dos levantamentos SOLOCAP (xlsx/PDF).
  Usada em TODOS os cálculos (Rc, PBD, segmentação, deflexão característica).
- **µm** (micrômetro): unidade exigida pelo **BackMeDiNa** na importação (CSV).

Relação dimensional: `1 unidade de 0,01 mm = 10 µm`.
Portanto `valor_µm = valor_0,01mm × 10`.
"""

from __future__ import annotations

import re
from enum import Enum


class UnidadeDeflexao(Enum):
    """Unidade em que as deflexões estão expressas."""

    DMM_001 = "0,01 mm"   # x10⁻² mm (SOLOCAP)
    MICROMETRO = "µm"     # micrômetro (BackMeDiNa)

    @property
    def rotulo(self) -> str:
        return self.value

    @property
    def fator_para_micrometro(self) -> float:
        """Multiplicador que leva um valor nesta unidade para µm."""
        return {UnidadeDeflexao.DMM_001: 10.0, UnidadeDeflexao.MICROMETRO: 1.0}[self]


def fator_conversao(origem: UnidadeDeflexao, destino: UnidadeDeflexao) -> float:
    """Fator para converter de `origem` para `destino` (multiplicativo)."""
    return origem.fator_para_micrometro / destino.fator_para_micrometro


# Marcadores textuais para detecção automática de unidade.
_MARCADORES_MICROMETRO = ("µm", "μm", "micrômetro", "micrometro", "micron")
_MARCADORES_DMM = (
    "x10", "10⁻²", "10-2", "10ˉ²", "10ˉ2", "0,01 mm", "0.01 mm",
)

# Grafia ASCII "um" — usada por equipamentos KUAB nos nomes de coluna
# (`D0_um`, `D1_um`, …). Marcador FRACO: só vale se nada mais decidiu, e exige
# que não haja letra colada, senão casaria dentro de "numero", "resumo",
# "volume", "algum". Daí o padrão, em vez de um simples `in`.
_LETRA = "a-záàâãéêíóôõúüçñ"
_RE_UM_ASCII = re.compile(rf"(?<![{_LETRA}])um(?![{_LETRA}])")


def detectar_unidade_explicita(texto: str) -> UnidadeDeflexao | None:
    """Unidade **declarada** no texto, ou ``None`` se nada for reconhecido.

    Diferente de :func:`detectar_unidade`, não inventa um padrão — permite à UI
    distinguir "o arquivo declarou 0,01 mm" de "não declarou nada e assumimos
    0,01 mm", que é onde nasce o erro de 10x.
    """
    t = (texto or "").lower()
    if any(k in t for k in _MARCADORES_MICROMETRO):
        return UnidadeDeflexao.MICROMETRO
    if any(k in t for k in _MARCADORES_DMM):
        return UnidadeDeflexao.DMM_001
    if _RE_UM_ASCII.search(t):
        return UnidadeDeflexao.MICROMETRO
    return None


def detectar_unidade(
    texto: str, default: UnidadeDeflexao = UnidadeDeflexao.DMM_001
) -> UnidadeDeflexao:
    """Detecta a unidade de deflexão a partir de um texto de metadado.

    Ex.: 'UNIDADE DAS LEITURAS (x10⁻² mm)' -> DMM_001; texto com 'µm' -> MICROMETRO.
    Retorna `default` quando nenhum marcador é reconhecido.
    """
    return detectar_unidade_explicita(texto) or default
