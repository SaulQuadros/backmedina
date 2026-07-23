"""Glossário técnico dos parâmetros da bacia deflectométrica (PBD).

Explica o que é e para que serve cada coluna da planilha de índices (Rocha, 2020).
Deflexões em 0,01 mm; sensores a 0/20/30/45/60/90/120/150/180 cm do centro da carga
(D0=D1, D20=D2, D30=D3, D45=D4, D60=D5, D90=D6, D120=D7, D150=D8, D180=D9).
"""

from __future__ import annotations

# Cada item: sigla, nome, unidade, formula, o_que_e, para_que_serve.
GLOSSARIO_PBD: list[dict] = [
    {
        "sigla": "Metros",
        "nome": "Posição / estaca",
        "unidade": "m",
        "formula": "—",
        "o_que_e": "Posição da estação de ensaio ao longo da via.",
        "para_que_serve": "Localiza cada bacia no trecho; é o eixo das análises "
        "(perfis, segmentação).",
    },
    {
        "sigla": "Rc",
        "nome": "Raio de curvatura",
        "unidade": "m",
        "formula": "6250 / [2·(D0 − D25)],  com D25 = (D20 + D30)/2",
        "o_que_e": "Raio da parábola que aproxima a parte central da bacia "
        "(a curvatura logo abaixo da carga).",
        "para_que_serve": "Avalia a rigidez/integridade das camadas superiores "
        "(revestimento). Rc grande = bacia central rasa (superfície rígida); "
        "Rc pequeno = bacia muito encurvada (superfície flexível ou trincada).",
    },
    {
        "sigla": "AREA",
        "nome": "Área normalizada da bacia (AASHTO 1993)",
        "unidade": "cm",
        "formula": "15·[1 + 2·(D30/D0) + 2·(D60/D0) + (D90/D0)]",
        "o_que_e": "Índice de forma que sintetiza a abertura da bacia, "
        "normalizado por D0 (independe da magnitude da deflexão).",
        "para_que_serve": "Reflete a rigidez global da estrutura. AREA maior = "
        "bacia mais espraiada = estrutura mais rígida/uniforme.",
    },
    {
        "sigla": "SCI",
        "nome": "Surface Curvature Index (Índice de Curvatura Superficial)",
        "unidade": "0,01 mm",
        "formula": "D0 − D30",
        "o_que_e": "Diferença de deflexão entre o centro (0 cm) e 30 cm.",
        "para_que_serve": "Sensível às camadas superiores (revestimento e topo da "
        "base). SCI alto indica camadas superiores mais deformáveis/danificadas.",
    },
    {
        "sigla": "BDI",
        "nome": "Base Damage Index (Índice de Dano da Base)",
        "unidade": "0,01 mm",
        "formula": "D30 − D60",
        "o_que_e": "Diferença de deflexão entre 30 e 60 cm.",
        "para_que_serve": "Sensível às camadas intermediárias (base/sub-base). "
        "BDI alto indica base mais fraca ou danificada.",
    },
    {
        "sigla": "BCI",
        "nome": "Base Curvature Index (Índice de Curvatura da Base)",
        "unidade": "0,01 mm",
        "formula": "D60 − D90",
        "o_que_e": "Diferença de deflexão entre 60 e 90 cm.",
        "para_que_serve": "Sensível às camadas inferiores e ao subleito. BCI alto "
        "indica subleito/camadas profundas mais deformáveis.",
    },
    {
        "sigla": "CF",
        "nome": "Curvature Factor (Fator de Curvatura)",
        "unidade": "0,01 mm",
        "formula": "D0 − D20",
        "o_que_e": "Curvatura bem junto à carga (entre 0 e 20 cm).",
        "para_que_serve": "Indica a condição da superfície/revestimento na região "
        "de maior curvatura da bacia.",
    },
    {
        "sigla": "S",
        "nome": "Spreadability / Achatamento",
        "unidade": "%",
        "formula": "(D0 + D30 + D60 + D90 + D120) / (5·D0) · 100",
        "o_que_e": "Média das deflexões normalizada por D0, em porcentagem.",
        "para_que_serve": "Mede o espraiamento (achatamento) da bacia. S maior = "
        "carga distribuída em área maior = estrutura mais rígida/profunda.",
    },
]
