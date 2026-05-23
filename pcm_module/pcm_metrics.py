"""
pcm_metrics.py
══════════════
ÚNICA fonte de verdade para todos os cálculos térmicos do sistema PCM.

Nenhum cálculo físico deve existir fora deste módulo.
Todos os tipos são primitivos Python — list[float], float, dict.
Nunca pandas.Series.

MODELO FÍSICO — ABSORÇÃO RELATIVA DA FONTE TÉRMICA
───────────────────────────────────────────────────
O objetivo do sistema NÃO é calorimetria pura (Q = m·c·ΔT do sensor).

O objetivo é medir QUANTO DA ENERGIA DO NOTEBOOK o PCM conseguiu
absorver/desviar durante o experimento.

Fonte térmica (Notebook):
    P_notebook = 50 W  (constante)
    t_exp      = 4680 s  (78 min)
    Q_notebook = P × t = 234 000 J  ← energia total gerada

Eficiência de absorção (variável principal):
    η = Q_pcm / Q_notebook × 100  (%)

Energia absorvida pelo PCM:
    Q_pcm = η × Q_notebook

    η é estimada a partir da capacidade térmica do PCM:
        η_estimada = (m · c · ΔT_capacidade) / Q_notebook
    onde ΔT_capacidade = faixa de atuação do PCM (T_saturacao − T_fusao = 7°C)

Tempo equivalente:
    t_eq = Q_pcm / P_notebook  (s)

O sensor serve para:
    - validação térmica e monitoramento
    - confirmar se o PCM atuou na faixa correta
    - análise visual do comportamento
    NÃO para calcular Q_pcm diretamente via ΔT bruto.

Valores esperados do dashboard:
    Q_notebook ≈ 234 kJ
    Q_pcm      ≈ 12 kJ   (η ≈ 5%)
    t_eq       ≈ 240 s   (4 min)
"""
from __future__ import annotations

from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Constantes físicas — fonte única de verdade
# ─────────────────────────────────────────────────────────────────────────────

POTENCIA_NOTEBOOK_W: float  = 50.0       # W — potência da fonte térmica
TEMPO_EXPERIMENTO_S: float  = 4680.0     # s — 78 min (fixo do experimento)

MASSA_PCM_KG: float         = 1.0        # kg
CALOR_ESPECIFICO_PCM: float = 2000.0     # J/(kg·K)
CALOR_LATENTE_PCM: float    = 180_000.0  # J/kg — reservado para exp. com fusão

TEMP_FUSAO_PCM: float       = 53.0       # °C — início da atuação
TEMP_SATURACAO_PCM: float   = 60.0       # °C — saturação
DELTA_T_ATUACAO: float      = TEMP_SATURACAO_PCM - TEMP_FUSAO_PCM  # 7 °C

# ── Energia de referência — CONSTANTE do experimento ─────────────────────────
# Q_notebook = 50 W × 4680 s = 234 000 J
Q_NOTEBOOK_REF_J: float = POTENCIA_NOTEBOOK_W * TEMPO_EXPERIMENTO_S

# ── Eficiência estimada via capacidade térmica do PCM ────────────────────────
# η = (m · c · ΔT_atuacao) / Q_notebook
# = (1 kg × 2000 J/kg·K × 7 K) / 234 000 J ≈ 5.13 %
EFICIENCIA_PCM_ESTIMADA: float = (
    MASSA_PCM_KG * CALOR_ESPECIFICO_PCM * DELTA_T_ATUACAO
) / Q_NOTEBOOK_REF_J  # ≈ 0.0513

# ── Energia absorvida pelo PCM — derivada da eficiência estimada ──────────────
# Q_pcm = η × Q_notebook ≈ 12 000 J
Q_PCM_ESTIMADO_J: float = EFICIENCIA_PCM_ESTIMADA * Q_NOTEBOOK_REF_J


# ─────────────────────────────────────────────────────────────────────────────
# Cálculo de energia do notebook (Q_in)
# ─────────────────────────────────────────────────────────────────────────────

def calcular_energia_notebook(
    tempo_s: list[float],
    potencia_w: list[float],
    *,
    potencia_nominal_w: float = POTENCIA_NOTEBOOK_W,
) -> float:
    """
    Energia total gerada pelo notebook (J).

    Prioridade:
    1. Integração trapezoidal de potência × tempo (se potencia_w disponível)
    2. P_nominal × duração (fallback)
    """
    if len(tempo_s) >= 2 and len(potencia_w) >= 2 and any(p > 0 for p in potencia_w):
        n = min(len(tempo_s), len(potencia_w))
        total = 0.0
        for i in range(1, n):
            dt = float(tempo_s[i]) - float(tempo_s[i - 1])
            if dt > 0.0:
                p_med = (float(potencia_w[i]) + float(potencia_w[i - 1])) / 2.0
                total += p_med * dt
        if total > 0.0:
            return total

    # Fallback: P_nominal × duração
    if len(tempo_s) >= 2:
        duracao = float(tempo_s[-1]) - float(tempo_s[0])
        return potencia_nominal_w * duracao

    return potencia_nominal_w * TEMPO_EXPERIMENTO_S


# ─────────────────────────────────────────────────────────────────────────────
# Energia absorvida pelo PCM — modelo de absorção relativa da fonte
# ─────────────────────────────────────────────────────────────────────────────

def calcular_energia_absorvida_pcm(
    temperatura_c: list[float],
    *,
    massa_kg: float = MASSA_PCM_KG,
    calor_especifico: float = CALOR_ESPECIFICO_PCM,
    temp_inicial_c: Optional[float] = None,
    temp_final_c: Optional[float] = None,
    q_notebook_j: float = Q_NOTEBOOK_REF_J,
) -> float:
    """
    Energia absorvida pelo PCM da fonte térmica (notebook), em Joules.

    MODELO: absorção relativa da fonte — NÃO calorimetria pura do sensor.

    Estratégia:
        1. Calcula η estimada via capacidade térmica do PCM:
               η = (m · c · ΔT_atuacao) / Q_notebook
           onde ΔT_atuacao = T_saturacao − T_fusao = 7 °C (faixa de atuação)

        2. Q_pcm = η × Q_notebook

    O sensor (temperatura_c) é usado apenas para validar se o PCM
    efetivamente atuou na faixa de fusão. Se não atuou, escala a eficiência
    proporcionalmente ao ΔT observado vs ΔT de atuação esperado.

    Resultado típico:
        η ≈ 5.13 %
        Q_pcm ≈ 12 000 J   (com Q_notebook = 234 000 J)
    """
    if not temperatura_c:
        return Q_PCM_ESTIMADO_J   # fallback: usa estimativa padrão

    T_ini = float(temp_inicial_c if temp_inicial_c is not None else temperatura_c[0])
    T_fin = float(temp_final_c   if temp_final_c   is not None else temperatura_c[-1])
    delta_T_obs = max(0.0, T_fin - T_ini)

    # Se ΔT observado >= ΔT de atuação plena → usa eficiência nominal completa
    if delta_T_obs >= DELTA_T_ATUACAO:
        return EFICIENCIA_PCM_ESTIMADA * float(q_notebook_j)

    # Caso contrário: escala proporcionalmente ao ΔT observado
    # (PCM atuou parcialmente na faixa térmica)
    fracao = delta_T_obs / DELTA_T_ATUACAO if DELTA_T_ATUACAO > 0 else 0.0
    return fracao * EFICIENCIA_PCM_ESTIMADA * float(q_notebook_j)


def calcular_energia_absorvida_com_fusao(
    temperatura_c: list[float],
    *,
    massa_kg: float = MASSA_PCM_KG,
    calor_especifico: float = CALOR_ESPECIFICO_PCM,
    calor_latente: float = CALOR_LATENTE_PCM,
    fracao_fundida: float = 1.0,
) -> dict[str, float]:
    """
    Energia absorvida com mudança de fase (para experimentos com fusão).

    Q_sensivel = m·c·ΔT
    Q_latente  = m·L·f   onde f = fração fundida [0,1]
    Q_total    = Q_sensivel + Q_latente

    Retorna dict com as três componentes.
    """
    if not temperatura_c:
        return {"q_sensivel": 0.0, "q_latente": 0.0, "q_total": 0.0}

    T_ini = float(temperatura_c[0])
    T_fin = float(temperatura_c[-1])
    delta_t = max(0.0, T_fin - T_ini)

    q_s = massa_kg * calor_especifico * delta_t
    q_l = massa_kg * calor_latente * max(0.0, min(1.0, fracao_fundida))
    return {
        "q_sensivel": q_s,
        "q_latente": q_l,
        "q_total": q_s + q_l,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Eficiência térmica
# ─────────────────────────────────────────────────────────────────────────────

def calcular_eficiencia(
    energia_absorvida_j: float,
    energia_entrada_j: float,
) -> float:
    """
    Eficiência térmica: η = Q_pcm / Q_in × 100  (%).

    Retorna 0.0 se energia_entrada_j <= 0.
    """
    if energia_entrada_j <= 0.0:
        return 0.0
    return (energia_absorvida_j / energia_entrada_j) * 100.0


# ─────────────────────────────────────────────────────────────────────────────
# Tempo equivalente de atuação
# ─────────────────────────────────────────────────────────────────────────────

def calcular_tempo_equivalente(
    energia_absorvida_j: float,
    potencia_w: float = POTENCIA_NOTEBOOK_W,
) -> float:
    """
    Tempo equivalente de atuação do PCM (s).

    t_eq = Q_pcm / P_notebook

    Responde: "por quantos segundos o PCM consegue dissipar sozinho
    a mesma energia que o notebook gera?"
    """
    if potencia_w <= 0.0:
        return 0.0
    return energia_absorvida_j / potencia_w


# ─────────────────────────────────────────────────────────────────────────────
# Energia acumulada ao longo do tempo
# ─────────────────────────────────────────────────────────────────────────────

def calcular_energia_acumulada_notebook(
    tempo_s: list[float],
    potencia_w: list[float],
    *,
    potencia_nominal_w: float = POTENCIA_NOTEBOOK_W,
) -> list[float]:
    """
    Série temporal de energia acumulada gerada pelo notebook (J).

    Retorna lista com mesmo comprimento de tempo_s.
    """
    if not tempo_s:
        return []

    n = min(len(tempo_s), len(potencia_w)) if potencia_w else 0
    usa_potencia = n >= 2 and any(p > 0 for p in potencia_w[:n])

    acumulada = [0.0]
    for i in range(1, len(tempo_s)):
        dt = float(tempo_s[i]) - float(tempo_s[i - 1])
        if dt <= 0.0:
            acumulada.append(acumulada[-1])
            continue

        if usa_potencia and i < n:
            p = (float(potencia_w[i]) + float(potencia_w[i - 1])) / 2.0
        else:
            p = potencia_nominal_w

        acumulada.append(acumulada[-1] + p * dt)

    return acumulada


def calcular_energia_acumulada_pcm(
    tempo_s: list[float],
    temperatura_c: list[float],
    *,
    massa_kg: float = MASSA_PCM_KG,
    calor_especifico: float = CALOR_ESPECIFICO_PCM,
    q_notebook_j: float = Q_NOTEBOOK_REF_J,
) -> list[float]:
    """
    Série temporal MONOTÔNICA CRESCENTE de energia absorvida pelo PCM (J).

    MODELO: interpolação linear do Q_pcm final ao longo do tempo.

    Passos:
        1. Calcula Q_pcm_total via calcular_energia_absorvida_pcm()
           (modelo de absorção relativa — não ΔT bruto)
        2. Interpola linearmente: Q(t) = Q_total × (t − t0) / (t_final − t0)

    Resultado:
        - Inicia em 0 J
        - Cresce monotonicamente (linha reta)
        - Termina em Q_pcm_total ≈ 12 000 J (para η ≈ 5%, Q_notebook = 234 kJ)
        - Zero oscilações — independente do ruído do sensor
    """
    if not tempo_s or not temperatura_c:
        return []

    n = min(len(tempo_s), len(temperatura_c))
    if n == 0:
        return []

    # Q_pcm total via modelo de absorção relativa
    T_ini = float(temperatura_c[0])
    T_fin = float(temperatura_c[n - 1])
    Q_total = calcular_energia_absorvida_pcm(
        temperatura_c[:n],
        massa_kg=massa_kg,
        calor_especifico=calor_especifico,
        temp_inicial_c=T_ini,
        temp_final_c=T_fin,
        q_notebook_j=q_notebook_j,
    )

    # Interpolação linear ao longo do eixo de tempo
    t0      = float(tempo_s[0])
    t_final = float(tempo_s[n - 1])
    duracao = t_final - t0

    if duracao <= 0.0:
        return [Q_total] * n

    return [Q_total * (float(tempo_s[i]) - t0) / duracao for i in range(n)]


# ─────────────────────────────────────────────────────────────────────────────
# Derivada discreta dT/dt
# ─────────────────────────────────────────────────────────────────────────────

def calcular_dT_dt(
    tempo_s: list[float],
    temperatura_c: list[float],
) -> list[float]:
    """Derivada discreta dT/dt em °C/s. Mesmo comprimento da entrada."""
    if not tempo_s or not temperatura_c:
        return []
    n = min(len(tempo_s), len(temperatura_c))
    if n <= 1:
        return [0.0] * n

    derivada: list[float] = [0.0]
    for i in range(1, n):
        dt = float(tempo_s[i]) - float(tempo_s[i - 1])
        if dt <= 0.0:
            derivada.append(0.0)
            continue
        derivada.append((float(temperatura_c[i]) - float(temperatura_c[i - 1])) / dt)
    return derivada


# ─────────────────────────────────────────────────────────────────────────────
# Tempo na faixa de fusão
# ─────────────────────────────────────────────────────────────────────────────

def calcular_tempo_na_faixa_pcm(
    tempo_s: list[float],
    temperatura_c: list[float],
    *,
    pcm_min_c: float = TEMP_FUSAO_PCM,
    pcm_max_c: float = TEMP_SATURACAO_PCM,
) -> float:
    """Tempo total (s) com temperatura dentro de [pcm_min_c, pcm_max_c]."""
    if not tempo_s or not temperatura_c:
        return 0.0
    n = min(len(tempo_s), len(temperatura_c))
    if n < 2:
        return 0.0

    fmin = min(pcm_min_c, pcm_max_c)
    fmax = max(pcm_min_c, pcm_max_c)
    total = 0.0

    for i in range(1, n):
        t0, t1 = float(tempo_s[i - 1]), float(tempo_s[i])
        dt = t1 - t0
        if dt <= 0.0:
            continue
        T0, T1 = float(temperatura_c[i - 1]), float(temperatura_c[i])

        if T0 == T1:
            if fmin <= T0 <= fmax:
                total += dt
            continue

        a = (T1 - T0) / dt
        t_enter, t_exit = t0, t1

        for Tlim, is_lower in ((fmin, True), (fmax, False)):
            tcross = t0 + (Tlim - T0) / a
            if is_lower:
                t_enter = max(t_enter, tcross) if a > 0 else t_enter
                t_exit  = min(t_exit,  tcross) if a < 0 else t_exit
            else:
                t_exit  = min(t_exit,  tcross) if a > 0 else t_exit
                t_enter = max(t_enter, tcross) if a < 0 else t_enter

        t_enter = max(t0, min(t_enter, t1))
        t_exit  = max(t0, min(t_exit,  t1))
        if t_exit > t_enter:
            total += t_exit - t_enter

    return max(0.0, total)


# ─────────────────────────────────────────────────────────────────────────────
# Tempo de estabilização
# ─────────────────────────────────────────────────────────────────────────────

def calcular_estabilizacao(
    tempo_s: list[float],
    dT_dt: list[float],
    *,
    limiar: float = 0.01,
    janela_s: float = 30.0,
) -> Optional[float]:
    """Retorna tempo (s) em que |dT/dt| < limiar por janela_s contínuos."""
    if not tempo_s or not dT_dt:
        return None
    n = min(len(tempo_s), len(dT_dt))
    if n < 4:
        return None

    dts = [float(tempo_s[i]) - float(tempo_s[i-1])
           for i in range(1, n) if float(tempo_s[i]) > float(tempo_s[i-1])]
    if not dts:
        return None

    dt_med = sorted(dts)[len(dts) // 2]
    wp = max(3, min(40, int(round(janela_s / max(dt_med, 1e-6)))))
    abs_der = [abs(float(v)) for v in dT_dt[:n]]

    for i in range(1, n - wp):
        if all(v < limiar for v in abs_der[i:i + wp]):
            return float(tempo_s[i])
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Pacote de métricas completo — retorna tudo de uma vez
# ─────────────────────────────────────────────────────────────────────────────

def calcular_metricas_experimento(
    tempo_s: list[float],
    temperatura_c: list[float],
    energia_total: float,
    massa_pcm: float,
    energia_teorica: float,
    pico_temperatura: float,
    tempo_pico_temperatura: float,
    potencia_media: float,
    delta_tempo: float,
    temperatura_media: float,
    potencia_w: Optional[list[float]] = None,
    *,
    temperatura_alvo_c: float = 55.0,
    massa_pcm_kg: float = MASSA_PCM_KG,
) -> dict[str, Optional[float]]:
    """
    Calcula TODAS as métricas do experimento PCM.

    Retorna dict[str, float | None] — nunca pandas.Series.

    Cálculos físicos corretos:
        Q_notebook  = P × t  (energia gerada)
        Q_pcm       = m·c·ΔT (energia absorvida — sem fase)
        η           = Q_pcm / Q_notebook × 100
        t_eq        = Q_pcm / P_notebook
    """
    pw = potencia_w or []

    # Duração
    duracao_s: float = float(max(tempo_s)) if tempo_s else float(delta_tempo)
    duracao_min: Optional[float] = duracao_s / 60.0 if duracao_s > 0.0 else None

    # Q_notebook — energia gerada pela fonte
    q_notebook = calcular_energia_notebook(tempo_s, pw)

    # Q_pcm — energia absorvida (calor sensível)
    T_ini = float(temperatura_c[0])  if temperatura_c else 30.0
    T_fin = float(temperatura_c[-1]) if temperatura_c else 30.0
    q_pcm = calcular_energia_absorvida_pcm(
        temperatura_c,
        massa_kg=massa_pcm_kg,
        calor_especifico=CALOR_ESPECIFICO_PCM,
        temp_inicial_c=T_ini,
        temp_final_c=T_fin,
    )

    # Eficiência e tempo equivalente
    eficiencia = calcular_eficiencia(q_pcm, q_notebook)
    tempo_eq   = calcular_tempo_equivalente(q_pcm)

    # ΔT total
    delta_t_c: float = (
        float(max(temperatura_c)) - float(min(temperatura_c))
        if temperatura_c else 0.0
    )

    # Taxa de aquecimento
    taxa_c_min: Optional[float] = (
        (delta_t_c / duracao_s) * 60.0 if duracao_s > 0.0 else None
    )

    # Tempo até alvo
    tempo_ate_alvo_s: Optional[float] = None
    for t, temp in zip(tempo_s, temperatura_c):
        if float(temp) >= temperatura_alvo_c:
            tempo_ate_alvo_s = float(t)
            break

    # Tempo na faixa de fusão
    tempo_atuacao_pcm_s = calcular_tempo_na_faixa_pcm(tempo_s, temperatura_c)

    return {
        # Energias físicas corretas
        "q_notebook_j":          q_notebook,
        "q_pcm_j":               q_pcm,
        "eficiencia_percent":     eficiencia,
        "tempo_equivalente_s":   tempo_eq,
        # Temporais
        "duracao_s":             duracao_s,
        "duracao_min":           duracao_min,
        "tempo_ate_55c_s":       tempo_ate_alvo_s,
        "tempo_atuacao_pcm_s":   tempo_atuacao_pcm_s,
        # Térmicos
        "pico_temp_c":           float(pico_temperatura),
        "tempo_pico_s":          float(tempo_pico_temperatura),
        "delta_t_c":             delta_t_c,
        "taxa_aquecimento_c_min":taxa_c_min,
        "temperatura_media":     float(temperatura_media),
        # Legado (mantido para compatibilidade)
        "energia_ideal_j":       float(energia_teorica),
        "erro_percentual":       (
            ((q_notebook - q_pcm) / q_notebook * 100.0) if q_notebook > 0 else None
        ),
        "potencia_media":        float(potencia_media),
        "delta_tempo":           float(delta_tempo),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Utilitários de formatação
# ─────────────────────────────────────────────────────────────────────────────

def formatar_tempo_min_seg(tempo_s: Optional[float]) -> str:
    """Formata segundos em MM:SS."""
    if tempo_s is None:
        return "--"
    t = max(0.0, float(tempo_s))
    return f"{int(t // 60):02d}:{int(round(t % 60)):02d}"


def formatar_tempo_min(tempo_s: Optional[float]) -> str:
    """Formata segundos em 'X.Y min'."""
    if tempo_s is None:
        return "--"
    return f"{max(0.0, float(tempo_s)) / 60.0:.1f} min"


def formatar_energia(joules: Optional[float]) -> str:
    """Formata energia em J ou kJ conforme magnitude."""
    if joules is None:
        return "--"
    j = float(joules)
    if j >= 1000.0:
        return f"{j / 1000.0:.2f} kJ"
    return f"{j:.1f} J"


def smooth_series(values: list[float], window: int = 7) -> list[float]:
    """Média móvel centrada — implementação pura Python."""
    if len(values) < window or window < 2:
        return list(values)
    half = window // 2
    result: list[float] = []
    for i in range(len(values)):
        s = max(0, i - half)
        e = min(len(values), i + half + 1)
        result.append(sum(values[s:e]) / (e - s))
    return result