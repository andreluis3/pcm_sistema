from __future__ import annotations
import os
from tkinter import filedialog, messagebox

import customtkinter as ctk

from ui_styles import BG_COLOR

from .pcm_kpi import PCMKPIFrame
from .pcm_charts import PCMChartFrame
from .pcm_analysis import PANEL_COLOR, TEXT_SECONDARY, PCMAnalysisFrame
from .pcm_import import BORDER_COLOR, SUCCESS_COLOR, SUCCESS_COLOR, TEXT_PRIMARY, PCMImportFrame

from pcm_module.sensor_pcm_screen import (
    SensorKPIFrame,
    SensorChartFrame,
    PCMTemperatureSensor,
)


class PCMCalcScreen(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color=BG_COLOR)
        self.sensor = PCMTemperatureSensor()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=BG_COLOR
        )
        scroll.grid(row=0, column=0, sticky="nsew")

        scroll.grid_columnconfigure(0, weight=1)

        # =====================================================
        # PCM PRINCIPAL
        # =====================================================

        self.import_frame = PCMImportFrame(
            scroll,
            on_result=self._on_pcm_result
        )
        self.import_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(20, 10)
        )

        self.kpi_frame = PCMKPIFrame(scroll)
        self.kpi_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=10
        )

        self.chart_frame = PCMChartFrame(scroll)
        self.chart_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=20,
            pady=10
        )

        self.analysis_frame = PCMAnalysisFrame(scroll)
        self.analysis_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 30)
        )
        
        # =====================================================
        # HEADER SENSOR IR
        # =====================================================

        sensor_header = ctk.CTkFrame(
            scroll,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR
        )

        sensor_header.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=20,
            pady=(10, 10)
        )

        sensor_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sensor_header,
            text="Sensor Infravermelho — Monitoramento Térmico",
            font=("Inter", 24, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=24,
            pady=(20, 6)
        )

        ctk.CTkLabel(
            sensor_header,
            text="Importe o CSV do sensor IR para comparar temperatura e comportamento térmico.",
            font=("Inter", 13),
            text_color=TEXT_SECONDARY,
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=24,
            pady=(0, 18)
        )

        self.sensor_status = ctk.CTkLabel(
            sensor_header,
            text="Aguardando CSV do sensor...",
            font=("Inter", 12),
            text_color=TEXT_SECONDARY,
        )

        self.sensor_status.grid(
            row=2,
            column=0,
            sticky="w",
            padx=24,
            pady=(0, 18)
        )

        sensor_actions = ctk.CTkFrame(
            sensor_header,
            fg_color="transparent"
        )

        sensor_actions.grid(
            row=0,
            column=1,
            rowspan=3,
            padx=24,
            pady=20
        )

        ctk.CTkButton(
            sensor_actions,
            text="Importar CSV Sensor",
            width=220,
            height=42,
            command=self._import_sensor_csv,
        ).pack()

        # =====================================================
        # SENSOR IR
        # =====================================================
        # =====================================================
        # SENSOR IR KPI
        # =====================================================

        self.sensor_kpi = SensorKPIFrame(scroll)

        self.sensor_kpi.grid(
            row=5,
            column=0,
            sticky="ew",
            padx=20,
            pady=10
        )
       
        # =====================================================
        # GRÁFICO SENSOR
        # =====================================================

        self.sensor_chart = SensorChartFrame(scroll)

        self.sensor_chart.grid(
            row=6,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 40)
        )
    def _on_pcm_result(self, result):

        # =========================
        # KPI CARDS
        # =========================
        
        erro_percentual = (
            abs(result.q_notebook_j - 234000.0)
            / 234000.0
        ) * 100.0

        
        self.kpi_frame.update_kpis(
        q_notebook_j=result.q_notebook_j,
        massa_pcm_kg=1.0,
        eficiencia=result.eficiencia,
        erro_percentual=erro_percentual,
        potencia_w=result.potencia_media,
        duracao_min=result.delta_tempo / 60.0,
    )
    

        # =========================
        # GRÁFICOS
        # =========================
        self.chart_frame.render_charts(
            tempo_s=result.tempo_s,
            temperatura_c=result.temperatura_c,
            pico_temperatura=result.pico_temperatura,
            tempo_pico_s=result.tempo_pico_temperatura,
        )

        # =========================
        # ANÁLISE
        # =========================
        self.analysis_frame.update_analysis(result)
            
    def _import_sensor_csv(self):

        fp = filedialog.askopenfilename(
            title="Selecionar CSV do Sensor",
            filetypes=[("CSV", "*.csv")]
        )

        if not fp:
            return

        try:
            result = self.sensor.load_csv(fp)

            self.sensor_status.configure(
                text=f"CSV carregado: {os.path.basename(fp)}",
                text_color=SUCCESS_COLOR
            )

            self.sensor_kpi.update_from_result(result)

            self.sensor_chart.render(result)

        except Exception as e:
            messagebox.showerror(
                "Erro",
                str(e)
            )