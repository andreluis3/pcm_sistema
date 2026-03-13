import customtkinter as ctk


class ManualMeasurementPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Medição Manual",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(6, 16))

        form = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        form.grid(row=1, column=0, sticky="ew", padx=16)
        form.grid_columnconfigure(1, weight=1)

        self._field(form, 0, "Material", "Oleo de Coco")
        self._field(form, 1, "Temperatura", "42.0 °C")
        self._field(form, 2, "Tempo", "120 s")
        self._field(form, 3, "Massa", "120 g")

        obs_label = ctk.CTkLabel(form, text="Observações", text_color="#9AA0AB", font=ctk.CTkFont(size=12))
        obs_label.grid(row=4, column=0, sticky="w", padx=16, pady=(0, 6))
        self.obs = ctk.CTkTextbox(form, height=120)
        self.obs.grid(row=5, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))

        salvar = ctk.CTkButton(
            form,
            text="Salvar Medição",
            corner_radius=12,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
        )
        salvar.grid(row=6, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 16))

    def _field(self, parent, row: int, label: str, placeholder: str) -> None:
        lbl = ctk.CTkLabel(parent, text=label, text_color="#9AA0AB", font=ctk.CTkFont(size=12))
        lbl.grid(row=row, column=0, sticky="w", padx=16, pady=(0, 6))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder)
        entry.grid(row=row, column=1, sticky="ew", padx=16, pady=(0, 12))
