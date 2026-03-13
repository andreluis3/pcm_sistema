from collections import deque
from typing import Deque, List

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class LineChart:
    def __init__(self, parent, titulo: str, cor: str) -> None:
        self._data: Deque[float] = deque(maxlen=80)
        self.figure = Figure(figsize=(5.6, 2.8), dpi=100)
        self.figure.patch.set_facecolor("#161B22")
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#161B22")
        self.ax.tick_params(colors="#8B93A5", labelsize=9)
        for side in ["bottom", "top", "left", "right"]:
            self.ax.spines[side].set_color("#161B22")
        self.ax.grid(True, color="#1F252E", linestyle="--", linewidth=0.6, alpha=0.7)
        self.ax.set_title(titulo, color="#E5E7EB", fontsize=11, pad=10)
        self.ax.set_xlabel("Amostras", color="#8B93A5", fontsize=9)
        self.ax.set_ylabel("Valor", color="#8B93A5", fontsize=9)
        self.line, = self.ax.plot([], [], color=cor, linewidth=2.8)

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()

    def push(self, valor: float) -> None:
        self._data.append(valor)

    def draw(self) -> None:
        data: List[float] = list(self._data)
        if not data:
            return
        self.line.set_data(range(len(data)), data)
        self.ax.set_xlim(0, max(79, len(data)))
        self.ax.set_ylim(min(data) - 1, max(data) + 1)
        self.canvas.draw_idle()
