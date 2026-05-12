import json
import threading
import tkinter as tk
from datetime import datetime
from typing import List

import customtkinter as ctk
import serial
import serial.tools.list_ports

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    FONT_TITLE,
    FONT_TEMP,
    FONT_LABEL,
    WIDGET_HEIGHT_NORMAL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
    THEME_COLORS,
    button_style,
)

COLORS = THEME_COLORS


# =========================================================
# CHART
# =========================================================

class MinimalLineChart:
    def __init__(self, parent) -> None:
        self.figure = Figure(figsize=(5.6, 2.4), dpi=100)

        self.figure.patch.set_facecolor(COLORS["card"])

        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(COLORS["card"])

        for side in ["bottom", "top", "left", "right"]:
            self.ax.spines[side].set_visible(False)

        self.ax.tick_params(colors=COLORS["text_secondary"])
        self.ax.grid(True, alpha=0.15)

        (self.line,) = self.ax.plot(
            [],
            [],
            color=COLORS["accent_alt"],
            linewidth=2.5
        )

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()

    def update(self, data: List[float]) -> None:
        if not data:
            return

        self.line.set_data(range(len(data)), data)

        self.ax.set_xlim(0, max(30, len(data)))

        min_v = min(data)
        max_v = max(data)

        spread = max(1, (max_v - min_v) * 0.2)

        self.ax.set_ylim(min_v - spread, max_v + spread)

        self.canvas.draw_idle()


# =========================================================
# SENSOR PAGE
# =========================================================

class SensorPage(ctk.CTkFrame):

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(2, weight=1)

        # =========================
        # STATE
        # =========================

        self.temperature_history: List[float] = []
        self.sensor_logs: List[dict] = []

        self.serial_connection = None
        self.serial_running = False
        self.serial_thread = None

        self.connection_mode = ctk.StringVar(value="Serial")

        self.sensor_temperature_var = ctk.StringVar(value="-- °C")

        self.connection_status_var = ctk.StringVar(
            value="🔴 Desconectado"
        )

        self.last_reading_var = ctk.StringVar(
            value="Última leitura: --"
        )

        # =========================
        # UI REFS
        # =========================

        self._chart = None
        self._status_label = None

        self._build_layout()

    # =====================================================
    # LAYOUT
    # =====================================================

    def _build_layout(self):

        self.create_header()

        self.create_temperature_gauge()

        self.create_temperature_graph()

        self.create_config_panel()

    # =====================================================
    # HEADER
    # =====================================================

    def create_header(self):

        header = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        header.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PAD_LARGE,
            pady=(10, PAD_NORMAL)
        )

        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Sensor",
            font=FONT_HEADER,
            text_color=COLORS["text_primary"]
        )

        title.grid(row=0, column=0, sticky="w")

        status_card = ctk.CTkFrame(
            header,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )

        status_card.grid(row=0, column=1)

        self._status_label = ctk.CTkLabel(
            status_card,
            textvariable=self.connection_status_var,
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )

        self._status_label.grid(
            row=0,
            column=0,
            padx=18,
            pady=8
        )

    # =====================================================
    # GAUGE
    # =====================================================

    def create_temperature_gauge(self):

        gauge_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )

        gauge_card.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=PAD_LARGE,
            pady=(0, PAD_NORMAL)
        )

        canvas_size = 260

        canvas = tk.Canvas(
            gauge_card,
            width=canvas_size,
            height=canvas_size,
            bg=COLORS["card"],
            highlightthickness=0
        )

        canvas.pack(pady=PAD_LARGE)

        canvas.create_oval(
            20,
            20,
            canvas_size - 20,
            canvas_size - 20,
            fill=COLORS["card_soft"],
            outline=COLORS["border"],
            width=2
        )

        canvas.create_arc(
            26,
            26,
            canvas_size - 26,
            canvas_size - 26,
            start=110,
            extent=320,
            style="arc",
            width=5,
            outline=COLORS["primary"]
        )

        value_label = ctk.CTkLabel(
            gauge_card,
            textvariable=self.sensor_temperature_var,
            font=FONT_TEMP,
            text_color=COLORS["primary"]
        )

        value_label.place(
            relx=0.5,
            rely=0.48,
            anchor="center"
        )

        info = ctk.CTkLabel(
            gauge_card,
            text="Temperatura IR",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )

        info.place(
            relx=0.5,
            rely=0.80,
            anchor="center"
        )

    # =====================================================
    # GRAPH
    # =====================================================

    def create_temperature_graph(self):

        graph_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )

        graph_card.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=PAD_LARGE,
            pady=(0, PAD_LARGE)
        )

        graph_card.grid_columnconfigure(0, weight=1)
        graph_card.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            graph_card,
            text="Tendência Térmica",
            font=FONT_TITLE,
            text_color=COLORS["text_primary"]
        )

        title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=PAD_LARGE,
            pady=(PAD_NORMAL, 0)
        )

        self._chart = MinimalLineChart(graph_card)

        self._chart.widget.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=PAD_LARGE,
            pady=PAD_NORMAL
        )

    # =====================================================
    # CONFIG PANEL
    # =====================================================

    def create_config_panel(self):

        panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )

        panel.grid(
            row=1,
            column=1,
            rowspan=2,
            sticky="nsew",
            padx=(0, PAD_LARGE),
            pady=(0, PAD_LARGE)
        )

        panel.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="Central de Conexão",
            font=FONT_TITLE,
            text_color=COLORS["text_primary"]
        )

        title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=PAD_LARGE,
            pady=(PAD_NORMAL, PAD_SMALL)
        )

        # ==========================================
        # CONNECTION MODE
        # ==========================================

        mode_frame = ctk.CTkFrame(
            panel,
            fg_color=COLORS["card_soft"]
        )

        mode_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PAD_NORMAL,
            pady=(0, PAD_NORMAL)
        )

        mode_label = ctk.CTkLabel(
            mode_frame,
            text="Modo de conexão",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )

        mode_label.pack(
            anchor="w",
            padx=PAD_NORMAL,
            pady=(PAD_NORMAL, 4)
        )

        self.connection_option = ctk.CTkOptionMenu(
            mode_frame,
            values=[
                "Serial",
                "MQTT",
                "API",
                "Simulação"
            ],
            variable=self.connection_mode,
            command=self.on_connection_mode_changed
        )

        self.connection_option.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_NORMAL)
        )

        # ==========================================
        # SERIAL SECTION
        # ==========================================

        self.serial_section = ctk.CTkFrame(
            panel,
            fg_color=COLORS["card_soft"]
        )

        self.serial_section.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=PAD_NORMAL,
            pady=(0, PAD_NORMAL)
        )

        self._build_serial_section()

        # ==========================================
        # LOG SECTION
        # ==========================================

        self._build_logs(panel)

    # =====================================================
    # SERIAL SECTION
    # =====================================================

    def _build_serial_section(self):

        title = ctk.CTkLabel(
            self.serial_section,
            text="Conexão Serial",
            font=FONT_TITLE,
            text_color=COLORS["text_primary"]
        )

        title.pack(
            anchor="w",
            padx=PAD_NORMAL,
            pady=(PAD_NORMAL, PAD_SMALL)
        )

        # COM PORT

        label = ctk.CTkLabel(
            self.serial_section,
            text="Porta COM",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )

        label.pack(anchor="w", padx=PAD_NORMAL)

        ports = self.get_serial_ports()

        self.com_option = ctk.CTkOptionMenu(
            self.serial_section,
            values=ports if ports else ["COM3"]
        )

        self.com_option.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_SMALL)
        )

        # BAUDRATE

        baud_label = ctk.CTkLabel(
            self.serial_section,
            text="Baudrate",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )

        baud_label.pack(anchor="w", padx=PAD_NORMAL)

        self.baudrate_option = ctk.CTkOptionMenu(
            self.serial_section,
            values=["9600", "115200"]
        )

        self.baudrate_option.set("115200")

        self.baudrate_option.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_NORMAL)
        )

        # BUTTONS

        button_frame = ctk.CTkFrame(
            self.serial_section,
            fg_color="transparent"
        )

        button_frame.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_NORMAL)
        )

        self.connect_btn = ctk.CTkButton(
            button_frame,
            text="Conectar",
            command=self.connect_serial,
            **button_style("primary")
        )

        self.connect_btn.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(0, 5)
        )

        self.disconnect_btn = ctk.CTkButton(
            button_frame,
            text="Desconectar",
            command=self.disconnect_serial,
            **button_style("danger")
        )

        self.disconnect_btn.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(5, 0)
        )

    # =====================================================
    # LOGS
    # =====================================================

    def _build_logs(self, parent):

        log_frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["card_soft"]
        )

        log_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=PAD_NORMAL,
            pady=(0, PAD_NORMAL)
        )

        title = ctk.CTkLabel(
            log_frame,
            text="Logs do Sensor",
            font=FONT_TITLE,
            text_color=COLORS["text_primary"]
        )

        title.pack(
            anchor="w",
            padx=PAD_NORMAL,
            pady=(PAD_NORMAL, PAD_SMALL)
        )

        self.log_textbox = ctk.CTkTextbox(
            log_frame,
            height=180,
            fg_color=COLORS["card"],
            text_color=COLORS["text_primary"]
        )

        self.log_textbox.pack(
            fill="both",
            expand=True,
            padx=PAD_NORMAL,
            pady=(0, PAD_NORMAL)
        )

    # =====================================================
    # SERIAL
    # =====================================================

    def connect_serial(self):

        try:

            port = self.com_option.get()
            baudrate = int(self.baudrate_option.get())

            self.serial_connection = serial.Serial(
                port,
                baudrate,
                timeout=1
            )

            self.serial_running = True

            self.serial_thread = threading.Thread(
                target=self.serial_read_loop,
                daemon=True
            )

            self.serial_thread.start()

            self.update_connection_status(
                f"🟢 Serial conectada ({port})",
                success=True
            )

            self.add_log(
                f"Conectado na porta {port}"
            )

        except Exception as e:

            self.update_connection_status(
                "🔴 Falha na conexão",
                success=False
            )

            self.add_log(
                f"ERRO: {e}"
            )

    def disconnect_serial(self):

        self.serial_running = False

        try:

            if self.serial_connection:
                self.serial_connection.close()

        except:
            pass

        self.update_connection_status(
            "🔴 Serial desconectada",
            success=False
        )

        self.add_log(
            "Conexão encerrada"
        )

    def serial_read_loop(self):

        while self.serial_running:

            try:

                raw = self.serial_connection.readline()

                line = raw.decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                if not line:
                    continue

                self.process_sensor_data(line)

            except Exception as e:

                self.add_log(
                    f"Erro leitura serial: {e}"
                )

    # =====================================================
    # PROCESS DATA
    # =====================================================

    def process_sensor_data(self, raw_data):

        try:

            # FORMATO:
            # TEMP:35.7

            if "TEMP:" in raw_data:

                value = raw_data.replace(
                    "TEMP:",
                    ""
                ).strip()

                temperature = float(value)

            else:

                # JSON
                data = json.loads(raw_data)

                temperature = float(
                    data["temperatura"]
                )

            self.after(
                0,
                lambda: self.update_temperature(
                    temperature
                )
            )

        except Exception as e:

            self.add_log(
                f"Erro processamento: {e}"
            )

    # =====================================================
    # UPDATE TEMP
    # =====================================================

    def update_temperature(self, value):

        self.sensor_temperature_var.set(
            f"{value:.1f} °C"
        )

        self.last_reading_var.set(
            f"Última leitura: {value:.1f} °C"
        )

        self.temperature_history.append(value)

        if len(self.temperature_history) > 120:
            self.temperature_history = self.temperature_history[-120:]

        if self._chart:
            self._chart.update(
                self.temperature_history
            )

        self.save_sensor_log(value)

        self.add_log(
            f"🌡 Temperatura: {value:.2f} °C"
        )

    # =====================================================
    # SAVE LOG
    # =====================================================

    def save_sensor_log(self, temperature):

        self.sensor_logs.append({

            "timestamp": datetime.now(),

            "temperature": temperature,

            "mode": self.connection_mode.get()
        })

    # =====================================================
    # STATUS
    # =====================================================

    def update_connection_status(
        self,
        text,
        success=False
    ):

        self.connection_status_var.set(text)

        color = (
            COLORS["primary"]
            if success
            else COLORS["danger"]
        )

        if self._status_label:
            self._status_label.configure(
                text_color=color
            )

    # =====================================================
    # LOG UI
    # =====================================================

    def add_log(self, message):

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        self.log_textbox.insert(
            "end",
            f"[{timestamp}] {message}\n"
        )

        self.log_textbox.see("end")

    # =====================================================
    # UTILS
    # =====================================================

    def get_serial_ports(self):

        ports = serial.tools.list_ports.comports()

        return [p.device for p in ports]

    def on_connection_mode_changed(self, mode):

        self.add_log(
            f"Modo alterado para {mode}"
        )