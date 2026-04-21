from __future__ import annotations

from tkinter import filedialog, messagebox

import customtkinter as ctk

from .pcm_repository import PCMRepository
from .pcm_service import PCMService


class PCMCalcScreen(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0B0F19")
        self.service = PCMService()
        self.repository = PCMRepository()

        self._build_layout()

    def _build_layout(self) -> None:
        container = ctk.CTkFrame(self, fg_color="#0B0F19")
        container.pack(fill="both", expand=True, padx=40, pady=40)

        self.title_label = ctk.CTkLabel(
            container,
            text="Quanto de óleo de coco (PCM) eu preciso para absorver a energia do meu notebook durante X tempo?",
            font=("Arial", 24, "bold"),
            text_color="white",
            justify="center",
            wraplength=900,
        )
        self.title_label.pack(pady=(20, 30))

        self.import_button = ctk.CTkButton(
            container,
            text="Importar CSV",
            command=self.import_csv,
            width=220,
            height=42,
        )
        self.import_button.pack(pady=10)

        self.mass_label = ctk.CTkLabel(
            container,
            text="Massa de PCM: -- g",
            font=("Arial", 28, "bold"),
            text_color="#4ADE80",
            justify="center",
        )
        self.mass_label.pack(pady=(20, 16))

        self.output_box = ctk.CTkTextbox(
            container,
            width=760,
            height=340,
            fg_color="#111827",
            text_color="white",
            corner_radius=12,
            font=("Arial", 16),
        )
        self.output_box.pack(pady=10, fill="both", expand=True)
        self.output_box.insert(
            "1.0",
            "Importe um arquivo CSV para visualizar:\n"
            "- Energia total\n"
            "- Tempo total\n"
            "- Potência média\n"
            "- Pico de potência\n"
            "- Pico de temperatura\n"
            "- Massa de PCM necessária\n"
        )
        self.output_box.configure(state="disabled")

    def import_csv(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo CSV",
            filetypes=[("Arquivos CSV", "*.csv")],
        )
        if not file_path:
            return

        try:
            result = self.service.process_csv(file_path)
            self.repository.save(result)
        except ValueError as exc:
            messagebox.showerror("CSV inválido", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Erro", f"Não foi possível processar o arquivo.\n{exc}")
            return

        self.mass_label.configure(text=f"Massa de PCM: {result.massa_pcm:.2f} g")

        output = (
            f"Energia total: {result.energia_total:.2f} J\n"
            f"Tempo total: {result.tempo_total:.2f} s\n"
            f"Potência média: {result.potencia_media:.2f} W\n"
            f"Pico de potência: {result.pico_potencia:.2f} W\n"
            f"Pico de temperatura: {result.pico_temperatura:.2f} °C\n"
            f"Massa de PCM: {result.massa_pcm:.2f} g\n"
        )

        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", output)
        self.output_box.configure(state="disabled")


# Compatibilidade com integrações anteriores.
PCMScreen = PCMCalcScreen
