"""Página 5 — Relatório do projeto (PDF e Word) com rastreabilidade + segmentação."""

from __future__ import annotations

import _bootstrap  # noqa: F401
import _sidebar
import streamlit as st

from backmedina.plots.basins import fig_para_png, plot_curva_z
from backmedina.report.relatorio_docx import gerar_docx
from backmedina.report.relatorio_pdf import (
    gerar_pdf,
    lualatex_disponivel,
    verificar_sem_type1,
)

st.set_page_config(page_title="Relatório", page_icon="📄", layout="wide")
_sidebar.render()
st.title("📄 Relatório do Projeto")

if "dados" not in st.session_state:
    st.info("Carregue um arquivo em **Importar e Converter** primeiro.")
    st.stop()

dados = st.session_state["dados"]
df_seg = st.session_state.get("df_segmentado")
segmentos = st.session_state.get("segmentos")

if df_seg is None or not segmentos:
    st.warning(
        "Defina a segmentação (automática ou manual) em **📐 Segmentação "
        "Homogênea** antes de gerar o relatório."
    )
    st.stop()

projeto = st.session_state.get("projeto", {})
desvio_label = st.session_state.get("desvio_label", "Amostral (n−1)")
classificacao = st.session_state.get("classificacao")

if classificacao is None:  # fallback (caso não tenha passado por Índices de Bacia)
    import pandas as pd

    from backmedina.analytics.benchmarks import classificar, resumo_por_classe
    from backmedina.analytics.pbd_indices import indices_com_contexto

    idx = st.session_state.get("indices")
    if idx is None:
        idx = indices_com_contexto(dados.tabela, unidade=dados.unidade_deflexao)
    _tcol = next(
        (c for c in ("Temp Pav (°C)", "Temp. Do Pavimento") if c in dados.tabela.columns),
        None,
    )
    _temp = (
        pd.to_numeric(dados.tabela[_tcol], errors="coerce").to_numpy()
        if _tcol else None
    )
    _tc = classificar(idx, temp_pav=_temp, corrigir=_temp is not None)
    _nota = "Benchmarks de Horak — Base granular; " + (
        "SCI corrigido para 25 °C (2 %/°C)" if _temp is not None else "sem correção"
    )
    classificacao = {"resumo": resumo_por_classe(_tc), "nota": _nota}

st.markdown(
    "O relatório inclui os **dados de rastreabilidade** (aba Rastreabilidade do "
    "sidebar), a **imagem da segmentação** (curva Zi), o **resumo** dos trechos "
    "(Dm, σ, Dc) e a **classificação estrutural (Horak)**. Formato 14×21 cm."
)

col_dist = "Metros" if "Metros" in df_seg.columns else df_seg.columns[0]
zi_png = fig_para_png(plot_curva_z(df_seg, coluna_dist=col_dist))

c1, c2 = st.columns(2)

# --- Word (.docx) ---
with c1:
    st.subheader("Word (.docx)")
    docx_bytes = gerar_docx(
        projeto, dados.metadados, segmentos, zi_png, desvio_label, classificacao
    )
    st.download_button(
        "⬇️ Baixar relatório (.docx)",
        data=docx_bytes,
        file_name="relatorio_retroanalise.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    st.caption("Fonte Palatino Linotype (família Palatino).")

# --- PDF (lualatex + TeX Gyre Pagella) ---
with c2:
    st.subheader("PDF (LuaLaTeX + Pagella)")
    if not lualatex_disponivel():
        st.info(
            "PDF requer **lualatex** (TeX com LuaLaTeX + família tex-gyre). "
            "Disponível localmente; na nuvem, ver `packages.txt`. Use o .docx "
            "enquanto isso."
        )
    elif st.button("Gerar relatório (PDF)", type="primary"):
        with st.spinner("Compilando PDF (Pagella, sem Type 1)…"):
            try:
                pdf = gerar_pdf(
                    projeto, dados.metadados, segmentos, zi_png, desvio_label,
                    classificacao,
                )
                ok, tipos = verificar_sem_type1(pdf)
                st.session_state["_rel_pdf"] = pdf
                st.session_state["_rel_pdf_ok"] = ok
                st.session_state["_rel_pdf_tipos"] = tipos
            except Exception as exc:  # noqa: BLE001
                st.error(f"Falha ao gerar PDF: {exc}")

    if "_rel_pdf" in st.session_state:
        st.download_button(
            "⬇️ Baixar relatório (.pdf)",
            data=st.session_state["_rel_pdf"],
            file_name="relatorio_retroanalise.pdf",
            mime="application/pdf",
        )
        if st.session_state.get("_rel_pdf_ok"):
            st.success("✔ Fontes OpenType/CFF (CID Type 0C) — sem Type 1.")
        else:
            st.error("⚠ Detectada fonte Type 1 no PDF — revisar.")
        st.caption("Fontes: " + ", ".join(st.session_state.get("_rel_pdf_tipos", [])))
