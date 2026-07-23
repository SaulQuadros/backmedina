"""Conteúdo comum dos relatórios (rastreabilidade + resumo da segmentação).

Usado tanto pela geração PDF (LaTeX) quanto DOCX, para que os dois formatos
mostrem exatamente as mesmas informações.
"""

from __future__ import annotations

TITULO = "Relatório de Retroanálise — Deflectometria FWD"


def _num_br(v, casas: int = 2) -> str:
    """Formata número com vírgula decimal (padrão BR)."""
    try:
        return f"{float(v):.{casas}f}".replace(".", ",")
    except (TypeError, ValueError):
        return "—"


def linhas_rastreabilidade(projeto: dict | None, metadados) -> list[tuple[str, str]]:
    """Pares (rótulo, valor) dos dados de rastreabilidade do projeto."""
    p = projeto or {}
    m = metadados

    def val(x) -> str:
        s = "" if x is None else str(x).strip()
        return s or "—"

    km_ini, km_fim = p.get("km_inicial", 0.0), p.get("km_final", 0.0)
    km = f"{_num_br(km_ini, 3)} – {_num_br(km_fim, 3)}"
    carac = p.get("caracteristica_via", "")
    faixas = p.get("n_faixas", "")
    carac_txt = f"{carac} ({faixas} faixas)" if carac else "—"

    linhas = [
        ("Projeto", val(p.get("nome"))),
        ("Responsável técnico", val(p.get("responsavel_tecnico"))),
        ("Empresa responsável (LWD/FWD)", val(p.get("empresa_lwd"))),
        ("Rodovia / Identificação", val(p.get("rodovia"))),
        ("Trecho", val(p.get("trecho"))),
        ("km inicial – final", km),
        ("Tipo de via (MeDiNa)", val(p.get("tipo_via"))),
        ("Característica da via", carac_txt),
        ("Sentido", val(p.get("sentido"))),
        ("Data do FWD", val(p.get("data_fwd"))),
        ("Cliente", val(getattr(m, "cliente", "") if m else "")),
        (
            "Relatório / OS",
            val(
                f"{getattr(m, 'relatorio', '')} / {getattr(m, 'os_numero', '')}"
                if m else ""
            ),
        ),
        ("Observações", val(p.get("observacoes"))),
    ]
    return linhas


RESUMO_CABECALHO = ["Segmento", "Estacas (m)", "Comp. (m)", "Dm", "σ", "Dc"]


def linhas_resumo(segmentos) -> list[list[str]]:
    """Linhas da tabela-resumo da segmentação (deflexões em 0,01 mm)."""
    linhas = []
    for s in segmentos:
        linhas.append(
            [
                f"seg_{s.indice:02d}",
                f"{s.ini_m:g}–{s.fim_m:g}",
                f"{s.comprimento_m:.0f}",
                _num_br(s.d0_media),
                _num_br(s.d0_desvio),
                _num_br(s.d0_caracteristica),
            ]
        )
    return linhas


def legenda_resumo(desvio_label: str = "Amostral (n−1)") -> str:
    return (
        "Deflexões em 0,01 mm. Dm = deflexão média · "
        f"σ = desvio padrão ({desvio_label}) · Dc = Dm + σ."
    )
