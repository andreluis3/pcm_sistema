"""
pcm_import.py
═════════════
Frame de importação de arquivos CSV para o dashboard PCM.

Responsabilidade única: UI de importação + feedback de status.
Sem matplotlib, sem cálculos, sem sensors.

Comunica resultado via callback on_result(PCMResult).
"""
from __future__ import annotations

import os
from tkinter import filedialog, messagebox
from typing import Callable, Optional

import customtkinter as ctk

from .pcm_model import PCMResult
from .pcm_repository import PCMRepository
from .pcm_service import PCMService


PANEL_COLOR = "#111827"
BORDER_COLOR = "#334155"
TEXT_PRIMARY = "#F3F4F6"
TEXT_SECONDARY = "#9CA3AF"
SUCCESS_COLOR = "#E5E7EB"
BUTTON_COLOR = "#6B7280"
BUTTON_HOVER = "#4B5563"

# Diretório padrão de logs — ajuste conforme seu ambiente
DEFAULT_LOG_DIR = "/home/andre/pc_temperature"


class PCMImportFrame(ctk.CTkFrame):
    """
    Header + botão de importação CSV do experimento PCM.

    Após importação bem-sucedida, chama on_result(result: PCMResult).
    Em caso de erro, exibe messagebox e atualiza label de status.
    """

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        on_result: Callable[[PCMResult], None],
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            **kwargs,
        )
        self._on_result = on_result
        self._service = PCMService()
        self._repository = PCMRepository()
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        # Título
        ctk.CTkLabel(
            self,
            text="Cálculos de PCM — Dashboard Térmico",
            font=("Arial", 30, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(22, 6))

        # Subtítulo
        ctk.CTkLabel(
            self,
            text=(
                "Análise profissional de logs térmicos e energéticos com estimativa "
                "de massa de PCM para aplicações em hardware."
            ),
            font=("Arial", 15),
            text_color=TEXT_SECONDARY,
            wraplength=1080,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 16))

        # Botão de importação
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=2, sticky="e", padx=24, pady=18)

        ctk.CTkButton(
            actions,
            text="Importar CSV",
            command=self._import,
            width=190,
            height=42,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER,
            font=("Arial", 15, "bold"),
        ).pack()

        # Label de status
        self._status = ctk.CTkLabel(
            self,
            text="Aguardando arquivo CSV do diretório padrão de logs.",
            font=("Arial", 13),
            text_color=SUCCESS_COLOR,
        )
        self._status.grid(row=2, column=0, columnspan=2, sticky="w", padx=24, pady=(0, 20))

    # ── Importação ────────────────────────────────────────────────────────────

    def _import(self) -> None:
        initial = DEFAULT_LOG_DIR if os.path.isdir(DEFAULT_LOG_DIR) else os.path.expanduser("~")

        file_path = filedialog.askopenfilename(
            initialdir=initial,
            title="Selecionar arquivo CSV",
            filetypes=[("Arquivos CSV", "*.csv")],
        )
        if not file_path:
            return

        try:
            result = self._service.process_csv(file_path)
            self._repository.save(result)
        except Exception as exc:
            messagebox.showerror("Falha ao processar CSV", str(exc))
            self._set_status(f"Erro: {exc}", color=TEXT_PRIMARY)
            return

        self._set_status(
            f"Arquivo processado com sucesso: {os.path.basename(file_path)}",
            color=SUCCESS_COLOR,
        )
        self._on_result(result)

    def _set_status(self, text: str, *, color: str) -> None:
        if self._status.winfo_exists():
            self._status.configure(text=text, text_color=color)