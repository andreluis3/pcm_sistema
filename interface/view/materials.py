import customtkinter as ctk

from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    WIDGET_HEIGHT_NORMAL,
    WIDGET_HEIGHT_SMALL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
)


class MaterialsPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Materiais",
            text_color="#E5E7EB",
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(6, PAD_LARGE))

        form = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        form.grid(row=1, column=0, sticky="ew", padx=PAD_LARGE)
        form.grid_columnconfigure(1, weight=1)

        self._field(form, 0, "Nome do material", "Oleo de Coco")
        self._field(form, 1, "Tipo", "PCM")

        desc_label = ctk.CTkLabel(form, text="Descrição", text_color="#9AA0AB", font=FONT_NORMAL)
        desc_label.grid(row=2, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))
        self.desc = ctk.CTkTextbox(form, height=120, font=FONT_NORMAL)
        self.desc.grid(row=3, column=0, columnspan=2, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

        lista = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        lista.grid(row=2, column=0, sticky="nsew", padx=PAD_LARGE, pady=PAD_LARGE)
        lista.grid_columnconfigure(0, weight=1)

        titulo_lista = ctk.CTkLabel(
            lista,
            text="Lista de materiais cadastrados",
            text_color="#9AA0AB",
            font=FONT_NORMAL,
        )
        titulo_lista.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self._item_material(lista, 1, "Oleo de Coco", "PCM")
        self._item_material(lista, 2, "Parafina", "PCM")

    def _field(self, parent, row: int, label: str, placeholder: str) -> None:
        lbl = ctk.CTkLabel(parent, text=label, text_color="#9AA0AB", font=FONT_NORMAL)
        lbl.grid(row=row, column=0, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=WIDGET_HEIGHT_NORMAL, font=FONT_NORMAL)
        entry.grid(row=row, column=1, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

    def _item_material(self, parent, row: int, nome: str, tipo: str) -> None:
        item = ctk.CTkFrame(parent, fg_color="#0F141C", corner_radius=14)
        item.grid(row=row, column=0, sticky="ew", padx=PAD_LARGE, pady=PAD_SMALL)
        item.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            item,
            text=f"{nome} • {tipo}",
            text_color="#E5E7EB",
            font=FONT_TITLE,
        )
        label.grid(row=0, column=0, sticky="w", padx=PAD_NORMAL, pady=PAD_SMALL)

        edit_btn = ctk.CTkButton(
            item,
            text="Editar",
            corner_radius=10,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
            width=100,
            height=WIDGET_HEIGHT_SMALL,
            font=FONT_NORMAL,
        )
        edit_btn.grid(row=0, column=1, padx=PAD_SMALL, pady=PAD_SMALL)

        remove_btn = ctk.CTkButton(
            item,
            text="Remover",
            corner_radius=10,
            fg_color="#FF5252",
            text_color="#0D1117",
            hover_color="#FF6B6B",
            width=100,
            height=WIDGET_HEIGHT_SMALL,
            font=FONT_NORMAL,
        )
        remove_btn.grid(row=0, column=2, padx=PAD_SMALL, pady=PAD_SMALL)
