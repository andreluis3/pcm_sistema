"""Thermal calculations placeholder for future PCM computations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ThermalMetrics:
    latent_heat: float
    stored_energy: float
    efficiency: float


def compute_metrics(*, mass: float, initial_temp: float, final_temp: float) -> ThermalMetrics:
    """Placeholder API for future thermal calculations.

    The implementation will be replaced with validated scientific formulas.
    """
    return ThermalMetrics(latent_heat=0.0, stored_energy=0.0, efficiency=0.0)
