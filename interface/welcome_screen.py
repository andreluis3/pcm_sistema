from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image

from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    FONT_LABEL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
    THEME_COLORS,
    card_style,
    button_style,
)


class WelcomeScreen(ctk.CTk):
    def __init__(self, username: str = "Usuário") -> None:
        super().__init__()

        self._proceed = False
        self._username = username

        self.title("ThermalManager")
        self.geometry("520x420")
        self.configure(fg_color=THEME_COLORS["bg"])
        self.resizable(False, False)

        self._center_window(520, 420)
        self._build_ui()

    @property
    def proceed(self) -> bool:
        return self._proceed

    def _build_ui(self) -> None:
        # UI REFATORADA: welcome card com borda e tipografia moderna
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(self, **card_style())
        card.grid(row=0, column=0, sticky="nsew", padx=PAD_LARGE, pady=PAD_LARGE)
        card.grid_rowconfigure(0, weight=1)
        card.grid_rowconfigure(5, weight=1)
        card.grid_columnconfigure(0, weight=1)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        self._logo_image = ctk.CTkImage(Image.open(logo_path), size=(100, 100))
        logo = ctk.CTkLabel(card, image=self._logo_image, text="")
        logo.grid(row=1, column=0, pady=(PAD_LARGE, PAD_SMALL))

        title = ctk.CTkLabel(
            card,
            text=f"Bem-vindo ao ThermalManager",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        title.grid(row=2, column=0, pady=(0, PAD_SMALL))

        subtitle = ctk.CTkLabel(
            card,
            text="Sistema de análise térmica e monitoramento de experimentos PCM.",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
            wraplength=380,
            justify="center",
        )
        subtitle.grid(row=3, column=0, padx=PAD_LARGE, pady=(0, PAD_NORMAL))

        enter_btn = ctk.CTkButton(
            card,
            text="Entrar no Sistema",
            font=FONT_NORMAL,
            command=self._handle_enter,
            **button_style("primary"),
        )
        enter_btn.grid(row=4, column=0, pady=(0, PAD_LARGE), padx=PAD_LARGE, sticky="ew")

    def _handle_enter(self) -> None:
        self._proceed = True
        self.destroy()

    def _center_window(self, width: int, height: int) -> None:
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
