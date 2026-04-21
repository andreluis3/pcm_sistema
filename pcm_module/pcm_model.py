from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PCMResult:
    energia_total: float
    tempo_total: float
    potencia_media: float
    massa_pcm: float
    pico_potencia: float
    pico_temperatura: float
    data_execucao: str
