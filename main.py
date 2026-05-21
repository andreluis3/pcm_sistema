import tkinter as tk
import customtkinter as ctk

from interface.loading_screen import LoadingScreen
from interface.login_window import LoginWindow
from interface.main_ui import MainUI
from interface.welcome_screen import WelcomeScreen
from utils.user_session import load_user
import tkinter as tk
from utils.paths import resource_path


def _configure_hidpi_scaling() -> None:
    """Best-effort HiDPI scaling based on current display DPI."""
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
    except Exception:
        pass

    ctk.set_widget_scaling(scaling)
    ctk.set_window_scaling(scaling)
    
def handle_bgerror(self, msg):
    print("BGERROR tratado:", msg)

    self.report_callback_exception = self.handle_bgerror


def main() -> None:
    _configure_hidpi_scaling()
    saved_user = load_user()

    if saved_user:
        app = MainUI(username=saved_user)
        app.mainloop()
        return

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

    root = tk.Tk()
    root.iconbitmap(resource_path("assets/logo.ico"))

    app = MainUI(username=login.username or "Usuário")
    app.mainloop()

if __name__ == "__main__":
    main()
    print("Aplicação encerrada.")
