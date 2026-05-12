from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image
import tkinter as tk

from ui_styles import FONT_HEADER, FONT_NORMAL, PAD_SMALL, PAD_LARGE, THEME_COLORS


class LoadingScreen(ctk.CTk):
    def __init__(self, duration_ms: int = 2000) -> None:
        super().__init__()

        self._duration_ms = duration_ms
        self._pulse_radius = 16
        self._pulse_dir = 1
        self._animate_id = None  # CORREÇÃO: Armazenar ID do after para cancelar
        self._finish_after_id = None

        self.title("ThermalManager")
        self.geometry("460x360")
        self.configure(fg_color=THEME_COLORS["bg"])
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._center_window(460, 360)
        self._build_ui()

        self._animate_id = self.after(80, self._animate_pulse)
        self._finish_after_id = self.after(self._duration_ms, self._finish)

    def _on_close(self) -> None:
        self._cleanup_after_jobs()
        self.destroy()

    def _cleanup_after_jobs(self) -> None:
        if self._finish_after_id is not None:
            try:
                self.after_cancel(self._finish_after_id)
            except Exception:
                pass
            self._finish_after_id = None
        if self._animate_id is not None:
            try:
                self.after_cancel(self._animate_id)
            except Exception:
                pass
            self._animate_id = None

    def _build_ui(self) -> None:
        # UI REFATORADA: loading com tipografia e cores consistentes
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg"], corner_radius=0)
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_rowconfigure(4, weight=1)
        container.grid_columnconfigure(0, weight=1)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        self._logo_image = ctk.CTkImage(Image.open(logo_path), size=(120, 120))
        logo = ctk.CTkLabel(container, image=self._logo_image, text="")
        logo.grid(row=1, column=0, pady=(PAD_LARGE, PAD_SMALL))

        title = ctk.CTkLabel(
            container,
            text="ThermalManager",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        title.grid(row=2, column=0, pady=(0, PAD_SMALL))

        subtitle = ctk.CTkLabel(
            container,
            text="Inicializando sistema...",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_NORMAL,
        )
        subtitle.grid(row=3, column=0, pady=(0, PAD_LARGE))

        self._pulse_canvas = tk.Canvas(
            container,
            width=80,
            height=80,
            highlightthickness=0,
            bg=THEME_COLORS["bg"],
        )
        self._pulse_canvas.grid(row=4, column=0)

        self._pulse_circle = self._pulse_canvas.create_oval(
            40 - self._pulse_radius,
            40 - self._pulse_radius,
            40 + self._pulse_radius,
            40 + self._pulse_radius,
            fill=THEME_COLORS["primary"],
            outline="",
        )

    def _animate_pulse(self) -> None:
        # CORREÇÃO: Verificar se widget ainda existe antes de animar
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
            
        radius = self._pulse_radius
        if radius >= 20:
            self._pulse_dir = -1
        elif radius <= 14:
            self._pulse_dir = 1

        self._pulse_radius += self._pulse_dir
        r = self._pulse_radius
        self._pulse_canvas.coords(self._pulse_circle, 40 - r, 40 - r, 40 + r, 40 + r)
        self._animate_id = self.after(60, self._animate_pulse)

    def _finish(self) -> None:
        self._cleanup_after_jobs()
        self.destroy()

    def destroy(self) -> None:
        self._cleanup_after_jobs()
        super().destroy()

    def _center_window(self, width: int, height: int) -> None:
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        self.geometry(f"{width}x{height}+{x}+{y}")


    def destroy(self):

        if self._animate_id is not None:

            try:
                self.after_cancel(self._animate_id)
            except Exception:
                pass

            self._animate_id = None

        if self._finish_after_id is not None:

            try:
                self.after_cancel(self._finish_after_id)
            except Exception:
                pass

            self._finish_after_id = None

        super().destroy()