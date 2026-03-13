import customtkinter as ctk
from tkinter import ttk


class DatabasePage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Banco de Dados",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(6, 12))

        controls = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        controls.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        controls.grid_columnconfigure(0, weight=1)

        self.search = ctk.CTkEntry(controls, placeholder_text="Buscar...")
        self.search.grid(row=0, column=0, sticky="ew", padx=16, pady=12)

        btn_filter = ctk.CTkButton(
            controls,
            text="Filtrar",
            corner_radius=10,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
            width=100,
        )
        btn_filter.grid(row=0, column=1, padx=8, pady=12)

        btn_order = ctk.CTkButton(
            controls,
            text="Ordenar",
            corner_radius=10,
            fg_color="#1E2530",
            text_color="#E5E7EB",
            hover_color="#2A3341",
            width=100,
        )
        btn_order.grid(row=0, column=2, padx=8, pady=12)

        table_frame = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "PCM.Treeview",
            background="#161B22",
            fieldbackground="#161B22",
            foreground="#E5E7EB",
            rowheight=28,
            borderwidth=0,
        )
        style.configure(
            "PCM.Treeview.Heading",
            background="#0F141C",
            foreground="#9AA0AB",
            font=("Segoe UI", 9, "bold"),
        )
        style.map("PCM.Treeview", background=[("selected", "#18212B")])

        columns = ("id", "material", "temperatura", "tempo", "origem")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="PCM.Treeview")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.tree.heading("id", text="ID")
        self.tree.heading("material", text="Material")
        self.tree.heading("temperatura", text="Temperatura")
        self.tree.heading("tempo", text="Tempo")
        self.tree.heading("origem", text="Origem")

        dados = [
            (1, "Oleo de Coco", "42.3 °C", "120 s", "Sensor"),
            (2, "Parafina", "38.1 °C", "90 s", "Manual"),
            (3, "Cera", "35.0 °C", "70 s", "Sensor"),
        ]
        for row in dados:
            self.tree.insert("", "end", values=row)
