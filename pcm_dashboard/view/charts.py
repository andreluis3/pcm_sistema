from collections import deque
from typing import Deque, List

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class LineChart:
    def __init__(self, parent, title: str, color: str) -> None:
        self._data: Deque[float] = deque(maxlen=60)
        self.figure = Figure(figsize=(4, 2.2), dpi=100)
        self.figure.patch.set_facecolor("#1B1E25")
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#1B1E25")
        self.ax.tick_params(colors="#7C828D", labelsize=8)
        for side in ["bottom", "top", "left", "right"]:
            self.ax.spines[side].set_color("#2A2E38")
        self.ax.grid(True, color="#20242D", linestyle="--", linewidth=0.5, alpha=0.7)
        self.ax.set_title(title, color="#E5E7EB", fontsize=10)
        self.line, = self.ax.plot([], [], color=color, linewidth=2.2)

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()

    def push(self, value: float) -> None:
        self._data.append(value)

    def draw(self) -> None:
        data: List[float] = list(self._data)
        if not data:
            return
        self.line.set_data(range(len(data)), data)
        self.ax.set_xlim(0, max(59, len(data)))
        self.ax.set_ylim(min(data) - 1, max(data) + 1)
        self.canvas.draw_idle()


class BarChart:
    def __init__(self, parent, title: str, color: str) -> None:
        self._values: Deque[float] = deque(maxlen=8)
        self.figure = Figure(figsize=(6, 2.1), dpi=100)
        self.figure.patch.set_facecolor("#1B1E25")
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#1B1E25")
        self.ax.tick_params(colors="#7C828D", labelsize=8)
        for side in ["bottom", "top", "left", "right"]:
            self.ax.spines[side].set_color("#2A2E38")
        self.ax.grid(True, axis="y", color="#20242D", linestyle="--", linewidth=0.5, alpha=0.7)
        self.ax.set_title(title, color="#E5E7EB", fontsize=10)
        self.color = color

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()

    def push(self, value: float) -> None:
        self._values.append(value)

    def draw(self) -> None:
        values = list(self._values)
        if not values:
            return
        self.ax.clear()
        self.ax.set_facecolor("#1B1E25")
        self.ax.set_title("Cycle Efficiency", color="#E5E7EB", fontsize=10)
        self.ax.tick_params(colors="#7C828D", labelsize=8)
        for side in ["bottom", "top", "left", "right"]:
            self.ax.spines[side].set_color("#2A2E38")
        self.ax.grid(True, axis="y", color="#20242D", linestyle="--", linewidth=0.5, alpha=0.7)
        self.ax.bar(range(len(values)), values, color=self.color, alpha=0.85)
        self.ax.set_ylim(0, 100)
        self.canvas.draw_idle()
