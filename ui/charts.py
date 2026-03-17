from __future__ import annotations

from typing import Iterable, Sequence

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class BaseChart:
    def __init__(self, parent, title: str) -> None:
        self._title = title
        self.figure = Figure(figsize=(4.6, 2.6), dpi=100)
        self.figure.patch.set_facecolor("#121821")
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#121821")
        self.ax.set_title(self._title, color="#E2E8F0", fontsize=11, pad=10)
        self.ax.tick_params(colors="#94A3B8", labelsize=8)
        self.ax.grid(True, color="#1F2733", linestyle="--", linewidth=0.6, alpha=0.7)
        for side in ["bottom", "top", "left", "right"]:
            self.ax.spines[side].set_color("#121821")

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()

    def _coerce_series(self, data: Sequence[float] | Iterable[float]) -> list[float]:
        return list(data)

    def draw(self) -> None:
        self.canvas.draw_idle()


class LineChart(BaseChart):
    def __init__(self, parent, title: str, color: str) -> None:
        super().__init__(parent, title)
        self._line_color = color
        self._line, = self.ax.plot([], [], color=color, linewidth=2.4)
        self.ax.set_xlabel("Time", color="#94A3B8", fontsize=8)
        self.ax.set_ylabel("Value", color="#94A3B8", fontsize=8)

    def update(self, data: Sequence[float] | Iterable[float]) -> None:
        series = self._coerce_series(data)
        if not series:
            return
        self._line.set_data(range(len(series)), series)
        self.ax.set_xlim(0, max(1, len(series) - 1))
        self.ax.set_ylim(min(series) - 1, max(series) + 1)
        self.draw()


class AreaChart(BaseChart):
    def __init__(self, parent, title: str, color: str) -> None:
        super().__init__(parent, title)
        self._area_color = color
        self._line, = self.ax.plot([], [], color=color, linewidth=2.0)
        self._fill = None
        self.ax.set_xlabel("Time", color="#94A3B8", fontsize=8)
        self.ax.set_ylabel("Energy", color="#94A3B8", fontsize=8)

    def update(self, data: Sequence[float] | Iterable[float]) -> None:
        series = self._coerce_series(data)
        if not series:
            return
        x = list(range(len(series)))
        self._line.set_data(x, series)
        if self._fill is not None:
            self._fill.remove()
        self._fill = self.ax.fill_between(x, series, color=self._area_color, alpha=0.22)
        self.ax.set_xlim(0, max(1, len(series) - 1))
        self.ax.set_ylim(0, max(series) + (max(series) * 0.15))
        self.draw()


class BarChart(BaseChart):
    def __init__(self, parent, title: str, color: str) -> None:
        super().__init__(parent, title)
        self._bar_color = color
        self._bars = None
        self.ax.set_xlabel("Experiments", color="#94A3B8", fontsize=8)
        self.ax.set_ylabel("Efficiency (%)", color="#94A3B8", fontsize=8)

    def update(self, data: Sequence[float] | Iterable[float]) -> None:
        series = self._coerce_series(data)
        if not series:
            return
        x = list(range(1, len(series) + 1))
        self.ax.clear()
        self.ax.set_facecolor("#121821")
        self.ax.set_title(self._title, color="#E2E8F0", fontsize=11, pad=10)
        self.ax.tick_params(colors="#94A3B8", labelsize=8)
        self.ax.grid(True, color="#1F2733", linestyle="--", linewidth=0.6, alpha=0.7)
        for side in ["bottom", "top", "left", "right"]:
            self.ax.spines[side].set_color("#121821")
        self.ax.set_xlabel("Experiments", color="#94A3B8", fontsize=8)
        self.ax.set_ylabel("Efficiency (%)", color="#94A3B8", fontsize=8)
        self._bars = self.ax.bar(x, series, color=self._bar_color, alpha=0.85)
        self.ax.set_ylim(0, max(series) + 10)
        self.draw()
