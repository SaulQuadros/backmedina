---
name: segmentacao-homogenea
description: Dividir a via em trechos homogêneos pelo método das diferenças acumuladas (AASHTO 1993) sobre a deflexão máxima D0, e calcular a deflexão característica (média+σ) por segmento. Use quando o usuário pedir segmentação/trechos homogêneos ou deflexão característica.
---

# Segmentação homogênea (diferenças acumuladas AASHTO)

## Entrada
`DadosFWD` carregado; tabela com coluna de distância (`Metros`) e de deflexão
máxima (`D1`/`d0`).

## Procedimento — modo AUTOMÁTICO
1. `from backmedina.segmentation.aashto_cumdiff import segmentar`.
2. `df_seg, segmentos = segmentar(df, coluna_dist="Metros", coluna_d0="D1",
   comprimento_min_m=100, comprimento_max_m=2000, unidade=dados.unidade_deflexao,
   ddof=1)`.
   - Cada trecho respeita **[comprimento_min_m, comprimento_max_m]** (padrão 100–2000 m):
     trechos curtos são fundidos, longos são subdivididos.
   - `ddof`: 1 = σ amostral (n−1); 0 = populacional (n).
3. Para cada `Segmento`: `ini_m`, `fim_m`, `comprimento_m` (fronteira-a-fronteira),
   `n_pontos`, `d0_media` (Dm), `d0_desvio` (σ), `d0_caracteristica` (Dc = Dm+σ, 0,01 mm).
4. (Opcional) plotar a curva Z: `from backmedina.plots.basins import plot_curva_z`.

## Procedimento — modo MANUAL
1. `from backmedina.segmentation.aashto_cumdiff import segmentar_manual,
   validar_fronteiras_manuais`.
2. `df_seg, segmentos, violacoes = segmentar_manual(df, fronteiras_m=[...],
   comprimento_min_m=100, comprimento_max_m=2000, circuito_fechado=False,
   unidade=dados.unidade_deflexao, ddof=1)`.
   - `fronteiras_m`: posições (m) das estações que **iniciam** um novo trecho.
   - Se `violacoes` não for vazio, **não segmenta** (retorna `(None, [], violacoes)`),
     com mensagens no padrão do ConversorDadosFWD ("Seleção vazia", "distância menor/
     maior que o comprimento mínimo/máximo", "(segmento circular)").
   - `circuito_fechado=True`: valida também o trecho circular (envolve do último
     marcador de volta ao início).

## Notas de engenharia
- Fronteiras ficam nos extremos de `Z(x)` (troca de sinal da inclinação),
  priorizadas por nitidez e restritas pelo comprimento mín./máx.
- A deflexão característica alimenta o "Modo Reforço" do MeDiNa por segmento
  (reportada em 0,01 mm). Com 100–2000 m, o arquivo da UFJF gera ~9 trechos
  (Machado 2019 obteve 8 no anel viário).

## Regras
Ver `.claude/rules/dados_fwd.md`. Testes: `tests/test_segmentation.py`.
