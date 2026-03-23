from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk

from database.database_manager import DatabaseManager
from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    FONT_SMALL,
    WIDGET_HEIGHT_NORMAL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
    THEME_COLORS,
)


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
        super().__init__(parent, fg_color=THEME_COLORS["bg"])
        self.db = db_manager
        self.on_edit_requested = on_edit_requested
        self._search_after_id: str | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Banco de Dados",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(6, PAD_NORMAL))

        controls = ctk.CTkFrame(self, fg_color=THEME_COLORS["card"], corner_radius=18)
        controls.grid(row=1, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        controls.grid_columnconfigure(0, weight=0)
        controls.grid_columnconfigure(1, weight=1)
        controls.grid_columnconfigure(2, weight=0)
        controls.grid_columnconfigure(3, weight=0)

        self.view_selector = ctk.CTkSegmentedButton(
            controls,
            values=["Experimentos", "Cálculos térmicos"],
            font=FONT_NORMAL,
            height=WIDGET_HEIGHT_NORMAL,
            command=self._on_view_changed,
        )
        self.view_selector.grid(row=0, column=0, sticky="w", padx=(PAD_LARGE, PAD_SMALL), pady=PAD_NORMAL)
        self.view_selector.set("Experimentos")

        self.search_entry = ctk.CTkEntry(
            controls,
            placeholder_text="Buscar por operador, material, cápsula, experimento ou data",
            height=WIDGET_HEIGHT_NORMAL,
            font=FONT_NORMAL,
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, PAD_SMALL), pady=PAD_NORMAL)
        self.search_entry.bind("<KeyRelease>", self._on_search_keyrelease)

        self.btn_refresh = ctk.CTkButton(
            controls,
            text="🔄 Atualizar",
            corner_radius=10,
            height=WIDGET_HEIGHT_NORMAL,
            fg_color=THEME_COLORS["card_soft"],
            text_color=THEME_COLORS["text_primary"],
            hover_color=THEME_COLORS["border"],
            width=130,
            font=FONT_NORMAL,
            command=self.refresh_current_view,
        )
        self.btn_refresh.grid(row=0, column=2, padx=(0, PAD_SMALL), pady=PAD_NORMAL)

        self.btn_clear = ctk.CTkButton(
            controls,
            text="🧹 Limpar busca",
            corner_radius=10,
            height=WIDGET_HEIGHT_NORMAL,
            fg_color=THEME_COLORS["card_soft"],
            text_color=THEME_COLORS["text_primary"],
            hover_color=THEME_COLORS["border"],
            width=140,
            font=FONT_NORMAL,
            command=self.clear_search,
        )
        self.btn_clear.grid(row=0, column=3, padx=(0, PAD_LARGE), pady=PAD_NORMAL)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="nw", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        self.btn_edit = ctk.CTkButton(
            actions,
            text="Editar",
            corner_radius=10,
            height=WIDGET_HEIGHT_NORMAL,
            fg_color=THEME_COLORS["card_soft"],
            text_color=THEME_COLORS["text_primary"],
            hover_color=THEME_COLORS["border"],
            width=110,
            font=FONT_NORMAL,
            command=self.edit_selected_experiment,
        )
        self.btn_edit.grid(row=0, column=0, padx=(0, PAD_SMALL))

        self.btn_delete = ctk.CTkButton(
            actions,
            text="Deletar",
            corner_radius=10,
            height=WIDGET_HEIGHT_NORMAL,
            fg_color=THEME_COLORS["card_soft"],
            text_color=THEME_COLORS["text_primary"],
            hover_color=THEME_COLORS["border"],
            width=110,
            font=FONT_NORMAL,
            command=self.delete_selected_experiment,
        )
        self.btn_delete.grid(row=0, column=1)

        table_frame = ctk.CTkFrame(self, fg_color=THEME_COLORS["card"], corner_radius=18)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=PAD_LARGE, pady=(0, PAD_LARGE))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self._setup_treeview_style()

        self.tree = ttk.Treeview(table_frame, columns=EXPERIMENT_COLUMNS, show="headings", style="PCM.Treeview")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=PAD_NORMAL, pady=PAD_NORMAL)
        self._configure_tree_columns(EXPERIMENT_COLUMNS)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=PAD_NORMAL)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", lambda _e: self.edit_selected_experiment())
        self._current_view = "experimentos"

    def _setup_treeview_style(self) -> None:
        style = ttk.Style()
        style.configure(
            "PCM.Treeview",
            background=THEME_COLORS["card"],
            fieldbackground=THEME_COLORS["card"],
            foreground=THEME_COLORS["text_primary"],
            rowheight=32,
            borderwidth=0,
        )
        style.configure(
            "PCM.Treeview.Heading",
            background=THEME_COLORS["bg"],
            foreground=THEME_COLORS["text_secondary"],
            font=FONT_SMALL,
        )
        style.map("PCM.Treeview", background=[("selected", THEME_COLORS["accent_soft"])])

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
        query = self.search_entry.get().strip()
        rows = self.db.search_experiments_flexible(query)
        self.refresh_treeview(rows)

    def _on_search_keyrelease(self, _event=None) -> None:
        if self._current_view != "experimentos":
            return
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(200, self.search_experiment)

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
        self.search_entry.configure(state=state)
        self.btn_clear.configure(state=state)
        self.btn_edit.configure(state=state)
        self.btn_delete.configure(state=state)

    def refresh_current_view(self) -> None:
        if self._current_view == "experimentos":
            self.clear_search()
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

    def clear_search(self) -> None:
        if self._current_view != "experimentos":
            return
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
            self._search_after_id = None
        self.search_entry.delete(0, "end")
        self.load_experiments()
