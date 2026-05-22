"""
pcm_kpi.py
══════════
KPI cards do dashboard PCM.

CARDS FÍSICOS CORRETOS:
    1. Energia Gerada (notebook)    — Q_notebook = P × t
    2. Energia Absorvida (PCM)      — Q_pcm = m·c·ΔT
    3. Eficiência Térmica           — η = Q_pcm / Q_notebook × 100
    4. Tempo Equivalente            — t_eq = Q_pcm / P
    5. Duração do Experimento       — total em minutos
    6. Massa PCM                    — estimativa em gramas
    7. ΔT do PCM                    — variação de temperatura real
    8. Potência Média               — W

COMPONENTE COMPARTILHADO:
    ThermalCard — usado por pcm_kpi.py E sensor_pcm_screen.py.
    Mesma identidade visual, sem duplicação.
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
# Usado por PCMKPIFrame e SensorKPIFrame sem duplicar estilos
# ─────────────────────────────────────────────────────────────────────────────

class ThermalCard(ctk.CTkFrame):
    """
    Card de métrica térmica padronizado.

    Identidade visual única — usada em todo o sistema PCM.
    Parâmetros:
        accent_color — cor da barra de topo (diferencia PCM vs Sensor)
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
            corner_radius=16,
            border_width=1,
            border_color=BORDER_COLOR,
            **kwargs,
        )

        # Barra de acento no topo
        ctk.CTkFrame(
            self,
            fg_color=accent_color,
            height=3,
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
            wraplength=300,
        )
        self._value_lbl.pack(anchor="w", padx=16, pady=(0, 4))

        # Sub-label (unidade / contexto)
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
# Definição dos KPI cards do PCM — métricas físicas corretas
# ─────────────────────────────────────────────────────────────────────────────

_PCM_KPI_DEFS: list[tuple[str, str]] = [
    (
        "Energia Gerada",
        "Q_notebook = P × t  (J ou kJ)\nEnergia total produzida pelo notebook durante o experimento.",
    ),
    (
        "Energia Absorvida PCM",
        "Q_pcm = m · c · ΔT  (J)\nCalor sensível absorvido pelo PCM.\nEquação correta para experimento sem mudança de fase.",
    ),
    (
        "Eficiência Térmica",
        "η = Q_pcm / Q_notebook × 100  (%)\nFração da energia do notebook desviada para o PCM.",
    ),
    (
        "Tempo Equivalente",
        "t_eq = Q_pcm / P_notebook  (s)\nPor quantos segundos o PCM poderia alimentar o notebook sozinho.",
    ),
    (
        "Duração do Experimento",
        "Duração total do ensaio (min).",
    ),
    (
        "Massa PCM",
        "Estimativa de massa de PCM calculada via balanço energético (g).",
    ),
    (
        "ΔT do PCM",
        "Variação de temperatura do PCM: T_final − T_inicial  (°C).",
    ),
    (
        "Potência Média",
        "Potência média da fonte de calor durante o ensaio (W).",
    ),
]


class PCMKPIFrame(ctk.CTkFrame):
    """
    Grade de 8 KPI cards do experimento PCM — 2 linhas × 4 colunas.

    Atualização via update_kpis() — método centralizado.
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
            card = ThermalCard(
                self,
                title=key,
                tooltip=tip,
                accent_color=self._ACCENT,
            )
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
        duracao_min: Optional[float],
        massa_pcm_g: float,
        delta_t_c: float,
        potencia_media: float,
    ) -> None:
        """
        Atualiza todos os cards de uma vez com métricas físicas corretas.
        Todos os parâmetros são tipos primitivos — nunca pandas.Series.
        """
        self._set("Energia Gerada",       _fmt_energia(q_notebook_j),
                  sub=f"Q = P × t = {q_notebook_j/1000:.2f} kJ")
        self._set("Energia Absorvida PCM", _fmt_energia(q_pcm_j),
                  sub=f"Q = m·c·ΔT = {q_pcm_j:.1f} J")
        self._set("Eficiência Térmica",    f"{eficiencia:.2f} %",
                  color=_cor_eficiencia(eficiencia),
                  sub="η = Q_pcm / Q_notebook")
        self._set("Tempo Equivalente",     f"{tempo_eq_s:.0f} s",
                  sub=f"≈ {tempo_eq_s/60:.1f} min")
        self._set("Duração do Experimento",
                  f"{duracao_min:.1f} min" if duracao_min else "--")
        self._set("Massa PCM",             f"{massa_pcm_g:.2f} g")
        self._set("ΔT do PCM",             f"{delta_t_c:.2f} °C")
        self._set("Potência Média",         f"{potencia_media:.1f} W")

    def reset(self) -> None:
        for card in self._cards.values():
            card.reset()

    # ── Helpers ───────────────────────────────────────────────────────────────

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
            card.set_value(text, color=color)
            if sub:
                card.set_sub(sub)


def _fmt_energia(j: float) -> str:
    if j >= 1000:
        return f"{j/1000:.2f} kJ"
    return f"{j:.1f} J"


def _cor_eficiencia(eta: float) -> str:
    """Verde para alta eficiência, amarelo/vermelho para baixa."""
    if eta >= 5.0:
        return THEME_COLORS["export"]     # verde
    if eta >= 1.0:
        return "#FCD34D"                   # amarelo
    return "#F87171"                       # vermelho suave