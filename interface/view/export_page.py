import customtkinter as ctk

from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    FONT_TITLE,
    FONT_LABEL,
    WIDGET_HEIGHT_NORMAL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
    THEME_COLORS,
    card_style,
    button_style,
)


class ExportPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        # UI REFATORADA: exportação com cards e botões padronizados
        super().__init__(parent, fg_color=THEME_COLORS["bg"])
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Exportação",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(6, PAD_LARGE))

        card = ctk.CTkFrame(self, **card_style())
        card.grid(row=1, column=0, sticky="ew", padx=PAD_LARGE)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Exportar medições",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_TITLE,
        ).grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_LARGE, PAD_SMALL))

        formatos = ctk.CTkFrame(card, fg_color=THEME_COLORS["card_soft"], corner_radius=12, border_width=1, border_color=THEME_COLORS["border"])
        formatos.grid(row=1, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        formatos.grid_columnconfigure(0, weight=1)
        formatos.grid_columnconfigure(1, weight=1)
        formatos.grid_columnconfigure(2, weight=1)

        self._option(formatos, 0, "CSV")
        self._option(formatos, 1, "Excel")
        self._option(formatos, 2, "JSON")

        exportar_btn = ctk.CTkButton(
            card,
            text="Exportar",
            font=FONT_NORMAL,
            **button_style("export"),
        )
        exportar_btn.grid(row=2, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_LARGE))

    def _option(self, parent, col: int, label: str) -> None:
        box = ctk.CTkFrame(parent, fg_color=THEME_COLORS["card"], corner_radius=12, border_width=1, border_color=THEME_COLORS["border"])
        box.grid(row=0, column=col, sticky="ew", padx=PAD_NORMAL, pady=PAD_NORMAL)
        ctk.CTkLabel(
            box,
            text=label,
            text_color=THEME_COLORS["text_primary"],
            font=FONT_TITLE,
        ).grid(row=0, column=0, padx=PAD_NORMAL, pady=PAD_SMALL)
