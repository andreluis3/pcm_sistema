"""
pcm_kpi.py
══════════
KPI cards do Dashboard PCM.

MODELO: absorção relativa da fonte térmica.
O PCM é avaliado por quanto desviou da energia do notebook, não por ΔT interno.

6 CARDS DO DASHBOARD:
    1. Energia Gerada       — Q_notebook = P × t  ≈ 234 kJ
    2. Energia Absorvida    — Q_pcm = η × Q_notebook  ≈ 12 kJ
    3. Eficiência Térmica   — η = Q_pcm / Q_notebook × 100  ≈ 5.13%
    4. Tempo Equivalente    — t_eq = Q_pcm / P  ≈ 4 min
    5. Potência do Notebook — P = 50 W  (constante)
    6. Duração              — 78 min  (constante)

COMPONENTE COMPARTILHADO:
    ThermalCard — usado por pcm_kpi.py E sensor_pcm_screen.py.
    Mesma identidade visual, sem duplicação de estilos.
"""
from __future__ import annotations

from typing import Optional

import customtkinter as ctk
from ui_styles import (
    Tooltip,
    PANEL_COLOR, CARD_COLOR, BORDER_COLOR,
    TEXT_PRIMARY, TEXT_SECONDARY,
    FONT_LABEL, FONT_METRIC, FONT_SMALL,
    THEME_COLORS,
)


# ─────────────────────────────────────────────────────────────────────────────
# ThermalCard — componente visual COMPARTILHADO
# Usado por PCMKPIFrame E SensorKPIFrame — sem duplicação de estilos
# ─────────────────────────────────────────────────────────────────────────────

class ThermalCard(ctk.CTkFrame):
    """
    Card de métrica térmica padronizado.

    Identidade visual única em todo o sistema PCM.
    accent_color diferencia PCM (ciano) vs Sensor (azul).
    """

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

        # Barra de acento
        ctk.CTkFrame(
            self,
            fg_color=accent_color,
            height=5,
            corner_radius=0
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

        # Sub-label
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
            self._value_lbl.configure(text=text, text_color=color)

    def set_sub(self, text: str) -> None:
        if self._sub_lbl.winfo_exists():
            self._sub_lbl.configure(text=text)

    def reset(self) -> None:
        self.set_value("--")
        self.set_sub("")


# ─────────────────────────────────────────────────────────────────────────────
# 6 KPIs do dashboard — modelo de absorção relativa da fonte
# ─────────────────────────────────────────────────────────────────────────────
_PCM_KPI_DEFS: list[tuple[str, str]] = [
    (
        "Energia Total",
        "Energia total gerada pelo notebook durante o experimento.\n"
        "Q = P × t",
    ),
    (
        "Potência",
        "Potência média utilizada pelo notebook durante o experimento.",
    ),
    (
        "Massa PCM",
        "Massa total do material de mudança de fase utilizado.",
    ),
    (
        "Pico Temperatura",
        "Maior temperatura registrada durante o experimento.",
    ),
    (
        "ΔT Térmico",
        "Variação total de temperatura:\n"
        "ΔT = Tmax - Tmin",
    ),
    (
        "Tempo Atuação",
        "Tempo equivalente de dissipação térmica do PCM.",
    ),
    (
        "Eficiência",
        "Eficiência térmica de absorção:\n"
        "η = Qpcm / Qtotal × 100",
    ),
]


class PCMKPIFrame(ctk.CTkFrame):
    """
    Grade de 6 KPI cards — 2 linhas × 3 colunas.

    Atualização via update_kpis() — método central, sem configure() espalhado.
    Usa ThermalCard para identidade visual compartilhada com o sensor.
    """

    _ACCENT = THEME_COLORS["primary"]   # ciano — identidade PCM

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._cards: dict[str, ThermalCard] = {}
        self._build()

    def _build(self) -> None:
        cols = 4
        for c in range(cols):
            self.grid_columnconfigure(c, weight=1, uniform="kpi")

        for idx, (key, tip) in enumerate(_PCM_KPI_DEFS):
            card = ThermalCard(self, title=key, tooltip=tip,
                               accent_color=self._ACCENT)
            row, col = divmod(idx, cols)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            self._cards[key] = card

    # ── API pública ───────────────────────────────────────────────────────────

    def update_kpis(
            self,
            *,
            q_notebook_j: float,
            q_pcm_j: float,
            eficiencia: float,
            tempo_eq_s: float,
            potencia_w: float,
            duracao_min: Optional[float],
        ) -> None:

        self._set(
            "Energia Total",
            _fmt_energia(q_notebook_j),
            sub="Energia total do notebook",
        )

        self._set(
            "Potência",
            f"{potencia_w:.1f} W",
            sub="Potência média utilizada",
        )

        self._set(
            "Massa PCM",
            f"{q_pcm_j:.2f} kg",
            sub="Material de mudança de fase",
        )

        self._set(
            "Pico Temperatura",
            f"{q_pcm_j:.2f} °C",
            sub="Maior temperatura registrada",
        )
        self._set(
            "ΔT Térmico",
            f"{q_pcm_j:.2f} °C",
            sub="Variação total de temperatura",
        )

        self._set(
            "Eficiência",
            f"{eficiencia:.2f} %",
            color=_cor_eficiencia(eficiencia),
            sub="Eficiência térmica do sistema",
        )

    def reset(self) -> None:
        for card in self._cards.values():
            card.reset()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set(self, key: str, text: str, *, color: str = TEXT_PRIMARY, sub: str = "") -> None:
        card = self._cards.get(key)
        if card:
            card.set_value(text, color=color)
            if sub:
                card.set_sub(sub)


# ─────────────────────────────────────────────────────────────────────────────
# Utilitários de formatação
# ─────────────────────────────────────────────────────────────────────────────

def _fmt_energia(j: float) -> str:
    """Formata energia em kJ se >= 1000, senão em J."""
    if j >= 1_000:
        return f"{j / 1000:.2f} kJ"
    return f"{j:.1f} J"


def _cor_eficiencia(eta: float) -> str:
    """Cor semântica: verde ≥ 5%, amarelo ≥ 1%, vermelho < 1%."""
    if eta >= 5.0:
        return THEME_COLORS["export"]   # verde
    if eta >= 1.0:
        return "#FCD34D"                 # amarelo
    return "#F87171"                     # vermelho


# Importa constante de tempo para uso no sub-label
from .pcm_metrics import TEMPO_EXPERIMENTO_S