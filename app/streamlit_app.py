"""Conversor de Dados FWD — app Streamlit (Home).

Reimplementação aberta do ConversorDadosFWD: importa levantamentos FWD
(planilha SOLOCAP .xlsx ou CSV de bacias), padroniza, calcula índices de bacia
(PBD), faz segmentação homogênea e exporta CSV compatível com o BackMeDiNa.
"""

from __future__ import annotations

import _bootstrap  # noqa: F401  (garante src/ no sys.path)
import _sidebar
import streamlit as st

st.set_page_config(
    page_title="Conversor de Dados FWD",
    page_icon="🛣️",
    layout="wide",
)
_sidebar.render()

st.title("🛣️ Conversor de Dados FWD")
st.caption(
    "Deflectometria (FWD) em pavimentos flexíveis → fluxo MeDiNa / BackMeDiNa"
)

st.markdown(
    """
Bem-vindo. Este aplicativo reestrutura, em Python/Streamlit, a ferramenta
**ConversorDadosFWD**. Use as páginas na barra lateral, nesta ordem:

1. **Importar e Converter** — carregue a planilha SOLOCAP (`.xlsx`) ou o CSV de
   bacias, valide os dados e exporte o **CSV BackMeDiNa** e a planilha padronizada.
2. **Índices de Bacia** — calcule os parâmetros PBD (Rc, AREA, SCI, BDI, BCI, CF, S).
3. **Segmentação Homogênea** — divida a via em trechos homogêneos (diferenças
   acumuladas AASHTO) e obtenha a **deflexão característica** por segmento.
4. **Exportar BackMeDiNa** — baixe o CSV final para retroanálise no BackMeDiNa.

**Unidades:** deflexões em `0,01 mm`; carga em `kN`/`kgf`; sensores a
`0, 20, 30, 45, 60, 90, 120, 150, 180 cm` do centro da placa (raio `15 cm`).
"""
)

if "dados" in st.session_state:
    d = st.session_state["dados"]
    st.success(
        f"Arquivo carregado: **{d.origem}** — {len(d.tabela)} estações. "
        "Prossiga pelas páginas ao lado."
    )
else:
    st.info("Nenhum arquivo carregado ainda. Comece por **Importar e Converter**.")
