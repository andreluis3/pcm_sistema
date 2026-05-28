from __future__ import annotations

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from tkinter import Canvas, TclError, ttk
from services.dashboard_metrics import calcular_metricas_globais

from services.hybrid_repository import HybridRepository
from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    FONT_LABEL,
    FONT_METRIC,
    FONT_TITLE,
    WIDGET_HEIGHT_NORMAL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
    PAD_GAP,
    THEME_COLORS,
    card_style,
    button_style,
    style_ax_dark,
    FONT_SMALL,
)


# ─────────────────────────────────────────────────────────────────────────────
# STATUS PILL – pastilha colorida de status
# ─────────────────────────────────────────────────────────────────────────────

class _StatusPill(ctk.CTkFrame):
    """Pastilha compacta: ● Label  Value"""

    def __init__(self, parent, label: str, textvariable: ctk.StringVar, **kw):
        super().__init__(
            parent,
            fg_color=THEME_COLORS["card_soft"],
            corner_radius=20,
            border_width=1,
            border_color=THEME_COLORS["border"],
            **kw,
        )
        dot = ctk.CTkLabel(self, text="●", font=FONT_SMALL if hasattr(ctk, 'FONT_SMALL') else ("Inter", 10),
                           text_color=THEME_COLORS["accent"])
        dot.grid(row=0, column=0, padx=(PAD_NORMAL, 4), pady=PAD_SMALL)

        lbl = ctk.CTkLabel(self, text=label + ":", font=FONT_LABEL,
                           text_color=THEME_COLORS["text_secondary"])
        lbl.grid(row=0, column=1, pady=PAD_SMALL)

        val = ctk.CTkLabel(self, textvariable=textvariable, font=FONT_NORMAL,
                           text_color=THEME_COLORS["text_primary"])
        val.grid(row=0, column=2, padx=(4, PAD_NORMAL), pady=PAD_SMALL)


# ─────────────────────────────────────────────────────────────────────────────
# SEPARATOR
# ─────────────────────────────────────────────────────────────────────────────

class _Separator(ctk.CTkFrame):
    def __init__(self, parent, **kw):
        super().__init__(parent, height=1, fg_color=THEME_COLORS["border"], **kw)


# ─────────────────────────────────────────────────────────────────────────────
# INFO ROW – par label + valor em linha
# ─────────────────────────────────────────────────────────────────────────────

def _info_row(parent, row: int, col: int, label: str) -> ctk.CTkLabel:
    """Cria um bloco label/valor vertical e retorna o widget de valor."""
    lbl = ctk.CTkLabel(parent, text=label.upper(), font=FONT_LABEL,
                       text_color=THEME_COLORS["text_secondary"])
    lbl.grid(row=row * 2, column=col, sticky="w", padx=(PAD_LARGE, PAD_NORMAL),
             pady=(PAD_NORMAL, 0))
    val = ctk.CTkLabel(parent, text="--", font=FONT_TITLE,
                       text_color=THEME_COLORS["text_primary"])
    val.grid(row=row * 2 + 1, column=col, sticky="w", padx=(PAD_LARGE, PAD_NORMAL),
             pady=(0, PAD_NORMAL))
    return val


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD TAB
# ─────────────────────────────────────────────────────────────────────────────

class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, db_manager: HybridRepository | None = None) -> None:
        super().__init__(parent, fg_color=THEME_COLORS["bg"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)   # main content expands

        self.db = db_manager or HybridRepository()
        self._experiments: list[dict] = []
        self._experiment_map: dict[str, dict | None] = {}
        self._selected_experiment: dict | None = None
        self._avg_series: list[tuple[float, float]] | None = None
        self._phase_index: int | None = None

        self._sensor_status_var  = ctk.StringVar(value="Offline")
        self._mqtt_status_var    = ctk.StringVar(value="Desconectado")
        self._current_experiment_var = ctk.StringVar(value="--")
        self._canvas_temp_var    = ctk.StringVar(value="-- °C")
        self._animate_id: str | None = None

        # não há PCM canvas nesta versão
        self._pcm_state = "solid"
        self._anim_phase = 0

        self._build_layout()
        self.load_dashboard_data()

    # ─── Data ─────────────────────────────────────────────────────────────

    def load_dashboard_data(self) -> None:
        try:
            if not self.winfo_exists():
                return
            self._experiments = [dict(r) for r in self.db.list_experiments()]
            self._refresh_experiment_selector()
            self.update_dashboard()
            if self._selected_experiment:
                self._set_metrics_from_experiment(self._selected_experiment.get("id"))
            self._refresh_statistics()
        except Exception as e:
            print(f"[LOAD DASHBOARD ERROR] {e}")

    def update_dashboard(self) -> None:
        try:
            if not self.winfo_exists():
                return
            exp = self._selected_experiment
            if not exp:
                self._set_metrics(None, None, None, None)
                self._set_experiment_info({})
                self._canvas_temp_var.set("-- °C")
                self.plot_temperature_graph([])
                return
            exp_id = exp.get("id")
            self._set_metrics_from_experiment(exp_id)
            self._set_experiment_info(exp)
            series = self._build_temperature_series(exp)
            self._phase_index = self._detect_phase_change(series)
            self.plot_temperature_graph(series)
            current_temp = (exp.get("temperatura_final") or exp.get("temperatura_media") or 0)
            if current_temp is not None:
                self._canvas_temp_var.set(f"{current_temp:.1f} °C")
            else:
                self._canvas_temp_var.set("-- °C")
            self._update_thermo_cards(exp_id)
        except Exception as e:
            print(f"[DASHBOARD UPDATE ERROR] {e}")

    def _set_metrics_from_experiment(self, exp_id):
        if exp_id is None:
            self._set_metrics(None, None, None, None)
            return
        metricas = self.db.get_metricas(exp_id)
        self._set_metrics(
            metricas.get("temperatura_media"),
            metricas.get("delta_temperatura"),
            metricas.get("heating_rate"),
            metricas.get("energia_armazenada"),
        )

    # ─── Métricas ─────────────────────────────────────────────────────────

    def _set_metrics(self, temp_media, delta_t, heating_rate, energia) -> None:
        self._metric_temp.configure(text=f"{temp_media:.1f} °C"     if temp_media    is not None else "--")
        self._metric_delta.configure(text=f"{delta_t:.1f} °C"       if delta_t       is not None else "--")
        self._metric_rate.configure(text=f"{heating_rate:.2f} °C/min" if heating_rate is not None else "--")
        self._metric_energy.configure(text=f"{energia:.0f} J"       if energia       is not None else "--")

    # ─── Gráfico ──────────────────────────────────────────────────────────

    def plot_temperature_graph(self, series: list[tuple[float, float]]) -> None:
        try:
            if not self.winfo_exists():
                return
            self._temp_ax.clear()
            style_ax_dark(
                self._temp_ax,
                card_color=THEME_COLORS["card"],
                border_color=THEME_COLORS["border"],
                text_color=THEME_COLORS["text_secondary"],
            )
            if not series:
                self._temp_canvas.draw_idle()
                return
            x = [p[0] for p in series]
            y = [p[1] for p in series]
            self._temp_ax.plot(x, y, color=THEME_COLORS["accent"], linewidth=2.8,
                               solid_capstyle="round", solid_joinstyle="round")
            if self._avg_series:
                avg_x = [p[0] for p in self._avg_series]
                avg_y = [p[1] for p in self._avg_series]
                self._temp_ax.plot(avg_x, avg_y, color=THEME_COLORS["line_avg"],
                                   linewidth=2.2, linestyle="--", alpha=0.85)
            if self._phase_index is not None and 0 <= self._phase_index < len(series):
                px, py = series[self._phase_index]
                self._temp_ax.scatter([px], [py], color=THEME_COLORS["line_avg"],
                                      s=60, zorder=5, edgecolors=THEME_COLORS["card"],
                                      linewidths=2)
                self._temp_ax.axvline(px, color=THEME_COLORS["line_avg"],
                                      linewidth=1, linestyle=":", alpha=0.5)
            self._temp_ax.set_xlabel("Tempo (min)", color=THEME_COLORS["text_secondary"], fontsize=9, labelpad=8)
            self._temp_ax.set_ylabel("Temperatura (°C)", color=THEME_COLORS["text_secondary"], fontsize=9, labelpad=8)
            self._temp_fig.tight_layout(pad=1.6)
            self._temp_canvas.draw_idle()
        except Exception as e:
            print(f"[GRAPH ERROR] {e}")

    def _build_temperature_series(self, exp: dict) -> list[tuple[float, float]]:
        t_initial = exp.get("temperatura_inicial")
        t_final   = exp.get("temperatura_final")
        delta_tempo = exp.get("delta_tempo") or 0
        if t_initial is None or t_final is None:
            return []
        points  = 24
        x_values = [i * (delta_tempo / (points - 1)) if delta_tempo else i for i in range(points)]
        y_values = [t_initial + (t_final - t_initial) * (i / (points - 1)) for i in range(points)]
        return list(zip(x_values, y_values))

    def _detect_phase_change(self, series: list[tuple[float, float]]) -> int | None:
        if len(series) < 6:
            return None
        y_vals = [p[1] for p in series]
        for i in range(3, len(y_vals)):
            span = max(y_vals[i - 3:i + 1]) - min(y_vals[i - 3:i + 1])
            if span <= 0.25:
                return i - 1
        return None

    # ─── Layout ───────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        self._configure_ttk_style()
        self._build_header()
        self._build_main()
        self._build_thermo_row()

    # ── Header ──

    def _build_header(self) -> None:
        header = ctk.CTkFrame(
            self,
            fg_color=THEME_COLORS["card"],
            corner_radius=0,
            border_width=0,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        # Título + subtítulo
        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=PAD_NORMAL)

        ctk.CTkLabel(
            title_block,
            text="🧪  Dashboard de Experimento PCM",
            font=FONT_HEADER,
            text_color=THEME_COLORS["text_primary"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_block,
            text="Monitoramento térmico e análise experimental",
            font=FONT_LABEL,
            text_color=THEME_COLORS["text_secondary"],
        ).grid(row=1, column=0, sticky="w")

        # Separador vertical decorativo
        _Separator(header, width=1).grid(
            row=0, column=1, sticky="ns", padx=PAD_LARGE, pady=PAD_NORMAL
        )

        # Lado direito
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=PAD_LARGE, pady=PAD_NORMAL)

        # Status pills
        pills = ctk.CTkFrame(right, fg_color="transparent")
        pills.grid(row=0, column=0, columnspan=3, sticky="e", pady=(0, PAD_SMALL))
        pills.grid_columnconfigure((0, 1), weight=0)

        self._sensor_pill = _StatusPill(pills, "Sensor", self._sensor_status_var)
        self._sensor_pill.grid(row=0, column=0, padx=(0, PAD_SMALL))

        self._mqtt_pill = _StatusPill(pills, "MQTT", self._mqtt_status_var)
        self._mqtt_pill.grid(row=0, column=1)

        # Combobox + botão
        controls = ctk.CTkFrame(right, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="e")

        exp_label = ctk.CTkLabel(
            controls, text="Experimento", font=FONT_LABEL,
            text_color=THEME_COLORS["text_secondary"],
        )
        exp_label.grid(row=0, column=0, padx=(0, PAD_SMALL))

        self._experiment_combo = ttk.Combobox(controls, state="readonly", values=[], width=22)
        self._experiment_combo.grid(row=0, column=1, padx=(0, PAD_NORMAL))
        self._experiment_combo.bind("<<ComboboxSelected>>", self._on_experiment_combo_selected)

        self._avg_btn_header = ctk.CTkButton(
            controls,
            text="Calcular Média",
            font=FONT_NORMAL,
            command=self._on_average_clicked,
            width=140,
            **button_style("primary"),
        )
        self._avg_btn_header.grid(row=0, column=2)

        # Linha divisória inferior do header
        _Separator(self).grid(row=0, column=0, sticky="ews")

    # ── Main content ──

    def _build_main(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew", padx=PAD_LARGE, pady=PAD_GAP)
        main.grid_columnconfigure(0, weight=5)   # gráfico (dominante)
        main.grid_columnconfigure(1, weight=3)   # painel direito
        main.grid_rowconfigure(0, weight=3)      # gráfico
        main.grid_rowconfigure(1, weight=2)      # estatísticas + métricas

        # ── Gráfico (coluna 0, linha 0) ──
        self._build_graph_card(main)

        # ── Informações do Experimento (coluna 1, linha 0) ──
        self._build_info_card(main)

        # ── Métricas (linha 1, span 2) ──
        self._build_metrics_row(main)

    def _build_graph_card(self, parent) -> None:
        card = ctk.CTkFrame(parent, **card_style())
        card.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_NORMAL), pady=(0, PAD_NORMAL))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        # Header do card
        ch = ctk.CTkFrame(card, fg_color="transparent")
        ch.grid(row=0, column=0, sticky="ew", padx=PAD_LARGE, pady=(PAD_NORMAL, 0))
        ch.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(ch, text="Temperatura × Tempo", font=FONT_TITLE,
                     text_color=THEME_COLORS["text_primary"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(ch, text="Curva experimental do experimento selecionado",
                     font=FONT_LABEL, text_color=THEME_COLORS["text_secondary"]).grid(
            row=1, column=0, sticky="w")

        # Figura matplotlib
        self._temp_fig = Figure(dpi=100)
        self._temp_fig.patch.set_facecolor(THEME_COLORS["card"])
        self._temp_ax = self._temp_fig.add_subplot(111)
        self._temp_ax.set_facecolor(THEME_COLORS["card"])

        self._temp_canvas = FigureCanvasTkAgg(self._temp_fig, master=card)
        widget = self._temp_canvas.get_tk_widget()
        widget.grid(row=1, column=0, sticky="nsew", padx=PAD_NORMAL, pady=PAD_NORMAL)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

    def _build_info_card(self, parent) -> None:
        card = ctk.CTkFrame(parent, **card_style())
        card.grid(row=0, column=1, sticky="nsew", pady=(0, PAD_NORMAL))
        card.grid_columnconfigure((0, 1), weight=1)

        # Título
        ctk.CTkLabel(card, text="Informações do Experimento", font=FONT_TITLE,
                     text_color=THEME_COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=PAD_LARGE, pady=(PAD_LARGE, PAD_SMALL))

        _Separator(card).grid(row=1, column=0, columnspan=2, sticky="ew", padx=PAD_LARGE)

        self._info_labels = {}
        # Grid 2×2: (Material, Operador) / (Massa, Cápsula)
        fields = [
            ("Material", "material",  0, 0),
            ("Operador", "operador",  0, 1),
            ("Massa",    "massa",     1, 0),
            ("Cápsula",  "capsula",   1, 1),
        ]
        for label, key, r, c in fields:
            self._info_labels[key] = _info_row(card, r + 1, c, label)

        # Temperatura atual — linha de destaque
        _Separator(card).grid(row=6, column=0, columnspan=2, sticky="ew", padx=PAD_LARGE, pady=(PAD_NORMAL, 0))

        temp_block = ctk.CTkFrame(card, fg_color="transparent")
        temp_block.grid(row=7, column=0, columnspan=2, sticky="ew", padx=PAD_LARGE, pady=(PAD_SMALL, PAD_LARGE))
        temp_block.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(temp_block, text="Temperatura atual", font=FONT_LABEL,
                     text_color=THEME_COLORS["text_secondary"]).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(temp_block, textvariable=self._canvas_temp_var, font=FONT_METRIC,
                     text_color=THEME_COLORS["accent"]).grid(row=0, column=1, sticky="e")

        # compatibilidade: campos que o código existente tenta configurar mas não exibimos
        self._info_labels["quantidade"] = ctk.CTkLabel(card, text="")
        self._info_labels["tempo_total"] = ctk.CTkLabel(card, text="")

    def _build_metrics_row(self, parent) -> None:
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        row_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        row_frame.grid_rowconfigure(0, weight=1)

        # 4 métricas + Estatísticas Globais lado a lado
        # Deixamos col 0-3 para métricas e col 4 para estatísticas (mas reordenaremos em 2 linhas)
        # Layout: linha superior = métricas (4 cards), linha inferior = estatísticas (1 card largo)

        # Métricas
        self._metric_temp   = self._metric_card(row_frame, 0, "Temperatura média",     THEME_COLORS["accent"])
        self._metric_delta  = self._metric_card(row_frame, 1, "ΔT do experimento",     THEME_COLORS["line_avg"])
        self._metric_rate   = self._metric_card(row_frame, 2, "Taxa de aquecimento",   THEME_COLORS["export"])
        self._metric_energy = self._metric_card(row_frame, 3, "Energia armazenada",    THEME_COLORS["primary"])

        # Estatísticas globais — ocupa a linha seguinte, full-width
        self._build_statistics_card(parent)

    def _build_statistics_card(self, parent) -> None:
        card = ctk.CTkFrame(parent, **card_style())
        card.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(PAD_NORMAL, 0))
        card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(card, text="Estatísticas Globais", font=FONT_TITLE,
                     text_color=THEME_COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        _Separator(card).grid(row=1, column=0, columnspan=4, sticky="ew", padx=PAD_LARGE)

        self._stats_labels = {}
        stats = [
            ("Tempo médio de fusão",      "tempo_fusao",  0),
            ("Pico médio de temperatura", "pico_temp",    1),
            ("Energia média absorvida",   "energia_media", 2),
            ("Eficiência térmica",        "eficiencia",   3),
        ]
        for label, key, col in stats:
            lbl = ctk.CTkLabel(card, text=label.upper(), font=FONT_LABEL,
                               text_color=THEME_COLORS["text_secondary"])
            lbl.grid(row=2, column=col, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, 0))
            val = ctk.CTkLabel(card, text="--", font=FONT_TITLE,
                               text_color=THEME_COLORS["text_primary"])
            val.grid(row=3, column=col, sticky="w", padx=PAD_LARGE, pady=(0, PAD_LARGE))
            self._stats_labels[key] = val

    # ── Thermo cards (Calor Sensível / Latente) ──

    def _build_thermo_row(self) -> None:
        row_frame = ctk.CTkFrame(self, fg_color="transparent")
        row_frame.grid(row=2, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_LARGE))
        row_frame.grid_columnconfigure((0, 1), weight=1)

        self._card_sensible = self._thermo_card(row_frame, 0, "🔥  Calor Sensível",  "Q = m · c · ΔT")
        self._card_latent   = self._thermo_card(row_frame, 1, "⚛️  Calor Latente",   "Q = m · L")

        # card_storage esperado pelo código existente mas não exibido
        self._card_storage = {"card": ctk.CTkFrame(self, fg_color="transparent"), "value": ctk.CTkLabel(self, text="")}

    # ─── Card helpers ─────────────────────────────────────────────────────

    def _metric_card(self, parent, col: int, title: str, accent: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME_COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=THEME_COLORS["border"],
        )
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0 if col == 0 else PAD_SMALL, 0), pady=(0, PAD_SMALL))
        card.grid_columnconfigure(0, weight=1)

        # Accent bar top
        bar = ctk.CTkFrame(card, height=3, fg_color=accent, corner_radius=2)
        bar.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, PAD_SMALL))

        ctk.CTkLabel(card, text=title, font=FONT_LABEL,
                     text_color=THEME_COLORS["text_secondary"]).grid(
            row=1, column=0, sticky="w", padx=PAD_NORMAL, pady=(0, PAD_SMALL))

        val = ctk.CTkLabel(card, text="--", font=FONT_METRIC, text_color=accent)
        val.grid(row=2, column=0, sticky="w", padx=PAD_NORMAL, pady=(0, PAD_NORMAL))
        return val

    def _thermo_card(self, parent, col: int, title: str, formula: str) -> dict:
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME_COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=THEME_COLORS["border"],
        )
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0 if col == 0 else PAD_NORMAL, 0))
        card.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=PAD_LARGE, pady=PAD_LARGE)
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(inner, text=title, font=FONT_TITLE,
                     text_color=THEME_COLORS["text_primary"]).grid(
            row=0, column=0, sticky="w", pady=(0, PAD_SMALL))

        ctk.CTkLabel(inner, text=formula, font=FONT_LABEL,
                     text_color=THEME_COLORS["text_secondary"]).grid(
            row=1, column=0, sticky="w", pady=(0, PAD_NORMAL))

        _Separator(inner).grid(row=2, column=0, sticky="ew", pady=(0, PAD_NORMAL))

        val = ctk.CTkLabel(inner, text="--", font=FONT_METRIC,
                           text_color=THEME_COLORS["primary"])
        val.grid(row=3, column=0, sticky="w")

        return {"card": card, "value": val}

    # ─── Experiment info ──────────────────────────────────────────────────

    def _set_experiment_info(self, exp: dict) -> None:
        if not exp:
            self._current_experiment_var.set("--")
            for key in self._info_labels:
                try:
                    self._info_labels[key].configure(text="--")
                except Exception:
                    pass
            return

        material    = exp.get("material")    or "--"
        massa       = exp.get("massa")
        operador    = exp.get("operador")    or "--"
        capsula     = exp.get("capsula")     or "--"
        delta_tempo = exp.get("delta_tempo")

        self._current_experiment_var.set(
            f"#{exp.get('id') if exp.get('id') is not None else '--'}"
        )

        self._info_labels["material"].configure(text=material)
        self._info_labels["massa"].configure(text=f"{massa:.2f} g" if massa is not None else "--")
        self._info_labels["operador"].configure(text=operador)
        self._info_labels["capsula"].configure(text=capsula)
        # silent — campos ocultos mas mantidos para compatibilidade
        try:
            self._info_labels["quantidade"].configure(text=f"{massa:.2f} g" if massa is not None else "--")
            self._info_labels["tempo_total"].configure(text=f"{delta_tempo:.1f} min" if delta_tempo is not None else "--")
        except Exception:
            pass

    # ─── Thermo cards update ──────────────────────────────────────────────

    def _update_thermo_cards(self, exp_id: int | None) -> None:
        if not exp_id:
            self._card_sensible["value"].configure(text="--")
            self._card_latent["value"].configure(text="--")
            return

        sensivel = self.db.get_calculo_by_experimento_tipo(exp_id, "Calor Sensível")
        latente  = self.db.get_calculo_by_experimento_tipo(exp_id, "Calor Latente")

        sensivel_val = sensivel["resultado"] if sensivel and sensivel["resultado"] is not None else None
        latente_val  = latente["resultado"]  if latente  and latente["resultado"]  is not None else None

        self._card_sensible["value"].configure(text=f"{sensivel_val:.1f} J" if sensivel_val is not None else "--")
        self._card_latent["value"].configure(text=f"{latente_val:.1f} J"   if latente_val  is not None else "--")

        if self._phase_index is not None:
            self._card_latent["card"].configure(border_width=2, border_color=THEME_COLORS["line_avg"])
        else:
            self._card_latent["card"].configure(border_width=1, border_color=THEME_COLORS["border"])

    # ─── Statistics ───────────────────────────────────────────────────────

    def _refresh_statistics(self) -> None:
        if not self._experiments:
            for lbl in self._stats_labels.values():
                lbl.configure(text="--")
            return

        tempos = [float(e["delta_tempo"]) for e in self._experiments if e.get("delta_tempo") is not None]
        temps_finais = [float(e["temperatura_final"]) for e in self._experiments if e.get("temperatura_final") is not None]
        energias = [float(e) for e in (self.db.get_energia_armazenada(e.get("id")) for e in self._experiments) if e is not None]

        if tempos:
            self._stats_labels["tempo_fusao"].configure(text=f"{sum(tempos)/len(tempos):.1f} min")
        if temps_finais:
            self._stats_labels["pico_temp"].configure(text=f"{sum(temps_finais)/len(temps_finais):.1f} °C")
        if energias:
            self._stats_labels["energia_media"].configure(text=f"{sum(energias)/len(energias):.0f} J")

        efficiencies = [float(r["eficiencia"]) for r in self.db.list_thermal_calculations() if r.get("eficiencia") is not None]
        if efficiencies:
            self._stats_labels["eficiencia"].configure(text=f"{sum(efficiencies)/len(efficiencies):.0f} %")

    # ─── Buttons ──────────────────────────────────────────────────────────

    def _on_average_clicked(self) -> None:
        dados = calcular_metricas_globais(self._experiments, self.db)
        if not dados:
            return
        self._metric_temp.configure(text=f"{dados['media_temperatura']} °C")
        self._metric_energy.configure(text=f"{dados['media_energia']} J")
        self._metric_delta.configure(text=f"{dados['media_tempo']} min")
        self._metric_rate.configure(text=f"{dados['media_taxa']} °C/min")
        self._avg_series = self._compute_average_series()
        self.plot_temperature_graph(self._avg_series)

    def _on_export_clicked(self) -> None:
        return

    def _on_reset_clicked(self) -> None:
        self._avg_series = None
        self.update_dashboard()

    # ─── Status updates ───────────────────────────────────────────────────

    def update_sensor_status(self, status: str) -> None:
        self._sensor_status_var.set(status)

    def update_mqtt_status(self, status: str) -> None:
        self._mqtt_status_var.set(status)

    def update_current_temperature(self, temperature: float) -> None:
        self._canvas_temp_var.set(f"{temperature:.1f} °C")

    # ─── PCM stubs (mantidos para compatibilidade externa) ────────────────

    def _draw_pcm_state(self, state: str) -> None:
        self._pcm_state = state

    def _infer_pcm_state(self, exp: dict, current_temp: float) -> str:
        t_initial = exp.get("temperatura_inicial")
        t_final   = exp.get("temperatura_final")
        if t_initial is None or t_final is None:
            return "solid"
        span = t_final - t_initial
        if span <= 0:
            return "solid"
        ratio = (current_temp - t_initial) / span
        if ratio < 0.35:   return "solid"
        if ratio < 0.75:   return "transition"
        return "liquid"

    def _animate_pcm(self) -> None:
        pass  # removido nesta versão

    # ─── Experiments selector ─────────────────────────────────────────────

    def _refresh_experiment_selector(self) -> None:
        if not self.winfo_exists():
            return
        combo = getattr(self, "_experiment_combo", None)
        if combo is None:
            return
        try:
            if hasattr(combo, "winfo_exists") and not combo.winfo_exists():
                return
        except Exception:
            return

        options = []
        self._experiment_map.clear()

        for row in self._experiments:
            label = f"#{row['id']} – {row.get('material') or 'Sem material'}"
            options.append(label)
            self._experiment_map[label] = row

        if not options:
            options = ["Nenhum experimento"]
            self._experiment_map = {}

        try:
            self._experiment_combo["values"] = options
            self._experiment_combo.current(0)
            self._selected_experiment = self._experiment_map.get(options[0])
        except TclError:
            return

    def _on_experiment_selected(self) -> None:
        try:
            if not self.winfo_exists():
                return
            label = self._experiment_combo.get()
            self._selected_experiment = self._experiment_map.get(label)
            self.update_dashboard()
        except Exception as e:
            print(f"[EXPERIMENT SELECT ERROR] {e}")

    def _on_experiment_combo_selected(self, _event=None) -> None:
        self._on_experiment_selected()

    # ─── Average series ───────────────────────────────────────────────────

    def _compute_average_series(self) -> list[tuple[float, float]]:
        candidates = [e for e in self._experiments
                      if e.get("temperatura_inicial") is not None and e.get("temperatura_final") is not None]
        if not candidates:
            return []
        points = 24
        avg_delta = sum(float(e.get("delta_tempo") or 0) for e in candidates) / len(candidates)
        x_values = [i * (avg_delta / (points - 1)) if avg_delta else i for i in range(points)]
        y_values = []
        for i in range(points):
            ratio = i / (points - 1)
            temps = [float(e["temperatura_inicial"]) + (float(e["temperatura_final"]) - float(e["temperatura_inicial"])) * ratio
                     for e in candidates if e.get("temperatura_inicial") is not None and e.get("temperatura_final") is not None]
            y_values.append(sum(temps) / len(temps) if temps else 0)
        return list(zip(x_values, y_values))

    # ─── TTK style ────────────────────────────────────────────────────────

    def _configure_ttk_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "TCombobox",
            fieldbackground=THEME_COLORS["card_soft"],
            background=THEME_COLORS["card"],
            foreground=THEME_COLORS["text_primary"],
            bordercolor=THEME_COLORS["border"],
            arrowcolor=THEME_COLORS["accent"],
            selectbackground=THEME_COLORS["card_soft"],
            selectforeground=THEME_COLORS["text_primary"],
            font=("Inter", 13),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", THEME_COLORS["card_soft"])],
            foreground=[("readonly", THEME_COLORS["text_primary"])],
        )

    # ─── Destroy ──────────────────────────────────────────────────────────

    def destroy(self) -> None:
        try:
            if self._animate_id:
                self.after_cancel(self._animate_id)
                self._animate_id = None
        except Exception:
            pass
        try:
            if hasattr(self, "_temp_canvas"):
                widget = self._temp_canvas.get_tk_widget()
                if widget:
                    widget.destroy()
        except Exception:
            pass
        try:
            if hasattr(self, "_temp_fig"):
                self._temp_fig.clear()
                plt.close(self._temp_fig)
        except Exception:
            pass
        try:
            super().destroy()
        except Exception:
            pass