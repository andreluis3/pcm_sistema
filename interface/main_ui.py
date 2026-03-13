import customtkinter as ctk
from interface.view.login_page import LoginPage
from interface.view.sidebar import Sidebar
from interface.view.dashboard import DashboardPage
from interface.view.sensor_page import SensorPage
from interface.view.manual_measurement import ManualMeasurementPage
from interface.view.materials import MaterialsPage
from interface.view.experiments import ExperimentsPage
from interface.view.database_page import DatabasePage
from view.export_page import ExportPage


class MainUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.geometry("1280x760")
        self.title("PCM Thermal Manager")

        self._current_page = None
        self.show_login()

    def show_login(self):
        self.login_page = LoginPage(self, self.show_dashboard)

    def show_dashboard(self):
        self.login_page.destroy()
        self._build_layout()
        self.load_page("dashboard")

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, self.load_page)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ctk.CTkFrame(self, fg_color="#0D1117")
        self.content.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.status_bar = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Sensor: Conectado | Usuário: Andre | Banco: Ativo",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(padx=16, pady=8)

        self.pages = {
            "dashboard": DashboardPage,
            "sensor": SensorPage,
            "medicao": ManualMeasurementPage,
            "materiais": MaterialsPage,
            "experimentos": ExperimentsPage,
            "banco": DatabasePage,
            "exportar": ExportPage,
        }

    def load_page(self, page_name: str):
        if self._current_page is not None:
            self._current_page.destroy()

        page_class = self.pages.get(page_name)
        if page_class is None:
            return

        self._current_page = page_class(self.content)
        self._current_page.grid(row=0, column=0, sticky="nsew")
        self.sidebar.set_active(page_name)
