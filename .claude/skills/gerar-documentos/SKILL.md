---
name: gerar-documentos
description: Gerar documentos do projeto (relatórios, minutas) em PDF ou Word, com tipografia correta. Use SEMPRE que for produzir um documento — especialmente PDF. Impõe a regra de fontes (sem Type 1; OpenType/CFF via LuaLaTeX + TeX Gyre Pagella) e a verificação com pdffonts.
---

# Gerar documentos (PDF e Word)

## Regra de fontes — PDF (obrigatória, não negociável)
A Adobe encerrou o suporte a **Type 1** (jan/2023); leitores modernos
(Acrobat/Reader) travam ou renderizam mal PDFs com Type 1 embutida.
`pdflatex` + `lmodern` produz exatamente isso — **não usar**.

- **Gerar PDF só com `lualatex` (ou `xelatex`) + `fontspec`.** Embute a fonte
  OpenType/CFF como **CID Type 0C** (formato atual).
- **Fonte de miolo padrão: TeX Gyre Pagella** (família Palatino) — melhor para
  livro que a Latin Modern e adequada ao formato **14×21 cm**.
- **Matemática/símbolos (σ, etc.): `unicode-math` + `\setmathfont{TeX Gyre
  Pagella Math}`.** Se usar `$...$` sem isso, o LaTeX puxa **CMMI10 (Type 1)** —
  proibido. (No projeto: `src/backmedina/report/relatorio_pdf.py`.)
- **Imagens/plots como PNG** (raster) ou vetor sem Type 1/Type 3 — não deixar um
  PDF de figura reintroduzir fontes Type 1/Type 3 no documento final.
- **Escapar** caracteres especiais do LaTeX (`& % _ # $ { } ~ ^ \`) em todo texto
  dinâmico (use `report.relatorio_pdf.esc`).

## Verificação obrigatória (gate)
Após compilar, rodar **`pdffonts`** e **reprovar se aparecer qualquer linha
"Type 1"** (aceitas: `CID Type 0C`, `Type 1C`, `CID TrueType`, `TrueType`).
Use `report.relatorio_pdf.verificar_sem_type1(pdf_bytes) -> (ok, tipos)`.

```bash
pdffonts arquivo.pdf   # coluna "type" NUNCA pode ser "Type 1"
```

## Word (.docx) — alternativa
`python-docx`. O Word referencia a fonte pelo nome (não embute); usar
**"Palatino Linotype"** (Palatino, padrão no Windows). Sem o problema de Type 1.
No projeto: `src/backmedina/report/relatorio_docx.py`.

## Conteúdo comum
Montar rastreabilidade e resumo por `src/backmedina/report/comum.py`
(`linhas_rastreabilidade`, `linhas_resumo`) para PDF e DOCX mostrarem o mesmo.

## Deploy
`lualatex` + família tex-gyre são dependências de **sistema** (não pip):
ver `packages.txt` (Streamlit Cloud) e `Dockerfile` (`texlive-luatex`,
`texlive-fonts-extra`, `texlive-science`). Se `lualatex` faltar, oferecer o .docx
e avisar — nunca cair para `pdflatex`.

## Critérios de sucesso
- PDF compila e **`pdffonts` não lista nenhuma Type 1** (só Pagella CID Type 0C).
- Formato 14×21; acentuação e µm/σ corretos.
- `.docx` abre no Word com a fonte Palatino e as mesmas seções.
