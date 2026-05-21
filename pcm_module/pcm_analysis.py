"""
pcm_analysis.py
═══════════════
Frame de análise técnica e preview do CSV.

Responsabilidade única: exibir texto de análise e tabela de preview.
Sem matplotlib, sem cálculos, sem I/O.
"""
from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from .pcm_model import PCMResult
from .pcm_metrics import (
    calcular_metricas_experimento,
    formatar_tempo_min_seg,
)


PANEL_COLOR = "#111827"
CARD_COLOR = "#0F172A"
BORDER_COLOR = "#334155"
TEXT_PRIMARY = "#F3F4F6"
TEXT_SECONDARY = "#9CA3AF"


class PCMAnalysisFrame(ctk.CTkFrame):
    """
    Exibe a análise técnica automatizada e o preview tabular do CSV.

    Recebe PCMResult já processado — sem acesso ao pandas.
    """

    def __init__(self, parent: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(
            parent,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="Análise Técnica Automatizada",
            font=("Arial", 20, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(18, 6))

        self._analysis_box = ctk.CTkTextbox(
            self,
            height=160,
            fg_color=CARD_COLOR,
            text_color=TEXT_PRIMARY,
            font=("Courier New", 14),
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self._analysis_box.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 18))

        ctk.CTkLabel(
            self,
            text="Preview dos Dados do CSV",
            font=("Arial", 20, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=2, column=0, sticky="w", padx=22, pady=(10, 6))

        self._log_box = ctk.CTkTextbox(
            self,
            height=210,
            fg_color=CARD_COLOR,
            text_color=TEXT_PRIMARY,
            font=("Courier New", 13),
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self._log_box.grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 18))

        self._reset_text()

    # ── API pública ───────────────────────────────────────────────────────────

    def update(self, result: PCMResult) -> None:
        """
        Atualiza análise técnica e preview a partir de um PCMResult.

        Constrói texto a partir de tipos primitivos — sem pandas.Series.
        """
        metricas = calcular_metricas_experimento(
            tempo_s=result.tempo_s,
            temperatura_c=result.temperatura_c,
            energia_total=result.energia_total,
            massa_pcm=result.massa_pcm,
            energia_teorica=result.energia_teorica,
            pico_temperatura=result.pico_temperatura,
            tempo_pico_temperatura=result.tempo_pico_temperatura,
            potencia_media=result.potencia_media,
            delta_tempo=result.delta_tempo,
            temperatura_media=result.temperatura_media,
        )

        tempo_pcm_min = float(metricas.get("tempo_atuacao_pcm_s") or 0.0) / 60.0

        lines: list[str] = ["[Análise Técnica]"]
        lines.append(
            f"- Pico: {result.pico_temperatura:.2f} °C "
            f"em {formatar_tempo_min_seg(result.tempo_pico_temperatura)}."
        )
        lines.append(
            f"- Tempo até 55 °C: {formatar_tempo_min_seg(metricas.get('tempo_ate_55c_s'))}."
        )
        lines.append(f"- Atuação do PCM (50–60 °C): {tempo_pcm_min:.2f} min.")

        for line in result.analise_tecnica:
            lines.append(f"- {line}")

        lines.append(f"- Δt total analisado: {result.delta_tempo:.2f} s.")
        lines.append(f"- Temperatura média: {result.temperatura_media:.2f} °C.")
        lines.append("")
        lines.append("[Cálculo Detalhado]")
        for line in result.calculo_detalhado:
            lines.append(f"- {line}")

        self._write(self._analysis_box, "\n".join(lines))
        self._write(self._log_box, self._format_preview(result.csv_preview))

    def reset(self) -> None:
        """Reseta para o estado inicial."""
        self._reset_text()

    # ── Internos ──────────────────────────────────────────────────────────────

    def _reset_text(self) -> None:
        self._write(
            self._analysis_box,
            "Importe um arquivo CSV para gerar a interpretação técnica do ensaio.",
        )
        self._write(
            self._log_box,
            (
                "timestamp           tempo_s  potencia_w  temperatura_c  energia_j\n"
                "------------------  -------  ----------  -------------  ---------\n"
                "Aguardando importação do arquivo."
            ),
        )

    @staticmethod
    def _write(box: ctk.CTkTextbox, content: str) -> None:
        if not box.winfo_exists():
            return
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", content)
        box.configure(state="disabled")

    @staticmethod
    def _format_preview(preview_rows: list[dict[str, str]]) -> str:
        if not preview_rows:
            return "Nenhum dado disponível para exibição."

        headers = ["timestamp", "tempo_s", "potencia_w", "temperatura_c", "energia_j"]
        widths: dict[str, int] = {h: len(h) for h in headers}

        for row in preview_rows:
            for h in headers:
                widths[h] = max(widths[h], len(str(row.get(h, ""))))

        header_line = "  ".join(h.ljust(widths[h]) for h in headers)
        sep_line = "  ".join("-" * widths[h] for h in headers)
        data_lines = [
            "  ".join(str(row.get(h, "")).ljust(widths[h]) for h in headers)
            for row in preview_rows
        ]
        return "\n".join([header_line, sep_line, *data_lines])