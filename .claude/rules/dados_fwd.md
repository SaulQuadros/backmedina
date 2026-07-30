# Regras — Domínio de dados FWD (contratos de schema)

Aplica-se a `src/backmedina/**`. Estes contratos garantem compatibilidade com o
MeDiNa/BackMeDiNa e **não** mudam sem autorização explícita.

## Unidades (fixas)
- Deflexões nos **cálculos** (Rc, PBD, segmentação, deflexão característica):
  **0,01 mm** (`x10⁻² mm`). A constante `6250` do Rc embute esta unidade — não
  alimente as fórmulas com µm.
- Deflexões na **saída BackMeDiNa (CSV)**: **µm**. `1 (0,01 mm) = 10 µm` →
  `valor_µm = valor_0,01mm × 10`. **Único ponto de conversão:** `convert/backmedina_csv.py`.
- **Fonte por leitor:** SOLOCAP (xlsx/PDF) = 0,01 mm; CSV de bacias (formato do
  BackMeDiNa) = µm. A unidade é detectada em `model/units.detectar_unidade` e
  guardada em `DadosFWD.unidade_deflexao`; `analytics`/`segmentation` normalizam
  para 0,01 mm internamente via o parâmetro `unidade`.
- Carga: `kN` e `kgf`; no CSV BackMeDiNa a carga vai em **kgf** (não converter).
- Distâncias radiais dos sensores: **cm**. Estaca/posição: **m**.
- Planilha padronizada "Tabela" (.xlsx): sempre em **0,01 mm**. Fonte em µm é
  **convertida** em `convert/standardize._tabela_em_001mm` — o rótulo da linha 10
  é fixo, então gravar valor cru sob ele produz erro de 10× a cada round-trip.
- **Unidade não declarada ≠ unidade 0,01 mm.** `detectar_unidade_explicita`
  devolve `None` quando o arquivo nada declara; leitores não devem preencher o
  metadado com o padrão, e a UI (página 1) avisa que a unidade foi presumida e
  permite corrigi-la antes de qualquer cálculo.

## Mapa de sensores (autoritativo — Rocha/BackMeDiNa)
```
D1→d0(0)   D2→d20(20)  D3→d30(30)  D4→d45(45)  D5→d60(60)
D6→d90(90) D7→d120(120) D8→d150(150) D9→d180(180)   D10→(~210, DESCARTADO)
```
Placa FWD: **raio = 15 cm**. Fonte única: `model/schema.py` (`D_TO_SENSOR`,
`SENSOR_OFFSETS_CM`, `RAIO_PLACA_CM`). Não duplicar estas constantes.

## Números em formato BR
Todo texto numérico (`4.059`, `-21,77314`, `2.080,00`) passa por
`io/br_numbers.parse_br_number/parse_br_series`. Ponto = milhar, vírgula = decimal.

## Layouts de I/O (não alterar sem autorização)
- **SOLOCAP .xlsx** (aba "Tabela"): metadados linhas 1-10, cabeçalho linha 13,
  dados linha 14+; colunas `COLUNAS_TABELA`.
- **CSV bacias**: `;`-sep, CP1252, 1ª linha em branco, header com `d0..d180`.
- **CSV BackMeDiNa** (saída): `;`-sep, **CP1252**, **CRLF**. Cabeçalho de 3 linhas
  com rótulo e valor em **células separadas** — `BACKMEDINA` / `SEÇÃO:;<nome>` /
  `RAIO (cm):;15` — depois `BACKMEDINA_HEADER`. **Todas** as linhas (inclusive as
  3 de cabeçalho) preenchidas com `;` até o nº total de colunas.
  Colunas de deflexão: `d0..d180` (de D1..D9) **mais `d210`** (de D10), 18 no
  total. `d210` existe só no CSV — não entra em nenhum cálculo.
  Grafia da 6ª coluna: `Estaca – Descolamento` (com "c", como no template).
  `Estaca – Faixa`/`Estaca – Trilha`: valor **único** para o levantamento, vindo
  da UI (página 3, `st.session_state["estaca_faixa"]`/`["estaca_trilha"]`) — o
  SOLOCAP não traz essas colunas; o CSV de bacias traz e serve de valor inicial.
  Não confundir com `n_faixas` da sidebar (nº de faixas da via, só no relatório).
  Desvios nesses pontos fazem o importador falhar com "ERRO 1 — Problemas ao
  abrir o arquivo" (ver `z_docs/error/csv-backmedina/`).

## Fórmulas (referência Rocha 2020 / AASHTO 1993 / Machado 2019)
- `D25 = (D20+D30)/2`; `Rc = 6250 / [2·(D0−D25)]` (m).
- `AREA = 15·[1 + 2·(D30/D0) + 2·(D60/D0) + (D90/D0)]` (cm).
- `SCI=D0−D30`, `BDI=D30−D60`, `BCI=D60−D90`, `CF=D0−D20`.
- `S(%) = (D0+D30+D60+D90+D120)/(5·D0)·100`.
- Segmentação: diferenças acumuladas `Zᵢ = ΣAᵢ − (A_c/L_c)·ΣΔlᵢ` sobre D0.
- Deflexão característica do trecho: `D_c = média(D0) + σ` (σ amostral, ddof=1).

## Verificação
Qualquer mudança em parsing/contrato/fórmula deve ser coberta por `pytest` com
fixtures do arquivo real `z_docs/lwd/solocap/2-UFJF-VIA_LOCAL_FX1-FWD.xlsx`.
