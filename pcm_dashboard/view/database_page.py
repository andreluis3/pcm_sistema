import customtkinter as ctk


class DatabasePage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Database",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(4, 16))

        search_wrap = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=24)
        search_wrap.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
        search_wrap.grid_columnconfigure(0, weight=1)

        search = ctk.CTkEntry(
            search_wrap,
            placeholder_text="Search materials, tests, cycles...",
            fg_color="#0F141C",
            border_width=0,
            text_color="#E5E7EB",
        )
        search.grid(row=0, column=0, sticky="ew", padx=16, pady=12)

        cards = ctk.CTkFrame(self, fg_color="#0D1117")
        cards.grid(row=2, column=0, sticky="nsew", padx=16)
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)

        items = [
            ("Coconut Oil", "Material", "Phase-change material for low-temp tests"),
            ("Test 12", "Test", "Thermal cycle at 30°C for 45 minutes"),
            ("Paraffin", "Material", "High stability storage sample"),
            ("Test 11", "Test", "Ramp profile, 28°C to 34°C"),
        ]

        for idx, (name, kind, desc) in enumerate(items):
            card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
            row = idx // 2
            col = idx % 2
            card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

            name_label = ctk.CTkLabel(
                card,
                text=name,
                text_color="#E5E7EB",
                font=ctk.CTkFont(size=15, weight="bold"),
            )
            name_label.grid(row=0, column=0, sticky="w", padx=14, pady=(14, 4))

            kind_label = ctk.CTkLabel(
                card,
                text=kind,
                text_color="#00F5D4",
                font=ctk.CTkFont(size=11, weight="bold"),
            )
            kind_label.grid(row=1, column=0, sticky="w", padx=14)

            desc_label = ctk.CTkLabel(
                card,
                text=desc,
                text_color="#9AA0AB",
                font=ctk.CTkFont(size=11),
                wraplength=260,
                justify="left",
            )
            desc_label.grid(row=2, column=0, sticky="w", padx=14, pady=(4, 12))

            btn = ctk.CTkButton(
                card,
                text="Open",
                corner_radius=10,
                fg_color="#00F5D4",
                text_color="#0D1117",
                hover_color="#24FFE0",
            )
            btn.grid(row=3, column=0, sticky="w", padx=14, pady=(0, 14))
