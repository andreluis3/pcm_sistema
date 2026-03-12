import random
from collections import deque
from typing import Deque

import customtkinter as ctk
from tkinter import Canvas

from .charts import LineChart
from .sidebar import Sidebar
from .materials import MaterialsPage
from .tests import TemperatureTestsPage
from .database_page import DatabasePage


BG = "#0D1117"
CARD = "#161B22"
SIDEBAR = "#15181F"
CYAN = "#00F5D4"
AMBER = "#FFB800"
TEXT = "#E5E7EB"
MUTED = "#9AA0AB"


class PCMDashboard(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PCM Thermal Manager")
        self.geometry("1280x760")
        self.minsize(1100, 680)
        self.configure(fg_color=BG)

        self._temperature = 30.3
        self._temp_history: Deque[float] = deque(maxlen=80)
        self._energy_history: Deque[float] = deque(maxlen=80)

        self._build_layout()
        self.after(500, self._update_loop)

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, bg_color=SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ctk.CTkFrame(self, fg_color=BG)
        self.content.grid(row=0, column=1, sticky="nsew", padx=20, pady=16)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        self.pages = {}
        self.pages["Dashboard"] = self._build_dashboard_page(self.content)
        self.pages["Materials"] = MaterialsPage(self.content)
        self.pages["Temperature Tests"] = TemperatureTestsPage(self.content)
        self.pages["Database"] = DatabasePage(self.content)
        self.pages["Settings"] = self._build_placeholder_page("Settings")

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page("Dashboard")
        for btn in self.sidebar.menu_buttons:
            btn.configure(command=lambda b=btn: self._on_menu_click(b))

    def _on_menu_click(self, btn) -> None:
        label = getattr(btn, "_label", btn.cget("text"))
        self.sidebar.set_active(label)
        self.show_page(label)

    def show_page(self, name: str) -> None:
        for key, page in self.pages.items():
            page.grid_remove()
        self.pages[name].grid()

    def _build_placeholder_page(self, title: str) -> ctk.CTkFrame:
        page = ctk.CTkFrame(self.content, fg_color=BG)
        page.grid_columnconfigure(0, weight=1)
        label = ctk.CTkLabel(page, text=title, text_color=TEXT, font=ctk.CTkFont(size=22, weight="bold"))
        label.grid(row=0, column=0, sticky="w", padx=16, pady=16)
        return page

    def _build_dashboard_page(self, parent) -> ctk.CTkFrame:
        page = ctk.CTkFrame(parent, fg_color=BG)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(page, fg_color=BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="PCM Thermal Manager",
            text_color=TEXT,
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        self.temp_card = ctk.CTkFrame(header, fg_color=CARD, corner_radius=20)
        self.temp_card.grid(row=0, column=1, padx=(12, 0))

        self.temp_value = ctk.CTkLabel(
            self.temp_card,
            text="30.3 °C",
            text_color=CYAN,
            font=ctk.CTkFont(family="Courier", size=34, weight="bold"),
        )
        self.temp_value.grid(row=0, column=0, padx=18, pady=(12, 4))

        self.phase_label = ctk.CTkLabel(
            self.temp_card,
            text="Liquid",
            text_color=CYAN,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.phase_label.grid(row=1, column=0, padx=18, pady=(0, 14), sticky="w")

        body = ctk.CTkFrame(page, fg_color=BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, weight=1)
        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        chart_card_1 = ctk.CTkFrame(body, fg_color=CARD, corner_radius=18)
        chart_card_1.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=(0, 12), pady=(0, 12))
        chart_card_1.grid_columnconfigure(0, weight=1)

        self.temp_chart = LineChart(chart_card_1, "Temperature vs Time", color=CYAN)
        self.temp_chart.widget.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)

        chart_card_2 = ctk.CTkFrame(body, fg_color=CARD, corner_radius=18)
        chart_card_2.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(0, 12))
        chart_card_2.grid_columnconfigure(0, weight=1)

        self.energy_chart = LineChart(chart_card_2, "Energy vs Time", color="#62FFA7")
        self.energy_chart.widget.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)

        material_card = ctk.CTkFrame(body, fg_color=CARD, corner_radius=20)
        material_card.grid(row=0, column=2, rowspan=2, sticky="nsew")
        material_card.grid_rowconfigure(2, weight=1)

        mat_title = ctk.CTkLabel(
            material_card,
            text="Material State",
            text_color=TEXT,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        mat_title.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 6))

        self.cylinder = Canvas(material_card, width=240, height=340, bg=CARD, highlightthickness=0)
        self.cylinder.grid(row=1, column=0, padx=18, pady=(0, 10))
        self._draw_cylinder("Liquid")

        self.material_state = ctk.CTkLabel(
            material_card,
            text="Liquid",
            text_color=CYAN,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.material_state.grid(row=2, column=0, sticky="w", padx=18)

        self.material_name = ctk.CTkLabel(
            material_card,
            text="Coconut Oil",
            text_color=MUTED,
            font=ctk.CTkFont(size=13),
        )
        self.material_name.grid(row=3, column=0, sticky="w", padx=18, pady=(0, 18))

        return page

    def _draw_cylinder(self, state: str) -> None:
        self.cylinder.delete("all")
        self.cylinder.create_oval(50, 40, 190, 80, outline="", fill="#1E2530")
        self.cylinder.create_rectangle(50, 60, 190, 270, outline="", fill="#141820")
        self.cylinder.create_oval(50, 250, 190, 290, outline="", fill="#10141B")

        if state.lower() == "solid":
            top_color = AMBER
            bottom_color = "#F1F1F1"
            label = "Solid"
            label_color = "#0D1117"
        else:
            top_color = CYAN
            bottom_color = "#BFFCF0"
            label = "Liquid"
            label_color = "#0D1117"

        self.cylinder.create_rectangle(60, 90, 180, 190, outline="", fill=top_color)
        self.cylinder.create_rectangle(60, 190, 180, 250, outline="", fill=bottom_color)
        self.cylinder.create_text(120, 155, text=label, fill=label_color, font=("Courier", 16, "bold"))

    def _update_loop(self) -> None:
        self._temperature += random.uniform(-0.4, 0.7)
        self._temperature = max(20.0, min(36.0, self._temperature))

        phase = "Liquid" if self._temperature >= 27.5 else "Solid"
        phase_color = CYAN if phase == "Liquid" else AMBER

        self.temp_value.configure(text=f"{self._temperature:.1f} °C", text_color=phase_color)
        self.phase_label.configure(text=phase, text_color=phase_color)
        self.material_state.configure(text=phase, text_color=phase_color)
        self._draw_cylinder(phase)

        energy = self._temperature * 0.12 + random.uniform(-0.2, 0.2)
        self._temp_history.append(self._temperature)
        self._energy_history.append(energy)

        self.temp_chart.push(self._temperature)
        self.temp_chart.draw()
        self.energy_chart.push(energy)
        self.energy_chart.draw()

        self.after(1000, self._update_loop)
