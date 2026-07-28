import multiprocessing
import threading
import time
import tkinter as tk

import customtkinter as ctk
import uvicorn

from backend.main_api_completo import app as fastapi_app

from interface.loading_screen import LoadingScreen
from interface.login_window import LoginWindow
from interface.main_ui import MainUI
from interface.welcome_screen import WelcomeScreen

from utils.user_session import load_user
from utils.paths import resource_path


# ==========================================
# CONFIGURAÇÃO HIDPI
# ==========================================
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

    except Exception as e:
        print(f"[HIDPI] Erro ao configurar scaling: {e}")

    ctk.set_widget_scaling(scaling)
    ctk.set_window_scaling(scaling)


# ==========================================
# INICIALIZA API FASTAPI
# ==========================================
def start_api():

    try:

        print("[API] Iniciando servidor FastAPI...")

        uvicorn.run(
            fastapi_app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            access_log=False
        )

    except Exception as e:
        print(f"[API] Erro ao iniciar API: {e}")


# ==========================================
# THREAD DA API
# ==========================================
def start_api_thread():

    api_thread = threading.Thread(
        target=start_api,
        daemon=True
    )

    api_thread.start()

    # tempo para API subir
    time.sleep(2)

    print("[API] API iniciada com sucesso.")


# ==========================================
# CRIA JANELA PRINCIPAL
# ==========================================
def create_main_window(username: str):

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()

    root.title("Gerenciador Térmico de PCM")

    # ÍCONE
    try:
        root.iconbitmap(
            resource_path("assets/logo.ico")
        )

    except Exception as e:
        print(f"[UI] Erro ao carregar ícone: {e}")

    # TELA
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    root.geometry(
        f"{int(screen_w * 0.92)}x{int(screen_h * 0.92)}"
    )

    root.minsize(1200, 720)

    # ROOT RESPONSIVO
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # MAIN UI
    app = MainUI(
        root,
        username=username
    )

    app.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    return root


# ==========================================
# MAIN
# ==========================================
def main():

    print("=" * 50)
    print("INICIANDO PCM SYSTEM")
    print("=" * 50)

    # HIDPI
    _configure_hidpi_scaling()

    # INICIA API
    start_api_thread()

    # LOGIN SALVO
    saved_user = load_user()

    # ======================================
    # LOGIN AUTOMÁTICO
    # ======================================
    if saved_user:

        print(f"[LOGIN] Login automático: {saved_user}")

        root = create_main_window(saved_user)

        root.mainloop()

        return

    # ======================================
    # LOGIN
    # ======================================
    print("[LOGIN] Abrindo tela de login...")

    login = LoginWindow()

    login.mainloop()

    if not login.logged_in:

        print("[LOGIN] Login cancelado.")

        return

    # ======================================
    # LOADING
    # ======================================
    print("[SYSTEM] Carregando sistema...")

    loading = LoadingScreen()

    loading.mainloop()

    # ======================================
    # WELCOME
    # ======================================
    print("[SYSTEM] Exibindo welcome screen...")

    welcome = WelcomeScreen(
        username=login.username or "Usuário"
    )

    welcome.mainloop()

    if not welcome.proceed:

        print("[SYSTEM] Entrada cancelada.")

        return

    # ======================================
    # APP PRINCIPAL
    # ======================================
    print("[SYSTEM] Abrindo dashboard principal...")

    root = create_main_window(
        login.username or "Usuário"
    )

    root.mainloop()


# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":

    multiprocessing.freeze_support()

    main()

    print("=" * 50)
    print("APLICAÇÃO ENCERRADA")
    print("=" * 50)