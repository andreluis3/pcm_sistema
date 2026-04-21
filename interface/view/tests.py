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


class TemperatureTestsPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        # UI REFATORADA: testes com cards e botões padronizados
        super().__init__(parent, fg_color=THEME_COLORS["bg"])
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_LARGE, pady=(4, PAD_LARGE))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Testes de Temperatura",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w")

        add_btn = ctk.CTkButton(
            header,
            text="+ Adicionar Teste",
            font=FONT_NORMAL,
            **button_style("primary"),
        )
        add_btn.grid(row=0, column=1, sticky="e")

        table = ctk.CTkFrame(self, **card_style())
        table.grid(row=1, column=0, sticky="nsew", padx=PAD_LARGE, pady=PAD_NORMAL)
        table.grid_columnconfigure(0, weight=1)

        columns = ["Data", "Material", "Temperatura Pico", "Duração", "Status"]
        header_row = ctk.CTkFrame(table, fg_color=THEME_COLORS["card_soft"], corner_radius=12, border_width=1, border_color=THEME_COLORS["border"])
        header_row.grid(row=0, column=0, sticky="ew", padx=PAD_LARGE, pady=(PAD_LARGE, PAD_NORMAL))
        for idx, col in enumerate(columns):
            header_row.grid_columnconfigure(idx, weight=1)
            label = ctk.CTkLabel(
                header_row,
                text=col,
                text_color=THEME_COLORS["text_secondary"],
                font=FONT_LABEL,
            )
            label.grid(row=0, column=idx, padx=PAD_NORMAL, pady=PAD_SMALL, sticky="w")

        rows = [
            ("2026-03-10", "Oleo de Coco", "33.2°C", "42 min", "Concluído"),
            ("2026-03-08", "Parafina", "31.1°C", "38 min", "Concluído"),
            ("2026-03-05", "Cera", "29.4°C", "45 min", "Pausado"),
        ]
        for r, row in enumerate(rows, start=1):
            row_frame = ctk.CTkFrame(table, fg_color="transparent")
            row_frame.grid(row=r, column=0, sticky="ew", padx=PAD_LARGE, pady=PAD_SMALL)
            for idx, value in enumerate(row):
                row_frame.grid_columnconfigure(idx, weight=1)
                cell = ctk.CTkLabel(
                    row_frame,
                    text=value,
                    text_color=THEME_COLORS["text_primary"],
                    font=FONT_NORMAL,
                )
                cell.grid(row=0, column=idx, padx=PAD_NORMAL, pady=PAD_SMALL, sticky="w")
