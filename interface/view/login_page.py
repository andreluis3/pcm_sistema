import customtkinter as ctk
from services.auth_service import AuthService


class LoginPage(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color="#0D1117")

        self.auth = AuthService()
        self.on_login_success = on_login_success

        self.pack(fill="both", expand=True)

        self.title = ctk.CTkLabel(
            self,
            text="PCM THERMAL MANAGER",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title.pack(pady=(40, 20))

        self.username = ctk.CTkEntry(self, placeholder_text="Usuário")
        self.username.pack(pady=8, ipadx=20)

        self.password = ctk.CTkEntry(self, placeholder_text="Senha", show="*")
        self.password.pack(pady=8, ipadx=20)

        self.login_btn = ctk.CTkButton(
            self,
            text="Entrar",
            corner_radius=12,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
            command=self.login,
        )
        self.login_btn.pack(pady=20)

        self.message = ctk.CTkLabel(self, text="", text_color="#FF5252")
        self.message.pack()

    def login(self):
        username = self.username.get()
        password = self.password.get()

        if self.auth.login(username, password):
            self.message.configure(text="Login realizado com sucesso")
            self.on_login_success()
        else:
            self.message.configure(text="Credenciais inválidas")
