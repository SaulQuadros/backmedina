# Regras — Streamlit

Aplica-se a `app/**`.

- Páginas apenas **orquestram**: leem `st.session_state`, chamam o núcleo
  (`src/backmedina/*`) e renderizam. Nenhuma regra de engenharia na UI.
- Toda página começa com `import _bootstrap` (garante `src/` no `sys.path`).
- Estado compartilhado entre páginas via `st.session_state` (chaves: `dados`,
  `indices`, `segmentos`). Não recomputar o que já está no estado sem motivo.
- Preservar a estrutura de páginas (Home + `pages/1..4`) e a numeração dos arquivos
  (define a ordem no menu). Não alterar abas/textos não relacionados ao pedido.
- **Nunca** expor segredos, tokens ou caminhos absolutos sensíveis na interface.
- Plots via `plots/basins.py` (matplotlib backend `Agg`); exibir com `st.pyplot`.
- API atual: usar `width="stretch"` (não `use_container_width`, descontinuado).

**Verificação obrigatória (Streamlit):**
- `streamlit run app/streamlit_app.py` sobe sem traceback; a Home carrega.
- Páginas exercitadas headless com `streamlit.testing.v1.AppTest` sem `at.exception`
  (pré-carregar `st.session_state["dados"]` para as páginas 2-4).
- Conflito de porta: informar e sugerir `--server.port 8502`.
