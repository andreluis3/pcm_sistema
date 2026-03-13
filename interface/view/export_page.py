import customtkinter as ctk


class ExportPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Exportação",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(6, 16))

        card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        card.grid(row=1, column=0, sticky="ew", padx=16)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Exportar medições",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

        formatos = ctk.CTkFrame(card, fg_color="#0F141C", corner_radius=14)
        formatos.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        formatos.grid_columnconfigure(0, weight=1)
        formatos.grid_columnconfigure(1, weight=1)
        formatos.grid_columnconfigure(2, weight=1)

        self._option(formatos, 0, "CSV")
        self._option(formatos, 1, "Excel")
        self._option(formatos, 2, "JSON")

        exportar_btn = ctk.CTkButton(
            card,
            text="Exportar",
            corner_radius=12,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
        )
        exportar_btn.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))

    def _option(self, parent, col: int, label: str) -> None:
        box = ctk.CTkFrame(parent, fg_color="#161B22", corner_radius=12)
        box.grid(row=0, column=col, sticky="ew", padx=10, pady=12)
        ctk.CTkLabel(
            box,
            text=label,
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=10)
