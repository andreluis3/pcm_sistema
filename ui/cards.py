import tkinter as tk
import customtkinter as ctk

from ui_styles import (
    FONT_NORMAL,
    FONT_LABEL,
    FONT_TITLE,
    FONT_TEMP,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
    THEME_COLORS,
    card_style,
)


class StatusIndicator(ctk.CTkFrame):
    """
    Indicador visual de status:
    - Verde = conectado
    - Vermelho = desconectado
    """

    def __init__(self, parent, label: str, *, size: int = 12) -> None:
        super().__init__(parent, fg_color="transparent")

        self._size = size
        self._color_connected = THEME_COLORS["export"]
        self._color_disconnected = THEME_COLORS["danger"]

        self.grid_columnconfigure(1, weight=1)

        self._canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            highlightthickness=0,
            bd=0,
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

        self._canvas.grid(row=0, column=0, padx=(0, 8))

        self._label = ctk.CTkLabel(
            self,
            text=label,
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
        )
        self._label.grid(row=0, column=1, sticky="w")

    def set_status(self, connected: bool) -> None:
        color = (
            self._color_connected
            if connected
            else self._color_disconnected
        )

        self._canvas.itemconfigure(self._circle, fill=color)

    @staticmethod
    def _resolve_bg(value) -> str:
        if isinstance(value, (tuple, list)) and value:
            return value[0]
        return value or "#000000"


class MetricCard(ctk.CTkFrame):
    """
    Card padrão de métricas:
    - Visual moderno
    - Responsivo
    - Hover effect
    - Melhor espaçamento
    """

    def __init__(self, parent, title: str, unit: str) -> None:
        super().__init__(
            parent,
            **card_style(),
        )

        self._default_fg = THEME_COLORS["card"]
        self._hover_fg = "#243145"

        self.configure(
            corner_radius=18,
            border_width=1,
            border_color=THEME_COLORS["border"],
            fg_color=self._default_fg,
        )

        self.grid_columnconfigure(0, weight=1)

        # Hover effect
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # ---------------------------
        # TÍTULO
        # ---------------------------
        self._title = ctk.CTkLabel(
            self,
            text=title.upper(),
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
            anchor="w",
        )

        self._title.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PAD_LARGE,
            pady=(18, 4),
        )

        # ---------------------------
        # VALOR
        # ---------------------------
        self._value = ctk.CTkLabel(
            self,
            text="--",
            text_color=THEME_COLORS["primary"],
            font=FONT_TEMP,
            anchor="w",
        )

        self._value.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PAD_LARGE,
            pady=(2, 0),
        )

        # ---------------------------
        # UNIDADE
        # ---------------------------
        self._unit = ctk.CTkLabel(
            self,
            text=unit,
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_NORMAL,
            anchor="w",
        )

        self._unit.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=PAD_LARGE,
            pady=(4, 18),
        )

        # Hover nos widgets internos
        for widget in [self, self._title, self._value, self._unit]:
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def update_value(self, value: str) -> None:
        self._value.configure(text=value)

    # ---------------------------
    # HOVER EFFECT
    # ---------------------------
    def _on_enter(self, _event=None) -> None:
        self.configure(
            fg_color=self._hover_fg,
            border_color=THEME_COLORS["primary"],
        )

    def _on_leave(self, _event=None) -> None:
        self.configure(
            fg_color=self._default_fg,
            border_color=THEME_COLORS["border"],
        )


class PCMStateCard(ctk.CTkFrame):
    """
    Card principal do estado do PCM.
    Mostra:
    - Temperatura atual
    - Estado físico
    """

    def __init__(self, parent) -> None:
        super().__init__(
            parent,
            **card_style(),
        )

        self._default_fg = THEME_COLORS["card"]

        self.configure(
            corner_radius=20,
            border_width=1,
            border_color=THEME_COLORS["border"],
            fg_color=self._default_fg,
        )

        self.grid_columnconfigure(0, weight=1)

        # Hover
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # ---------------------------
        # TÍTULO
        # ---------------------------
        self._title = ctk.CTkLabel(
            self,
            text="PCM STATE",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_TITLE,
            anchor="w",
        )

        self._title.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PAD_LARGE,
            pady=(22, 0),
        )

        # ---------------------------
        # TEMPERATURA
        # ---------------------------
        self._temperature = ctk.CTkLabel(
            self,
            text="-- °C",
            text_color=THEME_COLORS["primary"],
            font=("Consolas", 38, "bold"),
            anchor="w",
        )

        self._temperature.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PAD_LARGE,
            pady=(10, 0),
        )

        # ---------------------------
        # ESTADO
        # ---------------------------
        self._state = ctk.CTkLabel(
            self,
            text="--",
            text_color=THEME_COLORS["accent_alt"],
            font=("Consolas", 20, "bold"),
            anchor="w",
        )

        self._state.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=PAD_LARGE,
            pady=(10, 22),
        )

        # Widgets internos recebem hover também
        for widget in [
            self,
            self._title,
            self._temperature,
            self._state,
        ]:
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def update_state(
        self,
        temperature: float,
        state_label: str,
        color: str,
    ) -> None:

        self._temperature.configure(
            text=f"{temperature:.1f} °C"
        )

        self._state.configure(
            text=state_label,
            text_color=color,
        )

    # ---------------------------
    # HOVER
    # ---------------------------
    def _on_enter(self, _event=None) -> None:
        self.configure(
            border_color=THEME_COLORS["primary"],
        )

    def _on_leave(self, _event=None) -> None:
        self.configure(
            border_color=THEME_COLORS["border"],
        )