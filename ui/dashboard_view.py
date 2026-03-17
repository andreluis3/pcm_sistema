from __future__ import annotations

import math
import random
import threading
from queue import Queue
from typing import Callable, Iterable, Sequence

import customtkinter as ctk

from ui.cards import MetricCard, PCMStateCard, StatusIndicator
from ui.charts import AreaChart, BarChart, LineChart


PHASE_SOLID = "SOLID"
PHASE_TRANSITION = "TRANSITION"
PHASE_LIQUID = "LIQUID"


def generate_demo_data() -> dict[str, object]:
    """Temporary demo data generator to validate layout and charts."""
    temperature_series = [
        24 + math.sin(i / 6) * 6 + random.uniform(-0.8, 0.8) for i in range(60)
    ]
    energy_series = [
        max(0.0, 120 + i * 3 + math.sin(i / 5) * 8 + random.uniform(-4, 4))
        for i in range(60)
    ]
    cycle_efficiency = [
        72 + random.uniform(-6, 6) for _ in range(5)
    ]
    return {
        "temperature_series": temperature_series,
        "energy_series": energy_series,
        "cycle_efficiency": cycle_efficiency,
        "latest_temperature": temperature_series[-1],
        "metrics": {
            "latent_heat": 158.4,
            "stored_energy": 1835,
            "cycle_count": 12,
            "efficiency": 84.6,
        },
    }


class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0B0F14")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._ui_queue: Queue[tuple[Callable, tuple, dict]] = Queue()

        self._build_layout()
        self._start_ui_queue()
        self._load_demo_data()

    # --- Public update API -------------------------------------------------
    def update_esp32_status(self, status: bool) -> None:
        self._run_on_ui(self._esp32_indicator.set_status, status)

    def update_database_status(self, status: bool) -> None:
        self._run_on_ui(self._db_indicator.set_status, status)

    def update_pcm_state(self, temperature: float) -> None:
        def _apply():
            state_label, color = self._resolve_phase(temperature)
            self._pcm_card.update_state(temperature, state_label, color)

        self._run_on_ui(_apply)

    def update_latent_heat(self, value: float) -> None:
        self._run_on_ui(self._latent_heat_card.update_value, f"{value:.1f}")

    def update_stored_energy(self, value: float) -> None:
        self._run_on_ui(self._stored_energy_card.update_value, f"{value:.0f}")

    def update_cycle_count(self, value: float) -> None:
        self._run_on_ui(self._cycle_count_card.update_value, f"{value:.0f}")

    def update_efficiency(self, value: float) -> None:
        self._run_on_ui(self._efficiency_card.update_value, f"{value:.1f}")

    def update_temperature_chart(self, data: Sequence[float] | Iterable[float]) -> None:
        self._run_on_ui(self._temperature_chart.update, data)

    def update_energy_chart(self, data: Sequence[float] | Iterable[float]) -> None:
        self._run_on_ui(self._energy_chart.update, data)

    def update_cycle_chart(self, data: Sequence[float] | Iterable[float]) -> None:
        self._run_on_ui(self._cycle_chart.update, data)

    # --- Layout ------------------------------------------------------------
    def _build_layout(self) -> None:
        header = ctk.CTkFrame(self, fg_color="#0B0F14")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 6))
        header.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            header,
            text="PCM GERENCIADOR TÉRMICO",
            text_color="#E2E8F0",
            font=ctk.CTkFont(family="IBM Plex Sans", size=20, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        indicator_frame = ctk.CTkFrame(header, fg_color="#121821", corner_radius=16)
        indicator_frame.grid(row=0, column=1, sticky="e", padx=6)
        indicator_frame.grid_columnconfigure(2, weight=1)

        self._esp32_indicator = StatusIndicator(indicator_frame, "ESP32")
        self._esp32_indicator.grid(row=0, column=0, padx=(14, 12), pady=10)

        self._db_indicator = StatusIndicator(indicator_frame, "DATABASE")
        self._db_indicator.grid(row=0, column=1, padx=(0, 14), pady=10)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", padx=20, pady=(6, 10))
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=1)

        self._pcm_card = PCMStateCard(content)
        self._pcm_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        metric_stack = ctk.CTkFrame(content, fg_color="transparent")
        metric_stack.grid(row=0, column=1, sticky="nsew")
        for row in range(4):
            metric_stack.grid_rowconfigure(row, weight=1)

        self._latent_heat_card = MetricCard(metric_stack, "Calor latente", "kJ/kg")
        self._latent_heat_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        self._stored_energy_card = MetricCard(metric_stack, "Energia armazenada", "J")
        self._stored_energy_card.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        self._cycle_count_card = MetricCard(metric_stack, "Contagem de ciclos", "cycles")
        self._cycle_count_card.grid(row=2, column=0, sticky="nsew", pady=(0, 10))

        self._efficiency_card = MetricCard(metric_stack, "Eficiência energética", "%")
        self._efficiency_card.grid(row=3, column=0, sticky="nsew")

        charts = ctk.CTkFrame(self, fg_color="transparent")
        charts.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        charts.grid_columnconfigure(0, weight=1)
        charts.grid_columnconfigure(1, weight=1)
        charts.grid_rowconfigure(0, weight=1)
        charts.grid_rowconfigure(1, weight=1)

        temp_card = ctk.CTkFrame(charts, fg_color="#121821", corner_radius=16)
        temp_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        temp_card.grid_columnconfigure(0, weight=1)
        temp_card.grid_rowconfigure(0, weight=1)

        energy_card = ctk.CTkFrame(charts, fg_color="#121821", corner_radius=16)
        energy_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))
        energy_card.grid_columnconfigure(0, weight=1)
        energy_card.grid_rowconfigure(0, weight=1)

        cycle_card = ctk.CTkFrame(charts, fg_color="#121821", corner_radius=16)
        cycle_card.grid(row=1, column=0, columnspan=2, sticky="nsew")
        cycle_card.grid_columnconfigure(0, weight=1)
        cycle_card.grid_rowconfigure(0, weight=1)

        self._temperature_chart = LineChart(temp_card, "Temperature vs Time", "#38BDF8")
        self._temperature_chart.widget.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self._energy_chart = AreaChart(energy_card, "Energy vs Time", "#FBBF24")
        self._energy_chart.widget.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self._cycle_chart = BarChart(cycle_card, "Cycle Efficiency (Last 5)", "#34D399")
        self._cycle_chart.widget.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

    # --- Thread safety -----------------------------------------------------
    def _run_on_ui(self, func, *args, **kwargs) -> None:
        if threading.current_thread() is threading.main_thread():
            func(*args, **kwargs)
        else:
            self._ui_queue.put((func, args, kwargs))

    def _start_ui_queue(self) -> None:
        self.after(50, self._process_ui_queue)

    def _process_ui_queue(self) -> None:
        if not self.winfo_exists():
            return
        while not self._ui_queue.empty():
            func, args, kwargs = self._ui_queue.get_nowait()
            func(*args, **kwargs)
        self.after(50, self._process_ui_queue)

    # --- Helpers -----------------------------------------------------------
    def _resolve_phase(self, temperature: float) -> tuple[str, str]:
        if temperature < 30:
            return PHASE_SOLID, "#0B3C5D"
        if temperature <= 55:
            return PHASE_TRANSITION, "#B45309"
        return PHASE_LIQUID, "#991B1B"

    def _load_demo_data(self) -> None:
        demo = generate_demo_data()
        metrics = demo["metrics"]

        self.update_esp32_status(True)
        self.update_database_status(True)
        self.update_pcm_state(demo["latest_temperature"])
        self.update_latent_heat(metrics["latent_heat"])
        self.update_stored_energy(metrics["stored_energy"])
        self.update_cycle_count(metrics["cycle_count"])
        self.update_efficiency(metrics["efficiency"])
        self.update_temperature_chart(demo["temperature_series"])
        self.update_energy_chart(demo["energy_series"])
        self.update_cycle_chart(demo["cycle_efficiency"])
