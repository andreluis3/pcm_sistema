import customtkinter as ctk

from ui_styles import (
    FONT_NORMAL,
    FONT_LABEL,
    FONT_TITLE,
    FONT_TEMP,
    THEME_COLORS,
    WIDGET_HEIGHT_LARGE,
    card_style,
    button_style,
)


class CardInformacao(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        titulo: str,
        valor: str,
        cor_valor: str = None,
        **kwargs,
    ) -> None:
        # UI REFATORADA: card com borda e padding padronizados
        super().__init__(parent, **card_style(), **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.titulo = ctk.CTkLabel(
            self,
            text=titulo,
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
        )
        self.titulo.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        self.valor = ctk.CTkLabel(
            self,
            text=valor,
            text_color=cor_valor or THEME_COLORS["primary"],
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
            font=FONT_NORMAL,
        )


class BotaoSidebar(ctk.CTkButton):
    def __init__(self, parent, texto: str, comando) -> None:
        super().__init__(
            parent,
            text=texto,
            anchor="w",
            height=WIDGET_HEIGHT_LARGE,
            **button_style("neutral"),
            font=FONT_NORMAL,
            command=comando,
        )

    def set_ativo(self, ativo: bool) -> None:
        self.configure(
            fg_color=THEME_COLORS["card_soft"] if ativo else THEME_COLORS["neutral"],
            text_color=THEME_COLORS["primary"] if ativo else THEME_COLORS["text_primary"],
            border_width=1 if ativo else 0,
            border_color=THEME_COLORS["primary"] if ativo else THEME_COLORS["neutral"],
        )
