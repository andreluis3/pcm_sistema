import json
import threading
import tkinter as tk
from datetime import datetime
from typing import List

import customtkinter as ctk


from sensor_module.serial_connection import SerialConnection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from sensor_module.sensor_manager import SensorManager
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
        
    def destroy(self):

        try:
            self.canvas.get_tk_widget().destroy()
        except Exception:
            pass

        try:
            self.figure.clear()
        except Exception:
            pass

        try:
            plt.close(self.figure)
        except Exception:
            pass

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
        
        self.sensor_manager = SensorManager(
        on_temperature=self.update_temperature,
        on_status=self.update_connection_status,
        on_log=self.add_log
        )

        # =========================
        # UI REFS
        # =========================

        self._chart = None
        self._status_label = None
        
        # ✅ NOVO: Referências para seções dinâmicas
        self.serial_section = None
        self.api_section = None
        self.mqtt_section = None
        self.simulation_section = None
        self.log_frame = None

        self._build_layout()
        
    def destroy(self):

        try:
            self._chart.destroy()
        except Exception:
            pass

        super().destroy()

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

        self.canvas_size = 260

        self.gauge_canvas = tk.Canvas(
            gauge_card,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=COLORS["card"],
            highlightthickness=0
        )

        self.gauge_canvas.pack(pady=PAD_LARGE)

        # FUNDO
        self.gauge_canvas.create_oval(
            20,
            20,
            self.canvas_size - 20,
            self.canvas_size - 20,
            fill=COLORS["card_soft"],
            outline=COLORS["border"],
            width=2
        )

        # ARCO DINÂMICO
        self.gauge_arc = self.gauge_canvas.create_arc(
            26,
            26,
            self.canvas_size - 26,
            self.canvas_size - 26,
            start=110,
            extent=0,
            style="arc",
            width=8,
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
        
        self.gauge_arc = self.gauge_canvas.create_arc(
                26,
                26,
                self.canvas_size - 26,
                self.canvas_size - 26,
                start=110,
                extent=0,
                style="arc",
                width=8,
                outline=COLORS["primary"]
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


    def update_temperature(self, value):

        self.sensor_temperature_var.set(
            f"{value:.1f} °C"
        )

        # ==========================================
        # TERMÔMETRO VISUAL
        # ==========================================

        max_temp = 100

        percent = min(max(value / max_temp, 0), 1)

        extent = percent * 320

        self.gauge_canvas.itemconfigure(
            self.gauge_arc,
            extent=extent
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
        # API SECTION (OCULTA INICIALMENTE)
        # ==========================================

        self.api_section = ctk.CTkFrame(
            panel,
            fg_color=COLORS["card_soft"]
        )

        # ✅ Não adicionar ao grid inicialmente
        # self.api_section.grid(...)

        self._build_api_section()

        # ==========================================
        # MQTT SECTION (OCULTA INICIALMENTE)
        # ==========================================

        self.mqtt_section = ctk.CTkFrame(
            panel,
            fg_color=COLORS["card_soft"]
        )

        self._build_mqtt_section()

        # ==========================================
        # SIMULATION SECTION (OCULTA INICIALMENTE)
        # ==========================================

        self.simulation_section = ctk.CTkFrame(
            panel,
            fg_color=COLORS["card_soft"]
        )

        self._build_simulation_section()

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
            command=self.connect_sensor,
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
            command=self.disconnect_sensor,
            **button_style("danger")
        )

        self.disconnect_btn.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(5, 0)
        )

    # =====================================================
    # API SECTION
    # =====================================================

    def _build_api_section(self):
        """Constrói seção de configuração HTTP/Wi-Fi."""

        title = ctk.CTkLabel(
            self.api_section,
            text="Conexão HTTP/Wi-Fi",
            font=FONT_TITLE,
            text_color=COLORS["text_primary"]
        )
        title.pack(
            anchor="w",
            padx=PAD_NORMAL,
            pady=(PAD_NORMAL, PAD_SMALL)
        )

        # IP DO ESP32
        ip_label = ctk.CTkLabel(
            self.api_section,
            text="IP do ESP32",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )
        ip_label.pack(anchor="w", padx=PAD_NORMAL)

        self.api_ip_entry = ctk.CTkEntry(
            self.api_section,
            placeholder_text="192.168.200.227"
        )
        self.api_ip_entry.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_SMALL)
        )
        self.api_ip_entry.insert(0, "192.168.200.227")

        # PORTA
        port_label = ctk.CTkLabel(
            self.api_section,
            text="Porta",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )
        port_label.pack(anchor="w", padx=PAD_NORMAL)

        self.api_port_entry = ctk.CTkEntry(
            self.api_section,
            placeholder_text="8080"
        )
        self.api_port_entry.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_SMALL)
        )
        self.api_port_entry.insert(0, "8080")

        # ENDPOINT
        endpoint_label = ctk.CTkLabel(
            self.api_section,
            text="Endpoint",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )
        endpoint_label.pack(anchor="w", padx=PAD_NORMAL)

        self.api_endpoint_entry = ctk.CTkEntry(
            self.api_section,
            placeholder_text="/sensor/temperature"
        )
        self.api_endpoint_entry.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_SMALL)
        )
        self.api_endpoint_entry.insert(0, "/sensor/temperature")

        # TESTE DE CONEXÃO
        test_frame = ctk.CTkFrame(
            self.api_section,
            fg_color="transparent"
        )
        test_frame.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_NORMAL)
        )

        self.api_test_btn = ctk.CTkButton(
            test_frame,
            text="🔍 Testar",
            command=self.api_test_connection,
            width=80
        )
        self.api_test_btn.pack(
            side="left",
            padx=(0, 5)
        )

        self.api_latency_label = ctk.CTkLabel(
            test_frame,
            text="Latência: --",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )
        self.api_latency_label.pack(
            side="left",
            padx=5
        )

        # BOTÕES DE CONEXÃO
        button_frame = ctk.CTkFrame(
            self.api_section,
            fg_color="transparent"
        )
        button_frame.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_NORMAL)
        )

        self.api_connect_btn = ctk.CTkButton(
            button_frame,
            text="Conectar",
            command=self.connect_sensor,
            **button_style("primary")
        )
        self.api_connect_btn.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(0, 5)
        )

        self.api_disconnect_btn = ctk.CTkButton(
            button_frame,
            text="Desconectar",
            command=self.disconnect_sensor,
            **button_style("danger")
        )
        self.api_disconnect_btn.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(5, 0)
        )

    # =====================================================
    # MQTT SECTION
    # =====================================================

    def _build_mqtt_section(self):
        """Constrói seção de configuração MQTT."""

        title = ctk.CTkLabel(
            self.mqtt_section,
            text="Conexão MQTT",
            font=FONT_TITLE,
            text_color=COLORS["text_primary"]
        )
        title.pack(
            anchor="w",
            padx=PAD_NORMAL,
            pady=(PAD_NORMAL, PAD_SMALL)
        )

        # BROKER
        broker_label = ctk.CTkLabel(
            self.mqtt_section,
            text="Broker",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )
        broker_label.pack(anchor="w", padx=PAD_NORMAL)

        self.mqtt_broker_entry = ctk.CTkEntry(
            self.mqtt_section,
            placeholder_text="mqtt.local"
        )
        self.mqtt_broker_entry.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_SMALL)
        )
        self.mqtt_broker_entry.insert(0, "mqtt.local")

        # PORTA
        port_label = ctk.CTkLabel(
            self.mqtt_section,
            text="Porta",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )
        port_label.pack(anchor="w", padx=PAD_NORMAL)

        self.mqtt_port_entry = ctk.CTkEntry(
            self.mqtt_section,
            placeholder_text="1883"
        )
        self.mqtt_port_entry.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_SMALL)
        )
        self.mqtt_port_entry.insert(0, "1883")

        # TÓPICO
        topic_label = ctk.CTkLabel(
            self.mqtt_section,
            text="Tópico",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )
        topic_label.pack(anchor="w", padx=PAD_NORMAL)

        self.mqtt_topic_entry = ctk.CTkEntry(
            self.mqtt_section,
            placeholder_text="sensors/pcm/temperature"
        )
        self.mqtt_topic_entry.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_SMALL)
        )
        self.mqtt_topic_entry.insert(0, "sensors/pcm/temperature")

        # ⚠️ MQTT ainda não implementado
        info_label = ctk.CTkLabel(
            self.mqtt_section,
            text="⚠️ MQTT ainda em desenvolvimento",
            font=FONT_LABEL,
            text_color=COLORS["danger"]
        )
        info_label.pack(
            anchor="w",
            padx=PAD_NORMAL,
            pady=PAD_SMALL
        )

    # =====================================================
    # SIMULATION SECTION
    # =====================================================

    def _build_simulation_section(self):
        """Constrói seção de configuração da simulação."""

        title = ctk.CTkLabel(
            self.simulation_section,
            text="Simulação Térmica",
            font=FONT_TITLE,
            text_color=COLORS["text_primary"]
        )
        title.pack(
            anchor="w",
            padx=PAD_NORMAL,
            pady=(PAD_NORMAL, PAD_SMALL)
        )

        # INTERVALO
        interval_label = ctk.CTkLabel(
            self.simulation_section,
            text="Intervalo (segundos)",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )
        interval_label.pack(anchor="w", padx=PAD_NORMAL)

        self.sim_interval_entry = ctk.CTkEntry(
            self.simulation_section,
            placeholder_text="1.0"
        )
        self.sim_interval_entry.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_SMALL)
        )
        self.sim_interval_entry.insert(0, "1.0")

        # TEMPERATURA MÁXIMA
        max_label = ctk.CTkLabel(
            self.simulation_section,
            text="Temperatura Máxima (°C)",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"]
        )
        max_label.pack(anchor="w", padx=PAD_NORMAL)

        self.sim_max_entry = ctk.CTkEntry(
            self.simulation_section,
            placeholder_text="82"
        )
        self.sim_max_entry.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_SMALL)
        )
        self.sim_max_entry.insert(0, "82")

        # BOTÕES
        button_frame = ctk.CTkFrame(
            self.simulation_section,
            fg_color="transparent"
        )
        button_frame.pack(
            fill="x",
            padx=PAD_NORMAL,
            pady=(0, PAD_NORMAL)
        )

        self.sim_connect_btn = ctk.CTkButton(
            button_frame,
            text="Iniciar",
            command=self.connect_sensor,
            **button_style("primary")
        )
        self.sim_connect_btn.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(0, 5)
        )

        self.sim_disconnect_btn = ctk.CTkButton(
            button_frame,
            text="Parar",
            command=self.disconnect_sensor,
            **button_style("danger")
        )
        self.sim_disconnect_btn.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(5, 0)
        )


    def connect_sensor(self):
        """Conecta ao sensor conforme modo selecionado."""

        mode = self.connection_mode.get()

        # ✅ NOVO: Configuração dinâmica conforme modo
        if mode == "Serial":
            config = {
                "port": self.com_option.get(),
                "baudrate": int(self.baudrate_option.get())
            }

        elif mode == "API":
            try:
                config = {
                    "host": self.api_ip_entry.get(),
                    "port": int(self.api_port_entry.get()),
                    "endpoint": self.api_endpoint_entry.get(),
                    "poll_interval": 2.0,
                    "timeout": 5.0
                }
            except ValueError:
                self.add_log("❌ Configuração API inválida")
                return

        elif mode == "MQTT":
            self.add_log("⚠️ MQTT ainda não implementado")
            return

        elif mode == "Simulação":
            try:
                config = {
                    "interval": float(self.sim_interval_entry.get()),
                    "max_temp": float(self.sim_max_entry.get())
                }
            except ValueError:
                self.add_log("❌ Configuração de simulação inválida")
                return

        else:
            self.add_log(f"❌ Modo desconhecido: {mode}")
            return

        self.sensor_manager.connect(mode, config)

    def disconnect_sensor(self):

        self.sensor_manager.disconnect()
        
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

        # ✅ IMPORTANTE
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            log_frame,
            text="Logs do Sensor",
            font=FONT_TITLE,
            text_color=COLORS["text_primary"]
        )

        title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=PAD_NORMAL,
            pady=(PAD_NORMAL, PAD_SMALL)
        )

        # ==========================================
        # CONTAINER DO LOG + SCROLLBAR
        # ==========================================

        textbox_frame = ctk.CTkFrame(
            log_frame,
            fg_color="transparent"
        )

        textbox_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=PAD_NORMAL,
            pady=(0, PAD_NORMAL)
        )

        textbox_frame.grid_columnconfigure(0, weight=1)
        textbox_frame.grid_rowconfigure(0, weight=1)

        # ==========================================
        # TEXTBOX
        # ==========================================

        self.log_textbox = ctk.CTkTextbox(
            textbox_frame,
            height=180,
            fg_color=COLORS["card"],
            text_color=COLORS["text_primary"],
            wrap="word"
        )

        self.log_textbox.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        # ==========================================
        # SCROLLBAR
        # ==========================================

        scrollbar = ctk.CTkScrollbar(
            textbox_frame,
            command=self.log_textbox.yview
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
            padx=(5, 0)
        )

        # ✅ Vincula scrollbar ao textbox
        self.log_textbox.configure(
            yscrollcommand=scrollbar.set
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

    def on_connection_mode_changed(self, mode):
        """
        Chamado quando modo de conexão muda.
        Mostra/esconde seções dinamicamente.
        """

        self.add_log(f"Modo alterado para {mode}")

        # ✅ NOVO: Esconder todas as seções
        self._hide_all_sections()

        # ✅ NOVO: Mostrar a seção correspondente
        if mode == "Serial":
            self.serial_section.grid(
                row=2,
                column=0,
                sticky="ew",
                padx=PAD_NORMAL,
                pady=(0, PAD_NORMAL)
            )

        elif mode == "API":
            self.api_section.grid(
                row=2,
                column=0,
                sticky="ew",
                padx=PAD_NORMAL,
                pady=(0, PAD_NORMAL)
            )

        elif mode == "MQTT":
            self.mqtt_section.grid(
                row=2,
                column=0,
                sticky="ew",
                padx=PAD_NORMAL,
                pady=(0, PAD_NORMAL)
            )

        elif mode == "Simulação":
            self.simulation_section.grid(
                row=2,
                column=0,
                sticky="ew",
                padx=PAD_NORMAL,
                pady=(0, PAD_NORMAL)
            )

    # =====================================================
    # HIDE SECTIONS
    # =====================================================

    def _hide_all_sections(self):
        """Esconde todas as seções de configuração."""
        if self.serial_section and self.serial_section.winfo_exists():
            self.serial_section.grid_remove()

        if self.api_section and self.api_section.winfo_exists():
            self.api_section.grid_remove()

        if self.mqtt_section and self.mqtt_section.winfo_exists():
            self.mqtt_section.grid_remove()

        if self.simulation_section and self.simulation_section.winfo_exists():
            self.simulation_section.grid_remove()

    # =====================================================
    # API TEST CONNECTION
    # =====================================================

    def api_test_connection(self):
        """Testa conexão HTTP com ESP32 e mostra latência."""
        try:
            from sensor_module.api_sensor_driver import APISensorDriver

            host = self.api_ip_entry.get()
            port = int(self.api_port_entry.get())
            endpoint = self.api_endpoint_entry.get()

            driver = APISensorDriver(
                host=host,
                port=port,
                endpoint=endpoint
            )

            latency = driver.ping()

            if latency is not None:
                self.api_latency_label.configure(
                    text=f"Latência: {latency:.1f}ms",
                    text_color=COLORS["primary"]
                )
                self.add_log(f"✅ ESP32 respondeu em {latency:.1f}ms")
            else:
                self.api_latency_label.configure(
                    text="Latência: --",
                    text_color=COLORS["danger"]
                )
                self.add_log("❌ ESP32 não responde")

        except ValueError:
            self.add_log("❌ Porta deve ser um número")
            self.api_latency_label.configure(
                text="Latência: --",
                text_color=COLORS["danger"]
            )
        except Exception as e:
            self.add_log(f"❌ Erro ao testar: {e}")
            self.api_latency_label.configure(
                text="Latência: --",
                text_color=COLORS["danger"]
            )
        
    def get_serial_ports(self):

        return SerialConnection.get_available_ports()