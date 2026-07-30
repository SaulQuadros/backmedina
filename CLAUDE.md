# CLAUDE.md — Conversor de Dados FWD (backmedina)

## 1. Objetivo do projeto
Reestruturar, em Python/Streamlit, a ferramenta Windows `ConversorDadosFWD`.
O app importa levantamentos de deflectometria **FWD** (planilha SOLOCAP `.xlsx`
ou CSV de bacias), valida e padroniza os dados, calcula índices da bacia
deflectométrica (PBD), faz **segmentação homogênea** e exporta um **CSV
compatível com o BackMeDiNa** para retroanálise no fluxo **MeDiNa**.

## 2. Papel do Claude Code
Implementar e evoluir os módulos de núcleo (`src/backmedina/`) e as páginas
Streamlit (`app/`) preservando os **contratos de dados** que garantem
compatibilidade com MeDiNa/BackMeDiNa. Não faz retroanálise (fica no BackMeDiNa).

## 3. Princípios operacionais
- **3.1 Pensar antes de executar:** diagnostique antes de alterar; identifique o
  ponto de entrada afetado e as dependências. Registre ambiguidades e pergunte
  quando afetarem dados, schema/unidades ou estrutura global.
- **3.2 Simplicidade primeiro:** funções puras, curtas e testáveis no núcleo;
  a UI só orquestra. Sem refatorações amplas não solicitadas.
- **3.3 Mudanças cirúrgicas:** cada linha alterada deve se relacionar ao pedido.
  Preserve o padrão existente (núcleo puro em `src/`, UI em `app/`).
- **3.4 Metas verificáveis:** conclua uma tarefa só após `pytest` passar e/ou o
  app subir sem traceback. Não afirmar que algo foi testado se não foi.

## 4. Estrutura do projeto
```
app/                     UI Streamlit (Home + pages/1..4). Só orquestra.
src/backmedina/          Núcleo puro (sem Streamlit), testável por pytest:
  io/        br_numbers, xlsx_solocap, xlsx_kuab, csv_bacias, pdf_fwd,
             validacao, loader (despacho .xlsx SOLOCAP/KUAB por conteúdo)
  model/     schema.py   -> CONTRATOS FIXOS (sensores, unidades, layouts)
  convert/   standardize (-> Modelo.xlsx), backmedina_csv (-> CSV BackMeDiNa)
  analytics/ pbd_indices (Rocha), deflexao_caracteristica
  segmentation/ aashto_cumdiff (diferenças acumuladas)
  report/    relatorio_pdf (LuaLaTeX+Pagella, sem Type 1), relatorio_docx, comum
  plots/     basins.py (matplotlib, backend Agg)
templates/               Modelo.xlsx, Modelo_Arquivo_Bacias.csv (contratos de I/O)
tests/                   suíte pytest (fixtures a partir do arquivo real da UFJF)
z_docs/                  dados reais + PDFs acadêmicos — SOMENTE LEITURA
```
- **Entrada principal:** `app/streamlit_app.py`.
- **Entradas de dados:** `.xlsx` SOLOCAP, `.csv` de bacias e `.pdf` do relatório
  FWD (via `pdftotext`/poppler — dependência de sistema, ver `packages.txt`).
- **Saídas:** CSV BackMeDiNa, planilha "Tabela" padronizada, CSVs de índices/segmentos.

## 5. Arquivos e diretórios críticos
- `z_docs/**` — dados brutos de campo e PDFs de referência. **Nunca** sobrescrever,
  mover ou apagar; é fonte de verdade e fixture de teste.
- `src/backmedina/model/schema.py` — contratos com o MeDiNa/BackMeDiNa
  (mapa de sensores `D1→d0…D9→d180`, `RAIO=15`, unidade `0,01 mm`, layouts de
  planilha/CSV). Alterar aqui pode quebrar toda a compatibilidade das saídas.
- `templates/` — contratos de I/O de referência.

Antes de mexer em algo crítico: (1) explique a mudança; (2) aponte o risco;
(3) faça cópia quando aplicável; (4) peça autorização se houver risco de perda,
sobrescrita ou mudança estrutural.

## 6. Regras específicas
- **Python:** usar a venv existente; não instalar dependências sem autorização;
  preservar `requirements.txt` e `pyproject.toml`. Núcleo não importa Streamlit.
- **Streamlit:** preservar a estrutura de páginas; não expor segredos/caminhos na
  UI; `streamlit run` deve subir sem traceback; em conflito de porta, sugerir
  `--server.port` alternativa.
- **Dados/números BR:** todo parsing numérico passa por `io/br_numbers.py`
  (vírgula decimal, ponto de milhar).
- **Unidades:** cálculos em `0,01 mm`; **CSV BackMeDiNa em µm** (×10, único ponto
  de conversão em `convert/backmedina_csv.py`); carga em kgf. Unidade da fonte
  detectada em `model/units.py` e guardada em `DadosFWD.unidade_deflexao`.
- **Contratos:** manter exatamente `BACKMEDINA_HEADER`, o cabeçalho de 3 linhas do
  CSV (`BACKMEDINA` / `SEÇÃO:;<nome>` / `RAIO (cm):;15`, rótulo e valor em células
  separadas) e o layout da aba "Tabela". O CSV BackMeDiNa é `;`-sep, **CP1252** e
  **CRLF** — o importador é rígido nesses três pontos.
- **Documentos/PDF:** seguir a skill `gerar-documentos` — PDF só via LuaLaTeX +
  `fontspec` + TeX Gyre Pagella (proibido Type 1); validar com `pdffonts`.

## 7. Ações permitidas sem autorização
Editar/criar módulos em `src/` e páginas em `app/`; escrever/rodar testes; rodar
`pytest` e `streamlit run` localmente; gerar arquivos em `templates/` a partir do
schema; ler qualquer coisa em `z_docs/`.

## 8. Ações que exigem autorização
Instalar/atualizar dependências; alterar `schema.py` (mapa de sensores, unidades,
layouts); apagar/mover/sobrescrever arquivos em `z_docs/` ou `templates/`;
refatorações amplas; qualquer deploy (nuvem) ou publicação externa.

- **Workflows / pesquisa multi-agente:** executar qualquer Workflow ou pesquisa
  multi-agente (ex.: `deep-research`) exige **anunciar antes** a estimativa —
  número previsto de agentes, teto de tokens (com orçamento `+Nk` obrigatório) e
  modelos por estágio — e **aguardar autorização explícita**, mesmo quando houver
  permissão técnica configurada em `settings*.json`. Preferir a variante econômica
  `.claude/workflows/deep-research-eco.js` (Haiku/Sonnet por estágio, votos e
  fetches reduzidos, guarda de orçamento) à skill embutida `deep-research`.

## 9. Comandos de trabalho e validação
```bash
python3 -m venv .venv && source .venv/bin/activate   # ambiente
pip install -r requirements.txt                       # dependências
python3 -m pytest -q                                  # testes (núcleo)
streamlit run app/streamlit_app.py                    # app (porta 8501)
# conflito de porta:
streamlit run app/streamlit_app.py --server.port 8502
```

## 10. Critérios de sucesso
Tarefa concluída quando: objetivo atendido; mudanças no escopo; arquivos críticos
preservados; `pytest` passa (ou verificação equivalente descrita); e, se a UI foi
tocada, o app sobe sem traceback e o fluxo alterado é alcançável. Compatibilidade
com BackMeDiNa mantida (cabeçalho/colunas/unidades do CSV).

## 11. Resposta final esperada
Resumo breve; arquivos criados/alterados; comandos executados; verificações
realizadas (resultado do `pytest` / subida do app); pendências, riscos e
limitações. Não omitir falhas nem verificações que não puderam ser feitas.
```
