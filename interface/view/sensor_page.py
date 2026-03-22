import customtkinter as ctk

from core.mqtt_client import MQTTClient
from ui_styles import BUTTON_HEIGHT, ENTRY_HEIGHT, FONT_NORMAL, FONT_SUBTITLE, FONT_TITLE, SECTION_PAD_X, SECTION_PAD_Y, FONT_TEMP


class SensorPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.grid_columnconfigure(0, weight=1)
        self._mqtt_client = None

        title = ctk.CTkLabel(
            self,
            text="Sensor",
            text_color="#E5E7EB",
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, sticky="w", padx=SECTION_PAD_X, pady=(6, SECTION_PAD_Y))

        card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        card.grid(row=1, column=0, sticky="ew", padx=SECTION_PAD_X)
        card.grid_columnconfigure(1, weight=1)

        modo_label = ctk.CTkLabel(card, text="Modo de Conexão", text_color="#9AA0AB", font=FONT_NORMAL)
        modo_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 6))

        self.modo = ctk.CTkSegmentedButton(card, values=["Serial", "WiFi"], font=FONT_NORMAL)
        self.modo.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 12))

        porta_label = ctk.CTkLabel(card, text="Porta Serial", text_color="#9AA0AB", font=FONT_NORMAL)
        porta_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 6))
        self.porta = ctk.CTkEntry(card, placeholder_text="COM3 ou /dev/ttyUSB0", height=ENTRY_HEIGHT, font=FONT_NORMAL)
        self.porta.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))

        ip_label = ctk.CTkLabel(card, text="IP do Sensor", text_color="#9AA0AB", font=FONT_NORMAL)
        ip_label.grid(row=2, column=1, sticky="w", padx=16, pady=(0, 6))
        self.ip = ctk.CTkEntry(card, placeholder_text="192.168.0.10", height=ENTRY_HEIGHT, font=FONT_NORMAL)
        self.ip.grid(row=3, column=1, sticky="ew", padx=16, pady=(0, 12))

        self.conectar_btn = ctk.CTkButton(
            card,
            text="Conectar Sensor",
            height=BUTTON_HEIGHT,
            corner_radius=12,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
            font=FONT_SUBTITLE,
            command=self._on_connect_clicked,
        )
        self.conectar_btn.grid(row=4, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 16))

        status_card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        status_card.grid(row=2, column=0, sticky="ew", padx=SECTION_PAD_X, pady=SECTION_PAD_Y)
        status_card.grid_columnconfigure(1, weight=1)

        temp_label = ctk.CTkLabel(
            status_card,
            text="Temperatura atual",
            text_color="#9AA0AB",
            font=FONT_NORMAL,
        )
        temp_label.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        self.temp_value = ctk.CTkLabel(
            status_card,
            text="-- °C",
            text_color="#E5E7EB",
            font=FONT_TEMP,
        )
        self.temp_value.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 10))

        status_label = ctk.CTkLabel(
            status_card,
            text="Status",
            text_color="#9AA0AB",
            font=FONT_NORMAL,
        )
        status_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 4))

        self.status_value = ctk.CTkLabel(
            status_card,
            text="Desconectado 🔴",
            text_color="#FF5252",
            font=FONT_SUBTITLE,
        )
        self.status_value.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 14))

        log_card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        log_card.grid(row=3, column=0, sticky="nsew", padx=SECTION_PAD_X, pady=(0, SECTION_PAD_Y))
        log_card.grid_columnconfigure(0, weight=1)

        log_label = ctk.CTkLabel(
            log_card,
            text="Log",
            text_color="#9AA0AB",
            font=FONT_NORMAL,
        )
        log_label.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        self.log_text = ctk.CTkTextbox(
            log_card,
            height=160,
            fg_color="#0D1117",
            text_color="#E5E7EB",
            wrap="word",
            font=FONT_NORMAL,
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.log_text.configure(state="disabled")

    def destroy(self) -> None:
        if self._mqtt_client:
            self._mqtt_client.stop()
            self._mqtt_client = None
        super().destroy()

    def _on_connect_clicked(self) -> None:
        if self._mqtt_client:
            return
        self.conectar_btn.configure(state="disabled")
        self._mqtt_client = MQTTClient(
            on_temperature=self._handle_temperature,
            on_log=self._handle_log,
            on_status=self._handle_status,
        )
        try:
            self._mqtt_client.connect()
        except Exception as exc:
            self._handle_log(f"Erro ao conectar: {exc}")
            self._handle_status(False)
            self._mqtt_client = None
            self.conectar_btn.configure(state="normal")

    def _handle_temperature(self, temperature: float) -> None:
        self.after(0, lambda: self._set_temperature(temperature))

    def _handle_log(self, message: str) -> None:
        self.after(0, lambda: self._append_log(message))

    def _handle_status(self, connected: bool) -> None:
        self.after(0, lambda: self._set_status(connected))

    def _set_temperature(self, temperature: float) -> None:
        self.temp_value.configure(text=f"{temperature:.1f} °C")

    def _set_status(self, connected: bool) -> None:
        if connected:
            self.status_value.configure(text="CONECTADO 🟢", text_color="#00F5D4")
        else:
            self.status_value.configure(text="Desconectado 🔴", text_color="#FF5252")
            self.conectar_btn.configure(state="normal")

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
