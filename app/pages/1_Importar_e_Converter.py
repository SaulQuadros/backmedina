"""Página 1 — Importar levantamento FWD, validar e converter."""

from __future__ import annotations

import tempfile
from pathlib import Path

import _bootstrap  # noqa: F401
import _sidebar
import streamlit as st

from backmedina.io.loader import carregar
from backmedina.io.validacao import validar

st.set_page_config(page_title="Importar e Converter", page_icon="📥", layout="wide")
_sidebar.render()
st.title("📥 Importar e Converter")

st.markdown(
    "Carregue a planilha SOLOCAP (`.xlsx`), o CSV de bacias **ou** o relatório "
    "**PDF** do levantamento FWD (SOLOCAP/SWECO)."
)

col_a, col_b = st.columns([2, 1])
with col_a:
    arquivo = st.file_uploader(
        "Arquivo FWD (.xlsx, .csv ou .pdf)", type=["xlsx", "csv", "pdf"]
    )
with col_b:
    exemplo = _bootstrap.DIR_EXEMPLO / "2-UFJF-VIA_LOCAL_FX1-FWD.xlsx"
    usar_exemplo = st.button(
        "Usar arquivo de exemplo (UFJF)", disabled=not exemplo.exists()
    )

caminho: Path | None = None
if arquivo is not None:
    suf = Path(arquivo.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suf)
    tmp.write(arquivo.getbuffer())
    tmp.flush()
    caminho = Path(tmp.name)
    nome_origem = arquivo.name
elif usar_exemplo:
    caminho = exemplo
    nome_origem = exemplo.name

if caminho is not None:
    try:
        dados = carregar(caminho)
        dados.origem = nome_origem
        st.session_state["dados"] = dados
    except Exception as exc:  # noqa: BLE001
        st.error(f"Falha ao ler o arquivo: {exc}")
        st.stop()

if "dados" in st.session_state:
    dados = st.session_state["dados"]
    st.subheader(f"Dados carregados — {dados.origem}")

    m = dados.metadados
    if m.cliente or m.obra_trecho:
        st.write(
            {
                "Cliente": m.cliente,
                "Obra/Trecho": m.obra_trecho,
                "Pista": m.pista,
                "Relatório": m.relatorio,
            }
        )

    avisos = validar(dados)
    if avisos:
        with st.expander(f"⚠️ Validação — {len(avisos)} aviso(s)", expanded=True):
            for a in avisos:
                st.warning(a)
    else:
        st.success("Validação sem avisos.")

    st.dataframe(dados.tabela, width="stretch", height=360)
    st.caption(
        f"{len(dados.tabela)} estações. Prossiga para **Índices de Bacia**, "
        "**Segmentação Homogênea** ou **Exportar BackMeDiNa**."
    )
