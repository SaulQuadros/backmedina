# Orientação para o NotebookLM — Análise Deflectométrica FWD (UFJF)

> **Como usar este documento:** carregue-o no NotebookLM **junto** com os dois
> arquivos-fonte abaixo. Ele é o **guia metodológico**: define unidades, o cálculo
> dos valores plotados e as regras de segmentação. Quando houver conflito entre um
> valor bruto das fontes e uma regra aqui, **prevalece a metodologia deste guia**.

---

## 1. Fontes de dados

Ambos os arquivos descrevem o **mesmo** levantamento (a planilha é a extração fiel
da tabela do PDF):

- **PDF (relatório de campo):**
  `…\backmedina\z_docs\lwd\2-UFJF-VIA_LOCAL_FX1-FWD.pdf`
- **XLSX (tabela extraída):**
  `…\backmedina\z_docs\lwd\2-UFJF-VIA_LOCAL_FX1-FWD.xlsx` (aba `Tabela`)

**Metadados do ensaio:**
- Equipamento: **Falling Weight Deflectometer (FWD) SWECO PRIMAX 1500** — norma
  **DNER PRO 273/96**.
- Cliente: **Universidade Federal de Juiz de Fora (UFJF)** — Juiz de Fora/MG.
- Pista: **1984 – VIA LOCAL – FAIXA 1 – PD**; sentido **ENTRADA DA UNIVERSIDADE**.
- Relatório nº **500-100000/23**; OS nº **500/23**; data do relatório **16/11/2023**;
  ensaios executados em **11/09/2023**.
- **105 estações**, de **0 m a 2.080 m**, espaçadas a cada **20 m**.
- Carga aplicada: nominal **40 kN ≈ 4.000 kgf** (placa circular de **raio 15 cm**).

---

## 2. Estrutura da tabela e geometria dos sensores

Colunas (na ordem da tabela): `Metros`, `Target Load kN`, `Target Load (Kgf)`,
`D1 … D10`, `Temp Ar (°C)`, `Temp Pav (°C)`, `Latitude`, `Longitude`, `Raio`,
`Data e Hora`, `Obs`.

Os 10 geofones `D1…D10` medem a **bacia de deflexão**. As distâncias radiais ao
centro da carga (padrão BackMeDiNa/Rocha) são:

| Coluna | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 |
|--------|----|----|----|----|----|----|----|----|----|-----|
| Distância (cm) | 0 | 20 | 30 | 45 | 60 | 90 | 120 | 150 | 180 | ~210 |
| Rótulo | d0 | d20 | d30 | d45 | d60 | d90 | d120 | d150 | d180 | (não usado) |

- **D0 ≡ D1** é a **deflexão máxima** (sob o centro da carga).
- **D10 é descartado** na análise (fora do conjunto padrão do BackMeDiNa).
- Números em formato brasileiro: **vírgula = decimal**, **ponto = milhar**
  (ex.: `4.059` = 4059; `-21,77314` = −21,77314; `2.080,00` = 2080).

---

## 3. Unidades e conversão para micrômetro (µm)

**Regra central — há duas unidades no fluxo:**

| Uso | Unidade | Observação |
|-----|---------|------------|
| Leituras nas fontes (SOLOCAP) | **0,01 mm** (`×10⁻² mm`) | é como o PDF/XLSX apresentam D1…D10 |
| **Cálculos** (Rc, índices PBD, segmentação, deflexão característica) | **0,01 mm** | as fórmulas pressupõem esta unidade |
| **Saída para o BackMeDiNa** | **µm (micrômetro)** | exigência do programa |

**Fator de conversão (dimensional, exato):**

> `1 unidade de 0,01 mm = 10 µm`  ⇒  **valor_µm = valor_(0,01 mm) × 10**

Exemplos: `D0 = 44` (0,01 mm) → **440 µm**; `D9 = 3` → **30 µm**.

**Quando converter:** a conversão ×10 é aplicada **somente na geração dos valores
que vão ao BackMeDiNa e nos gráficos exibidos em µm**. Os **cálculos** de índices e
segmentação permanecem em **0,01 mm** (ver §6, item sobre o Rc). A **carga**
continua em **kgf** — não se converte carga.

---

## 4. Valores plotados no gráfico — como são gerados

Há três gráficos possíveis. Em todos, se o eixo estiver rotulado em **µm**, os
valores de deflexão são os da fonte **× 10**.

### 4.1 Bacia de deflexão (gráfico principal)
Para **cada estação**, plote **deflexão × distância radial**:
- Eixo X: distância do sensor ao centro (0, 20, 30, 45, 60, 90, 120, 150, 180 cm).
- Eixo Y: deflexão do sensor, **em µm** (valor da fonte × 10), com o eixo Y
  **invertido** (a deflexão cresce para baixo).
- Uma curva por estação; a forma da bacia caracteriza a rigidez estrutural.

**Exemplo (estação 0,00 m):**
Fonte (0,01 mm): `44, 29, 21, 13, 9, 6, 4, 3, 3` →
Plotado (µm): **`440, 290, 210, 130, 90, 60, 40, 30, 30`**.

### 4.2 Perfil de D0 ao longo da via (base da segmentação)
- Eixo X: estaca/posição em metros (0 → 2.080 m).
- Eixo Y: **D0 (deflexão máxima)** de cada estação, em µm (D1 da fonte × 10).
- É este perfil que alimenta o método de segmentação (§5).

### 4.3 Curva de diferenças acumuladas Z(x) (auxiliar da segmentação)
- Eixo X: posição em metros; Eixo Y: valor **Z** (ver §5).
- As **mudanças de inclinação** de Z(x) marcam as fronteiras dos trechos.

---

## 5. Segmentação em trechos homogêneos

**Método:** Diferenças Acumuladas — **AASHTO (1993)**, usando a **deflexão máxima
D0** como parâmetro. (Referência: Machado, 2019.)

### 5.1 Equações (com espaçamento Δlᵢ entre estações; aqui Δl = 20 m)
1. Média do intervalo: **D̄ᵢ = (Dᵢ₋₁ + Dᵢ) / 2**
2. Área do intervalo: **Aᵢ = D̄ᵢ · Δlᵢ**
3. Área acumulada até *i*: **ΣAᵢ**   |   Distância acumulada: **ΣΔlᵢ**
4. Totais: **A_c = Σ Aᵢ** (toda a via) e **L_c = Σ Δlᵢ** (comprimento total)
5. Diferença acumulada: **Zᵢ = ΣAᵢ − (A_c / L_c) · ΣΔlᵢ**

Plote **Zᵢ vs. posição**. Cada **troca de sinal da inclinação** de Z (um vértice da
curva) indica **mudança de comportamento estrutural** ⇒ fronteira de trecho.

> Observação: as **fronteiras** de Z são **invariantes à unidade** (0,01 mm ou µm
> dão os mesmos trechos), pois a escala é linear. Só os **valores** de D0
> reportados mudam de unidade.

### 5.2 Restrições de comprimento (regra deste projeto)
Cada trecho homogêneo deve respeitar:

- **Comprimento mínimo: 100 m**
- **Comprimento máximo: 2.000 m**

Como o espaçamento é **20 m**, isso equivale, em número de estações *n* por trecho:
- comprimento do trecho = **(n − 1) × 20 m**
- mínimo 100 m ⇒ **n ≥ 6 estações**;
- máximo 2.000 m ⇒ **n ≤ 101 estações**.

Como a via tem **2.080 m** (> 2.000 m), ela **não pode** ficar em um único trecho:
haverá **no mínimo 2 trechos**.

### 5.3 Pós-processamento das fronteiras (para cumprir as restrições)
Depois de detectar as fronteiras pela curva Z(x):
1. **Fusão:** se um trecho tiver **< 100 m**, funda-o com o trecho vizinho de
   comportamento mais parecido (menor diferença de D0 médio).
2. **Divisão:** se um trecho tiver **> 2.000 m**, divida-o (no vértice de Z mais
   interno, ou no meio) até que todos os subtrechos fiquem **≤ 2.000 m**.
3. Repita fusão/divisão até que **todos** os trechos estejam em **[100 m; 2.000 m]**.

### 5.4 Deflexão característica por trecho (para o MeDiNa)
Para cada trecho homogêneo, calcule sobre os D0 daquele trecho:

> **D_c = média(D0) + σ(D0)**  (σ = desvio-padrão amostral)

Reporte **D_c em 0,01 mm** (unidade do campo "deflexão característica" do MeDiNa –
Modo Reforço). Se precisar em µm, multiplique por 10.

---

## 6. Índices da Bacia Deflectométrica (PBD) — Rocha (2020)

Calculados **em 0,01 mm** (não converter para µm antes de calcular). Interpolação
para o sensor a 25 cm: **D25 = (D20 + D30) / 2**.

| Índice | Fórmula | Unidade | O que indica |
|--------|---------|---------|--------------|
| **Rc** (raio de curvatura) | `6250 / [2·(D0 − D25)]` | m | rigidez próxima à superfície |
| **AREA** | `15·[1 + 2·(D30/D0) + 2·(D60/D0) + (D90/D0)]` | cm | rigidez global da bacia |
| **SCI** | `D0 − D30` | 0,01 mm | camadas superiores (revestimento) |
| **BDI** | `D30 − D60` | 0,01 mm | base / meio da estrutura |
| **BCI** | `D60 − D90` | 0,01 mm | camadas inferiores / subleito |
| **CF** | `D0 − D20` | 0,01 mm | curvatura junto à carga |
| **S (%)** | `(D0 + D30 + D60 + D90 + D120) / (5·D0) · 100` | % | achatamento (espraiamento) |

> **Atenção ao Rc:** a constante **6250 embute a unidade 0,01 mm**. Se D0 e D25
> forem informados em µm, o Rc sai **10× menor (errado)**. Por isso o Rc — e os
> demais índices — são sempre calculados **em 0,01 mm**. `AREA` e `S` são razões
> **adimensionais** (não mudam com a unidade); `SCI/BDI/BCI/CF` são diferenças que
> herdam a unidade das deflexões.

**Exemplo verificado (estação 0,00 m, em 0,01 mm):**
`D0=44, D20=29, D30=21, D60=9, D90=6, D120=4` ⇒
`D25=25`; **Rc = 6250/(2·19) = 164,47 m**; **SCI=23**; **BDI=12**; **BCI=3**;
**CF=15**; **AREA=37,5 cm**; **S=38,18 %**.

---

## 7. Saída para o BackMeDiNa (formato do arquivo)

O BackMeDiNa importa um **CSV** com cabeçalho de 3 linhas e deflexões **em µm**:

```
BACKMEDINA
SEÇÃO: 1984 VIA LOCAL - FAIXA 1 - PD
RAIO (cm): 15
Data de Execução,Temp. Do Ar,Temp. Do Pavimento,Carga,Estaca – Número,Estaca – Deslocamento,Estaca – Faixa,Estaca – Trilha,d0,d20,d30,d45,d60,d90,d120,d150,d180
11/09/2023,36,41,4059,1,0,0,0,440,290,210,130,90,60,40,30,30
...
```
- `Carga` em **kgf**; `RAIO (cm): 15`; `d0…d180` **em µm** (fonte × 10).
- `d0=D1, d20=D2, d30=D3, d45=D4, d60=D5, d90=D6, d120=D7, d150=D8, d180=D9`.

---

## 8. Glossário rápido

- **FWD**: Falling Weight Deflectometer (deflectômetro de impacto).
- **Bacia de deflexão**: conjunto das deflexões dos geofones em uma estação.
- **D0**: deflexão máxima (sensor central). **D25**: valor interpolado a 25 cm.
- **PBD**: Parâmetros da Bacia Deflectométrica (índices de forma da bacia).
- **Trecho homogêneo**: segmento da via com comportamento estrutural semelhante.
- **Deflexão característica (D_c)**: média + 1 desvio-padrão dos D0 do trecho.
- **BackMeDiNa**: software de retroanálise (calcula módulos por camada).
- **MeDiNa**: método/software nacional de dimensionamento mecanístico-empírico.

---

## 9. Perguntas sugeridas ao NotebookLM

- "Qual a deflexão máxima (D0) em µm na estação X e como ela se compara à média?"
- "Liste os trechos homogêneos respeitando mínimo de 100 m e máximo de 2.000 m e
  informe a deflexão característica de cada um (em 0,01 mm)."
- "Calcule os índices PBD (Rc, SCI, BDI, BCI, AREA, S) da estação Y em 0,01 mm."
- "Explique por que as deflexões vão em µm para o BackMeDiNa mas os índices são
  calculados em 0,01 mm."
- "Gere os valores da bacia de deflexão (em µm) para plotar a estação Z."

---

### Resumo de unidades (cola rápida)
- Fonte e cálculos: **0,01 mm**.
- Gráfico/saída BackMeDiNa: **µm = fonte × 10**.
- Carga: **kgf** (sem conversão). Distâncias dos sensores: **cm**. Rc: **m**.
- Segmentação: parâmetro **D0**; trechos entre **100 m e 2.000 m**; **D_c = média + σ**.
