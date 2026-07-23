"""Página 2 — Índices da bacia deflectométrica (PBD, Rocha 2020)."""

from __future__ import annotations

import _bootstrap  # noqa: F401
import _sidebar
import pandas as pd
import streamlit as st

from backmedina.analytics.benchmarks import (
    BENCHMARKS,
    CLASSE_EMOJI,
    classificar,
    resumo_por_classe,
)
from backmedina.analytics.pbd_glossario import GLOSSARIO_PBD
from backmedina.analytics.pbd_indices import indices_com_contexto
from backmedina.model.units import UnidadeDeflexao, fator_conversao
from backmedina.plots.basins import plot_bacias

st.set_page_config(page_title="Índices de Bacia", page_icon="📈", layout="wide")
_sidebar.render()
st.title("📈 Índices de Bacia (PBD)")

if "dados" not in st.session_state:
    st.info("Carregue um arquivo em **Importar e Converter** primeiro.")
    st.stop()

dados = st.session_state["dados"]
df = dados.tabela

st.markdown(
    "Parâmetros da Bacia Deflectométrica: **Rc** (raio de curvatura, m), "
    "**AREA** (cm), **SCI**, **BDI**, **BCI**, **CF** (0,01 mm) e **S** (%)."
)
st.caption(
    f"Índices calculados em **0,01 mm** (unidade das fórmulas). "
    f"Unidade da fonte: **{dados.unidade_deflexao.rotulo}**."
)

# Índices sempre em 0,01 mm (normalização interna conforme a unidade da fonte).
indices = indices_com_contexto(df, unidade=dados.unidade_deflexao)
st.session_state["indices"] = indices

st.dataframe(indices.round(3), width="stretch", height=360)

st.download_button(
    "Baixar índices (CSV)",
    data=indices.to_csv(index=False).encode("utf-8"),
    file_name="indices_pbd.csv",
    mime="text/csv",
)

with st.expander("📖 Glossário técnico — o que é e para que serve cada parâmetro"):
    st.caption(
        "Deflexões em 0,01 mm; sensores a 0/20/30/45/60/90/120/150/180 cm do "
        "centro da carga. Referência: Rocha (2020)."
    )
    for g in GLOSSARIO_PBD:
        st.markdown(
            f"**{g['sigla']} — {g['nome']}**  ·  _{g['unidade']}_\n\n"
            f"`{g['formula']}`\n\n"
            f"**O que é:** {g['o_que_e']}\n\n"
            f"**Para que serve:** {g['para_que_serve']}"
        )
        st.divider()

# --- Classificação estrutural (benchmarks de Horak) ------------------------
st.subheader("Classificação estrutural (benchmarks de Horak)")

_temp_col = next(
    (c for c in ("Temp Pav (°C)", "Temp. Do Pavimento") if c in df.columns), None
)
_tem_temp = _temp_col is not None

tipo_base = st.selectbox("Tipo de base (benchmark)", list(BENCHMARKS.keys()))
benchmark = BENCHMARKS[tipo_base]
st.caption(
    "Limiares Sadio/Alerta/Crítico (µm) — "
    + " · ".join(
        f"**{k}**: <{int(v[0])} / {int(v[0])}–{int(v[1])} / >{int(v[1])}"
        for k, v in benchmark.items()
    )
)

c1, c2, c3 = st.columns(3)
corrigir = c1.checkbox(
    "Corrigir SCI por temperatura", value=_tem_temp, disabled=not _tem_temp,
    help="Usa a temperatura do pavimento por estação. BDI/BCI não são corrigidos "
    "(camadas profundas não dependem da temperatura).",
)
temp_ref = c2.number_input(
    "Temp. de referência (°C)", value=25.0, min_value=0.0, max_value=60.0,
    step=1.0, disabled=not corrigir,
)
coef = c3.number_input(
    "Sensibilidade (fração/°C)", value=0.020, min_value=0.0, max_value=0.10,
    step=0.005, format="%.3f", disabled=not corrigir,
    help="Ex.: 0,020 = 2%/°C. Calibre conforme a espessura do revestimento.",
)

_corr_ativa = corrigir and _tem_temp
_temp_pav = (
    pd.to_numeric(df[_temp_col], errors="coerce").to_numpy() if _tem_temp else None
)
tab_class = classificar(
    indices, temp_pav=_temp_pav, temp_ref=temp_ref, coef_por_grau=coef,
    corrigir=_corr_ativa, benchmark=benchmark,
)

# Guarda para o relatório (página Relatório).
_nota = f"Benchmarks de Horak — {tipo_base}"
if _corr_ativa:
    _nota += f"; SCI corrigido para {temp_ref:g} °C ({coef * 100:g} %/°C)"
else:
    _nota += "; sem correção de temperatura"
st.session_state["classificacao"] = {
    "resumo": resumo_por_classe(tab_class),
    "nota": _nota,
}

_classe_cols = [c for c in tab_class.columns if c.startswith("Classe")]
tab_show = tab_class.copy()
for _c in _classe_cols:
    tab_show[_c] = tab_show[_c].map(lambda v: CLASSE_EMOJI.get(v, v))
st.dataframe(tab_show, width="stretch", height=340)

# Resumo por classe
linhas_resumo = []
for col in _classe_cols:
    vc = tab_class[col].value_counts()
    partes = " · ".join(f"{cl}: {int(n)}" for cl, n in vc.items())
    linhas_resumo.append(f"**{col.replace('Classe ', '')}** — {partes}")
st.markdown("Resumo (nº de estações):  \n" + "  \n".join(linhas_resumo))

st.download_button(
    "Baixar classificação (CSV)",
    data=tab_class.to_csv(index=False).encode("utf-8"),
    file_name="classificacao_horak.csv",
    mime="text/csv",
)
st.caption(
    "⚠ Benchmarks de **Horak (2008)** para **base granular**, carga **40 kN**, "
    "deflexões em **µm** (índices convertidos de 0,01 mm ×10). SCI/BDI/BCI escalam "
    "com a carga (normalize a 40 kN). Só o **SCI** é corrigido por temperatura; "
    "o coeficiente deve ser calibrado à espessura do revestimento. "
    "SCI=camadas superiores · BDI=base · BCI=subleito."
)

st.subheader("Bacias de deflexão")
opcao = st.radio(
    "Unidade do gráfico", ["0,01 mm", "µm"], horizontal=True,
    help="Apenas exibição — não altera os cálculos.",
)
destino = (
    UnidadeDeflexao.MICROMETRO if opcao == "µm" else UnidadeDeflexao.DMM_001
)
fator = fator_conversao(dados.unidade_deflexao, destino)
st.pyplot(plot_bacias(df, unidade_label=opcao, fator=fator))
