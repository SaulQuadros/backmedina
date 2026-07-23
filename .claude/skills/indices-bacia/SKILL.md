---
name: indices-bacia
description: Calcular os parâmetros da bacia deflectométrica (PBD de Rocha 2020) — Rc, AREA, SCI, BDI, BCI, CF, S — a partir de um levantamento FWD carregado. Use quando o usuário pedir índices de bacia ou caracterização estrutural por deflexão.
---

# Índices da bacia deflectométrica (PBD)

## Entrada
Um `DadosFWD` já carregado (via `converter-fwd` ou `io.loader.carregar`), cuja
tabela tem colunas `D1..D10` (SOLOCAP) ou `d0..d180`.

## Procedimento
1. `from backmedina.analytics.pbd_indices import indices_com_contexto`.
2. `idx = indices_com_contexto(dados.tabela)` → DataFrame com `Metros` + índices.
3. Reportar/exportar: colunas `Rc` (m), `AREA` (cm), `SCI`, `BDI`, `BCI`, `CF`
   (0,01 mm), `S` (%).

## Verificação
Conferir em uma estação conhecida (ex.: UFJF estação 0 m, D0=44, D30=21, D60=9):
`SCI=23`, `BDI=12`, `BCI=3`, `CF=15`, `Rc=6250/38`. Ver `tests/test_indices.py`.

## Regras
Fórmulas e mapa de sensores em `.claude/rules/dados_fwd.md`; não duplicar
constantes fora de `model/schema.py`.
