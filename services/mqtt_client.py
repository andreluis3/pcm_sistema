"""MQTT client placeholder for ESP32 telemetry integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class TelemetryPayload:
    temperature: float
    timestamp: str


def start_client(on_message: Callable[[TelemetryPayload], None]) -> None:
    """Start the MQTT client and route messages to the callback.

    This is a placeholder; the real implementation will connect to the broker.
    """
    _ = on_message


def stop_client() -> None:
    """Stop the MQTT client."""
    return None
