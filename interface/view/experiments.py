import customtkinter as ctk
from tkinter import ttk

from database.database_manager import DatabaseManager
from interface.database_tab import DatabaseTab
from interface.experiment_tab import ExperimentTab


class ExperimentsPage(ctk.CTkFrame):
    def __init__(self, parent, db_manager: DatabaseManager | None = None, start_tab: str = "experimentos") -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if db_manager is None:
            db_manager = DatabaseManager()
        self.db = db_manager

        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nsew")

        self.experiment_tab = ExperimentTab(notebook, db_manager=self.db, on_saved=lambda: self.database_tab.load_experiments())
        self.database_tab = DatabaseTab(
            notebook,
            db_manager=self.db,
            on_edit_requested=self._handle_edit_requested,
        )

        notebook.add(self.experiment_tab, text="Experimentos")
        notebook.add(self.database_tab, text="Banco de Dados")

        self._notebook = notebook
        self.database_tab.load_experiments()

        if start_tab == "database":
            notebook.select(self.database_tab)
        else:
            notebook.select(self.experiment_tab)

    def _handle_edit_requested(self, experiment: dict) -> None:
        self.experiment_tab.load_for_edit(experiment)
        self._notebook.select(self.experiment_tab)
