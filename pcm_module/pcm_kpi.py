"""
pcm_kpi.py
══════════
KPI cards do Dashboard PCM.
"""
from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from ui_styles import (
    Tooltip,
    PANEL_COLOR,
    BORDER_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    FONT_LABEL,
    FONT_METRIC,
    FONT_SMALL,
    THEME_COLORS,
)


# ─────────────────────────────────────────────────────────────────────────────
# CARD BASE
# ─────────────────────────────────────────────────────────────────────────────

class ThermalCard(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        *,
        title: str,
        tooltip: str = "",
        accent_color: str = THEME_COLORS["primary"],
        **kwargs,
    ) -> None:

        super().__init__(
            parent,
            fg_color=PANEL_COLOR,
            corner_radius=22,
            border_width=1,
            border_color=BORDER_COLOR,
            **kwargs,
        )

        self.configure(height=160)

        # Barra superior
        ctk.CTkFrame(
            self,
            fg_color=accent_color,
            height=5,
            corner_radius=0,
        ).pack(fill="x")

        # Título
        title_lbl = ctk.CTkLabel(
            self,
            text=title,
            font=FONT_LABEL,
            text_color=TEXT_SECONDARY,
            anchor="w",
        )

        title_lbl.pack(anchor="w", padx=16, pady=(10, 2))

        if tooltip:
            Tooltip(title_lbl, tooltip)

        # Valor principal
        self._value_lbl = ctk.CTkLabel(
            self,
            text="--",
            font=FONT_METRIC,
            text_color=TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=240,
        )

        self._value_lbl.pack(anchor="w", padx=16, pady=(0, 4))

        # Texto secundário
        self._sub_lbl = ctk.CTkLabel(
            self,
            text="",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
            anchor="w",
        )

        self._sub_lbl.pack(anchor="w", padx=16, pady=(0, 12))

    def set_value(self, text: str, *, color: str = TEXT_PRIMARY) -> None:

        if self._value_lbl.winfo_exists():
            self._value_lbl.configure(
                text=text,
                text_color=color,
            )

    def set_sub(self, text: str) -> None:

        if self._sub_lbl.winfo_exists():
            self._sub_lbl.configure(text=text)

    def reset(self) -> None:

        self.set_value("--")
        self.set_sub("")


# ─────────────────────────────────────────────────────────────────────────────
# DEFINIÇÃO DOS KPIs
# ─────────────────────────────────────────────────────────────────────────────
_PCM_KPI_DEFS: list[tuple[str, str]] = [

    (
        "Energia Notebook",
        "Energia total gerada pelo notebook.",
    ),

    (
        "Massa PCM",
        "Massa total de PCM utilizada no experimento.",
    ),

    (
        "Eficiência",
        "Eficiência térmica do PCM.",
    ),

    (
        "Erro",
        "Erro percentual entre valor teórico e valor medido.",
    ),

    (
        "Potência",
        "Potência média absorvida pelo PCM.",
    ),

    (
        "Duração",
        "Tempo total do experimento.",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# FRAME KPI
# ─────────────────────────────────────────────────────────────────────────────

class PCMKPIFrame(ctk.CTkFrame):

    _ACCENT = THEME_COLORS["primary"]

    def __init__(self, parent, **kwargs) -> None:

        super().__init__(
            parent,
            fg_color="transparent",
            **kwargs,
        )

        self._cards: dict[str, ThermalCard] = {}

        self._build()

    def _build(self) -> None:

        cols = 3

        for c in range(cols):
            self.grid_columnconfigure(
                c,
                weight=1,
                uniform="kpi",
            )

        for idx, (key, tip) in enumerate(_PCM_KPI_DEFS):

            card = ThermalCard(
                self,
                title=key,
                tooltip=tip,
                accent_color=self._ACCENT,
            )

            row, col = divmod(idx, cols)

            card.grid(
                row=row,
                column=col,
                sticky="nsew",
                padx=6,
                pady=6,
            )

            self._cards[key] = card

    # ─────────────────────────────────────────────────────────────────────

    def update_kpis(
        self,
        *,
        q_notebook_j: float,
        massa_pcm_kg: float,
        eficiencia: float,
        erro_percentual: float,
        potencia_w: float,
        duracao_min: Optional[float],
    ) -> None:

        # Energia notebook
        self._set(
            "Energia Notebook",
            _fmt_energia(q_notebook_j),
            sub="Energia gerada",
        )

        

        # Eficiência
        self._set(
            "Eficiência",
            f"{eficiencia:.2f} %",
            color=_cor_eficiencia(eficiencia),
            sub="Eficiência térmica",
        )

                # Massa PCM
        self._set(
            "Massa PCM",
            f"{massa_pcm_kg:.2f} kg",
            sub="Massa utilizada",
        )

        # Erro
        self._set(
            "Erro",
            f"{erro_percentual:.3f} %",
            color="#F59E0B",
            sub="Calculado vs medido",
        )

        # Potência
        self._set(
            "Potência",
            f"{potencia_w:.1f} W",
            sub="Potência média",
        )

        # Duração
        self._set(
            "Duração",
            (
                f"{duracao_min:.1f} min"
                if duracao_min is not None
                else "--"
            ),
            sub="Tempo total",
        )

    # ─────────────────────────────────────────────────────────────────────

    def reset(self) -> None:

        for card in self._cards.values():
            card.reset()

    # ─────────────────────────────────────────────────────────────────────

    def _set(
        self,
        key: str,
        text: str,
        *,
        color: str = TEXT_PRIMARY,
        sub: str = "",
    ) -> None:

        card = self._cards.get(key)

        if card:

            card.set_value(
                text,
                color=color,
            )

            if sub:
                card.set_sub(sub)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _fmt_energia(j: float) -> str:

    if j >= 1000:
        return f"{j / 1000:.2f} kJ"

    return f"{j:.1f} J"


def _fmt_tempo(segundos: float) -> str:

    minutos = segundos / 60.0

    if minutos >= 1:
        return f"{minutos:.1f} min"

    return f"{segundos:.0f} s"


def _cor_eficiencia(eta: float) -> str:

    if eta >= 5.0:
        return THEME_COLORS["export"]

    if eta >= 1.0:
        return "#FCD34D"

    return "#F87171"