import customtkinter as ctk

from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    FONT_TITLE,
    WIDGET_HEIGHT_NORMAL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
)


class TemperatureTestsPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="#0D1117")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_LARGE, pady=(4, PAD_LARGE))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Testes de Temperatura",
            text_color="#E5E7EB",
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w")

        add_btn = ctk.CTkButton(
            header,
            text="+ Adicionar Teste",
            height=WIDGET_HEIGHT_NORMAL,
            corner_radius=12,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
            font=FONT_NORMAL,
        )
        add_btn.grid(row=0, column=1, sticky="e")

        table = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        table.grid(row=1, column=0, sticky="nsew", padx=PAD_LARGE, pady=PAD_NORMAL)
        table.grid_columnconfigure(0, weight=1)

        columns = ["Data", "Material", "Temperatura Pico", "Duração", "Status"]
        header_row = ctk.CTkFrame(table, fg_color="#0F141C", corner_radius=12)
        header_row.grid(row=0, column=0, sticky="ew", padx=PAD_LARGE, pady=(PAD_LARGE, PAD_NORMAL))
        for idx, col in enumerate(columns):
            header_row.grid_columnconfigure(idx, weight=1)
            label = ctk.CTkLabel(
                header_row,
                text=col,
                text_color="#9AA0AB",
                font=FONT_TITLE,
            )
            label.grid(row=0, column=idx, padx=PAD_NORMAL, pady=PAD_SMALL, sticky="w")

        rows = [
            ("2026-03-10", "Oleo de Coco", "33.2°C", "42 min", "Concluído"),
            ("2026-03-08", "Parafina", "31.1°C", "38 min", "Concluído"),
            ("2026-03-05", "Cera", "29.4°C", "45 min", "Pausado"),
        ]
        for r, row in enumerate(rows, start=1):
            row_frame = ctk.CTkFrame(table, fg_color="#161B22")
            row_frame.grid(row=r, column=0, sticky="ew", padx=PAD_LARGE, pady=PAD_SMALL)
            for idx, value in enumerate(row):
                row_frame.grid_columnconfigure(idx, weight=1)
                cell = ctk.CTkLabel(
                    row_frame,
                    text=value,
                    text_color="#E5E7EB",
                    font=FONT_NORMAL,
                )
                cell.grid(row=0, column=idx, padx=PAD_NORMAL, pady=PAD_SMALL, sticky="w")
