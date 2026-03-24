import tkinter as tk
import customtkinter as ctk

from ui_styles import FONT_NORMAL, FONT_SMALL, FONT_TITLE, FONT_TEMP, PAD_SMALL, PAD_NORMAL, PAD_LARGE


class StatusIndicator(ctk.CTkFrame):
    def __init__(self, parent, label: str, *, size: int = 12) -> None:
        super().__init__(parent, fg_color="transparent")
        self._size = size
        self._color_connected = "#2DD4BF"
        self._color_disconnected = "#F87171"

        self.grid_columnconfigure(1, weight=1)

        self._canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            highlightthickness=0,
            bg=self._resolve_bg(parent.cget("fg_color")),
        )
        self._circle = self._canvas.create_oval(
            2,
            2,
            size - 2,
            size - 2,
            fill=self._color_disconnected,
            outline="",
        )
        self._canvas.grid(row=0, column=0, padx=(0, 6))

        self._label = ctk.CTkLabel(
            self,
            text=label,
            text_color="#CBD5F5",
            font=FONT_NORMAL,
        )
        self._label.grid(row=0, column=1, sticky="w")

    def set_status(self, connected: bool) -> None:
        color = self._color_connected if connected else self._color_disconnected
        self._canvas.itemconfigure(self._circle, fill=color)

    @staticmethod
    def _resolve_bg(value) -> str:
        if isinstance(value, (tuple, list)) and value:
            return value[0]
        return value or "#000000"


class MetricCard(ctk.CTkFrame):
    def __init__(self, parent, title: str, unit: str) -> None:
        super().__init__(parent, fg_color="#121821", corner_radius=16)
        self.grid_columnconfigure(0, weight=1)

        self._title = ctk.CTkLabel(
            self,
            text=title,
            text_color="#92A0B6",
            font=FONT_NORMAL,
        )
        self._title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, 0))

        self._value = ctk.CTkLabel(
            self,
            text="--",
            text_color="#E2E8F0",
            font=FONT_TITLE,
        )
        self._value.grid(row=1, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_SMALL, 0))

        self._unit = ctk.CTkLabel(
            self,
            text=unit,
            text_color="#64748B",
            font=FONT_SMALL,
        )
        self._unit.grid(row=2, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

    def update_value(self, value: str) -> None:
        self._value.configure(text=value)


class PCMStateCard(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#111827", corner_radius=20)
        self.grid_columnconfigure(0, weight=1)

        self._title = ctk.CTkLabel(
            self,
            text="PCM STATE",
            text_color="#8CA0B3",
            font=FONT_TITLE,
        )
        self._title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_LARGE, 0))

        self._temperature = ctk.CTkLabel(
            self,
            text="-- °C",
            text_color="#E2E8F0",
            font=FONT_TEMP,
        )
        self._temperature.grid(row=1, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_SMALL, 0))

        self._state = ctk.CTkLabel(
            self,
            text="--",
            text_color="#38BDF8",
            font=FONT_TITLE,
        )
        self._state.grid(row=2, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_SMALL, PAD_LARGE))

    def update_state(self, temperature: float, state_label: str, color: str) -> None:
        self.configure(fg_color=color)
        self._temperature.configure(text=f"{temperature:.1f} °C")
        self._state.configure(text=state_label)
