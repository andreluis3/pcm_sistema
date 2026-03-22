import customtkinter as ctk

from ui_styles import (
    BUTTON_HEIGHT,
    FONT_NORMAL,
    FONT_SIDEBAR,
    FONT_SUBTITLE,
    FONT_TEMP,
    SIDEBAR_BUTTON_HEIGHT,
)


class CardInformacao(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        titulo: str,
        valor: str,
        cor_valor: str = "#E5E7EB",
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color="#161B22", corner_radius=18, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.titulo = ctk.CTkLabel(
            self,
            text=titulo,
            text_color="#9AA0AB",
            font=FONT_NORMAL,
        )
        self.titulo.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        self.valor = ctk.CTkLabel(
            self,
            text=valor,
            text_color=cor_valor,
            font=FONT_TEMP,
        )
        self.valor.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

    def atualizar(self, valor: str, cor: str | None = None) -> None:
        self.valor.configure(text=valor)
        if cor:
            self.valor.configure(text_color=cor)


class LabelStatus(ctk.CTkLabel):
    def __init__(self, parent, texto: str, cor: str) -> None:
        super().__init__(
            parent,
            text=texto,
            text_color=cor,
            font=FONT_SUBTITLE,
        )


class BotaoSidebar(ctk.CTkButton):
    def __init__(self, parent, texto: str, comando) -> None:
        super().__init__(
            parent,
            text=texto,
            anchor="w",
            height=SIDEBAR_BUTTON_HEIGHT,
            corner_radius=14,
            fg_color="#161B22",
            hover_color="#1E2530",
            text_color="#E5E7EB",
            font=FONT_SIDEBAR,
            command=comando,
        )

    def set_ativo(self, ativo: bool) -> None:
        self.configure(
            fg_color="#18212B" if ativo else "#161B22",
            text_color="#00F5D4" if ativo else "#E5E7EB",
            border_width=1 if ativo else 0,
            border_color="#00B3FF" if ativo else "#161B22",
        )
