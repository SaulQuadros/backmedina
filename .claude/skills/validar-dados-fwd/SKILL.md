---
name: validar-dados-fwd
description: Rodar checagens de qualidade em um levantamento FWD (monotonicidade da bacia D1≥D2≥…, faixa de carga, D0 válido, unidades) antes de converter. Use quando o usuário quiser validar/inspecionar a qualidade dos dados FWD.
---

# Validar dados FWD

## Entrada
`DadosFWD` carregado (via `io.loader.carregar`).

## Procedimento
1. `from backmedina.io.validacao import validar`.
2. `avisos = validar(dados)` → lista de strings (pt-BR).
3. Reportar cada aviso. Checagens cobertas:
   - bacia não monotônica (deflexão aumenta com a distância);
   - carga fora de 2000–12000 kgf;
   - D0 (D1) nula/ausente;
   - avisos herdados do parsing (`dados.avisos`).

## Critério de sucesso
O usuário recebe um relatório claro de qualidade **sem** que o fluxo seja
interrompido (validação é informativa, não bloqueante). Se algo sério aparecer
(ex.: muitas bacias não monotônicas), sugerir revisão do arquivo de origem.
