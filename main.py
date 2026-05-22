import tkinter as tk
import customtkinter as ctk

from interface.loading_screen import LoadingScreen
from interface.login_window import LoginWindow
from interface.main_ui import MainUI
from interface.welcome_screen import WelcomeScreen

from utils.user_session import load_user
from utils.paths import resource_path


def _configure_hidpi_scaling():

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


def create_main_window(username: str):

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()

    root.title("Gerenciador Térmico de PCM")

    try:
        root.iconbitmap(resource_path("assets/logo.ico"))
    except Exception:
        pass

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    root.geometry(f"{int(screen_w * 0.92)}x{int(screen_h * 0.92)}")

    root.minsize(1200, 720)

    # ROOT RESPONSIVO
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    app = MainUI(root, username=username)

    app.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    return root


def main():

    _configure_hidpi_scaling()

    saved_user = load_user()

    # LOGIN AUTOMÁTICO
    if saved_user:

        root = create_main_window(saved_user)

        root.mainloop()

        return

    # LOGIN
    login = LoginWindow()
    login.mainloop()

    if not login.logged_in:
        return

    # LOADING
    loading = LoadingScreen()
    loading.mainloop()

    # WELCOME
    welcome = WelcomeScreen(
        username=login.username or "Usuário"
    )

    welcome.mainloop()

    if not welcome.proceed:
        return

    # APP PRINCIPAL
    root = create_main_window(
        login.username or "Usuário"
    )

    root.mainloop()


if __name__ == "__main__":

    main()

    print("Aplicação encerrada.")