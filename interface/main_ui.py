import customtkinter as ctk
from .view.sidebar import Sidebar
from .dashboard_tab import DashboardTab
from .view.sensor_page import SensorPage
from ui.materials_view import MaterialsView
from .view.experiments import ExperimentsPage
from .view.database_page import DatabasePage
from .view.export_page import ExportPage
from .view.thermal_calculations_page import ThermalCalculationsPage

from services.sensor_service import SensorService  # Versão modular com callback
from database.database_manager import DatabaseManager
from ui_styles import FONT_SMALL, PAD_LARGE, PAD_NORMAL


class MainUI(ctk.CTk):
    def __init__(self, username: str = "Usuário"):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.geometry("1280x760")
        self.title("PCM Thermal Manager")
        self.username = username

        self._current_page = None
        self._dashboard_ref = None

        # === Layout principal ===
        self._build_layout()

        # === SensorService modular com callback para atualizar status ===
        self.sensor_service = SensorService(self.update_status)
        self.sensor_service.start(self)  # self = root, necessário para after()

        # === Banco de dados ===
        self.db_manager = DatabaseManager()

        # === Carrega o dashboard após login ===
        self.load_page("dashboard")

    def _build_layout(self):
        # Configurações de grid do MainUI
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar fixa
        self.sidebar = Sidebar(self, self.load_page)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        # Área de conteúdo
        self.content = ctk.CTkFrame(self, fg_color="#0D1117")
        self.content.grid(row=0, column=1, sticky="nsew", padx=PAD_LARGE, pady=PAD_LARGE)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Barra de status
        self.status_bar = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text=f"Sensor: Desconectado | Usuário: {self.username} | Banco: Ativo",
            text_color="#E5E7EB",
            font=FONT_SMALL
        )
        self.status_label.pack(padx=PAD_LARGE, pady=PAD_NORMAL)

        # Páginas do sistema
        self.pages = {
            "dashboard": DashboardTab,
            "sensor": SensorPage,
            "materiais": MaterialsView,
            "experimentos": ExperimentsPage,
            "calculos": ThermalCalculationsPage,
            "banco": DatabasePage,
            "exportar": ExportPage,
        }

    # Callback para atualizar a barra de status
    def update_status(self, temp):
        self.status_label.configure(
            text=f"Sensor: Conectado | Última Temp: {temp:.1f} °C | Usuário: {self.username} | Banco: Ativo"
        )

    # Carrega uma página no content frame
    def load_page(self, page_name: str):
        if self._current_page is not None:
            self._current_page.destroy()

        page_class = self.pages.get(page_name)
        if page_class is None:
            return

        if page_name == "experimentos":
            self._current_page = page_class(
                self.content,
                db_manager=self.db_manager,
                on_experiment_saved=self._handle_experiment_saved,
            )
        elif page_name == "calculos":
            self._current_page = page_class(
                self.content,
                db_manager=self.db_manager,
                on_calculation_saved=self._handle_calculation_saved,
            )
        else:
            try:
                self._current_page = page_class(self.content, db_manager=self.db_manager)
            except TypeError:
                self._current_page = page_class(self.content)

        if page_name == "dashboard":
            self._dashboard_ref = self._current_page
        self._current_page.grid(row=0, column=0, sticky="nsew")
        self.sidebar.set_active(page_name)

        if hasattr(self._current_page, "load_dashboard_data"):
            self._current_page.load_dashboard_data()

    def _handle_experiment_saved(self) -> None:
        if self._dashboard_ref is not None and hasattr(self._dashboard_ref, "load_dashboard_data"):
            self._dashboard_ref.load_dashboard_data()

    def _handle_calculation_saved(self) -> None:
        if self._dashboard_ref is not None and hasattr(self._dashboard_ref, "load_dashboard_data"):
            self._dashboard_ref.load_dashboard_data()
