import customtkinter as ctk


class StatCard(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        title: str,
        value: str = "--",
        value_color: str = "#FFFFFF",
        **kwargs,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.configure(corner_radius=16)

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            text_color="#BDBDBD",
            font=ctk.CTkFont(size=14, weight="normal"),
        )
        self.title_label.pack(anchor="w", padx=16, pady=(14, 4))

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            text_color=value_color,
            font=ctk.CTkFont(family="Courier", size=44, weight="bold"),
        )
        self.value_label.pack(anchor="w", padx=16, pady=(0, 14))

    def set_value(self, value: str, color: str | None = None) -> None:
        self.value_label.configure(text=value)
        if color:
            self.value_label.configure(text_color=color)
