import customtkinter as ctk
from .view.sidebar import Sidebar
from .dashboard_tab import DashboardTab
from .view.sensor_page import SensorPage
from ui.materials_view import MaterialsView
from .view.experiments import ExperimentsPage
from .view.database_page import DatabasePage
from .view.export_page import ExportPage
from .view.thermal_calculations_page import ThermalCalculationsPage
from pcm_module.pcm_screen import PCMCalcScreen
from services.hybrid_repository import HybridRepository

from database.database_manager import DatabaseManager
from ui_styles import FONT_SMALL, PAD_LARGE, PAD_NORMAL, THEME_COLORS
from utils.user_session import clear_user


class MainUI(ctk.CTk):
    def __init__(self, username: str = "Usuário"):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.geometry("1280x760")
        self.title("PCM Thermal Manager")
        self.username = username

        self.current_screen = None
        self._dashboard_ref = None

        # === Layout principal ===
        self._build_layout()

        # === Banco de dados ===
        self.db_manager = HybridRepository()

        # === Carrega o dashboard após login ===
        self.load_page("dashboard")

    def _build_layout(self):
        # UI REFATORADA: layout principal com padding e cores padronizadas
        # Configurações de grid do MainUI
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar fixa
        self.sidebar = Sidebar(self, self.load_page, user_name=self.username)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.grid_columnconfigure(0, weight=0)  # 🔥 ESSENCIAL

        # Área de conteúdo
        self.main_frame = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg"])
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=PAD_LARGE, pady=PAD_LARGE)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Barra de status
        self.status_bar = ctk.CTkFrame(self, fg_color=THEME_COLORS["card"], corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)
        self.status_bar.grid_columnconfigure(1, weight=0)

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text=f"Sensor: Desconectado | Usuário: {self.username} | Banco: Ativo",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_SMALL
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=PAD_NORMAL)

        self.user_label = ctk.CTkLabel(
            self.status_bar,
            text=f"Usuário: {self.username}",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_SMALL,
        )
        self.user_label.grid(row=0, column=1, sticky="e", padx=(PAD_NORMAL, PAD_NORMAL), pady=PAD_NORMAL)

        self.logout_button = ctk.CTkButton(
            self.status_bar,
            text="Logout",
            width=90,
            command=self.logout,
        )
        self.logout_button.grid(row=0, column=2, sticky="e", padx=(0, PAD_LARGE), pady=PAD_NORMAL)

        # Páginas do sistema
        self.pages = {
            "dashboard": DashboardTab,
            "sensor": SensorPage,
            "materiais": MaterialsView,
            "experimentos": ExperimentsPage,
            "calculos": ThermalCalculationsPage,
            "pcm": PCMCalcScreen,
            "banco": DatabasePage,
            "exportar": ExportPage,
        }

    # Callback para atualizar a barra de status
    def update_status(self, temp):
        try:
            if not self.winfo_exists():
                return

            self.status_label.configure(
                text=f"Sensor: Conectado | Última Temp: {temp:.1f} °C | Usuário: {self.username} | Banco: Ativo"
            )

            self.user_label.configure(text=f"Usuário: {self.username}")

        except Exception as e:
            print("Erro update_status:", e)
        

    # Carrega uma página no content frame
    def load_page(self, page_name: str):
        if self.current_screen is not None:
            self.current_screen.destroy()

        page_class = self.pages.get(page_name)
        if page_class is None:
            return

        if page_name == "pcm":
            self.current_screen = PCMCalcScreen(self.main_frame)
        elif page_name == "experimentos":
            self.current_screen = page_class(
                self.main_frame,
                db_manager=self.db_manager,
                on_experiment_saved=self._handle_experiment_saved,
            )
        elif page_name == "calculos":
            self.current_screen = page_class(
                self.main_frame,
                db_manager=self.db_manager,
                on_calculation_saved=self._handle_calculation_saved,
            )
        else:
            try:
                self.current_screen = page_class(self.main_frame, db_manager=self.db_manager)
            except TypeError:
                self.current_screen = page_class(self.main_frame)

        if page_name == "dashboard":
            self._dashboard_ref = self.current_screen
        self.current_screen.pack(fill="both", expand=True)
        self.sidebar.set_active(page_name)

        if hasattr(self.current_screen, "load_dashboard_data"):
            self.current_screen.load_dashboard_data()

    def _handle_experiment_saved(self) -> None:
        if self._dashboard_ref is not None and hasattr(self._dashboard_ref, "load_dashboard_data"):
            self._dashboard_ref.load_dashboard_data()

    def _handle_calculation_saved(self) -> None:
        if self._dashboard_ref is not None and hasattr(self._dashboard_ref, "load_dashboard_data"):
            self._dashboard_ref.load_dashboard_data()

    def logout(self) -> None:
        clear_user()
        try:
            # REMOVIDO: sensor_service não existe
            # self.sensor_service.stop()
            pass
        except Exception:
            pass

        self.destroy()

        from interface.loading_screen import LoadingScreen
        from interface.login_window import LoginWindow
        from interface.welcome_screen import WelcomeScreen

        login = LoginWindow()
        login.mainloop()

        if not login.logged_in:
            return

        loading = LoadingScreen()
        loading.mainloop()

        welcome = WelcomeScreen(username=login.username or "Usuário")
        welcome.mainloop()

        if not welcome.proceed:
            return

        app = MainUI(username=login.username or "Usuário")
        app.mainloop()
