"""
pcm_kpi.py
══════════
Componente de KPI cards do dashboard PCM.

Responsabilidade única: renderizar e atualizar cards de métricas.
Sem lógica de cálculo, sem matplotlib, sem I/O.
"""
from __future__ import annotations

from typing import Optional

import customtkinter as ctk


# ─────────────────────────────────────────────────────────────────────────────
# Tooltip helper
# ─────────────────────────────────────────────────────────────────────────────

class _Tooltip:
    """Tooltip flutuante para widgets customtkinter."""

    def __init__(self, widget: ctk.CTkBaseClass, text: str) -> None:
        self.widget = widget
        self.text = text
        self._win: Optional[ctk.CTkToplevel] = None
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
            win, fg_color="#0B0F16", corner_radius=10,
            border_width=1, border_color="#334155",
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
        try:
            self._win.destroy()
        except Exception:
            pass
        self._win = None


# ─────────────────────────────────────────────────────────────────────────────
# KPI Frame
# ─────────────────────────────────────────────────────────────────────────────

# Definição dos cards — (chave, tooltip)
KPI_DEFS: list[tuple[str, str]] = [
    (
        "Energia Total",
        "Energia total integrada ao longo do ensaio (J).",
    ),
    (
        "Potência Média",
        "Potência média aplicada/observada durante o ensaio (W).",
    ),
    (
        "Massa PCM",
        "Massa estimada de PCM necessária para absorver a energia do ensaio (g).",
    ),
    (
        "Erro Percentual",
        "Erro percentual: energia_perdida / energia_total × 100 (%).",
    ),
    (
        "Tempo de Atuação do PCM",
        "Tempo total em que 50 °C ≤ T ≤ 60 °C (min).",
    ),
    (
        "Delta T",
        "Variação térmica total: max(T) − min(T) (°C).",
    ),
    (
        "Eficiência Térmica",
        "Eficiência: energia_real / energia_ideal × 100 (%), entre 60–99 %.",
    ),
    (
        "Energia Ideal",
        "Energia ideal que o sistema deveria absorver para desempenho perfeito (J).",
    ),
    (
        "Duração do Experimento",
        "Duração total do ensaio (min).",
    ),
]


class PCMKPIFrame(ctk.CTkFrame):
    """
    Grade de KPI cards do experimento PCM.

    Layout: 3 linhas × 4 colunas (última linha pode ter menos cards).
    Atualização centralizada via update_kpis(metricas).
    """

    # Paleta de cores — deve ser consistente com PCMCalcScreen
    PANEL_COLOR = "#111827"
    CARD_COLOR = "#0F172A"
    BORDER_COLOR = "#334155"
    TEXT_PRIMARY = "#F3F4F6"
    TEXT_SECONDARY = "#9CA3AF"

    def __init__(self, parent: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._values: dict[str, ctk.CTkLabel] = {}
        self._subvalues: dict[str, ctk.CTkLabel] = {}
        self._build()

    def _build(self) -> None:
        cols = 4
        for col in range(cols):
            self.grid_columnconfigure(col, weight=1, uniform="kpi")

        for idx, (key, tooltip) in enumerate(KPI_DEFS):
            self._create_card(idx, key, tooltip, cols=cols)

    def _create_card(self, index: int, title: str, tooltip: str, *, cols: int) -> None:
        card = ctk.CTkFrame(
            self,
            fg_color=self.PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        row, col = divmod(index, cols)
        card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

        title_lbl = ctk.CTkLabel(
            card,
            text=title,
            font=("Arial", 14, "bold"),
            text_color=self.TEXT_SECONDARY,
        )
        title_lbl.pack(anchor="w", padx=18, pady=(16, 8))
        _Tooltip(title_lbl, tooltip)

        value_lbl = ctk.CTkLabel(
            card,
            text="--",
            font=("Arial", 22, "bold"),
            text_color=self.TEXT_PRIMARY,
            justify="left",
            wraplength=320,
        )
        value_lbl.pack(anchor="w", padx=18, pady=(0, 8))
        self._values[title] = value_lbl

        sub_lbl = ctk.CTkLabel(
            card,
            text="",
            font=("Arial", 12),
            text_color=self.TEXT_SECONDARY,
            justify="left",
            wraplength=320,
        )
        sub_lbl.pack(anchor="w", padx=18, pady=(0, 12))
        self._subvalues[title] = sub_lbl

    # ── API pública ───────────────────────────────────────────────────────────

    def update_kpis(
        self,
        *,
        energia_total: float,
        potencia_media: float,
        massa_pcm: float,
        erro_percentual: Optional[float],
        tempo_atuacao_pcm_s: float,
        delta_t_c: float,
        eficiencia_percent: Optional[float],
        energia_ideal_j: Optional[float],
        duracao_min: Optional[float],
    ) -> None:
        """
        Atualiza todos os cards de uma vez.

        Método central: evita self._values["..."].configure() espalhado.
        Todos os parâmetros são tipos primitivos Python — nunca pandas.Series.
        """
        self._set("Energia Total", f"{energia_total:.0f} J")
        self._set("Potência Média", f"{potencia_media:.2f} W")
        self._set("Massa PCM", f"{massa_pcm:.2f} g")
        self._set(
            "Erro Percentual",
            f"{erro_percentual:.1f} %" if erro_percentual is not None else "--",
        )

        tempo_pcm_min = float(tempo_atuacao_pcm_s) / 60.0
        self._set("Tempo de Atuação do PCM", f"{tempo_pcm_min:.1f} min")
        self._set_sub("Tempo de Atuação do PCM", "Faixa: 50–60 °C")

        self._set("Delta T", f"{delta_t_c:.2f} °C")
        self._set(
            "Eficiência Térmica",
            f"{eficiencia_percent:.1f} %" if eficiencia_percent is not None else "--",
        )
        self._set(
            "Energia Ideal",
            f"{energia_ideal_j:.0f} J" if energia_ideal_j is not None else "--",
        )
        self._set(
            "Duração do Experimento",
            f"{duracao_min:.2f} min" if duracao_min is not None else "--",
        )

    def reset(self) -> None:
        """Reseta todos os cards para o estado inicial '--'."""
        for lbl in self._values.values():
            if lbl.winfo_exists():
                lbl.configure(text="--")
        for lbl in self._subvalues.values():
            if lbl.winfo_exists():
                lbl.configure(text="")

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _set(self, key: str, text: str) -> None:
        lbl = self._values.get(key)
        if lbl is not None and lbl.winfo_exists():
            lbl.configure(text=text)

    def _set_sub(self, key: str, text: str) -> None:
        lbl = self._subvalues.get(key)
        if lbl is not None and lbl.winfo_exists():
            lbl.configure(text=text)