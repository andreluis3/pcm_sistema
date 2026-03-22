from __future__ import annotations

from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox


class LoginWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.logged_in = False
        self.username: str | None = None

        self.title("PCM Thermal Manager")
        self.geometry("520x360")
        self.configure(fg_color="#0D1117")
        self.resizable(False, False)

        self._center_window(520, 360)
        self._build_ui()

        self.bind("<Return>", lambda _e: self._handle_login())
        self.password_entry.bind("<Return>", lambda _e: self._handle_login())

    def _build_ui(self) -> None:
        title = ctk.CTkLabel(
            self,
            text="PCM Thermal Manager",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.pack(pady=(28, 12))

        card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        card.pack(padx=28, pady=(0, 24), fill="x")

        user_label = ctk.CTkLabel(card, text="Usuário", text_color="#9AA0AB", font=ctk.CTkFont(size=12))
        user_label.pack(anchor="w", padx=20, pady=(20, 6))

        self.username_entry = ctk.CTkEntry(card, placeholder_text="Digite seu nome")
        self.username_entry.pack(fill="x", padx=20)

        pass_label = ctk.CTkLabel(card, text="Senha", text_color="#9AA0AB", font=ctk.CTkFont(size=12))
        pass_label.pack(anchor="w", padx=20, pady=(16, 6))

        self.password_entry = ctk.CTkEntry(card, show="*", placeholder_text="YYMMDD")
        self.password_entry.pack(fill="x", padx=20)

        self.login_button = ctk.CTkButton(
            card,
            text="Entrar",
            corner_radius=12,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
            command=self._handle_login,
        )
        self.login_button.pack(padx=20, pady=(20, 22), fill="x")

    def _handle_login(self) -> None:
        username = self.username_entry.get().strip() or "Usuário"
        password = self.password_entry.get().strip()

        expected_password = datetime.now().strftime("%y%m%d")

        if password != expected_password:
            messagebox.showerror("Erro", "Senha incorreta.", parent=self)
            return

        self.logged_in = True
        self.username = username
        self.destroy()

    def _center_window(self, width: int, height: int) -> None:
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
