from interface.loading_screen import LoadingScreen
from interface.login_window import LoginWindow
from interface.main_ui import MainUI


def main() -> None:
    loading = LoadingScreen()
    loading.mainloop()

    login = LoginWindow()
    login.mainloop()

    if not login.logged_in:
        return

    app = MainUI(username=login.username or "Usuário")
    app.mainloop()



if __name__ == "__main__":
    main()
