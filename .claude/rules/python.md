# Regras — Python

Aplica-se a `src/**` e `tests/**`.

- Usar a venv existente; **não** instalar/atualizar dependências sem autorização.
  Preservar `requirements.txt` e `pyproject.toml`.
- **Separação núcleo/UI:** `src/backmedina/` não importa `streamlit`. Regras de
  engenharia ficam no núcleo (funções puras `DataFrame→DataFrame`), testáveis sem UI.
- Preferir funções simples, curtas e legíveis; evitar refatorações amplas.
- Identificar pontos de entrada e dependências internas antes de alterar módulos
  centrais (`model/schema.py`, `io/loader.py`, `convert/*`).
- Testes: cobrir parsing BR, mapa de sensores, índices PBD (valores conferidos à
  mão), segmentação e o cabeçalho do CSV BackMeDiNa. Rodar `python3 -m pytest -q`.
- Ao ler `.xlsx` com openpyxl, **não** usar `read_only=True` com acesso por célula
  (`ws.cell`) — é ordens de magnitude mais lento; os arquivos são pequenos.

**Sucesso:** o módulo alterado roda sem exceção no cenário esperado; os testes
existentes passam; nenhum arquivo crítico alterado fora de escopo.
