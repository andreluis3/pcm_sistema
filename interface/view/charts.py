from collections import deque
import time
from typing import Deque, List

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ui_styles import THEME_COLORS

class LineChart:
    def __init__(self, parent, titulo: str, cor: str) -> None:
        self._data: Deque[float] = deque(maxlen=80)
        self.figure = Figure(figsize=(5.6, 2.8), dpi=100)
        self._last_draw_time = 0
        # UI REFATORADA: gráfico integrado no dark mode
        self.figure.patch.set_facecolor(THEME_COLORS["card"])
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(THEME_COLORS["card"])
        self.ax.tick_params(colors=THEME_COLORS["text_secondary"], labelsize=9)
        self.ax.grid(True, color=THEME_COLORS["border"], linestyle="--", linewidth=0.6, alpha=0.65)
        self.ax.set_title(titulo, color=THEME_COLORS["white"], fontsize=11, pad=10)
        self.ax.set_xlabel("Amostras", color=THEME_COLORS["white"], fontsize=9)
        self.ax.set_ylabel("Valor", color=THEME_COLORS["white"], fontsize=9)
        for side in ["bottom", "left"]:
            self.ax.spines[side].set_color(THEME_COLORS["border"])
        for side in ["top", "right"]:
            self.ax.spines[side].set_visible(False)
        self.line, = self.ax.plot([], [], color=cor, linewidth=2.8)

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()

    def push(self, valor: float) -> None:
        self._data.append(valor)



    def draw(self) -> None:

        data = list(self._data)

        if not data:
            return

        now = time.time()

        # limita redraw
        if now - self._last_draw_time < 0.25:
            return

        self._last_draw_time = now

        try:

            self.line.set_data(
                range(len(data)),
                data
            )

            self.ax.set_xlim(
                0,
                max(79, len(data))
            )

            self.ax.set_ylim(
                min(data) - 1,
                max(data) + 1
            )

            self.canvas.draw_idle()

        except Exception as e:
            print(f"[CHART DRAW ERROR] {e}")
