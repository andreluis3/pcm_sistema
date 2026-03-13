import random
from collections import deque
from typing import Deque

import customtkinter as ctk

from .charts import LineChart
from .widgets import CardInformacao, LabelStatus


class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._temperatura = 42.3
        self._tempo = 120
        self._serie: Deque[float] = deque(maxlen=80)

        self._build_layout()
        self.after(1000, self._update_loop)

    def _build_layout(self) -> None:
        header = ctk.CTkFrame(self, fg_color="#0D1117")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(6, 10))
        header.grid_columnconfigure(1, weight=1)

        titulo = ctk.CTkLabel(
            header,
            text="Dashboard",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        titulo.grid(row=0, column=0, sticky="w")

        status_frame = ctk.CTkFrame(header, fg_color="#161B22", corner_radius=16)
        status_frame.grid(row=0, column=1, sticky="e")
        status_label = ctk.CTkLabel(
            status_frame,
            text="Status do Sensor:",
            text_color="#9AA0AB",
            font=ctk.CTkFont(size=12),
        )
        status_label.grid(row=0, column=0, padx=(16, 6), pady=10)
        self.status = LabelStatus(status_frame, "CONECTADO", "#00C853")
        self.status.grid(row=0, column=1, padx=(0, 16), pady=10)

        cards = ctk.CTkFrame(self, fg_color="#0D1117")
        cards.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)

        self.card_temp = CardInformacao(cards, "Última Temperatura", "42.3 °C", cor_valor="#00F5D4")
        self.card_temp.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.card_tempo = CardInformacao(cards, "Tempo do Experimento", "120 s", cor_valor="#E5E7EB")
        self.card_tempo.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        chart_card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        chart_card.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 12))
        chart_card.grid_columnconfigure(0, weight=1)

        self.grafico = LineChart(chart_card, "Gráfico de Temperatura", cor="#00F5D4")
        self.grafico.widget.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)

    def _update_loop(self) -> None:
        self._temperatura += random.uniform(-0.6, 0.8)
        self._temperatura = max(20.0, min(60.0, self._temperatura))
        self._tempo += 1

        self.card_temp.atualizar(f"{self._temperatura:.1f} °C")
        self.card_tempo.atualizar(f"{self._tempo} s")

        self._serie.append(self._temperatura)
        self.grafico.push(self._temperatura)
        self.grafico.draw()

        self.after(1000, self._update_loop)
