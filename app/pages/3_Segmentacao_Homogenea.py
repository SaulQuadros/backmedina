"""Página 3 — Segmentação homogênea (automática ou manual).

Reproduz os dois modos do ConversorDadosFWD: automática (diferenças acumuladas
AASHTO) e manual (marcação das fronteiras no gráfico, com validação de
comprimento mín./máx. e mensagens quando as regras não são atendidas).
"""

from __future__ import annotations

import _bootstrap  # noqa: F401
import _sidebar
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backmedina.convert.backmedina_csv import valores_estaca_do_arquivo
from backmedina.convert.zi_export import zi_xlsx_bytes
from backmedina.plots.basins import fig_para_png, plot_curva_z
from backmedina.report.apresentacao_zi import gerar_pdf_zi
from backmedina.report.relatorio_pdf import lualatex_disponivel
from backmedina.segmentation.aashto_cumdiff import (
    curva_zi_do_df,
    segmentar,
    segmentar_manual,
    tabela_zi,
)

st.set_page_config(page_title="Segmentação Homogênea", page_icon="📐", layout="wide")
_sidebar.render()
st.title("📐 Segmentação Homogênea")

if "dados" not in st.session_state:
    st.info("Carregue um arquivo em **Importar e Converter** primeiro.")
    st.stop()

dados = st.session_state["dados"]
df = dados.tabela

col_dist = "Metros" if "Metros" in df.columns else df.columns[0]
col_d0 = "D1" if "D1" in df.columns else ("d0" if "d0" in df.columns else None)
if col_d0 is None:
    st.error("Não foi possível identificar a coluna de deflexão máxima (D0/D1).")
    st.stop()

# --- controles comuns -------------------------------------------------------
c1, c2, c3 = st.columns(3)
with c1:
    comp_min = st.number_input(
        "Seg. mín (m)", min_value=20.0, max_value=2000.0, value=100.0, step=20.0
    )
with c2:
    comp_max = st.number_input(
        "Seg. máx (m)", min_value=200.0, max_value=10000.0, value=2000.0, step=100.0
    )
with c3:
    desvio_opt = st.selectbox(
        "Desvio-padrão (Dc = Dm + σ)", ["Amostral (n−1)", "Populacional (n)"]
    )
ddof = 1 if desvio_opt.startswith("Amostral") else 0

# Validação dos limites (mensagem verbatim do ConversorDadosFWD).
if comp_min > comp_max:
    st.error("O comprimento mínimo não pode ser maior que o máximo.")
    st.stop()

# Cálculo detalhado de Zi (independe do modo) — para rastreabilidade/estudo.
_tab_zi, _totais_zi = tabela_zi(
    df, coluna_dist=col_dist, coluna_d0=col_d0, unidade=dados.unidade_deflexao
)
st.download_button(
    "⬇️ Baixar cálculo detalhado do Zi (xlsx)",
    data=zi_xlsx_bytes(_tab_zi, _totais_zi),
    file_name="calculo_zi.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    help="Passo a passo: D̄ᵢ, Δlᵢ, Aᵢ, ΣAᵢ, ΣΔlᵢ, Zi + A_c, L_c, tanα (0,01 mm).",
)

modo = st.radio(
    "Segmentação", ["Segmentação automática", "Manual"], horizontal=True,
)
# Começam em 0. Exceção: se o arquivo de entrada já trouxer as colunas (caso do
# CSV de bacias), esse valor vira o inicial — para não descartar dado importado.
_faixa_arq, _trilha_arq = valores_estaca_do_arquivo(dados)
st.session_state.setdefault("estaca_faixa", _faixa_arq)
st.session_state.setdefault("estaca_trilha", _trilha_arq)

cf1, cf2, cf3 = st.columns(3, vertical_alignment="bottom")
with cf1:
    circuito_fechado = st.checkbox(
        "Circuito fechado",
        help="Marque quando o início da via coincide com o fim (valida também o "
        "trecho circular). Aplica-se ao modo manual.",
    )
# Faixa/Trilha: preenchimento opcional do usuário — se não mexer, ficam 0.
# Vão para as colunas homônimas do CSV BackMeDiNa, iguais em todas as estações.
with cf2:
    st.number_input(
        "Estaca – Faixa", min_value=0, max_value=99, step=1, key="estaca_faixa",
        help="Opcional. Faixa de tráfego do levantamento, na coluna "
        "`Estaca – Faixa` do CSV BackMeDiNa. Deixe 0 se não se aplicar.",
    )
with cf3:
    st.number_input(
        "Estaca – Trilha", min_value=0, max_value=99, step=1, key="estaca_trilha",
        help="Opcional. Trilha de roda do levantamento, na coluna "
        "`Estaca – Trilha` do CSV BackMeDiNa. Deixe 0 se não se aplicar.",
    )


def _tabela(segmentos) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Segmento": s.indice,
                "Início (m)": s.ini_m,
                "Fim (m)": s.fim_m,
                "Comprimento (m)": s.comprimento_m,
                "Nº pontos": s.n_pontos,
                "Dm (D0 médio)": round(s.d0_media, 2),
                "σ": round(s.d0_desvio, 2),
                "Dc (Dm + σ)": round(s.d0_caracteristica, 2),
            }
            for s in segmentos
        ]
    )


def _mostrar_resultado(df_seg, segmentos):
    st.session_state["segmentos"] = segmentos
    st.session_state["df_segmentado"] = df_seg  # base p/ exportar por segmento
    st.session_state["desvio_label"] = desvio_opt  # p/ o Resumo_Seg.xlsx
    st.caption(
        "Dc (deflexão característica) em **0,01 mm** (unidade do MeDiNa). "
        f"Trechos entre **{comp_min:g} m** e **{comp_max:g} m** — "
        f"σ {desvio_opt.lower()}."
    )
    st.subheader(f"Segmentos: {len(segmentos)}")
    tab = _tabela(segmentos)
    st.dataframe(tab, width="stretch")
    st.download_button(
        "Baixar segmentos (CSV)",
        data=tab.to_csv(index=False).encode("utf-8"),
        file_name="segmentos_homogeneos.csv",
        mime="text/csv",
    )
    fig = plot_curva_z(df_seg, coluna_dist=col_dist)
    st.pyplot(fig)

    # PDF autocontido do cálculo de Zi (método + gráfico + tabela + trechos).
    if lualatex_disponivel():
        if st.button("Gerar PDF do cálculo de Zi", key="btn_pdf_zi"):
            with st.spinner("Compilando PDF (Pagella, sem Type 1)…"):
                tab_zi, tot_zi = tabela_zi(
                    df, coluna_dist=col_dist, coluna_d0=col_d0,
                    unidade=dados.unidade_deflexao,
                )
                try:
                    st.session_state["_pdf_zi"] = gerar_pdf_zi(
                        tab_zi, tot_zi, segmentos, fig_para_png(fig)
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Falha ao gerar PDF: {exc}")
        if "_pdf_zi" in st.session_state:
            st.download_button(
                "⬇️ Baixar PDF do cálculo de Zi",
                data=st.session_state["_pdf_zi"],
                file_name="calculo_zi.pdf",
                mime="application/pdf",
            )
    else:
        st.caption("PDF do Zi requer lualatex (ver `packages.txt` para nuvem).")


# ===========================================================================
if modo == "Segmentação automática":
    df_seg, segmentos = segmentar(
        df, coluna_dist=col_dist, coluna_d0=col_d0,
        comprimento_min_m=comp_min, comprimento_max_m=comp_max,
        unidade=dados.unidade_deflexao, ddof=ddof,
    )
    _mostrar_resultado(df_seg, segmentos)

else:  # ---------------------------- Manual --------------------------------
    # A marcação manual ocorre sobre a MESMA curva da automática: Zi × distância.
    dist_v, z = curva_zi_do_df(
        df, coluna_dist=col_dist, coluna_d0=col_d0, unidade=dados.unidade_deflexao
    )
    metros = list(map(float, dist_v))

    CHAVE = "fronteiras_manuais"
    st.session_state.setdefault(CHAVE, [])

    st.info(
        "Marque no gráfico da **curva Zi (diferenças acumuladas)** os pontos que "
        "delimitam os segmentos homogêneos, considerando as distâncias máximas e "
        "mínimas definidas. As fronteiras ficam nos vértices (mudanças de "
        "inclinação) de Zi."
    )

    # Gráfico interativo da curva Zi (clique num ponto adiciona a fronteira).
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=metros, y=list(map(float, z)), mode="lines+markers",
                   name="Zi", marker=dict(size=6))
    )
    for b in st.session_state[CHAVE]:
        fig.add_vline(x=b, line_dash="dash", line_color="red")
    fig.update_layout(
        xaxis_title="Distância (m)",
        yaxis_title="Zi (diferenças acumuladas)",
        height=400, margin=dict(l=10, r=10, t=30, b=10),
    )
    evento = st.plotly_chart(
        fig, key="zi_plot", on_select="rerun", selection_mode=("points", "box"),
    )

    # Une os pontos clicados às fronteiras (mapeando à estação mais próxima).
    pts = []
    try:
        pts = evento["selection"]["points"]
    except (KeyError, TypeError):
        pts = []
    if pts:
        def _mais_proxima(x):
            return min(metros, key=lambda m: abs(m - x))
        novas = {_mais_proxima(float(p["x"])) for p in pts if "x" in p}
        uniao = sorted(set(st.session_state[CHAVE]) | novas)
        if uniao != st.session_state[CHAVE]:
            st.session_state[CHAVE] = uniao
            st.rerun()

    # Lista (alternativa/acessível) — editor autoritativo das fronteiras.
    escolha = st.multiselect(
        "Fronteiras (m)", options=metros, default=st.session_state[CHAVE],
        help="Estações que iniciam um novo trecho.",
    )
    if sorted(escolha) != st.session_state[CHAVE]:
        st.session_state[CHAVE] = sorted(escolha)
        st.rerun()

    if st.button("Partir das fronteiras da automática"):
        _, segs_auto = segmentar(
            df, coluna_dist=col_dist, coluna_d0=col_d0,
            comprimento_min_m=comp_min, comprimento_max_m=comp_max,
            unidade=dados.unidade_deflexao, ddof=ddof,
        )
        seed = sorted(float(s.ini_m) for s in segs_auto if s.ini_m > metros[0])
        st.session_state[CHAVE] = seed
        st.rerun()

    n_marc = len(st.session_state[CHAVE])
    prev = (n_marc if circuito_fechado else n_marc + 1) if n_marc else (
        0 if circuito_fechado else 1
    )
    st.write(f"**Segmentos: {prev}**  ·  fronteiras marcadas: {n_marc}")

    b1, b2, b3 = st.columns(3)
    if b1.button("Desfazer", disabled=n_marc == 0):
        st.session_state[CHAVE] = st.session_state[CHAVE][:-1]
        st.rerun()
    if b2.button("Limpar seleção", disabled=n_marc == 0):
        st.session_state[CHAVE] = []
        st.rerun()
    segmentar_agora = b3.button("Segmentar Trechos", type="primary")

    if segmentar_agora:
        df_seg, segmentos, violacoes = segmentar_manual(
            df, st.session_state[CHAVE],
            coluna_dist=col_dist, coluna_d0=col_d0,
            comprimento_min_m=comp_min, comprimento_max_m=comp_max,
            unidade=dados.unidade_deflexao, ddof=ddof,
            circuito_fechado=circuito_fechado,
        )
        if violacoes:
            st.error(
                "Segmentação **não aplicada** — as regras não foram atendidas:"
            )
            for v in violacoes:
                st.write("• " + v)
        else:
            st.success("Segmentação manual aplicada com sucesso.")
            _mostrar_resultado(df_seg, segmentos)
