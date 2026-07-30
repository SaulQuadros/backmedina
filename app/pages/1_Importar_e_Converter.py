"""Página 1 — Importar levantamento FWD, validar e converter."""

from __future__ import annotations

import tempfile
from pathlib import Path

import _bootstrap  # noqa: F401
import _sidebar
import streamlit as st

from backmedina.io.loader import carregar
from backmedina.io.validacao import validar
from backmedina.model.units import UnidadeDeflexao, detectar_unidade_explicita
from backmedina.plots.basins import plot_d0_por_estaca

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

    # --- Unidade da fonte ---------------------------------------------------
    # Vinha de um texto livre no arquivo, sem exibição nem correção possível: um
    # rótulo errado (ou ausente) contaminava índices, Rc, segmentação e o CSV
    # BackMeDiNa por um fator 10, em silêncio. Aqui fica visível e editável.
    _declarada = detectar_unidade_explicita(dados.metadados.unidade or "")
    _opcoes = [u.rotulo for u in UnidadeDeflexao]
    escolha = st.selectbox(
        "Unidade das deflexões no arquivo de origem",
        _opcoes,
        index=_opcoes.index(dados.unidade_deflexao.rotulo),
        help="Define como as deflexões serão interpretadas em TODO o fluxo. "
        "Os cálculos usam 0,01 mm e o CSV BackMeDiNa usa µm — a conversão é "
        "feita a partir desta escolha.",
    )
    # Sem `key=`: o índice vem do próprio estado, então a escolha persiste entre
    # reruns e é reinicializada quando um novo arquivo é carregado.
    dados.unidade_deflexao = next(
        u for u in UnidadeDeflexao if u.rotulo == escolha
    )
    if _declarada is None:
        st.warning(
            f"⚠️ O arquivo **não declara** a unidade das leituras — assumido "
            f"**{dados.unidade_deflexao.rotulo}**. Confirme acima antes de "
            "prosseguir: se estiver errada, todos os índices e o CSV "
            "BackMeDiNa saem com erro de 10×."
        )
    elif _declarada is not dados.unidade_deflexao:
        st.warning(
            f"⚠️ O arquivo declara **{_declarada.rotulo}**, mas você escolheu "
            f"**{dados.unidade_deflexao.rotulo}**. Vale a sua escolha."
        )
    else:
        st.caption(f"Unidade lida do arquivo: **{_declarada.rotulo}**.")

    avisos = validar(dados)
    if avisos:
        with st.expander(f"⚠️ Validação — {len(avisos)} aviso(s)", expanded=True):
            for a in avisos:
                st.warning(a)
    else:
        st.success("Validação sem avisos.")

    st.dataframe(dados.tabela, width="stretch", height=560)
    st.caption(
        f"{len(dados.tabela)} estações. Prossiga para **Índices de Bacia**, "
        "**Segmentação Homogênea** ou **Exportar BackMeDiNa**."
    )

    # Perfil de D0 ao longo do trecho — leitura rápida do levantamento recém-lido,
    # na mesma unidade da tabela acima (nenhuma conversão).
    st.subheader("Deflexão máxima (D0) ao longo do trecho")
    st.pyplot(
        plot_d0_por_estaca(
            dados.tabela, unidade_label=dados.unidade_deflexao.rotulo
        )
    )
    st.caption(
        "D0 é a deflexão do geofone central (D1/d0), por estação, em "
        f"**{dados.unidade_deflexao.rotulo}** — mesma unidade da tabela. As linhas "
        "tracejadas são a média D̄ e a deflexão característica **Dc = D̄ + σ** do "
        "trecho todo (σ amostral); a segmentação em trechos homogêneos fica em "
        "**📐 Segmentação Homogênea**."
    )
