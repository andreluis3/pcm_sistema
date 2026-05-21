# Centralized UI style constants for PCM Thermal Manager
# UI REFATORADA: tipografia, cores e utilitários padronizados

from __future__ import annotations

import customtkinter as ctk

FONT_FAMILY = "Inter"

def _font(size: int, weight: str = "normal") -> tuple[str, int, str]:
    return (FONT_FAMILY, size, weight)

# Typography (requested)
FONT_HEADER = _font(30, "bold")          # Títulos
FONT_METRIC = _font(24, "bold")          # Métricas (valores)
FONT_LABEL = _font(13, "normal")         # Labels secundários (approx. medium)

# Supporting sizes
FONT_TITLE = _font(18, "bold")
FONT_NORMAL = _font(15, "normal")
FONT_CARD_VALUE = _font(16, "bold")
FONT_SMALL = _font(13, "normal")
FONT_TEMP = FONT_METRIC

WIDGET_HEIGHT_SMALL = 32
WIDGET_HEIGHT_NORMAL = 38
WIDGET_HEIGHT_LARGE = 44

PAD_SMALL = 8
PAD_NORMAL = 14
PAD_LARGE = 24
PAD_GAP = 18
PAD_CARD = 10          # padding interno dos cards
# padding externo entre cards

# ui_styles.py para o pcm
SENSOR_ACCENT  = "#38BDF8"
SENSOR_FUSION  = "#A78BFA"
SENSOR_ENERGY  = "#22C55E"
COLOR_WITH_PCM    = "#38BDF8"
COLOR_WITHOUT_PCM = "#F87171"
# =========================================================
# SENSOR / PCM COLORS
# =========================================================

BG_SENSOR = "#0B0F16"

SENSOR_ACCENT = "#38BDF8"
SENSOR_FUSION = "#A78BFA"
SENSOR_ENERGY = "#22C55E"

COLOR_WITH_PCM = "#38BDF8"
COLOR_WITHOUT_PCM = "#F87171"
CARD_BORDER_SENSOR = "#334155"
# Legacy aliases (keep for backward compatibility)
FONT_SUBTITLE = FONT_TITLE
FONT_SIDEBAR = FONT_NORMAL
FONT_MONO_LARGE = FONT_TEMP

ENTRY_HEIGHT = WIDGET_HEIGHT_NORMAL
BUTTON_HEIGHT = WIDGET_HEIGHT_LARGE
SIDEBAR_BUTTON_HEIGHT = WIDGET_HEIGHT_LARGE

SECTION_PAD_X = PAD_LARGE
SECTION_PAD_Y = PAD_NORMAL

# Theme colors (use across UI for consistent palette)
THEME_COLORS = {
    "bg": "#0B1120",
    "card": "#1E293B",
    "card_soft": "#243149",
    "border": "#334155",
    "shadow": "#0A0F14",
    "neutral": "#334155",
    "primary": "#06B6D4",
    "export": "#10B981",
    "danger": "#EF4444",
    "accent": "#06B6D4",
    "accent_alt": "#38BDF8",
    "line_avg": "#7DD3FC",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "text_muted": "#94A3B8",
    "white": "#F8FAFC",
    
}


BG_COLOR      = "#0B0F16"
PANEL_COLOR   = "#111827"
CARD_COLOR    = "#0F172A"
BORDER_COLOR  = "#334155"
TEXT_PRIMARY  = "#F3F4F6"
TEXT_SECONDARY = "#9CA3AF"
SUCCESS_COLOR = "#E5E7EB"
 
# Paleta científica do sensor (azul)
SENSOR_ACCENT   = "#60A5FA"   # azul principal
SENSOR_REAL     = "#94A3B8"   # cinza azulado — temperatura real
SENSOR_FUSION   = "#F59E0B"   # âmbar — região de fusão
SENSOR_ENERGY   = "#34D399"   # verde esmeralda — energia acumulada
 
# Paleta comparativa
COLOR_WITH_PCM    = "#60A5FA"   # azul
COLOR_WITHOUT_PCM = "#F87171"   # vermelho suave

def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def lighten(color: str, amount: float = 0.10) -> str:
    r, g, b = _hex_to_rgb(color)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return _rgb_to_hex(r, g, b)


def card_style() -> dict:
    return {
        "fg_color": THEME_COLORS["card"],
        "corner_radius": 12,
        "border_width": 1,
        "border_color": THEME_COLORS["border"],
    }


def make_card(parent, *, padded: bool = True, **kwargs):
    """Create a styled card. Returns (card, body) when padded=True."""
    card = ctk.CTkFrame(parent, **card_style(), **kwargs)
    if not padded:
        return card
    card.grid_columnconfigure(0, weight=1)
    card.grid_rowconfigure(0, weight=1)
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=0, column=0, sticky="nsew", padx=PAD_CARD, pady=PAD_CARD)
    body.grid_columnconfigure(0, weight=1)
    return card, body


def label_style(variant: str = "secondary") -> dict:
    if variant == "title":
        return {"text_color": THEME_COLORS["text_primary"], "font": FONT_HEADER}
    if variant == "metric":
        return {"text_color": THEME_COLORS["primary"], "font": FONT_METRIC}
    if variant == "primary":
        return {"text_color": THEME_COLORS["text_primary"], "font": FONT_NORMAL}
    return {"text_color": THEME_COLORS["text_secondary"], "font": FONT_LABEL}


def make_label(parent, text: str, *, variant: str = "secondary", **kwargs):
    return ctk.CTkLabel(parent, text=text, **label_style(variant), **kwargs)


def button_style(variant: str = "primary") -> dict:
    color_map = {
        "primary": THEME_COLORS["primary"],
        "export": THEME_COLORS["export"],
        "danger": THEME_COLORS["danger"],
        "neutral": THEME_COLORS["neutral"],
    }
    fg = color_map.get(variant, THEME_COLORS["primary"])

    return {
        "fg_color": fg,
        "hover_color": lighten(fg, 0.10),
        "text_color": THEME_COLORS["text_primary"],
        "corner_radius": 10
    }

def make_button(parent, text: str, *, variant: str = "primary", **kwargs):
    return ctk.CTkButton(parent, text=text, **button_style(variant), **kwargs)


import customtkinter as ctk

def style_ax_dark(
    ax,
    *,
    card_color="#0F172A",
    border_color="#334155",
    text_color="#9CA3AF",
):
    """
    Estilo científico escuro padronizado para matplotlib.
    """

    ax.set_facecolor(card_color)

    ax.tick_params(
        colors=text_color,
        labelsize=11,
        length=4,
        width=1.2,
    )

    ax.tick_params(axis="x", pad=6)
    ax.tick_params(axis="y", pad=4)

    ax.grid(
        True,
        linestyle="--",
        linewidth=0.55,
        alpha=0.30,
        color="#475569",
    )

    ax.minorticks_on()

    ax.grid(
        True,
        which="minor",
        linestyle=":",
        linewidth=0.3,
        alpha=0.15,
        color="#334155",
    )

    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)

    for side in ["bottom", "left"]:
        ax.spines[side].set_color(border_color)
        ax.spines[side].set_linewidth(1.4)


class Tooltip:
    def __init__(self, widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self._win = None

        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _show(self, _event=None) -> None:

        if self._win is not None:
            return

        try:
            x = self.widget.winfo_rootx() + 14
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10

        except Exception:
            return

        win = ctk.CTkToplevel(self.widget)

        win.overrideredirect(True)

        try:
            win.attributes("-topmost", True)
        except Exception:
            pass

        win.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(
            win,
            fg_color="#0B0F16",
            corner_radius=10,
            border_width=1,
            border_color="#334155",
        )

        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            frame,
            text=self.text,
            font=("Arial", 12),
            text_color="#F3F4F6",
            justify="left",
            wraplength=360,
        ).pack(padx=12, pady=10)

        self._win = win

    def _hide(self, _event=None) -> None:

        if self._win is None:
            return

        self._win.destroy()
        self._win = None