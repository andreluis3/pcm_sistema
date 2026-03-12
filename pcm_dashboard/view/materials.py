import customtkinter as ctk


class MaterialsPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Materials",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(4, 16))

        card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        card.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        card.grid_columnconfigure(0, weight=1)

        name = ctk.CTkLabel(
            card,
            text="Coconut Oil",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        name.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 6))

        description = ctk.CTkLabel(
            card,
            text=(
                "Coconut oil is used as a phase-change material in low-temperature "
                "thermal storage experiments. Its stable transition range makes it a "
                "good candidate for repeated lab cycles."
            ),
            text_color="#A3AAB6",
            font=ctk.CTkFont(size=12),
            wraplength=640,
            justify="left",
        )
        description.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 12))

        props = ctk.CTkFrame(card, fg_color="#0F141C", corner_radius=14)
        props.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))
        props.grid_columnconfigure(0, weight=1)
        props.grid_columnconfigure(1, weight=1)
        props.grid_columnconfigure(2, weight=1)

        self._prop(props, 0, "Melting Temperature", "24.0°C")
        self._prop(props, 1, "Latent Heat", "210 kJ/kg")
        self._prop(props, 2, "Density", "0.92 g/cm³")

        btn = ctk.CTkButton(
            card,
            text="Edit Material",
            corner_radius=12,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
        )
        btn.grid(row=3, column=0, sticky="w", padx=18, pady=(0, 18))

    def _prop(self, parent, col: int, title: str, value: str) -> None:
        block = ctk.CTkFrame(parent, fg_color="#161B22", corner_radius=12)
        block.grid(row=0, column=col, sticky="ew", padx=10, pady=12)

        label = ctk.CTkLabel(block, text=title, text_color="#9AA0AB", font=ctk.CTkFont(size=11))
        label.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))

        val = ctk.CTkLabel(
            block,
            text=value,
            text_color="#E5E7EB",
            font=ctk.CTkFont(family="Courier", size=14, weight="bold"),
        )
        val.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))
