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
    Resultado completo do processamento de um experimento PCM.

    Estrutura nova:
    ─────────────────────────────────────────────
    - Dados crus do CSV
    - Séries derivadas
    - Métricas físicas
    - Informações térmicas
    - Dados auxiliares para UI
    """

    # =========================================================
    # SÉRIES TEMPORAIS BRUTAS
    # =========================================================

    tempo_s: list[float] = field(default_factory=list)

    temperatura_c: list[float] = field(default_factory=list)

    potencia_w: list[float] = field(default_factory=list)

    energia_j: list[float] = field(default_factory=list)

    # =========================================================
    # SÉRIES DERIVADAS
    # =========================================================

    energia_acum_notebook: list[float] = field(default_factory=list)

    energia_acum_pcm: list[float] = field(default_factory=list)

    # =========================================================
    # ENERGIAS FÍSICAS
    # =========================================================

    # Energia total gerada pelo notebook
    q_notebook_j: float = 0.0

    # Energia absorvida pelo PCM
    q_pcm_j: float = 0.0

    # Eficiência térmica (%)
    eficiencia: float = 0.0

    # Tempo equivalente de atuação térmica
    tempo_eq_s: float = 0.0

    # =========================================================
    # MÉTRICAS TÉRMICAS
    # =========================================================

    potencia_media: float = 0.0

    massa_pcm: float = 0.0

    massa_pcm_g: float = 0.0
    
    massa_pcm_necessaria: float = 0.0
    massa_pcm_utilizada: float = 0.0

    temperatura_media: float = 0.0

    temperatura_inicial: float = 0.0

    temperatura_final: float = 0.0

    pico_temperatura: float = 0.0

    tempo_pico_temperatura: float = 0.0

    delta_t_c: float = 0.0

    # =========================================================
    # TEMPORAIS
    # =========================================================

    duracao_s: float = 0.0

    duracao_min: float = 0.0

    delta_tempo: float = 0.0

    tempo_ate_55c_s: Optional[float] = None

    tempo_atuacao_pcm_s: float = 0.0

    # =========================================================
    # ENERGIAS AUXILIARES
    # =========================================================

    energia_total: float = 0.0

    energia_teorica: float = 0.0

    erro_percentual: float = 0.0

    # =========================================================
    # TEXTO / UI
    # =========================================================

    analise_tecnica: list[str] = field(default_factory=list)

    calculo_detalhado: list[str] = field(default_factory=list)

    csv_preview: list[dict[str, str]] = field(default_factory=list)

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