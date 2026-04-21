import random
from collections import deque
from typing import Deque

import customtkinter as ctk

from .charts import LineChart
from .widgets import CardInformacao, LabelStatus
from ui_styles import FONT_HEADER, FONT_SMALL, PAD_SMALL, PAD_NORMAL, PAD_LARGE, PAD_GAP, THEME_COLORS


class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        # UI REFATORADA: dashboard com cards e gráficos modernizados
        super().__init__(parent, fg_color=THEME_COLORS["bg"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._temperatura = 42.3
        self._tempo = 120
        self._serie: Deque[float] = deque(maxlen=80)

        self._build_layout()
        self.after(1000, self._update_loop)

    def _build_layout(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_NORMAL))
        header.grid_columnconfigure(1, weight=1)

        titulo = ctk.CTkLabel(
            header,
            text="Dashboard",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        titulo.grid(row=0, column=0, sticky="w")

        status_frame = ctk.CTkFrame(
            header,
            fg_color=THEME_COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=THEME_COLORS["border"],
        )
        status_frame.grid(row=0, column=1, sticky="e", padx=PAD_NORMAL)
        status_label = ctk.CTkLabel(
            status_frame,
            text="Status do Sensor:",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_SMALL,
        )
        status_label.grid(row=0, column=0, padx=(PAD_LARGE, 6), pady=PAD_SMALL)
        self.status = LabelStatus(status_frame, "CONECTADO", "#00C853")
        self.status.grid(row=0, column=1, padx=(0, PAD_LARGE), pady=PAD_SMALL)

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_GAP))
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)

        self.card_temp = CardInformacao(cards, "Última Temperatura", "42.3 °C", cor_valor=THEME_COLORS["primary"])
        self.card_temp.grid(row=0, column=0, sticky="ew", padx=(0, PAD_NORMAL))

        self.card_tempo = CardInformacao(cards, "Tempo do Experimento", "120 s", cor_valor=THEME_COLORS["text_primary"])
        self.card_tempo.grid(row=0, column=1, sticky="ew", padx=(PAD_NORMAL, 0))

        chart_card = ctk.CTkFrame(
            self,
            fg_color=THEME_COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=THEME_COLORS["border"],
        )
        chart_card.grid(row=2, column=0, sticky="nsew", padx=PAD_LARGE, pady=(0, PAD_LARGE))
        chart_card.grid_columnconfigure(0, weight=1)

        self.grafico = LineChart(chart_card, "Gráfico de Temperatura", cor=THEME_COLORS["accent_alt"])
        self.grafico.widget.grid(row=0, column=0, sticky="nsew", padx=PAD_NORMAL, pady=PAD_NORMAL)

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
