import customtkinter as ctk

from ui_styles import (
    FONT_NORMAL,
    FONT_LABEL,
    WIDGET_HEIGHT_NORMAL,
    PAD_NORMAL,
    PAD_LARGE,
    THEME_COLORS,
    button_style,
)

class LoginPage(ctk.CTkFrame):
    def __init__(self, parent, on_login):
        # UI REFATORADA: login page com paleta moderna
        super().__init__(parent, fg_color=THEME_COLORS["bg"])
        self.on_login = on_login

        # Deve usar grid, porque parent usa grid
        self.grid(row=0, column=0, sticky="nsew")

        # Widgets internos podem usar pack dentro do frame
        self.username_label = ctk.CTkLabel(self, text="Usuário", font=FONT_LABEL, text_color=THEME_COLORS["text_secondary"])
        self.username_label.pack(pady=PAD_NORMAL)

        self.username_entry = ctk.CTkEntry(self, height=WIDGET_HEIGHT_NORMAL, font=FONT_NORMAL)
        self.username_entry.pack(pady=PAD_NORMAL)

        self.password_label = ctk.CTkLabel(self, text="Senha", font=FONT_LABEL, text_color=THEME_COLORS["text_secondary"])
        self.password_label.pack(pady=PAD_NORMAL)

        self.password_entry = ctk.CTkEntry(self, show="*", height=WIDGET_HEIGHT_NORMAL, font=FONT_NORMAL)
        self.password_entry.pack(pady=PAD_NORMAL)

        self.login_button = ctk.CTkButton(
            self,
            text="Login",
            font=FONT_NORMAL,
            command=self.login,
            **button_style("primary"),
        )
        self.login_button.pack(pady=PAD_LARGE)

    def login(self):
        # Aqui você pode validar usuário/senha
        # Por enquanto, apenas chama callback
        self.on_login()
