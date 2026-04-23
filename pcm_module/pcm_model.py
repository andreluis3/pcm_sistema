from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PCMResult:
    energia_total: float
    tempo_total: float
    potencia_media: float
    massa_pcm: float
    pico_potencia: float
    pico_temperatura: float
    data_execucao: str
    delta_tempo: float = 0.0
    tempo_pico_potencia: float = 0.0
    tempo_pico_temperatura: float = 0.0
    temperatura_media: float = 0.0
    status_termico: str = "indefinido"
    analise_tecnica: list[str] = field(default_factory=list)
    timestamps: list[str] = field(default_factory=list)
    tempo_s: list[float] = field(default_factory=list)
    potencia_w: list[float] = field(default_factory=list)
    temperatura_c: list[float] = field(default_factory=list)
    energia_j: list[float] = field(default_factory=list)
    potencia_media_movel: list[float] = field(default_factory=list)
    temperatura_media_movel: list[float] = field(default_factory=list)
    energia_media_movel: list[float] = field(default_factory=list)
    csv_preview: list[dict[str, str]] = field(default_factory=list)
