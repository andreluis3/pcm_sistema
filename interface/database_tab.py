from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk

from database.database_manager import DatabaseManager


EXPERIMENT_COLUMNS: tuple[str, ...] = (
    "id",
    "date_created",
    "material",
    "tempo_inicio",
    "tempo_final",
    "delta_tempo",
    "temperatura_final",
    "delta_temperatura",
    "operador",
)

THERMAL_COLUMNS: tuple[str, ...] = (
    "id",
    "experimento_id",
    "tipo_calculo",
    "massa",
    "calor_especifico",
    "delta_t",
    "resultado",
    "data_calculo",
)


class DatabaseTab(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        db_manager: DatabaseManager,
        on_edit_requested: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.db = db_manager
        self.on_edit_requested = on_edit_requested

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Banco de Dados",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(6, 12))

        controls = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        controls.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        controls.grid_columnconfigure(1, weight=1)
        controls.grid_columnconfigure(2, weight=1)

        self.view_selector = ctk.CTkSegmentedButton(
            controls,
            values=["Experimentos", "Cálculos térmicos"],
            command=self._on_view_changed,
        )
        self.view_selector.grid(row=0, column=0, sticky="w", padx=(16, 8), pady=12)
        self.view_selector.set("Experimentos")

        self.search_material = ctk.CTkEntry(controls, placeholder_text="Material (contém...)")
        self.search_material.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=12)

        self.search_date = ctk.CTkEntry(controls, placeholder_text="Data (DD-MM-YY)")
        self.search_date.grid(row=0, column=2, sticky="ew", padx=(0, 8), pady=12)

        btn_search = ctk.CTkButton(
            controls,
            text="Buscar",
            corner_radius=10,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
            width=110,
            command=self.search_experiment,
        )
        btn_search.grid(row=0, column=3, padx=(0, 8), pady=12)
        self.btn_search = btn_search

        btn_refresh = ctk.CTkButton(
            controls,
            text="Atualizar Tabela",
            corner_radius=10,
            fg_color="#1E2530",
            text_color="#E5E7EB",
            hover_color="#2A3341",
            width=140,
            command=self.refresh_current_view,
        )
        btn_refresh.grid(row=0, column=4, padx=(0, 16), pady=12)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="nw", padx=16, pady=(0, 10))

        self.btn_edit = ctk.CTkButton(
            actions,
            text="Editar",
            corner_radius=10,
            fg_color="#1E2530",
            text_color="#E5E7EB",
            hover_color="#2A3341",
            width=110,
            command=self.edit_selected_experiment,
        )
        self.btn_edit.grid(row=0, column=0, padx=(0, 8))

        self.btn_delete = ctk.CTkButton(
            actions,
            text="Deletar",
            corner_radius=10,
            fg_color="#1E2530",
            text_color="#E5E7EB",
            hover_color="#2A3341",
            width=110,
            command=self.delete_selected_experiment,
        )
        self.btn_delete.grid(row=0, column=1)

        table_frame = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self._setup_treeview_style()

        self.tree = ttk.Treeview(table_frame, columns=EXPERIMENT_COLUMNS, show="headings", style="PCM.Treeview")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self._configure_tree_columns(EXPERIMENT_COLUMNS)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=12)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", lambda _e: self.edit_selected_experiment())
        self._current_view = "experimentos"

    def _setup_treeview_style(self) -> None:
        style = ttk.Style()
        style.configure(
            "PCM.Treeview",
            background="#161B22",
            fieldbackground="#161B22",
            foreground="#E5E7EB",
            rowheight=28,
            borderwidth=0,
        )
        style.configure(
            "PCM.Treeview.Heading",
            background="#0F141C",
            foreground="#9AA0AB",
            font=("Segoe UI", 9, "bold"),
        )
        style.map("PCM.Treeview", background=[("selected", "#18212B")])

    def load_experiments(self) -> None:
        rows = self.db.list_experiments()
        if self._current_view != "experimentos":
            return
        self.refresh_treeview(rows)

    def load_calculations(self) -> None:
        rows = self.db.list_tabela_calculos()
        if self._current_view == "experimentos":
            return
        self.refresh_treeview(rows)

    def refresh_treeview(self, rows: list[Any]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self._current_view == "experimentos":
            for r in rows:
                values = (
                    r["id"],
                    r["date_created"],
                    r["material"],
                    r["tempo_inicio"],
                    r["tempo_final"],
                    r["delta_tempo"],
                    r["temperatura_final"],
                    r["delta_temperatura"],
                    r["operador"],
                )
                self.tree.insert("", "end", values=values)
        else:
            for r in rows:
                values = (
                    r["id"],
                    r["experimento_id"],
                    r["tipo_calculo"],
                    r["massa"],
                    r["calor_especifico"],
                    r["delta_t"],
                    r["resultado"],
                    r["data_calculo"],
                )
                self.tree.insert("", "end", values=values)

    def _get_selected_id(self) -> int | None:
        selected = self.tree.selection()
        if not selected:
            return None
        values = self.tree.item(selected[0], "values")
        if not values:
            return None
        try:
            return int(values[0])
        except (ValueError, TypeError):
            return None

    def search_experiment(self) -> None:
        if self._current_view != "experimentos":
            return
        material = self.search_material.get().strip() or None
        date = self._normalize_date(self.search_date.get().strip()) or None

        rows = self.db.search_experiments(material=material, date=date)
        self.refresh_treeview(rows)

    def delete_selected_experiment(self) -> None:
        if self._current_view != "experimentos":
            return
        experiment_id = self._get_selected_id()
        if experiment_id is None:
            messagebox.showwarning("Seleção", "Selecione um experimento para deletar.", parent=self.winfo_toplevel())
            return

        if not messagebox.askyesno(
            "Confirmar",
            f"Deletar experimento ID {experiment_id}?",
            parent=self.winfo_toplevel(),
        ):
            return

        try:
            self.db.delete_experiment(experiment_id)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Erro", f"Falha ao deletar: {e}", parent=self.winfo_toplevel())
            return

        self.load_experiments()

    def edit_selected_experiment(self) -> None:
        if self._current_view != "experimentos":
            return
        experiment_id = self._get_selected_id()
        if experiment_id is None:
            messagebox.showwarning("Seleção", "Selecione um experimento para editar.", parent=self.winfo_toplevel())
            return

        row = self.db.get_experiment_by_id(experiment_id)
        if row is None:
            messagebox.showerror("Erro", "Experimento não encontrado.", parent=self.winfo_toplevel())
            self.load_experiments()
            return

        if self.on_edit_requested is not None:
            self.on_edit_requested(dict(row))

    def _on_view_changed(self, value: str) -> None:
        if value == "Cálculos térmicos":
            self._current_view = "calculos"
            self._configure_tree_columns(THERMAL_COLUMNS)
            self._set_experiment_controls_enabled(False)
            self.load_calculations()
        else:
            self._current_view = "experimentos"
            self._configure_tree_columns(EXPERIMENT_COLUMNS)
            self._set_experiment_controls_enabled(True)
            self.load_experiments()

    def _set_experiment_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.search_material.configure(state=state)
        self.search_date.configure(state=state)
        self.btn_search.configure(state=state)
        self.btn_edit.configure(state=state)
        self.btn_delete.configure(state=state)

    def refresh_current_view(self) -> None:
        if self._current_view == "experimentos":
            self.load_experiments()
        else:
            self.load_calculations()

    def _configure_tree_columns(self, columns: tuple[str, ...]) -> None:
        self.tree.configure(columns=columns)
        for col in self.tree["columns"]:
            self.tree.heading(col, text="")
            self.tree.column(col, width=120, anchor="w")

        headings = {
            "id": "ID",
            "date_created": "Data",
            "material": "Material",
            "tempo_inicio": "Início",
            "tempo_final": "Fim",
            "delta_tempo": "Δ tempo (min)",
            "temperatura_final": "T final (°C)",
            "delta_temperatura": "Δ T (°C)",
            "operador": "Operador",
            "experimento_id": "Experimento",
            "tipo_calculo": "Tipo",
            "massa": "Massa (g)",
            "calor_especifico": "Calor específico (J/g°C)",
            "delta_t": "ΔT (°C)",
            "resultado": "Resultado",
            "data_calculo": "Data",
        }
        for col in columns:
            self.tree.heading(col, text=headings.get(col, col))
            self.tree.column(col, width=130, anchor="w")
        self.tree.column("id", width=70, anchor="center")

    def _normalize_date(self, value: str) -> str | None:
        if not value:
            return None
        try:
            parsed = datetime.strptime(value, "%d-%m-%y")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            return value
