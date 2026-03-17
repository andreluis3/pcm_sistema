from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk

from database.database_manager import DatabaseManager


TREE_COLUMNS: tuple[str, ...] = (
    "id",
    "date",
    "material",
    "temperatura_final",
    "energia_armazenada",
    "eficiencia",
    "operador",
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
        controls.grid_columnconfigure(0, weight=1)

        self.search_material = ctk.CTkEntry(controls, placeholder_text="Material (contém...)")
        self.search_material.grid(row=0, column=0, sticky="ew", padx=(16, 8), pady=12)

        self.search_date = ctk.CTkEntry(controls, placeholder_text="Data (YYYY-MM-DD)")
        self.search_date.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=12)

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
        btn_search.grid(row=0, column=2, padx=(0, 8), pady=12)

        btn_refresh = ctk.CTkButton(
            controls,
            text="Atualizar Tabela",
            corner_radius=10,
            fg_color="#1E2530",
            text_color="#E5E7EB",
            hover_color="#2A3341",
            width=140,
            command=self.load_experiments,
        )
        btn_refresh.grid(row=0, column=3, padx=(0, 16), pady=12)

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

        self.tree = ttk.Treeview(table_frame, columns=TREE_COLUMNS, show="headings", style="PCM.Treeview")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        headings = {
            "id": "ID",
            "date": "Data",
            "material": "Material",
            "temperatura_final": "T final (°C)",
            "energia_armazenada": "Energia (J)",
            "eficiencia": "Eficiência (%)",
            "operador": "Operador",
        }
        for col in TREE_COLUMNS:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=120, anchor="w")
        self.tree.column("id", width=70, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=12)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", lambda _e: self.edit_selected_experiment())

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
        self.refresh_treeview(rows)

    def refresh_treeview(self, experiments: list[Any]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in experiments:
            values = (
                r["id"],
                r["date"],
                r["material"],
                r["temperatura_final"],
                r["energia_armazenada"],
                r["eficiencia"],
                r["operador"],
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
        material = self.search_material.get().strip() or None
        date = self.search_date.get().strip() or None

        rows = self.db.search_experiments(material=material, date=date)
        self.refresh_treeview(rows)

    def delete_selected_experiment(self) -> None:
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

