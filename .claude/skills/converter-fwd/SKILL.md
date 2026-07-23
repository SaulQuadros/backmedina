---
name: converter-fwd
description: Fluxo ponta-a-ponta para converter um levantamento FWD (SOLOCAP .xlsx ou CSV de bacias) em CSV BackMeDiNa e planilha padronizada. Use quando o usuário quiser importar/converter dados FWD ou gerar a saída para o BackMeDiNa.
---

# Converter dados FWD → BackMeDiNa

## Entradas
- Caminho de um arquivo `.xlsx` (SOLOCAP, aba "Tabela") **ou** `.csv` de bacias.
- (Opcional) nome da SEÇÃO para o cabeçalho do CSV.

## Procedimento
1. `from backmedina.io.loader import carregar` → `dados = carregar(caminho)`.
2. Validar: `from backmedina.io.validacao import validar` → reporte os avisos.
   Não interrompa por avisos; apenas informe o usuário.
3. (Opcional) padronizar planilha:
   `from backmedina.convert.standardize import exportar_xlsx_bytes`.
4. Exportar CSV BackMeDiNa:
   `from backmedina.convert.backmedina_csv import exportar_csv_backmedina`
   → `csv = exportar_csv_backmedina(dados, secao=<nome>)`.
5. Conferir o cabeçalho: linha 1 `BACKMEDINA`, linha 2 `SEÇÃO: ...`,
   linha 3 `RAIO (cm): 15`, linha 4 = `BACKMEDINA_HEADER` (colunas `d0..d180`).

## Critérios de sucesso
- CSV começa com as 3 linhas de cabeçalho corretas e uma linha por estação.
- Deflexões `d0..d180` vêm de `D1..D9`; `D10` é descartado; carga em kgf.
- Números BR parseados (nenhum campo numérico vazio por erro de parsing).

## Regras
Não alterar `model/schema.py` (contratos). Deflexões em 0,01 mm. Ver
`.claude/rules/dados_fwd.md`.
