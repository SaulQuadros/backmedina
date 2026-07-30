"""Segmentação homogênea pelo método das diferenças acumuladas (AASHTO 1993).

Parâmetro de análise: deflexão máxima D0 (= D1). Equações (Machado, 2019):
  D̄ᵢ = (Dᵢ₋₁ + Dᵢ)/2            (média do intervalo)
  Aᵢ = D̄ᵢ · Δlᵢ                 (área do intervalo)
  A_c = Σ Aᵢ ; L_c = Σ Δlᵢ
  Zᵢ = ΣAᵢ − (A_c / L_c) · ΣΔlᵢ  (diferença acumulada)
Mudanças de inclinação de Z(x) delimitam os segmentos homogêneos.

Restrição de comprimento (regra do projeto): cada trecho homogêneo deve ter
comprimento entre **100 m** (mínimo) e **2.000 m** (máximo). Trechos curtos são
fundidos e trechos longos são subdivididos (ver `_fronteiras_por_comprimento`).
"""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from backmedina.analytics.deflexao_caracteristica import deflexao_caracteristica
from backmedina.model.units import UnidadeDeflexao, fator_conversao


@dataclass
class Segmento:
    indice: int
    ini_m: float
    fim_m: float
    comprimento_m: float
    n_pontos: int
    d0_media: float
    d0_desvio: float
    d0_caracteristica: float


def curva_z(distancias: np.ndarray, d0: np.ndarray) -> np.ndarray:
    """Curva de diferenças acumuladas Z(x) para (distâncias, D0)."""
    distancias = np.asarray(distancias, dtype=float)
    d0 = np.asarray(d0, dtype=float)
    n = len(distancias)
    if n == 0:
        return np.array([])
    z = np.zeros(n)
    area_acum = 0.0
    dist_acum = 0.0
    areas = np.zeros(n)
    dists = np.zeros(n)
    for i in range(1, n):
        dl = distancias[i] - distancias[i - 1]
        d_media = (d0[i - 1] + d0[i]) / 2.0
        areas[i] = d_media * dl
        dists[i] = dl
    a_total = areas.sum()
    l_total = dists.sum()
    tan_alpha = a_total / l_total if l_total != 0 else 0.0
    for i in range(n):
        area_acum += areas[i]
        dist_acum += dists[i]
        z[i] = area_acum - tan_alpha * dist_acum
    return z


def _extremos_z(z: np.ndarray, tol: float) -> list[tuple[int, float]]:
    """Candidatos a fronteira: extremos de Z (onde a inclinação troca de sinal).

    O último sinal não-nulo é carregado através de trechos de inclinação ~0, de
    modo que uma transição com passo plano intermediário ainda seja detectada.
    Retorna pares ``(índice_do_ponto, nitidez)``, onde a nitidez (2ª diferença de
    Z) mede o quão marcado é o vértice — usada para priorizar as fronteiras mais
    fortes quando há restrição de comprimento.
    """
    n = len(z)
    cand: list[tuple[int, float]] = []
    dz = np.diff(z)
    sinal_ant = 0
    for k in range(len(dz)):
        if abs(dz[k]) <= tol:
            continue
        sinal = 1 if dz[k] > 0 else -1
        if sinal_ant != 0 and sinal != sinal_ant:
            p = k  # extremo de Z
            if 0 < p < n - 1:
                nitidez = abs(z[p - 1] - 2.0 * z[p] + z[p + 1])
            else:
                nitidez = abs(dz[k])
            cand.append((p, nitidez))
        sinal_ant = sinal
    return cand


def _fronteiras_por_comprimento(
    dist_v: np.ndarray,
    z: np.ndarray,
    comp_min: float,
    comp_max: float,
    tol: float,
    min_pontos: int,
) -> list[int]:
    """Fronteiras respeitando comprimento mínimo e máximo dos trechos (em metros).

    1. **Aceitação gulosa** dos extremos de Z por nitidez decrescente, aceitando
       um corte só se ambos os lados resultantes tiverem ≥ ``comp_min`` (e
       ≥ ``min_pontos`` estações). Isso garante o **comprimento mínimo**.
    2. **Divisão forçada:** qualquer trecho com comprimento > ``comp_max`` é
       subdividido (em estações internas, mantendo os pedaços ≥ ``comp_min``
       quando possível) até que todos fiquem ≤ ``comp_max``.
    Retorna os índices de corte (início de cada novo trecho), ordenados.
    """
    n = len(dist_v)
    if n < 2:
        return []
    comp_max = max(comp_max, comp_min)  # sanidade

    def comprimento(a: int, b: int) -> float:
        return _comp_faixa(dist_v, a, b)

    # --- 1) aceitação gulosa com piso de comprimento ---
    cortes: list[int] = []
    for p, _ in sorted(_extremos_z(z, tol), key=lambda t: -t[1]):
        pos = bisect.bisect_left(cortes, p)
        esq = cortes[pos - 1] if pos > 0 else 0
        dir_ = cortes[pos] if pos < len(cortes) else n
        len_esq, len_dir = comprimento(esq, p), comprimento(p, dir_)
        n_esq, n_dir = p - esq, dir_ - p
        if (
            len_esq >= comp_min and len_dir >= comp_min
            and n_esq >= min_pontos and n_dir >= min_pontos
        ):
            cortes.insert(pos, p)

    # --- 2) divisão forçada por comprimento máximo ---
    def limites(cs: list[int]) -> list[tuple[int, int]]:
        return list(zip([0, *cs], [*cs, n]))

    guard = 0
    while guard < n:  # backstop: no máximo ~n inserções
        guard += 1
        alterou = False
        for ini, fim in limites(cortes):
            if comprimento(ini, fim) <= comp_max:
                continue
            seg_len = comprimento(ini, fim)
            npieces = math.ceil(seg_len / comp_max)
            alvo = dist_v[ini] + seg_len / npieces
            idx = ini + int(np.argmin(np.abs(dist_v[ini:fim] - alvo)))
            idx = min(max(idx, ini + 1), fim - 1)
            # empurra para respeitar comp_min de cada lado, se possível
            while idx < fim - 1 and comprimento(ini, idx) < comp_min:
                idx += 1
            while idx > ini + 1 and comprimento(idx, fim) < comp_min:
                idx -= 1
            if ini < idx < fim and idx not in cortes:
                bisect.insort(cortes, idx)
                alterou = True
                break
        if not alterou:
            break

    return cortes


def segmentar(
    df: pd.DataFrame,
    coluna_dist: str = "Metros",
    coluna_d0: str = "D1",
    comprimento_min_m: float = 100.0,
    comprimento_max_m: float = 2000.0,
    min_pontos: int = 2,
    tol: float | None = None,
    unidade: UnidadeDeflexao = UnidadeDeflexao.DMM_001,
    ddof: int = 1,
    coluna_estat: str | None = None,
) -> tuple[pd.DataFrame, list[Segmento]]:
    """Segmenta a via em trechos homogêneos por diferenças acumuladas.

    Cada trecho respeita **comprimento mínimo** (``comprimento_min_m``, padrão
    100 m) e **máximo** (``comprimento_max_m``, padrão 2.000 m). Trechos curtos
    demais são fundidos (via aceitação gulosa dos cortes) e trechos longos demais
    são subdivididos.

    A deflexão característica (média+σ) é reportada em **0,01 mm** (unidade do
    MeDiNa). Se ``coluna_d0`` estiver em outra unidade, informe ``unidade`` para
    a normalização interna. As fronteiras dos segmentos são invariantes à escala.

    ``coluna_d0`` é a variável que **gera as fronteiras** — D0 (padrão) ou outra,
    p.ex. a área da bacia. ``coluna_estat`` é a variável das **estatísticas** do
    trecho (Dm, σ, Dc); quando ``None``, usa a própria variável de segmentação,
    preservando o comportamento clássico.

    Retorna (df_com_colunas_Z_e_segmento, lista_de_Segmento).
    """
    mask, dist_v, d0_v, z = _prep_segmentacao(df, coluna_dist, coluna_d0, unidade)
    if coluna_estat is not None:
        d0_v = _serie_estatistica(df, mask, coluna_estat, unidade)
    if tol is None:
        # Tolerância proporcional à amplitude de Z (robusto a ruído).
        amp = (z.max() - z.min()) if z.size else 0.0
        tol = max(amp * 0.001, 1e-9)

    cortes = _fronteiras_por_comprimento(
        dist_v, z,
        comp_min=comprimento_min_m,
        comp_max=comprimento_max_m,
        tol=tol,
        min_pontos=min_pontos,
    )
    return _montar_saida(df, mask, dist_v, d0_v, z, cortes, ddof=ddof)


def _comp_faixa(dist_v: np.ndarray, a: int, b: int) -> float:
    """Comprimento (m) da faixa de estações [a, b): da fronteira inicial à próxima.

    Convenção fronteira-a-fronteira (como o ConversorDadosFWD): o comprimento vai
    da posição da estação inicial ``a`` até a fronteira seguinte — a posição da
    estação ``b`` (início do próximo trecho) ou, no último trecho, a última estação.
    """
    n = len(dist_v)
    fim = dist_v[b] if b < n else dist_v[n - 1]
    return float(fim - dist_v[a])


def _blocos(
    cortes: list[int], n: int, circuito_fechado: bool
) -> list[list[tuple[int, int]]]:
    """Divide as estações em blocos; cada bloco é uma lista de faixas (ini, fim).

    Aberto: um bloco contíguo por trecho ``[0, c1), [c1, c2), …, [ck, n)``.
    Fechado (circuito): os trechos internos ``[c1, c2), …`` mais o **trecho
    circular** que envolve do último marcador ao fim e do início ao 1º marcador:
    ``[ck, n) ∪ [0, c1)`` (duas faixas).
    """
    cortes = sorted(cortes)
    if not circuito_fechado:
        fr = [0, *cortes, n]
        return [[(fr[i], fr[i + 1])] for i in range(len(fr) - 1)]
    if not cortes:
        return [[(0, n)]]
    blocos: list[list[tuple[int, int]]] = [
        [(cortes[j], cortes[j + 1])] for j in range(len(cortes) - 1)
    ]
    blocos.append([(cortes[-1], n), (0, cortes[0])])  # trecho circular
    return blocos


def _montar_saida(
    df: pd.DataFrame,
    mask: np.ndarray,
    dist_v: np.ndarray,
    d0_v: np.ndarray,
    z: np.ndarray,
    cortes: list[int],
    ddof: int = 1,
    circuito_fechado: bool = False,
) -> tuple[pd.DataFrame, list[Segmento]]:
    """Constrói (DataFrame com Z/Segmento, lista de Segmento) a partir dos cortes.

    Reutilizado pela segmentação automática e pela manual. ``cortes`` são índices
    (início de cada novo trecho); D0 já normalizado para 0,01 mm. ``ddof`` escolhe
    desvio amostral (1) ou populacional (0).
    """
    n = len(dist_v)
    segmentos: list[Segmento] = []
    rotulo = np.zeros(n, dtype=int)
    for s, bloco in enumerate(_blocos(cortes, n, circuito_fechado), start=1):
        subs, npts, comp = [], 0, 0.0
        for (a, b) in bloco:
            rotulo[a:b] = s
            subs.append(d0_v[a:b])
            npts += b - a
            comp += _comp_faixa(dist_v, a, b)
        sub = np.concatenate(subs) if subs else np.array([])
        media = float(np.mean(sub)) if sub.size else float("nan")
        desvio = float(np.std(sub, ddof=ddof)) if sub.size > ddof else 0.0
        _ultimo_a, _ultimo_b = bloco[-1]
        fim_m = dist_v[_ultimo_b] if _ultimo_b < n else dist_v[n - 1]
        segmentos.append(
            Segmento(
                indice=s,
                ini_m=float(dist_v[bloco[0][0]]),
                fim_m=float(fim_m),
                comprimento_m=comp,
                n_pontos=int(npts),
                d0_media=media,
                d0_desvio=desvio,
                d0_caracteristica=deflexao_caracteristica(sub, ddof=ddof),
            )
        )

    out = df.loc[mask].copy().reset_index(drop=True)
    out["Z"] = z
    out["Segmento"] = rotulo
    return out, segmentos


def _serie_estatistica(
    df: pd.DataFrame,
    mask: np.ndarray,
    coluna: str,
    unidade: UnidadeDeflexao,
) -> np.ndarray:
    """Série usada nas ESTATÍSTICAS do trecho (Dm, σ, Dc), em 0,01 mm.

    Separada da variável de segmentação: as fronteiras podem vir da área da
    bacia, mas `Dc = D̄₀ + σ` é uma grandeza definida sobre D0 e não muda de
    significado conforme o método usado para achar os cortes.
    """
    k = fator_conversao(unidade, UnidadeDeflexao.DMM_001)
    return pd.to_numeric(df[coluna], errors="coerce").to_numpy(dtype=float)[mask] * k


def _prep_segmentacao(
    df: pd.DataFrame, coluna_dist: str, coluna_d0: str, unidade: UnidadeDeflexao
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Extrai (mask, dist_v, d0_v em 0,01 mm, z) — base comum de auto/manual."""
    k = fator_conversao(unidade, UnidadeDeflexao.DMM_001)  # -> 0,01 mm
    dist = pd.to_numeric(df[coluna_dist], errors="coerce").to_numpy()
    d0 = pd.to_numeric(df[coluna_d0], errors="coerce").to_numpy() * k
    mask = ~(np.isnan(dist) | np.isnan(d0))
    dist_v, d0_v = dist[mask], d0[mask]
    z = curva_z(dist_v, d0_v)
    return mask, dist_v, d0_v, z


def curva_zi_do_df(
    df: pd.DataFrame,
    coluna_dist: str = "Metros",
    coluna_d0: str = "D1",
    unidade: UnidadeDeflexao = UnidadeDeflexao.DMM_001,
) -> tuple[np.ndarray, np.ndarray]:
    """Retorna (dist_v, z): distância e a curva de diferenças acumuladas **Zi**.

    É a mesma curva usada pela segmentação automática — sobre ela o usuário marca
    as fronteiras no modo manual.
    """
    _, dist_v, _, z = _prep_segmentacao(df, coluna_dist, coluna_d0, unidade)
    return dist_v, z


def tabela_zi(
    df: pd.DataFrame,
    coluna_dist: str = "Metros",
    coluna_d0: str = "D1",
    unidade: UnidadeDeflexao = UnidadeDeflexao.DMM_001,
    rotulo_var: str = "D0 (0,01 mm)",
) -> tuple[pd.DataFrame, dict]:
    """Tabela detalhada do cálculo de Zi (diferenças acumuladas), em 0,01 mm.

    Colunas: Metros, <rotulo_var>, D_media (D̄ᵢ), Delta_l (Δlᵢ), A_i, Soma_A
    (ΣAᵢ), Soma_L (ΣΔlᵢ), Zi. Retorna (DataFrame, totais) com A_c, L_c e
    tan_alpha. A variável é normalizada para 0,01 mm conforme ``unidade``.

    ``rotulo_var`` nomeia a 2ª coluna — os consumidores (xlsx/PDF) a leem pela
    posição, então a tabela acompanha a variável usada na segmentação.
    """
    _, dist_v, d0_v, z = _prep_segmentacao(df, coluna_dist, coluna_d0, unidade)
    n = len(dist_v)
    dbar = np.zeros(n)
    dl = np.zeros(n)
    A = np.zeros(n)
    for i in range(1, n):
        dl[i] = dist_v[i] - dist_v[i - 1]
        dbar[i] = (d0_v[i - 1] + d0_v[i]) / 2.0
        A[i] = dbar[i] * dl[i]
    soma_A = np.cumsum(A)
    soma_L = np.cumsum(dl)
    a_c, l_c = float(A.sum()), float(dl.sum())
    tan_alpha = a_c / l_c if l_c else 0.0

    # A 1ª estação não tem intervalo anterior: D̄/Δl/A ficam vazios (NaN).
    dbar_out = dbar.copy(); dl_out = dl.copy(); a_out = A.copy()
    if n:
        dbar_out[0] = dl_out[0] = a_out[0] = np.nan

    tab = pd.DataFrame(
        {
            "Metros": dist_v,
            rotulo_var: d0_v,
            "D_media": dbar_out,
            "Delta_l (m)": dl_out,
            "A_i": a_out,
            "Soma_A": soma_A,
            "Soma_L": soma_L,
            "Zi": z,
        }
    )
    totais = {"A_c": a_c, "L_c": l_c, "tan_alpha": tan_alpha}
    return tab, totais


def cortes_de_fronteiras(
    dist_v: np.ndarray, fronteiras_m, tol_m: float = 0.5
) -> tuple[list[int], list[str]]:
    """Converte posições de fronteira (m) em índices de corte (início de trecho).

    Cada fronteira marca a estação onde **começa** um novo trecho. Retorna
    (cortes_ordenados_unicos, avisos). Avisos para fronteiras que não coincidem
    com uma estação, ou que caem nos extremos da via.
    """
    n = len(dist_v)
    cortes: set[int] = set()
    avisos: list[str] = []
    for b in fronteiras_m:
        b = float(b)
        idx = int(np.argmin(np.abs(dist_v - b)))
        if abs(dist_v[idx] - b) > tol_m:
            avisos.append(
                f"Fronteira em {b:g} m não coincide com uma estação do "
                f"levantamento (mais próxima: {dist_v[idx]:g} m)."
            )
            continue
        if idx <= 0 or idx >= n:
            avisos.append(
                f"Fronteira em {b:g} m está no extremo da via e foi ignorada."
            )
            continue
        cortes.add(idx)
    return sorted(cortes), avisos


def validar_fronteiras_manuais(
    dist_v: np.ndarray,
    fronteiras_m,
    comprimento_min_m: float = 100.0,
    comprimento_max_m: float = 2000.0,
    min_pontos: int = 2,
    circuito_fechado: bool = False,
) -> tuple[list[int], list[str]]:
    """Valida fronteiras manuais. Retorna (cortes, violacoes).

    ``violacoes`` vazio ⇒ segmentação manual é válida. As regras são as mesmas da
    automática: cada trecho com comprimento em [min, max] e ≥ ``min_pontos``
    estações. Com ``circuito_fechado``, valida também o trecho circular (que
    envolve do último marcador de volta ao início).
    """
    n = len(dist_v)
    cortes, violacoes = cortes_de_fronteiras(dist_v, fronteiras_m)

    if n < 2:
        violacoes.append("Levantamento sem estações suficientes para segmentar.")
        return cortes, violacoes
    if not cortes:
        # Espelha a mensagem "Seleção vazia" do ConversorDadosFWD.
        violacoes.append(
            "Seleção vazia: marque no gráfico os pontos que delimitam os "
            "segmentos homogêneos."
        )
        return cortes, violacoes

    for s, bloco in enumerate(_blocos(cortes, n, circuito_fechado), start=1):
        comp = sum(_comp_faixa(dist_v, a, b) for (a, b) in bloco)
        npts = sum(b - a for (a, b) in bloco)
        circular = len(bloco) > 1
        suf = " (segmento circular)" if circular else ""
        _ub = bloco[-1][1]
        _fim = dist_v[_ub] if _ub < n else dist_v[n - 1]
        faixa = f"Trecho {s} ({dist_v[bloco[0][0]]:g}–{_fim:g} m)"
        if comp < comprimento_min_m:
            violacoes.append(
                f"{faixa}: distância menor que o comprimento mínimo{suf}."
            )
        if comp > comprimento_max_m:
            violacoes.append(
                f"{faixa}: distância maior que o comprimento máximo{suf}."
            )
        if npts < min_pontos:
            violacoes.append(
                f"{faixa}: {npts} estação(ões) < mínimo de {min_pontos}{suf}."
            )
    return cortes, violacoes


def segmentar_manual(
    df: pd.DataFrame,
    fronteiras_m,
    coluna_dist: str = "Metros",
    coluna_d0: str = "D1",
    comprimento_min_m: float = 100.0,
    comprimento_max_m: float = 2000.0,
    min_pontos: int = 2,
    unidade: UnidadeDeflexao = UnidadeDeflexao.DMM_001,
    ddof: int = 1,
    circuito_fechado: bool = False,
    coluna_estat: str | None = None,
) -> tuple[pd.DataFrame | None, list[Segmento], list[str]]:
    """Segmentação MANUAL a partir de fronteiras (m) marcadas pelo usuário.

    Valida as regras (mesmas da automática). Se houver violações, **não segmenta**
    e retorna ``(None, [], violacoes)``. Se válido, retorna ``(df_seg, segmentos, [])``.

    ``coluna_estat``: variável das estatísticas do trecho — ver :func:`segmentar`.
    """
    mask, dist_v, d0_v, z = _prep_segmentacao(df, coluna_dist, coluna_d0, unidade)
    if coluna_estat is not None:
        d0_v = _serie_estatistica(df, mask, coluna_estat, unidade)
    cortes, violacoes = validar_fronteiras_manuais(
        dist_v, fronteiras_m,
        comprimento_min_m=comprimento_min_m,
        comprimento_max_m=comprimento_max_m,
        min_pontos=min_pontos,
        circuito_fechado=circuito_fechado,
    )
    if violacoes:
        return None, [], violacoes
    out, segmentos = _montar_saida(
        df, mask, dist_v, d0_v, z, cortes,
        ddof=ddof, circuito_fechado=circuito_fechado,
    )
    return out, segmentos, []
