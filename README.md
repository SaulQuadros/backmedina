# Conversor de Dados FWD (backmedina)

Reimplementação aberta, em **Python/Streamlit**, da ferramenta `ConversorDadosFWD`.
Converte levantamentos de **deflectometria FWD** em pavimentos flexíveis para o
fluxo **MeDiNa / BackMeDiNa** (retroanálise de módulos de resiliência).

## O que faz
- Importa **planilha SOLOCAP `.xlsx`**, **CSV de bacias** ou o **relatório PDF**
  do levantamento FWD (extração via `pdftotext`/poppler — ver `packages.txt`).
- Valida os dados (monotonicidade da bacia, carga, D0).
- Padroniza a planilha "Tabela" e exporta **CSV compatível com o BackMeDiNa**.
- Calcula **índices da bacia (PBD)**: Rc, AREA, SCI, BDI, BCI, CF, S (Rocha 2020).
- Faz **segmentação homogênea** (diferenças acumuladas AASHTO) e a **deflexão
  característica** (média+σ) por trecho.

Fora de escopo: a **retroanálise** propriamente dita (permanece no BackMeDiNa).

## Como rodar
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py            # http://localhost:8501
# conflito de porta:
streamlit run app/streamlit_app.py --server.port 8502
```

## Testes
```bash
python3 -m pytest -q
```

## Estrutura
- `app/` — UI Streamlit (Home + `pages/1..4`), apenas orquestra.
- `src/backmedina/` — núcleo puro e testável (io, model, convert, analytics,
  segmentation, plots).
- `templates/` — `Modelo.xlsx` e `Modelo_Arquivo_Bacias.csv` (contratos de I/O).
- `z_docs/` — dados reais e PDFs de referência (**somente leitura**).
- `.claude/` — `CLAUDE.md`, `rules/`, `skills/`, `agents/` (Kit Claude Mestre).

## Docker (deploy híbrido, opcional)
```bash
docker build -t backmedina .
docker run -p 8501:8501 backmedina
```

## Unidades e convenções
Deflexões em `0,01 mm`; carga em `kN`/`kgf`; sensores a
`0, 20, 30, 45, 60, 90, 120, 150, 180 cm` (raio da placa `15 cm`).
Mapa: `D1→d0, D2→d20, …, D9→d180` (`D10` descartado). Números em formato BR.

## Referências
- Machado (2019) — dissertação (retroanálise, MeDiNa, segmentação).
- Rocha (2020) — parâmetros da bacia deflectométrica (PBD).
- `z_docs/academic/` contém os PDFs.
