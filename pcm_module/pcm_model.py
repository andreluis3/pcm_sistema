"""
pcm_model.py
════════════
Modelos de dados — dataclasses com campos físicos corretos.

REGRA: nenhum campo armazena pandas.Series.
Todos os campos de séries são list[float].
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PCMResult:
    """
    Resultado completo do processamento de um CSV de experimento PCM.

    Campos físicos adicionados:
        q_notebook_j  — energia total gerada pelo notebook (J)
        q_pcm_j       — energia absorvida pelo PCM  (J)
        eficiencia    — η = Q_pcm / Q_notebook × 100  (%)
        tempo_eq_s    — tempo equivalente de atuação (s)
        energia_acum_notebook  — série temporal (J)
        energia_acum_pcm       — série temporal (J)
    """

    # ── Séries temporais brutas ───────────────────────────────────────────────
    tempo_s: list[float]        = field(default_factory=list)
    temperatura_c: list[float]  = field(default_factory=list)
    potencia_w: list[float]     = field(default_factory=list)
    energia_j: list[float]      = field(default_factory=list)

    # ── Séries derivadas ──────────────────────────────────────────────────────
    energia_acum_notebook: list[float] = field(default_factory=list)
    energia_acum_pcm: list[float]      = field(default_factory=list)

    # ── Escalares físicos ─────────────────────────────────────────────────────
    q_notebook_j: float   = 0.0   # energia gerada (J)
    q_pcm_j: float        = 0.0   # energia absorvida pelo PCM (J)
    eficiencia: float     = 0.0   # η (%)
    tempo_eq_s: float     = 0.0   # tempo equivalente (s)

    # ── Escalares legados ─────────────────────────────────────────────────────
    energia_total: float         = 0.0
    energia_teorica: float       = 0.0
    potencia_media: float        = 0.0
    massa_pcm: float             = 0.0
    pico_temperatura: float      = 0.0
    tempo_pico_temperatura: float = 0.0
    temperatura_media: float     = 0.0
    delta_tempo: float           = 0.0
    temperatura_inicial: float   = 0.0
    temperatura_final: float     = 0.0

    # ── Metadados textuais ────────────────────────────────────────────────────
    analise_tecnica: list[str]          = field(default_factory=list)
    calculo_detalhado: list[str]        = field(default_factory=list)
    csv_preview: list[dict[str, str]]   = field(default_factory=list)

    def __post_init__(self) -> None:
        """Garante tipos corretos — bloqueia pandas.Series."""
        _listas = (
            "tempo_s", "temperatura_c", "potencia_w", "energia_j",
            "energia_acum_notebook", "energia_acum_pcm",
        )
        for attr in _listas:
            v = getattr(self, attr)
            if not isinstance(v, list):
                try:
                    setattr(self, attr, [float(x) for x in v])
                except Exception:
                    setattr(self, attr, [])
            else:
                setattr(self, attr, [float(x) for x in v])

        _escalares = (
            "q_notebook_j", "q_pcm_j", "eficiencia", "tempo_eq_s",
            "energia_total", "energia_teorica", "potencia_media",
            "massa_pcm", "pico_temperatura", "tempo_pico_temperatura",
            "temperatura_media", "delta_tempo",
            "temperatura_inicial", "temperatura_final",
        )
        for attr in _escalares:
            try:
                setattr(self, attr, float(getattr(self, attr)))
            except (TypeError, ValueError):
                setattr(self, attr, 0.0)