import customtkinter as ctk

class LoginPage(ctk.CTkFrame):
    def __init__(self, parent, on_login):
        super().__init__(parent, fg_color="#0D1117")
        self.on_login = on_login

        # Deve usar grid, porque parent usa grid
        self.grid(row=0, column=0, sticky="nsew")

        # Widgets internos podem usar pack dentro do frame
        self.username_label = ctk.CTkLabel(self, text="Usuário")
        self.username_label.pack(pady=10)

        self.username_entry = ctk.CTkEntry(self)
        self.username_entry.pack(pady=10)

        self.password_label = ctk.CTkLabel(self, text="Senha")
        self.password_label.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self, show="*")
        self.password_entry.pack(pady=10)

        self.login_button = ctk.CTkButton(self, text="Login", command=self.login)
        self.login_button.pack(pady=20)

    def login(self):
        # Aqui você pode validar usuário/senha
        # Por enquanto, apenas chama callback
        self.on_login()