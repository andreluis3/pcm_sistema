import tkinter as tk
import customtkinter as ctk

from interface.loading_screen import LoadingScreen
from interface.login_window import LoginWindow
from interface.main_ui import MainUI
from interface.welcome_screen import WelcomeScreen

from utils.user_session import load_user
from utils.paths import resource_path


# =========================================================
# CONFIGURAÇÕES GLOBAIS
# =========================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def _configure_hidpi_scaling() -> None:
    """
    Ajusta escala automaticamente para monitores HiDPI.
    """
    scaling = 1.1

    try:
        root = tk.Tk()
        root.withdraw()

        tk_scaling = float(root.tk.call("tk", "scaling"))

        root.destroy()

        if tk_scaling >= 2.0:
            scaling = 1.4

        elif tk_scaling >= 1.5:
            scaling = 1.25

        elif tk_scaling >= 1.25:
            scaling = 1.15

    except Exception as exc:
        print(f"[WARN] Falha ao configurar HiDPI: {exc}")

    ctk.set_widget_scaling(scaling)
    ctk.set_window_scaling(scaling)


# =========================================================
# HANDLER GLOBAL DE ERROS TKINTER
# =========================================================

def handle_bgerror(exc, val, tb):
    """
    Evita crashes silenciosos do Tkinter.
    """
    import traceback

    print("\n[TKINTER ERROR]")
    traceback.print_exception(exc, val, tb)


# =========================================================
# INICIALIZAÇÃO DA APP
# =========================================================

def create_main_app(username: str) -> MainUI:
    """
    Cria a interface principal já configurada.
    """

    app = MainUI(username=username)

    try:
        app.iconbitmap(resource_path("assets/logo.ico"))
    except Exception as exc:
        print(f"[WARN] Não foi possível carregar ícone: {exc}")

    app.report_callback_exception = handle_bgerror

    app.grid_columnconfigure(0, weight=1)
    app.grid_rowconfigure(0, weight=1)

    return app


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    # -----------------------------------------------------
    # Configuração inicial
    # -----------------------------------------------------

    _configure_hidpi_scaling()

    # -----------------------------------------------------
    # Login automático por sessão salva
    # -----------------------------------------------------

    saved_user = load_user()

    if saved_user:

        app = create_main_app(saved_user)

        app.mainloop()

        print("Aplicação encerrada.")
        return

    # -----------------------------------------------------
    # Login manual
    # -----------------------------------------------------

    login = LoginWindow()
    login.mainloop()

    if not login.logged_in:
        print("Login cancelado.")
        return

    username = login.username or "Usuário"

    # -----------------------------------------------------
    # Loading
    # -----------------------------------------------------

    loading = LoadingScreen()
    loading.mainloop()

    # -----------------------------------------------------
    # Welcome screen
    # -----------------------------------------------------

    welcome = WelcomeScreen(username=username)
    welcome.mainloop()

    if not welcome.proceed:
        print("Acesso cancelado na tela de boas-vindas.")
        return

    # -----------------------------------------------------
    # App principal
    # -----------------------------------------------------

    app = create_main_app(username)

    app.mainloop()

    print("Aplicação encerrada.")


# =========================================================
# ENTRYPOINT
# =========================================================

if __name__ == "__main__":
    main()