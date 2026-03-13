import customtkinter as ctk
from .view.login_page import LoginPage
from .view.sidebar import Sidebar
from .view.dashboard import DashboardPage
from .view.sensor_page import SensorPage
from .view.manual_measurement import ManualMeasurementPage
from .view.materials import MaterialsPage
from .view.experiments import ExperimentsPage
from .view.database_page import DatabasePage
from .view.export_page import ExportPage

from services.sensor_service import SensorService  # Versão modular com callback


class MainUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.geometry("1280x760")
        self.title("PCM Thermal Manager")

        self._current_page = None

        # === Layout principal ===
        self._build_layout()

        # === SensorService modular com callback para atualizar status ===
        self.sensor_service = SensorService(self.update_status)
        self.sensor_service.start(self)  # self = root, necessário para after()

        # === Mostra a tela de login ===
        self.show_login()

    def _build_layout(self):
        # Configurações de grid do MainUI
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar fixa
        self.sidebar = Sidebar(self, self.load_page)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        # Área de conteúdo
        self.content = ctk.CTkFrame(self, fg_color="#0D1117")
        self.content.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Barra de status
        self.status_bar = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Sensor: Desconectado | Usuário: Andre | Banco: Ativo",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(padx=16, pady=8)

        # Páginas do sistema
        self.pages = {
            "dashboard": DashboardPage,
            "sensor": SensorPage,
            "medicao": ManualMeasurementPage,
            "materiais": MaterialsPage,
            "experimentos": ExperimentsPage,
            "banco": DatabasePage,
            "exportar": ExportPage,
        }

    # Callback para atualizar a barra de status
    def update_status(self, temp):
        self.status_label.configure(
            text=f"Sensor: Conectado | Última Temp: {temp:.1f} °C | Usuário: Andre | Banco: Ativo"
        )

    # Mostra a tela de login
    def show_login(self):
        self.login_page = LoginPage(self.content, self.show_dashboard)

    # Ao fazer login, destrói a página de login e abre o dashboard
    def show_dashboard(self):
        if self.login_page is not None:
            self.login_page.destroy()
        self.load_page("dashboard")

    # Carrega uma página no content frame
    def load_page(self, page_name: str):
        if self._current_page is not None:
            self._current_page.destroy()

        page_class = self.pages.get(page_name)
        if page_class is None:
            return

        self._current_page = page_class(self.content)
        self._current_page.grid(row=0, column=0, sticky="nsew")
        self.sidebar.set_active(page_name)