"""Sidebar compartilhado: abas Deflectometria (navegação) e Rastreabilidade.

Cada página chama `render()` logo após `st.set_page_config(...)`. Os campos de
rastreabilidade são preenchidos no próprio sidebar e ficam em
`st.session_state["projeto"]` (persistem entre as páginas).
"""

from __future__ import annotations

import streamlit as st

# Tipo de via ("Sistema") — exatamente as opções do MeDiNa
# (ref.: z_docs/pictures/00_sistema-vias-medina.png).
TIPOS_VIA = [
    "Sistema Arterial Primário",
    "Sistema Arterial Principal",
    "Sistema Arterial Secundário",
    "Sistema Coletor Primário",
    "Sistema Coletor Secundário",
    "Sistema Local",
]

CARACTERISTICAS_VIA = [
    "Pista simples",
    "Pista dupla (duplicada)",
    "Múltiplas pistas",
]

def _projeto_default() -> dict:
    return {
        "nome": "", "responsavel_tecnico": "", "empresa_lwd": "", "rodovia": "",
        "trecho": "", "km_inicial": 0.0, "km_final": 0.0,
        "tipo_via": TIPOS_VIA[0], "caracteristica_via": CARACTERISTICAS_VIA[0],
        "n_faixas": 2, "sentido": "", "data_fwd": "", "observacoes": "",
    }


def _idx(opcoes: list[str], valor) -> int:
    return opcoes.index(valor) if valor in opcoes else 0

_PAGINAS = [
    ("streamlit_app.py", "Início", "🏠"),
    ("pages/1_Importar_e_Converter.py", "Importar e Converter", "📥"),
    ("pages/2_Indices_de_Bacia.py", "Índices de Bacia", "📈"),
    ("pages/3_Segmentacao_Homogenea.py", "Segmentação Homogênea", "📐"),
    ("pages/4_Exportar_BackMeDiNa.py", "Exportar BackMeDiNa", "📤"),
    ("pages/5_Relatorio.py", "Relatório", "📄"),
]


def render() -> None:
    """Renderiza o sidebar (chamar após set_page_config em cada página)."""
    dados = st.session_state.get("dados")
    with st.sidebar:
        st.markdown("### 🛣️ Conversor FWD")
        aba_defl, aba_rastro = st.tabs(["Deflectometria", "Rastreabilidade"])

        with aba_defl:
            try:
                for caminho, rotulo, icone in _PAGINAS:
                    st.page_link(caminho, label=rotulo, icon=icone)
            except Exception:  # noqa: BLE001 (contexto sem MPA, ex.: AppTest)
                st.caption("Navegação disponível ao rodar o app (streamlit run).")
            if dados is not None:
                st.caption(f"Arquivo: {dados.origem} · {len(dados.tabela)} estações")

        with aba_rastro:
            _form_rastreabilidade(dados)


def _form_rastreabilidade(dados) -> None:
    st.caption("Dados do projeto (rastreabilidade técnica)")

    # Fonte única de verdade: um dict simples que SEMPRE persiste entre páginas.
    # Os widgets leem o default daqui (value=/index=) e gravam de volta o valor —
    # não dependemos da persistência de `key=` de widget entre páginas.
    proj = st.session_state.setdefault("projeto", _projeto_default())

    # Pré-preenchimento a partir dos metadados do arquivo (atualiza o dict e rerun).
    if dados is not None and st.button(
        "Preencher a partir do arquivo", use_container_width=True
    ):
        m = dados.metadados
        proj["empresa_lwd"] = m.cliente or proj.get("empresa_lwd", "")
        proj["trecho"] = m.obra_trecho or proj.get("trecho", "")
        proj["sentido"] = m.sentido or proj.get("sentido", "")
        if not proj.get("nome"):
            proj["nome"] = m.pista or m.obra_trecho
        st.rerun()

    proj["nome"] = st.text_input("Nome do projeto", value=proj.get("nome", ""))
    proj["responsavel_tecnico"] = st.text_input(
        "Responsável técnico", value=proj.get("responsavel_tecnico", "")
    )
    proj["empresa_lwd"] = st.text_input(
        "Empresa responsável (LWD/FWD)", value=proj.get("empresa_lwd", "")
    )
    proj["rodovia"] = st.text_input(
        "Rodovia / Identificação", value=proj.get("rodovia", "")
    )
    proj["trecho"] = st.text_input(
        "Trecho (descrição)", value=proj.get("trecho", "")
    )

    c1, c2 = st.columns(2)
    with c1:
        proj["km_inicial"] = st.number_input(
            "km inicial", value=float(proj.get("km_inicial", 0.0)),
            step=0.1, format="%.3f",
        )
    with c2:
        proj["km_final"] = st.number_input(
            "km final", value=float(proj.get("km_final", 0.0)),
            step=0.1, format="%.3f",
        )

    proj["tipo_via"] = st.selectbox(
        "Tipo de via (MeDiNa)", TIPOS_VIA, index=_idx(TIPOS_VIA, proj.get("tipo_via"))
    )
    proj["caracteristica_via"] = st.selectbox(
        "Característica da via", CARACTERISTICAS_VIA,
        index=_idx(CARACTERISTICAS_VIA, proj.get("caracteristica_via")),
    )
    proj["n_faixas"] = st.number_input(
        "Número de faixas", min_value=1, max_value=12, step=1,
        value=int(proj.get("n_faixas", 2)),
    )
    proj["sentido"] = st.text_input("Sentido", value=proj.get("sentido", ""))

    # Data do FWD: guarda o objeto date à parte (não vai no dict serializável).
    data_atual = st.date_input(
        "Data do FWD", value=st.session_state.get("_data_fwd_date"),
        format="DD/MM/YYYY",
    )
    st.session_state["_data_fwd_date"] = data_atual
    proj["data_fwd"] = data_atual.strftime("%d/%m/%Y") if data_atual else ""

    proj["observacoes"] = st.text_area(
        "Observações", value=proj.get("observacoes", ""), height=70
    )
