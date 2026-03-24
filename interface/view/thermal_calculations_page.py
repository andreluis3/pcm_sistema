from __future__ import annotations

from dataclasses import dataclass
import customtkinter as ctk
from tkinter import messagebox, ttk

from database.database_manager import DatabaseManager
from interface.database_tab import DatabaseTab
from ui.materials_view import MaterialsView
from ui_styles import (
    FONT_HEADER,
    FONT_TITLE,
    FONT_NORMAL,
    FONT_SMALL,
    FONT_TEMP,
    WIDGET_HEIGHT_NORMAL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
)


@dataclass
class CalculationField:
    key: str
    label: str
    placeholder: str


CALCULATION_DEFS: dict[str, dict] = {
    "Energia Absorvida": {
        "formula": "Q = m × c × ΔT",
        "where": "Onde:\nQ = energia absorvida\nm = massa\nc = calor específico\nΔT = variação de temperatura",
        "explain": "Este cálculo determina a energia necessária para elevar a temperatura sem mudança de fase.",
        "fields": [
            CalculationField("m", "Massa (g)", "Ex.: 100"),
            CalculationField("c", "Calor específico (J/g°C)", "Ex.: 2.1"),
            CalculationField("delta_t", "ΔT (°C)", "Ex.: 29"),
        ],
        "result_label": "Energia absorvida",
        "compute": lambda v: v["m"] * v["c"] * v["delta_t"],
        "unit": "J",
    },
    "Calor Específico": {
        "formula": "c = Q / (m × ΔT)",
        "where": "Onde:\nQ = energia absorvida\nm = massa\nΔT = variação de temperatura",
        "explain": "Este cálculo estima a capacidade térmica do material em absorver calor.",
        "fields": [
            CalculationField("m", "Massa (g)", "Ex.: 100"),
            CalculationField("energia", "Energia (J)", "Ex.: 18000"),
            CalculationField("delta_t", "ΔT (°C)", "Ex.: 29"),
        ],
        "result_label": "Calor específico",
        "compute": lambda v: v["energia"] / (v["m"] * v["delta_t"]) if v["m"] and v["delta_t"] else 0,
        "unit": "J/g°C",
    },
    "Calor Sensível": {
        "formula": "Q = m × c × ΔT",
        "where": "Onde:\nm = massa\nc = calor específico\nΔT = variação de temperatura",
        "explain": "Este cálculo determina a energia absorvida pelo material durante o aquecimento sensível.",
        "fields": [
            CalculationField("m", "Massa (g)", "Ex.: 100"),
            CalculationField("c", "Calor específico (J/g°C)", "Ex.: 2.1"),
            CalculationField("delta_t", "ΔT (°C)", "Ex.: 29"),
        ],
        "result_label": "Calor sensível",
        "compute": lambda v: v["m"] * v["c"] * v["delta_t"],
        "unit": "J",
    },
    "Calor Latente": {
        "formula": "Q = m × L",
        "where": "Onde:\nm = massa\nL = calor latente específico",
        "explain": "Este cálculo estima a energia envolvida na mudança de fase do material.",
        "fields": [
            CalculationField("m", "Massa (g)", "Ex.: 100"),
            CalculationField("l", "Calor latente (J/g)", "Ex.: 180"),
        ],
        "result_label": "Calor latente",
        "compute": lambda v: v["m"] * v["l"],
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
        super().__init__(parent, fg_color="#0D1117")
        self.db = db_manager
        self._on_calculation_saved = on_calculation_saved
        self._experiment_rows: list = []
        self._experiment_map: dict[str, dict] = {}
        self._selected_experiment: dict | None = None
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._last_result: float | None = None
        self._last_calc_type: str | None = None

        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Cálculos Térmicos",
            text_color="#E5E7EB",
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_SMALL, PAD_NORMAL))

        self.create_calculos_frame()
        self.load_experiment_data()
        self._build_inputs(self.calc_type.get())

    # --- Organização principal ------------------------------------------
    def create_calculos_frame(self) -> None:
        self._configure_ttk_style()
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=PAD_LARGE, pady=(0, PAD_LARGE))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(2, weight=1)

        self._build_selection_panel(body)
        self._build_explanation_panel(body)
        self._build_input_panel(body)
        self._build_result_panel(body)
        self._build_guide_panel(body)

    # --- Painéis ---------------------------------------------------------
    def _build_selection_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, fg_color="#141A22", corner_radius=18)
        panel.grid(row=0, column=0, sticky="ew", pady=(0, PAD_NORMAL))
        panel.grid_columnconfigure(1, weight=1)
        panel.grid_columnconfigure(3, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="1️⃣ Seleção do experimento",
            text_color="#E5E7EB",
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, columnspan=4, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        exp_label = ctk.CTkLabel(panel, text="Selecionar Experimento", text_color="#9AA0AB", font=FONT_NORMAL)
        exp_label.grid(row=1, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        self.experiment_combo = ttk.Combobox(panel, state="readonly", values=["Carregando..."])
        self.experiment_combo.grid(row=2, column=0, columnspan=2, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        self.experiment_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_experiment_selected())

        calc_label = ctk.CTkLabel(panel, text="Tipo de cálculo", text_color="#9AA0AB", font=FONT_NORMAL)
        calc_label.grid(row=1, column=2, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        self.calc_type = ctk.StringVar(value="Energia Absorvida")
        self.calc_combo = ttk.Combobox(panel, state="readonly", values=list(CALCULATION_DEFS.keys()), textvariable=self.calc_type)
        self.calc_combo.grid(row=2, column=2, columnspan=2, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        self.calc_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_calc_selected())
        if self.calc_combo["values"]:
            self.calc_combo.current(0)

    def _build_explanation_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, fg_color="#101722", corner_radius=18)
        panel.grid(row=1, column=0, sticky="ew", pady=(0, PAD_NORMAL))
        panel.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="2️⃣ Como este cálculo funciona",
            text_color="#E5E7EB",
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self.formula_label = ctk.CTkLabel(
            panel,
            text="",
            text_color="#00FFFF",
            font=FONT_TITLE,
            justify="left",
        )
        self.formula_label.grid(row=1, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        self.where_label = ctk.CTkLabel(
            panel,
            text="",
            text_color="#C5D1DE",
            font=FONT_NORMAL,
            justify="left",
        )
        self.where_label.grid(row=2, column=0, sticky="w", padx=PAD_LARGE)

        self.explain_label = ctk.CTkLabel(
            panel,
            text="",
            text_color="#9AA0AB",
            font=FONT_NORMAL,
            justify="left",
            wraplength=680,
        )
        self.explain_label.grid(row=3, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_SMALL, PAD_NORMAL))

    def _build_input_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, fg_color="#141A22", corner_radius=18)
        panel.grid(row=2, column=0, sticky="nsew", pady=(0, PAD_NORMAL))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="3️⃣ Dados do cálculo",
            text_color="#E5E7EB",
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self._inputs_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self._inputs_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self._inputs_frame.grid_columnconfigure(1, weight=1)

    def _build_result_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, fg_color="#101722", corner_radius=18)
        panel.grid(row=3, column=0, sticky="ew", pady=(0, PAD_NORMAL))
        panel.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="4️⃣ Resultado",
            text_color="#E5E7EB",
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self.result_label = ctk.CTkLabel(
            panel,
            text="Resultado: --",
            text_color="#00FFFF",
            font=FONT_TITLE,
        )
        self.result_label.grid(row=1, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        self.result_hint = ctk.CTkLabel(
            panel,
            text="Este valor representa a energia térmica armazenada no material.",
            text_color="#9AA0AB",
            font=FONT_NORMAL,
        )
        self.result_hint.grid(row=2, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=1, column=1, rowspan=2, sticky="e", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

        self.calculate_btn = ctk.CTkButton(
            actions,
            text="CALCULAR",
            corner_radius=12,
            height=WIDGET_HEIGHT_NORMAL,
            fg_color="#2563EB",
            text_color="#E5E7EB",
            hover_color="#1D4ED8",
            font=FONT_NORMAL,
            command=self.calculate_energy,
        )
        self.calculate_btn.grid(row=0, column=0, padx=(0, 0), pady=(0, PAD_SMALL))

        self.save_btn = ctk.CTkButton(
            actions,
            text="SALVAR CÁLCULO",
            corner_radius=12,
            height=WIDGET_HEIGHT_NORMAL,
            fg_color="#16A34A",
            text_color="#E5E7EB",
            hover_color="#15803D",
            font=FONT_NORMAL,
            command=self.save_calculation,
        )
        self.save_btn.grid(row=1, column=0)

    def _build_guide_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, fg_color="#141A22", corner_radius=18)
        panel.grid(row=4, column=0, sticky="ew")
        panel.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="Passo a passo",
            text_color="#E5E7EB",
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
            text_color="#9AA0AB",
            font=FONT_NORMAL,
            justify="left",
        )
        guide.grid(row=1, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

    # --- Dados ------------------------------------------------------------
    def load_experiment_data(self) -> None:
        self._experiment_rows = [dict(r) for r in self.db.list_experiments()]
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
            lbl = ctk.CTkLabel(self._inputs_frame, text=field.label, text_color="#9AA0AB", font=FONT_NORMAL)
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

        massa = experiment.get("massa")
        delta_t = experiment.get("delta_temperatura")
        calc_type = self.calc_type.get()
        cached_specific = None
        cached_energy = None
        if experiment.get("id") is not None:
            cached_specific = self.db.get_calculo_by_experimento_tipo(experiment["id"], "Calor Específico")
            cached_energy = self.db.get_calculo_by_experimento_tipo(experiment["id"], "Energia Absorvida")

        if "m" in self._entries and massa is not None:
            self._entries["m"].delete(0, "end")
            self._entries["m"].insert(0, str(massa))
        if "delta_t" in self._entries and delta_t is not None:
            self._entries["delta_t"].delete(0, "end")
            self._entries["delta_t"].insert(0, str(delta_t))
        if cached_specific is not None and "c" in self._entries:
            if cached_specific["calor_especifico"] is not None:
                self._entries["c"].delete(0, "end")
                self._entries["c"].insert(0, str(cached_specific["calor_especifico"]))

        if calc_type == "Calor Específico" and cached_energy is not None and "energia" in self._entries:
            if cached_energy["resultado"] is not None:
                self._entries["energia"].delete(0, "end")
                self._entries["energia"].insert(0, str(cached_energy["resultado"]))

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

        result = float(definition["compute"](values))
        self._last_result = result
        self._last_calc_type = calc_type

        unit = definition.get("unit", "J")
        self.result_label.configure(text=f"{definition['result_label']}: {result:.3f} {unit}")
        if calc_type == "Calor Específico":
            self.result_hint.configure(text="Este valor representa a capacidade térmica do material.")
        else:
            self.result_hint.configure(text="Este valor representa a energia térmica armazenada no material.")

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

        payload = {
            "experimento_id": experiment_id,
            "massa": self._try_get_value("m"),
            "calor_especifico": self._infer_calor_especifico(),
            "delta_t": self._try_get_value("delta_t"),
            "resultado": self._last_result,
            "tipo_calculo": self._last_calc_type,
        }

        try:
            calc_id = self.db.upsert_tabela_calculos(payload)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erro", f"Falha ao salvar cálculo: {exc}", parent=self.winfo_toplevel())
            return

        self.update_dashboard_metrics()
        messagebox.showinfo("Salvo", f"Cálculo salvo com sucesso (ID {calc_id}).", parent=self.winfo_toplevel())

    def update_dashboard_metrics(self) -> None:
        if self._on_calculation_saved is not None:
            self._on_calculation_saved()

    def _infer_calor_especifico(self) -> float | None:
        if self._last_calc_type == "Calor Específico" and self._last_result is not None:
            return self._last_result
        return self._try_get_value("c")

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
            fieldbackground="#0D1117",
            background="#141A22",
            foreground="#E5E7EB",
            bordercolor="#1F2937",
            arrowcolor="#00FFFF",
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#0D1117")],
            foreground=[("readonly", "#E5E7EB")],
        )


class ThermalCalculationsPage(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        db_manager: DatabaseManager | None = None,
        on_calculation_saved=None,
    ) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        if db_manager is None:
            db_manager = DatabaseManager()
        self.db = db_manager
        self._on_calculation_saved = on_calculation_saved

        header = ctk.CTkFrame(self, fg_color="#0D1117")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_LARGE, pady=(PAD_SMALL, 0))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)
        header.grid_columnconfigure(2, weight=0)

        open_btn = ctk.CTkButton(
            header,
            text="Abrir em nova janela",
            height=WIDGET_HEIGHT_NORMAL,
            corner_radius=12,
            fg_color="#1E2530",
            text_color="#E5E7EB",
            hover_color="#2A3341",
            font=FONT_NORMAL,
            command=self._open_window,
        )
        open_btn.grid(row=0, column=2, sticky="e", padx=(PAD_SMALL, 0))

        db_btn = ctk.CTkButton(
            header,
            text="Consultar Banco de Dados",
            height=WIDGET_HEIGHT_NORMAL,
            corner_radius=12,
            fg_color="#1E2530",
            text_color="#E5E7EB",
            hover_color="#2A3341",
            font=FONT_NORMAL,
            command=self.open_database_window,
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
