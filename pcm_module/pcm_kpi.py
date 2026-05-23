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
            corner_radius=16,
            border_width=1,
            border_color=BORDER_COLOR,
            **kwargs,
        )

        # Barra de acento
        ctk.CTkFrame(self, fg_color=accent_color, height=3, corner_radius=0).pack(fill="x")

        # Título
        title_lbl = ctk.CTkLabel(
            self, text=title,
            font=FONT_LABEL, text_color=TEXT_SECONDARY, anchor="w",
        )
        title_lbl.pack(anchor="w", padx=16, pady=(10, 2))
        if tooltip:
            Tooltip(title_lbl, tooltip)

        # Valor principal
        self._value_lbl = ctk.CTkLabel(
            self, text="--",
            font=FONT_METRIC, text_color=TEXT_PRIMARY,
            anchor="w", justify="left", wraplength=300,
        )
        self._value_lbl.pack(anchor="w", padx=16, pady=(0, 4))

        # Sub-label
        self._sub_lbl = ctk.CTkLabel(
            self, text="",
            font=FONT_SMALL, text_color=TEXT_SECONDARY, anchor="w",
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
        "Energia Gerada",
        "Q_notebook = P × t\n"
        "Energia total produzida pelo notebook durante os 78 min.\n"
        "Valor fixo do experimento: 50 W × 4680 s = 234 000 J.",
    ),
    (
        "Energia Absorvida PCM",
        "Q_pcm = η × Q_notebook\n"
        "Energia térmica desviada da fonte (notebook) para o PCM.\n"
        "NÃO é calculada pelo ΔT do sensor — é derivada da eficiência de absorção.",
    ),
    (
        "Eficiência Térmica",
        "η = Q_pcm / Q_notebook × 100  (%)\n"
        "Fração da energia do notebook que foi absorvida pelo PCM.\n"
        "Calculada via capacidade térmica: η = (m·c·ΔT_atuacao) / Q_notebook.",
    ),
    (
        "Tempo Equivalente",
        "t_eq = Q_pcm / P_notebook  (s → min)\n"
        "Por quantos minutos o PCM poderia dissipar sozinho a energia do notebook.",
    ),
    (
        "Potência do Notebook",
        "P = 50 W  (constante do experimento)\n"
        "Fonte térmica principal — opera continuamente durante os 78 min.",
    ),
    (
        "Duração do Experimento",
        "t = 4680 s = 78 min  (constante do experimento)\n"
        "Período total de operação da fonte térmica e do PCM.",
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
        cols = 3
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
        """
        Atualiza os 6 cards com os valores do modelo de absorção relativa.

        Parâmetros — todos tipos primitivos, nunca pandas.Series:
            q_notebook_j  — energia gerada pelo notebook (J)
            q_pcm_j       — energia absorvida pelo PCM (J)
            eficiencia    — η (%)
            tempo_eq_s    — tempo equivalente (s)
            potencia_w    — potência da fonte (W)
            duracao_min   — duração do experimento (min)
        """
        # ── Card 1: Energia Gerada ────────────────────────────────────────────
        self._set(
            "Energia Gerada",
            _fmt_energia(q_notebook_j),
            sub=f"P × t = {potencia_w:.0f} W × {TEMPO_EXPERIMENTO_S:.0f} s",
        )

        # ── Card 2: Energia Absorvida PCM ─────────────────────────────────────
        self._set(
            "Energia Absorvida PCM",
            _fmt_energia(q_pcm_j),
            sub=f"η × Q_notebook = {q_pcm_j:.0f} J",
        )

        # ── Card 3: Eficiência Térmica ────────────────────────────────────────
        self._set(
            "Eficiência Térmica",
            f"{eficiencia:.2f} %",
            color=_cor_eficiencia(eficiencia),
            sub=f"Q_pcm / Q_notebook × 100",
        )

        # ── Card 4: Tempo Equivalente ─────────────────────────────────────────
        self._set(
            "Tempo Equivalente",
            f"{tempo_eq_s / 60:.1f} min",
            sub=f"= {tempo_eq_s:.0f} s  |  t_eq = Q_pcm / P",
        )

        # ── Card 5: Potência do Notebook ──────────────────────────────────────
        self._set(
            "Potência do Notebook",
            f"{potencia_w:.0f} W",
            sub="Fonte térmica constante",
        )

        # ── Card 6: Duração ───────────────────────────────────────────────────
        dur_txt = f"{duracao_min:.0f} min" if duracao_min else f"{TEMPO_EXPERIMENTO_S/60:.0f} min"
        self._set(
            "Duração do Experimento",
            dur_txt,
            sub=f"= {int(duracao_min * 60) if duracao_min else int(TEMPO_EXPERIMENTO_S)} s",
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