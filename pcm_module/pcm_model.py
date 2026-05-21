"""
pcm_model.py
════════════
Modelos de dados do sistema PCM.

REGRA CRÍTICA: nenhum campo pode armazenar pandas.Series.
Todos os campos de séries temporais são list[float].
Conversão obrigatória no PCMService antes de instanciar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PCMResult:
    """
    Resultado completo do processamento de um CSV de experimento PCM.

    Todos os campos de séries temporais são list[float] — NUNCA pandas.Series.
    O PCMService é responsável por converter antes de instanciar.
    """

    # ── Séries temporais ─────────────────────────────────────────────────────
    tempo_s: list[float] = field(default_factory=list)
    temperatura_c: list[float] = field(default_factory=list)
    potencia_w: list[float] = field(default_factory=list)
    energia_j: list[float] = field(default_factory=list)

    # ── Escalares calculados ─────────────────────────────────────────────────
    energia_total: float = 0.0
    energia_teorica: float = 0.0
    potencia_media: float = 0.0
    massa_pcm: float = 0.0
    pico_temperatura: float = 0.0
    tempo_pico_temperatura: float = 0.0
    temperatura_media: float = 0.0
    delta_tempo: float = 0.0

    # ── Metadados textuais ───────────────────────────────────────────────────
    analise_tecnica: list[str] = field(default_factory=list)
    calculo_detalhado: list[str] = field(default_factory=list)
    csv_preview: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Valida e garante que todas as séries são list[float]."""
        for attr in ("tempo_s", "temperatura_c", "potencia_w", "energia_j"):
            value = getattr(self, attr)
            # Se veio como pandas.Series ou outro iterável, converte
            if not isinstance(value, list):
                try:
                    setattr(self, attr, [float(v) for v in value])
                except Exception:
                    setattr(self, attr, [])
            else:
                # Garante que todos os elementos são float
                setattr(self, attr, [float(v) for v in value])

        # Garante escalares float
        for attr in (
            "energia_total", "energia_teorica", "potencia_media",
            "massa_pcm", "pico_temperatura", "tempo_pico_temperatura",
            "temperatura_media", "delta_tempo",
        ):
            try:
                setattr(self, attr, float(getattr(self, attr)))
            except (TypeError, ValueError):
                setattr(self, attr, 0.0)