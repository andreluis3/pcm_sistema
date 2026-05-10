from __future__ import annotations

from dataclasses import dataclass
import customtkinter as ctk
from tkinter import messagebox, ttk

from database.database_manager import DatabaseManager
from interface.database_tab import DatabaseTab
from ui.materials_view import MaterialsView
from services.controller_calculos import ControllerCalculos
from ui_styles import (
    FONT_HEADER,
    FONT_TITLE,
    FONT_NORMAL,
    FONT_SMALL,
    FONT_TEMP,
    FONT_LABEL,
    FONT_METRIC,
    WIDGET_HEIGHT_NORMAL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
    THEME_COLORS,
    card_style,
    button_style,
)


@dataclass
class CalculationField:
    key: str
    label: str
    placeholder: str


CALCULATION_DEFS: dict[str, dict] = {
    "Energia Absorvida": {
        "formula": "Q = m × c × ΔT",
        "where": (
            "Onde:\n"
            "Q = energia absorvida\n"
            "m = massa\n"
            "ΔT = variação de temperatura\n\n"
            "Calor específico: 2.0 kJ/kg·°C (valor fixo adotado com base em dados típicos de materiais orgânicos semelhantes à cera de coco)"
        ),
        "explain": "Este cálculo determina a energia necessária para elevar a temperatura sem mudança de fase.",
        "fields": [
            CalculationField("m", "Massa (g)", "Ex.: 100"),
            CalculationField("delta_t", "ΔT (°C)", "Ex.: 29"),
        ],
        "result_label": "Energia absorvida",
        "unit": "J",
    },
    "Calor Sensível": {
        "formula": "Q = m × c × ΔT",
        "where": (
            "Onde:\n"
            "m = massa\n"
            "ΔT = variação de temperatura\n\n"
            "Calor específico: 2.0 kJ/kg·°C (valor fixo adotado com base em dados típicos de materiais orgânicos semelhantes à cera de coco)"
        ),
        "explain": "Este cálculo determina a energia absorvida pelo material durante o aquecimento sensível.",
        "fields": [
            CalculationField("m", "Massa (g)", "Ex.: 100"),
            CalculationField("delta_t", "ΔT (°C)", "Ex.: 29"),
        ],
        "result_label": "Calor sensível",
        "unit": "J",
    },
    "Calor Latente": {
        "formula": "Q = m × L",
        "where": (
            "Onde:\n"
            "m = massa\n"
            "L = calor latente específico\n\n"
            "Calor específico: 2.0 kJ/kg·°C (valor fixo adotado com base em dados típicos de materiais orgânicos semelhantes à cera de coco)"
        ),
        "explain": "Este cálculo estima a energia envolvida na mudança de fase do material.",
        "fields": [
            CalculationField("m", "Massa (g)", "Ex.: 100"),
            CalculationField("l", "Calor latente (J/g)", "Ex.: 180"),
        ],
        "result_label": "Calor latente",
        "unit": "J",
    },
}


class ThermalCalculationsPanel(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        db_manager: DatabaseManager,
        on_calculation_saved=None,
    ) -> None:
        # UI REFATORADA: painel de cálculos com cards e botões padronizados
        super().__init__(parent, fg_color=THEME_COLORS["bg"])
        self.controller = ControllerCalculos(db_manager)
        self._on_calculation_saved = on_calculation_saved
        self._experiment_rows: list = []
        self._experiment_map: dict[str, dict] = {}
        self._selected_experiment: dict | None = None
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._last_result: float | None = None
        self._last_calc_type: str | None = None
        self._dashboard_refresh_scheduled = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Cálculos Térmicos",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_SMALL, PAD_NORMAL))

        self.create_calculos_frame()
        self.load_experiment_data()
        self._build_inputs(self.calc_type.get())

    # --- Organização principal ------------------------------------------
    def create_calculos_frame(self) -> None:
        self._configure_ttk_style()
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=PAD_LARGE, pady=(0, PAD_LARGE))
        body.grid_columnconfigure(0, weight=1)

        self._build_selection_panel(body)
        self._build_explanation_panel(body)
        self._build_input_panel(body)
        self._build_result_panel(body)
        self._build_guide_panel(body)
        self._build_computer_simulator_panel(body)

    # --- Painéis ---------------------------------------------------------
    def _build_selection_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, **card_style())
        panel.grid(row=0, column=0, sticky="ew", pady=(0, PAD_NORMAL))
        panel.grid_columnconfigure(1, weight=1)
        panel.grid_columnconfigure(3, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="1️⃣ Seleção do experimento",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, columnspan=4, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        exp_label = ctk.CTkLabel(panel, text="Selecionar Experimento", text_color=THEME_COLORS["text_secondary"], font=FONT_LABEL)
        exp_label.grid(row=1, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        self.experiment_combo = ttk.Combobox(panel, state="readonly", values=["Carregando..."])
        self.experiment_combo.grid(row=2, column=0, columnspan=2, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        self.experiment_combo.bind("<<ComboboxSelected>>", self._on_experiment_combo_selected)

        calc_label = ctk.CTkLabel(panel, text="Tipo de cálculo", text_color=THEME_COLORS["text_secondary"], font=FONT_LABEL)
        calc_label.grid(row=1, column=2, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        self.calc_type = ctk.StringVar(value="Energia Absorvida")
        self.calc_combo = ttk.Combobox(panel, state="readonly", values=list(CALCULATION_DEFS.keys()), textvariable=self.calc_type)
        self.calc_combo.grid(row=2, column=2, columnspan=2, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        self.calc_combo.bind("<<ComboboxSelected>>", self._on_calc_combo_selected)
        if self.calc_combo["values"]:
            self.calc_combo.current(0)

    def _on_experiment_combo_selected(self, _event=None) -> None:
        self._on_experiment_selected()

    def _on_calc_combo_selected(self, _event=None) -> None:
        self._on_calc_selected()

    def _build_explanation_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, **card_style())
        panel.grid(row=1, column=0, sticky="ew", pady=(0, PAD_NORMAL))
        panel.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="2️⃣ Como este cálculo funciona",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self.formula_label = ctk.CTkLabel(
            panel,
            text="",
            text_color=THEME_COLORS["primary"],
            font=FONT_TITLE,
            justify="left",
        )
        self.formula_label.grid(row=1, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        self.where_label = ctk.CTkLabel(
            panel,
            text="",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_NORMAL,
            justify="left",
        )
        self.where_label.grid(row=2, column=0, sticky="w", padx=PAD_LARGE)

        self.explain_label = ctk.CTkLabel(
            panel,
            text="",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
            justify="left",
            wraplength=680,
        )
        self.explain_label.grid(row=3, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_SMALL, PAD_NORMAL))

    def _build_input_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, **card_style())
        panel.grid(row=2, column=0, sticky="nsew", pady=(0, PAD_NORMAL))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="3️⃣ Dados do cálculo",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self._inputs_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self._inputs_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self._inputs_frame.grid_columnconfigure(1, weight=1)

    def _build_result_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, **card_style())
        panel.grid(row=3, column=0, sticky="ew", pady=(0, PAD_NORMAL))
        panel.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="4️⃣ Resultado",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self.result_label = ctk.CTkLabel(
            panel,
            text="Resultado: --",
            text_color=THEME_COLORS["primary"],
            font=FONT_METRIC,
        )
        self.result_label.grid(row=1, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        self.result_hint = ctk.CTkLabel(
            panel,
            text="Este valor representa a energia térmica armazenada no material.",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
        )
        self.result_hint.grid(row=2, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=1, column=1, rowspan=2, sticky="e", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

        self.calculate_btn = ctk.CTkButton(
            actions,
            text="CALCULAR",
            font=FONT_NORMAL,
            command=self.calculate_energy,
            **button_style("primary"),
        )
        self.calculate_btn.grid(row=0, column=0, padx=(0, 0), pady=(0, PAD_SMALL))

        self.save_btn = ctk.CTkButton(
            actions,
            text="SALVAR CÁLCULO",
            font=FONT_NORMAL,
            command=self.save_calculation,
            **button_style("export"),
        )
        self.save_btn.grid(row=1, column=0)

    def _build_guide_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, **card_style())
        panel.grid(row=4, column=0, sticky="ew")
        panel.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="Passo a passo",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        guide = ctk.CTkLabel(
            panel,
            text=(
                "1️⃣ Selecione o experimento\n"
                "2️⃣ Confira os dados carregados automaticamente\n"
                "3️⃣ Clique em calcular\n"
                "4️⃣ Salve o cálculo para análise futura"
            ),
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
            justify="left",
        )
        guide.grid(row=1, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

    def _build_computer_simulator_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, **card_style())
        panel.grid(row=5, column=0, sticky="ew", pady=(PAD_NORMAL, 0))
        panel.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="🆕 Simulação do Computador (PCM)",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self._sim_mode = ctk.StringVar(value="PCM necessário")
        self._sim_mode_toggle = ctk.CTkSegmentedButton(
            panel,
            values=["PCM necessário", "Tempo suportado"],
            variable=self._sim_mode,
            command=self._on_sim_mode_changed,
            font=FONT_NORMAL,
            height=WIDGET_HEIGHT_NORMAL,
        )
        self._sim_mode_toggle.grid(row=1, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

        self._sim_inputs_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self._sim_inputs_frame.grid(row=2, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        self._sim_inputs_frame.grid_columnconfigure(1, weight=1)
        self._sim_entries: dict[str, ctk.CTkEntry] = {}

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        self._sim_btn = ctk.CTkButton(
            actions,
            text="SIMULAR",
            font=FONT_NORMAL,
            command=self._run_computer_simulation,
            **button_style("primary"),
        )
        self._sim_btn.grid(row=0, column=0, padx=(0, PAD_SMALL))

        self._sim_status_label = ctk.CTkLabel(
            actions,
            text="Status: --",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_NORMAL,
        )
        self._sim_status_label.grid(row=0, column=1, padx=(0, PAD_SMALL))

        self._sim_result_label = ctk.CTkLabel(
            panel,
            text="Energia: --\nResultado: --",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
            justify="left",
        )
        self._sim_result_label.grid(row=4, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

        self._build_sim_inputs(self._sim_mode.get())

    def _on_sim_mode_changed(self, _value: str | None = None) -> None:
        self._build_sim_inputs(self._sim_mode.get())

    def _build_sim_inputs(self, mode: str) -> None:
        for widget in list(self._sim_inputs_frame.winfo_children()):
            widget.destroy()
        self._sim_entries.clear()

        row = 0
        row = self._sim_field(self._sim_inputs_frame, row, "power_w", "Potência (W)", "Ex.: 65")
        if mode == "Tempo suportado":
            row = self._sim_field(self._sim_inputs_frame, row, "mass_g", "Massa de PCM (g)", "Ex.: 250")
        else:
            row = self._sim_field(self._sim_inputs_frame, row, "time_min", "Tempo desejado (min)", "Ex.: 30")

        hint = ctk.CTkLabel(
            self._sim_inputs_frame,
            text="Usa calor específico fixo de 2.0 kJ/kg·°C (modelo de referência térmica).",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_SMALL,
            justify="left",
        )
        hint.grid(row=row, column=0, columnspan=2, sticky="w", pady=(PAD_SMALL, 0))

    def _sim_field(self, parent, row: int, key: str, label: str, placeholder: str) -> int:
        lbl = ctk.CTkLabel(parent, text=label, text_color=THEME_COLORS["text_secondary"], font=FONT_LABEL)
        lbl.grid(row=row, column=0, sticky="w", pady=(0, PAD_SMALL))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=WIDGET_HEIGHT_NORMAL, font=FONT_NORMAL)
        entry.grid(row=row, column=1, sticky="ew", padx=(PAD_LARGE, 0), pady=(0, PAD_SMALL))
        self._sim_entries[key] = entry
        return row + 1

    def _read_sim_float(self, key: str) -> float:
        value = self._sim_entries[key].get().strip().replace(",", ".")
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"Valor inválido para {key}.") from exc

    def _run_computer_simulation(self) -> None:
        try:
            power_w = self._read_sim_float("power_w")
            mode = self._sim_mode.get()
            if mode == "Tempo suportado":
                mass_g = self._read_sim_float("mass_g")
                result = self.controller.simulate_pcm_computer("time_supported", power_w, None, mass_g)
                extra = f"Tempo suportado: {float(result['time_supported']):.2f} min"
            else:
                time_min = self._read_sim_float("time_min")
                result = self.controller.simulate_pcm_computer("pcm_needed", power_w, time_min, None)
                extra = f"Massa PCM necessária: {float(result['pcm_mass']):.2f} g"
        except ValueError as exc:
            messagebox.showerror("Dados inválidos", str(exc), parent=self.winfo_toplevel())
            return
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erro", f"Falha na simulação: {exc}", parent=self.winfo_toplevel())
            return

        energy = float(result["energy"])
        status = str(result["status"])
        status_color = THEME_COLORS["export"] if status == "estável" else THEME_COLORS["danger"]

        self._sim_status_label.configure(text=f"Status: {status}", text_color=status_color)
        self._sim_result_label.configure(text=f"Energia total: {energy:.2f} J\n{extra}")

    # --- Dados ------------------------------------------------------------
    def load_experiment_data(self) -> None:
        self._experiment_rows = self.controller.list_experiments()
        options = []
        self._experiment_map.clear()

        for row in self._experiment_rows:
            label = f"#{row['id']} - {row.get('material') or 'Sem material'}"
            options.append(label)
            self._experiment_map[label] = row

        if not options:
            options = ["Nenhum experimento"]
            self._experiment_map[options[0]] = None

        self.experiment_combo["values"] = options
        self.experiment_combo.current(0)
        self._on_experiment_selected()

    def _on_experiment_selected(self) -> None:
        label = self.experiment_combo.get()
        self._selected_experiment = self._experiment_map.get(label)
        experiment_id = self._selected_experiment.get("id") if self._selected_experiment else None
        self.controller.set_current_experiment_id(experiment_id)
        self._prefill_inputs()

    def _on_calc_selected(self) -> None:
        self._build_inputs(self.calc_type.get())

    def _build_inputs(self, calc_type: str) -> None:
        for widget in list(self._inputs_frame.winfo_children()):
            widget.destroy()
        self._entries.clear()

        definition = CALCULATION_DEFS[calc_type]
        self.formula_label.configure(text=definition["formula"])
        self.where_label.configure(text=definition["where"])
        self.explain_label.configure(text=definition["explain"])

        row = 0
        for field in definition["fields"]:
            lbl = ctk.CTkLabel(self._inputs_frame, text=field.label, text_color=THEME_COLORS["text_secondary"], font=FONT_LABEL)
            lbl.grid(row=row, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_SMALL, PAD_SMALL))
            entry = ctk.CTkEntry(
                self._inputs_frame,
                placeholder_text=field.placeholder,
                height=WIDGET_HEIGHT_NORMAL,
                font=FONT_NORMAL,
            )
            entry.grid(row=row, column=1, sticky="ew", padx=PAD_LARGE, pady=(PAD_SMALL, PAD_SMALL))
            self._entries[field.key] = entry
            row += 1

        self._prefill_inputs()

    def _prefill_inputs(self) -> None:
        if not self._entries:
            return
        experiment = self._selected_experiment
        if not experiment:
            return

        calc_type = self.calc_type.get()
        prefill = self.controller.get_prefill_values(experiment, calc_type)
        for key, value in prefill.items():
            if key not in self._entries:
                continue
            self._entries[key].delete(0, "end")
            self._entries[key].insert(0, str(value))

    # --- Cálculos ---------------------------------------------------------
    def _read_float(self, key: str) -> float:
        value = self._entries[key].get().strip().replace(",", ".")
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"Valor inválido para {key}.") from exc

    def calculate_energy(self) -> None:
        self._calculate_current()

    def calculate_specific_heat(self) -> None:
        self._calculate_current()

    def _calculate_current(self) -> None:
        calc_type = self.calc_type.get()
        definition = CALCULATION_DEFS[calc_type]

        try:
            values = {field.key: self._read_float(field.key) for field in definition["fields"]}
        except ValueError as exc:
            messagebox.showerror("Dados inválidos", str(exc), parent=self.winfo_toplevel())
            return

        try:
            result = float(self.controller.calculate_thermal(calc_type, values))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erro", f"Falha ao calcular: {exc}", parent=self.winfo_toplevel())
            return
        self._last_result = result
        self._last_calc_type = calc_type

        unit = definition.get("unit", "J")
        self.result_label.configure(text=f"{definition['result_label']}: {result:.3f} {unit}")
        referencia = "Este cálculo utiliza um material de referência térmica com calor específico constante."
        if calc_type == "Calor Latente":
            base = "Este valor representa a energia envolvida na mudança de fase do material."
        else:
            base = "Este valor representa a energia térmica armazenada no material."
        self.result_hint.configure(text=f"{base}\n\n{referencia}")

    def save_calculation(self) -> None:
        if not self._selected_experiment:
            messagebox.showwarning("Seleção", "Selecione um experimento.", parent=self.winfo_toplevel())
            return
        if self._last_result is None or self._last_calc_type is None:
            messagebox.showwarning("Calcular", "Execute o cálculo antes de salvar.", parent=self.winfo_toplevel())
            return

        experiment_id = self._selected_experiment.get("id")
        if experiment_id is None:
            return

        try:
            inputs = {k: self._try_get_value(k) for k in ("m", "delta_t", "l")}
            calc_id = self.controller.save_thermal_calculation(
                experimento_id=int(experiment_id),
                tipo_calculo=self._last_calc_type,
                inputs=inputs,
                resultado=float(self._last_result),
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erro", f"Falha ao salvar cálculo: {exc}", parent=self.winfo_toplevel())
            return

        self.update_dashboard_metrics()
        messagebox.showinfo("Salvo", f"Cálculo salvo com sucesso (ID {calc_id}).", parent=self.winfo_toplevel())

    def update_dashboard_metrics(self) -> None:
        if self._on_calculation_saved is None:
            return
        if not self.winfo_exists():
            return
        if self._dashboard_refresh_scheduled:
            return

        self._dashboard_refresh_scheduled = True

        def _fire() -> None:
            self._dashboard_refresh_scheduled = False
            if not self.winfo_exists():
                return
            if self._on_calculation_saved is not None:
                self._on_calculation_saved()

        # Evita refresh em cascata no meio do fluxo de UI.
        try:
            self.after_idle(_fire)
        except Exception:
            self._dashboard_refresh_scheduled = False

    def _try_get_value(self, key: str) -> float | None:
        if key not in self._entries:
            return None
        value = self._entries[key].get().strip().replace(",", ".")
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _configure_ttk_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "TCombobox",
            fieldbackground=THEME_COLORS["bg"],
            background=THEME_COLORS["card"],
            foreground=THEME_COLORS["text_primary"],
            bordercolor=THEME_COLORS["border"],
            arrowcolor=THEME_COLORS["primary"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", THEME_COLORS["bg"])],
            foreground=[("readonly", THEME_COLORS["text_primary"])],
        )


class ThermalCalculationsPage(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        db_manager: DatabaseManager | None = None,
        on_calculation_saved=None,
    ) -> None:
        # UI REFATORADA: header com botões padrão
        super().__init__(parent, fg_color=THEME_COLORS["bg"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        if db_manager is None:
            db_manager = DatabaseManager()
        self.db = db_manager
        self._on_calculation_saved = on_calculation_saved

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_LARGE, pady=(PAD_SMALL, 0))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)
        header.grid_columnconfigure(2, weight=0)

        open_btn = ctk.CTkButton(
            header,
            text="Abrir em nova janela",
            font=FONT_NORMAL,
            command=self._open_window,
            **button_style("neutral"),
        )
        open_btn.grid(row=0, column=2, sticky="e", padx=(PAD_SMALL, 0))

        db_btn = ctk.CTkButton(
            header,
            text="Consultar Banco de Dados",
            font=FONT_NORMAL,
            command=self.open_database_window,
            **button_style("neutral"),
        )
        db_btn.grid(row=0, column=1, sticky="e")

        self.panel = ThermalCalculationsPanel(self, db_manager=self.db, on_calculation_saved=self._handle_calculation_saved)
        self.panel.grid(row=1, column=0, sticky="nsew")

    def _open_window(self) -> None:
        win = ctk.CTkToplevel(self)
        win.title("Cálculos Térmicos")
        win.geometry("860x820")
        panel = ThermalCalculationsPanel(win, db_manager=self.db, on_calculation_saved=self._handle_calculation_saved)
        panel.pack(fill="both", expand=True)

    def _handle_calculation_saved(self) -> None:
        if self._on_calculation_saved is not None:
            self._on_calculation_saved()

    def open_database_window(self) -> None:
        win = ctk.CTkToplevel(self)
        win.title("Banco de Dados — PCM Thermal Manager")
        win.geometry("980x720")

        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True)

        materials_tab = MaterialsView(notebook)
        notebook.add(materials_tab, text="Materiais")

        experiments_tab = DatabaseTab(notebook, db_manager=self.db)
        notebook.add(experiments_tab, text="Experimentos")
        experiments_tab.load_experiments()

        calculations_tab = DatabaseTab(notebook, db_manager=self.db)
        notebook.add(calculations_tab, text="Cálculos")
        calculations_tab.view_selector.set("Cálculos térmicos")
        calculations_tab._on_view_changed("Cálculos térmicos")
