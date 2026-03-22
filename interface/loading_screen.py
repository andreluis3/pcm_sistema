from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk


class LoadingScreen(ctk.CTk):
    def __init__(self, duration_ms: int = 2500) -> None:
        super().__init__()

        self._duration_ms = duration_ms

        self.title("PCM Thermal Manager")
        self.geometry("520x320")
        self.configure(fg_color="#0D1117")
        self.resizable(False, False)

        self._center_window(520, 320)
        self._build_ui()

        self.after(self._duration_ms, self._finish)

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, fg_color="#0D1117")
        container.pack(expand=True, fill="both", padx=24, pady=24)

        title = ctk.CTkLabel(
            container,
            text="PCM Thermal Manager",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        title.pack(pady=(24, 8))

        subtitle = ctk.CTkLabel(
            container,
            text="Inicializando sistema...",
            text_color="#9AA0AB",
            font=ctk.CTkFont(size=13),
        )
        subtitle.pack(pady=(0, 28))

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "PCM.Horizontal.TProgressbar",
            troughcolor="#161B22",
            background="#00F5D4",
            bordercolor="#161B22",
            lightcolor="#00F5D4",
            darkcolor="#00C9AE",
        )

        progress = ttk.Progressbar(
            container,
            style="PCM.Horizontal.TProgressbar",
            mode="indeterminate",
            length=360,
        )
        progress.pack(pady=(0, 12))
        progress.start(12)

    def _finish(self) -> None:
        self.destroy()

    def _center_window(self, width: int, height: int) -> None:
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
