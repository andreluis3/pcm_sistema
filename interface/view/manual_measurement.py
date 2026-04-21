import customtkinter as ctk

from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    FONT_LABEL,
    WIDGET_HEIGHT_NORMAL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
    THEME_COLORS,
    card_style,
    button_style,
)


class ManualMeasurementPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        # UI REFATORADA: formulário com card e botões padronizados
        super().__init__(parent, fg_color=THEME_COLORS["bg"])
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Medição Manual",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(6, PAD_LARGE))

        form = ctk.CTkFrame(self, **card_style())
        form.grid(row=1, column=0, sticky="ew", padx=PAD_LARGE)
        form.grid_columnconfigure(1, weight=1)

        self._field(form, 0, "Material", "Oleo de Coco")
        self._field(form, 1, "Temperatura", "42.0 °C")
        self._field(form, 2, "Tempo", "120 s")
        self._field(form, 3, "Massa", "120 g")

        obs_label = ctk.CTkLabel(form, text="Observações", text_color=THEME_COLORS["text_secondary"], font=FONT_LABEL)
        obs_label.grid(row=4, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))
        self.obs = ctk.CTkTextbox(form, height=140, font=FONT_NORMAL)
        self.obs.grid(row=5, column=0, columnspan=2, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

        salvar = ctk.CTkButton(
            form,
            text="Salvar Medição",
            font=FONT_NORMAL,
            **button_style("primary"),
        )
        salvar.grid(row=6, column=0, columnspan=2, sticky="w", padx=PAD_LARGE, pady=(0, PAD_LARGE))

    def _field(self, parent, row: int, label: str, placeholder: str) -> None:
        lbl = ctk.CTkLabel(parent, text=label, text_color=THEME_COLORS["text_secondary"], font=FONT_LABEL)
        lbl.grid(row=row, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=WIDGET_HEIGHT_NORMAL, font=FONT_NORMAL)
        entry.grid(row=row, column=1, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
