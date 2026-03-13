import customtkinter as ctk


class ExperimentsPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Experimentos",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(6, 16))

        form = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        form.grid(row=1, column=0, sticky="ew", padx=16)
        form.grid_columnconfigure(1, weight=1)

        self._field(form, 0, "Nome do teste", "Ciclo 01")
        self._field(form, 1, "Material", "Oleo de Coco")
        self._field(form, 2, "Operador", "Andre")
        self._field(form, 3, "Data", "2026-03-12")

        tabela = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        tabela.grid(row=2, column=0, sticky="nsew", padx=16, pady=16)
        tabela.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(tabela, fg_color="#0F141C", corner_radius=12)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Tempo", text_color="#9AA0AB", font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=0, column=0, padx=10, pady=8, sticky="w"
        )
        ctk.CTkLabel(
            header, text="Temperatura", text_color="#9AA0AB", font=ctk.CTkFont(size=11, weight="bold")
        ).grid(row=0, column=1, padx=10, pady=8, sticky="w")

        self._row(tabela, 1, "0 s", "24.0 °C")
        self._row(tabela, 2, "60 s", "28.5 °C")
        self._row(tabela, 3, "120 s", "32.1 °C")

    def _field(self, parent, row: int, label: str, placeholder: str) -> None:
        lbl = ctk.CTkLabel(parent, text=label, text_color="#9AA0AB", font=ctk.CTkFont(size=12))
        lbl.grid(row=row, column=0, sticky="w", padx=16, pady=(0, 6))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder)
        entry.grid(row=row, column=1, sticky="ew", padx=16, pady=(0, 12))

    def _row(self, parent, row: int, tempo: str, temperatura: str) -> None:
        line = ctk.CTkFrame(parent, fg_color="#161B22")
        line.grid(row=row, column=0, sticky="ew", padx=16, pady=6)
        line.grid_columnconfigure(0, weight=1)
        line.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(line, text=tempo, text_color="#E5E7EB", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, padx=10, pady=6, sticky="w"
        )
        ctk.CTkLabel(line, text=temperatura, text_color="#E5E7EB", font=ctk.CTkFont(size=12)).grid(
            row=0, column=1, padx=10, pady=6, sticky="w"
        )
