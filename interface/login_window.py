from __future__ import annotations

from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    FONT_LABEL,
    WIDGET_HEIGHT_NORMAL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
    THEME_COLORS,
    button_style,
    card_style,
)


class LoginWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.logged_in = False
        self.username: str | None = None

        self.title("PCM Thermal Manager")
        self.geometry("520x360")
        # UI REFATORADA: login com paleta e tipografia modernas
        self.configure(fg_color=THEME_COLORS["bg"])
        self.resizable(False, False)

        self._center_window(520, 360)
        self._build_ui()

        self.bind("<Return>", lambda _e: self._handle_login())
        self.password_entry.bind("<Return>", lambda _e: self._handle_login())

    def _build_ui(self) -> None:
        title = ctk.CTkLabel(
            self,
            text="PCM Thermal Manager",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        title.pack(pady=(PAD_LARGE, PAD_NORMAL))

        card = ctk.CTkFrame(self, **card_style())
        card.pack(padx=PAD_LARGE, pady=(0, PAD_LARGE), fill="x")

        user_label = ctk.CTkLabel(card, text="Usuário", text_color=THEME_COLORS["text_secondary"], font=FONT_LABEL)
        user_label.pack(anchor="w", padx=PAD_LARGE, pady=(PAD_LARGE, PAD_SMALL))

        self.username_entry = ctk.CTkEntry(
            card,
            placeholder_text="Digite seu nome",
            height=WIDGET_HEIGHT_NORMAL,
            font=FONT_NORMAL,
        )
        self.username_entry.pack(fill="x", padx=PAD_LARGE)

        pass_label = ctk.CTkLabel(card, text="Senha", text_color=THEME_COLORS["text_secondary"], font=FONT_LABEL)
        pass_label.pack(anchor="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self.password_entry = ctk.CTkEntry(
            card,
            show="*",
            placeholder_text="YYMMDD",
            height=WIDGET_HEIGHT_NORMAL,
            font=FONT_NORMAL,
        )
        self.password_entry.pack(fill="x", padx=PAD_LARGE)

        self.login_button = ctk.CTkButton(
            card,
            text="Entrar",
            font=FONT_NORMAL,
            command=self._handle_login,
            **button_style("primary"),
        )
        self.login_button.pack(padx=PAD_LARGE, pady=(PAD_LARGE, PAD_LARGE), fill="x")

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
