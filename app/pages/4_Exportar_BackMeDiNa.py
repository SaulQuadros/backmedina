"""Página 4 — Exportar CSV BackMeDiNa e planilha padronizada."""

from __future__ import annotations

import _bootstrap  # noqa: F401
import _sidebar
import streamlit as st

from backmedina.convert.backmedina_csv import (
    csvs_por_segmento,
    descricao_conversao_micrometro,
    exportar_csv_backmedina,
    exportar_csv_backmedina_bytes,
    valores_estaca_do_arquivo,
    zip_de_arquivos,
)
from backmedina.convert.resumo_seg import resumo_seg_xlsx_bytes
from backmedina.convert.standardize import exportar_xlsx_bytes

st.set_page_config(page_title="Exportar BackMeDiNa", page_icon="📤", layout="wide")
_sidebar.render()
st.title("📤 Exportar BackMeDiNa")

if "dados" not in st.session_state:
    st.info("Carregue um arquivo em **Importar e Converter** primeiro.")
    st.stop()

dados = st.session_state["dados"]

st.info("🔎 " + descricao_conversao_micrometro(dados))

secao = st.text_input(
    "Nome da SEÇÃO (cabeçalho do CSV)", value=dados.metadados.secao()
)

# Faixa/Trilha são definidas em "Segmentação Homogênea" e valem para todas as
# estações. Sem passar por lá, cai no valor do arquivo de entrada (ou 0).
_faixa_arq, _trilha_arq = valores_estaca_do_arquivo(dados)
faixa = st.session_state.get("estaca_faixa", _faixa_arq)
trilha = st.session_state.get("estaca_trilha", _trilha_arq)
st.caption(
    f"Identificação da estaca: **Faixa = {faixa}** · **Trilha = {trilha}** — "
    "definidas em **📐 Segmentação Homogênea**."
)

csv_txt = exportar_csv_backmedina(dados, secao=secao, faixa=faixa, trilha=trilha)

st.subheader("Prévia do CSV BackMeDiNa")
st.code("\n".join(csv_txt.splitlines()[:8]), language="text")

col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "⬇️ Baixar CSV BackMeDiNa",
        data=exportar_csv_backmedina_bytes(
            dados, secao=secao, faixa=faixa, trilha=trilha
        ),
        file_name=f"{secao or 'secao'}_backmedina.csv",
        mime="text/csv",
    )
with col2:
    st.download_button(
        "⬇️ Baixar planilha padronizada (.xlsx)",
        data=exportar_xlsx_bytes(dados),
        file_name="Tabela_padronizada.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.caption(
    "O CSV inclui o cabeçalho `BACKMEDINA` / `SEÇÃO:` / `RAIO (cm):` e as "
    "colunas d0…d210 **em µm**, pronto para importar no BackMeDiNa. "
    "Formato do arquivo: separador `;`, codificação **CP1252 (ANSI)** e fim de "
    "linha CRLF — exigências do importador. "
    "A planilha padronizada permanece em 0,01 mm (formato SOLOCAP)."
)

st.divider()
st.subheader("📦 Exportar por segmento (ZIP)")

df_seg = st.session_state.get("df_segmentado")
if df_seg is None:
    # Espelha o bloqueio do ConversorDadosFWD.
    st.warning(
        "Defina a segmentação (automática ou manual) antes de exportar os CSVs. "
        "Vá em **📐 Segmentação Homogênea** e gere os trechos."
    )
else:
    arquivos = csvs_por_segmento(dados, df_seg, faixa=faixa, trilha=trilha)
    n_csvs = len(arquivos)
    # Inclui o Resumo_Seg.xlsx (Segmento, Estacas, Comprimento, Dm, σ, Dc).
    segmentos = st.session_state.get("segmentos")
    if segmentos:
        arquivos["Resumo_Seg.xlsx"] = resumo_seg_xlsx_bytes(
            segmentos,
            desvio_label=st.session_state.get("desvio_label", "Amostral (n−1)"),
        )
    st.write(
        f"**{n_csvs} segmento(s)** — um CSV BackMeDiNa por trecho "
        "(`seg_01.csv`, `seg_02.csv`, …) em **µm** + **`Resumo_Seg.xlsx`** "
        "(Dm, σ, Dc por trecho)."
    )
    st.download_button(
        "⬇️ Baixar ZIP (CSVs por segmento + Resumo_Seg.xlsx)",
        data=zip_de_arquivos(arquivos),
        file_name="backmedina_segmentos.zip",
        mime="application/zip",
        type="primary",
    )
    with st.expander("Prévia — arquivos no ZIP"):
        for nome in arquivos:
            st.write(f"• {nome}")
        st.code("\n".join(arquivos["seg_01.csv"].splitlines()[:6]), language="text")
