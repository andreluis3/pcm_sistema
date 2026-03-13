import customtkinter as ctk


class SensorPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Sensor",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(6, 16))

        card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        card.grid(row=1, column=0, sticky="ew", padx=16)
        card.grid_columnconfigure(1, weight=1)

        modo_label = ctk.CTkLabel(card, text="Modo de Conexão", text_color="#9AA0AB", font=ctk.CTkFont(size=12))
        modo_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 6))

        self.modo = ctk.CTkSegmentedButton(card, values=["Serial", "WiFi"])
        self.modo.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 12))

        porta_label = ctk.CTkLabel(card, text="Porta Serial", text_color="#9AA0AB", font=ctk.CTkFont(size=12))
        porta_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 6))
        self.porta = ctk.CTkEntry(card, placeholder_text="COM3 ou /dev/ttyUSB0")
        self.porta.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))

        ip_label = ctk.CTkLabel(card, text="IP do Sensor", text_color="#9AA0AB", font=ctk.CTkFont(size=12))
        ip_label.grid(row=2, column=1, sticky="w", padx=16, pady=(0, 6))
        self.ip = ctk.CTkEntry(card, placeholder_text="192.168.0.10")
        self.ip.grid(row=3, column=1, sticky="ew", padx=16, pady=(0, 12))

        self.conectar_btn = ctk.CTkButton(
            card,
            text="Conectar Sensor",
            corner_radius=12,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
        )
        self.conectar_btn.grid(row=4, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 16))

        status_card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        status_card.grid(row=2, column=0, sticky="ew", padx=16, pady=16)

        status_label = ctk.CTkLabel(
            status_card,
            text="Status",
            text_color="#9AA0AB",
            font=ctk.CTkFont(size=12),
        )
        status_label.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        self.status_value = ctk.CTkLabel(
            status_card,
            text="Desconectado",
            text_color="#FF5252",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.status_value.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))
