import customtkinter as ctk


class TemperatureTestsPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="#0D1117")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(4, 16))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Testes de Temperatura",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        add_btn = ctk.CTkButton(
            header,
            text="+ Adicionar Teste",
            corner_radius=12,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
        )
        add_btn.grid(row=0, column=1, sticky="e")

        table = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        table.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        table.grid_columnconfigure(0, weight=1)

        columns = ["Data", "Material", "Temperatura Pico", "Duração", "Status"]
        header_row = ctk.CTkFrame(table, fg_color="#0F141C", corner_radius=12)
        header_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        for idx, col in enumerate(columns):
            header_row.grid_columnconfigure(idx, weight=1)
            label = ctk.CTkLabel(
                header_row,
                text=col,
                text_color="#9AA0AB",
                font=ctk.CTkFont(size=11, weight="bold"),
            )
            label.grid(row=0, column=idx, padx=10, pady=10, sticky="w")

        rows = [
            ("2026-03-10", "Oleo de Coco", "33.2°C", "42 min", "Concluído"),
            ("2026-03-08", "Parafina", "31.1°C", "38 min", "Concluído"),
            ("2026-03-05", "Cera", "29.4°C", "45 min", "Pausado"),
        ]
        for r, row in enumerate(rows, start=1):
            row_frame = ctk.CTkFrame(table, fg_color="#161B22")
            row_frame.grid(row=r, column=0, sticky="ew", padx=16, pady=6)
            for idx, value in enumerate(row):
                row_frame.grid_columnconfigure(idx, weight=1)
                cell = ctk.CTkLabel(
                    row_frame,
                    text=value,
                    text_color="#E5E7EB",
                    font=ctk.CTkFont(size=12),
                )
                cell.grid(row=0, column=idx, padx=10, pady=8, sticky="w")
