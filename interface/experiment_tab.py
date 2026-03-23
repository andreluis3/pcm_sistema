from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

import customtkinter as ctk
from tkinter import messagebox

from database.database_manager import DatabaseManager
from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    WIDGET_HEIGHT_NORMAL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
)

DATE_FORMAT = "%d-%m-%y %H:%M"


@dataclass
class ExperimentFormData:
    material: str | None = None
    operador: str | None = None
    capsula: str | None = None
    massa: float | None = None
    tempo_inicio: str | None = None
    tempo_final: str | None = None
    delta_tempo: float | None = None
    temperatura_inicial: float | None = None
    temperatura_final: float | None = None
    delta_temperatura: float | None = None

    def as_db_dict(self) -> dict[str, Any]:
        return {
            "material": self.material,
            "operador": self.operador,
            "capsula": self.capsula,
            "massa": self.massa,
            "tempo_inicio": self.tempo_inicio,
            "tempo_final": self.tempo_final,
            "delta_tempo": self.delta_tempo,
            "temperatura_inicial": self.temperatura_inicial,
            "temperatura_final": self.temperatura_final,
            "delta_temperatura": self.delta_temperatura,
        }


class ExperimentTab(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        db_manager: DatabaseManager,
        on_saved: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, fg_color="#0D1117")
        self.db = db_manager
        self.on_saved = on_saved

        self._editing_id: int | None = None
        self._entries: dict[str, ctk.CTkEntry] = {}

        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Experimentos",
            text_color="#E5E7EB",
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(6, PAD_NORMAL))

        form = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        form.grid(row=1, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_LARGE))
        form.grid_columnconfigure(1, weight=1)

        row = 0
        row = self._field(form, row, "material", "Material", "Ex.: Óleo de Coco")
        row = self._field(form, row, "operador", "Operador", "Ex.: André")
        row = self._field(form, row, "capsula", "Cápsula", "Ex.: A1")
        row = self._field(form, row, "massa", "Massa (g)", "Ex.: 120")
        row = self._field(form, row, "tempo_inicio", "Tempo início (DD-MM-YY HH:MM)", "21-03-26 14:32")
        row = self._field(form, row, "tempo_final", "Tempo final (DD-MM-YY HH:MM)", "21-03-26 14:52")
        row = self._field(form, row, "delta_tempo", "Δ tempo (min)", "Calculado automaticamente", disabled=True)
        row = self._field(form, row, "temperatura_inicial", "Temperatura inicial (°C)", "Ex.: 24.0")
        row = self._field(form, row, "temperatura_final", "Temperatura final (°C)", "Ex.: 42.0")
        row = self._field(form, row, "delta_temperatura", "Δ temperatura (°C)", "Calculado automaticamente", disabled=True)

        actions = ctk.CTkFrame(form, fg_color="transparent")
        actions.grid(row=row, column=0, columnspan=2, sticky="w", padx=PAD_LARGE, pady=(PAD_SMALL, PAD_LARGE))

        self.btn_save = ctk.CTkButton(
            actions,
            text="Salvar Experimento",
            height=WIDGET_HEIGHT_NORMAL,
            corner_radius=12,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
            font=FONT_NORMAL,
            command=self.save_experiment,
        )
        self.btn_save.grid(row=0, column=0, padx=(0, PAD_SMALL))

        self.btn_clear = ctk.CTkButton(
            actions,
            text="Limpar",
            height=WIDGET_HEIGHT_NORMAL,
            corner_radius=12,
            fg_color="#1E2530",
            text_color="#E5E7EB",
            hover_color="#2A3341",
            font=FONT_NORMAL,
            command=self.clear_form,
        )
        self.btn_clear.grid(row=0, column=1)

    def _field(
        self,
        parent,
        row: int,
        key: str,
        label: str,
        placeholder: str,
        disabled: bool = False,
    ) -> int:
        lbl = ctk.CTkLabel(parent, text=label, text_color="#9AA0AB", font=FONT_NORMAL)
        lbl.grid(row=row, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL if row == 0 else 0, PAD_SMALL))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=WIDGET_HEIGHT_NORMAL, font=FONT_NORMAL)
        entry.grid(row=row, column=1, sticky="ew", padx=PAD_LARGE, pady=(PAD_NORMAL if row == 0 else 0, PAD_NORMAL))
        if disabled:
            entry.configure(state="disabled")
        else:
            entry.bind("<KeyRelease>", lambda _e: self._recompute_deltas())
        self._entries[key] = entry
        return row + 1

    def _get_str(self, key: str) -> str | None:
        value = self._entries[key].get().strip()
        return value or None

    def _get_float(self, key: str) -> float | None:
        value = self._get_str(key)
        if value is None:
            return None
        try:
            return float(value.replace(",", "."))
        except ValueError:
            raise ValueError(f"Valor inválido para '{key}': {value!r}")

    def get_form_data(self) -> ExperimentFormData:
        delta_tempo = self._get_float("delta_tempo")
        delta_temperatura = self._get_float("delta_temperatura")
        return ExperimentFormData(
            material=self._get_str("material"),
            operador=self._get_str("operador"),
            capsula=self._get_str("capsula"),
            massa=self._get_float("massa"),
            tempo_inicio=self._get_str("tempo_inicio"),
            tempo_final=self._get_str("tempo_final"),
            delta_tempo=delta_tempo,
            temperatura_inicial=self._get_float("temperatura_inicial"),
            temperatura_final=self._get_float("temperatura_final"),
            delta_temperatura=delta_temperatura,
        )

    def clear_form(self) -> None:
        for entry in self._entries.values():
            entry.configure(state="normal")
            entry.delete(0, "end")
        for key in ("delta_tempo", "delta_temperatura"):
            self._entries[key].configure(state="disabled")
        self._editing_id = None
        self.btn_save.configure(text="Salvar Experimento")

    def load_for_edit(self, experiment: dict[str, Any]) -> None:
        self.clear_form()
        self._editing_id = int(experiment["id"])

        for key, entry in self._entries.items():
            if key not in experiment:
                continue
            value = experiment[key]
            if value is None:
                continue
            entry.configure(state="normal")
            entry.insert(0, str(value))
            if key in ("delta_tempo", "delta_temperatura"):
                entry.configure(state="disabled")

        self.btn_save.configure(text=f"Salvar Alterações (ID {self._editing_id})")

    def save_experiment(self) -> None:
        self._recompute_deltas()
        try:
            data = self.get_form_data().as_db_dict()
        except ValueError as e:
            messagebox.showerror("Dados inválidos", str(e), parent=self.winfo_toplevel())
            return

        if not data.get("material"):
            messagebox.showwarning("Campos obrigatórios", "Informe o material.", parent=self.winfo_toplevel())
            return
        if not data.get("tempo_inicio") or not data.get("tempo_final"):
            messagebox.showwarning("Campos obrigatórios", "Informe tempo início e tempo final.", parent=self.winfo_toplevel())
            return

        try:
            self._parse_datetime(data["tempo_inicio"])
            self._parse_datetime(data["tempo_final"])
        except ValueError:
            messagebox.showerror(
                "Formato inválido",
                f"Use o formato {DATE_FORMAT.replace('%d', 'DD').replace('%m', 'MM').replace('%y', 'YY').replace('%H', 'HH').replace('%M', 'MM')}.",
                parent=self.winfo_toplevel(),
            )
            return

        try:
            if self._editing_id is None:
                new_id = self.db.insert_experiment(data)
                messagebox.showinfo(
                    "Salvo",
                    f"Experimento salvo com sucesso (ID {new_id}).",
                    parent=self.winfo_toplevel(),
                )
                self.clear_form()
            else:
                self.db.update_experiment(self._editing_id, data)
                messagebox.showinfo(
                    "Atualizado",
                    f"Experimento atualizado com sucesso (ID {self._editing_id}).",
                    parent=self.winfo_toplevel(),
                )
                self.clear_form()
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Erro", f"Falha ao salvar no banco: {e}", parent=self.winfo_toplevel())
            return

        if self.on_saved is not None:
            self.on_saved()

    def _parse_datetime(self, value: str | None) -> datetime:
        if not value:
            raise ValueError("Data vazia.")
        return datetime.strptime(value, DATE_FORMAT)

    def _recompute_deltas(self) -> None:
        tempo_inicio = self._get_str("tempo_inicio")
        tempo_final = self._get_str("tempo_final")
        temperatura_inicial = self._get_str("temperatura_inicial")
        temperatura_final = self._get_str("temperatura_final")

        delta_tempo_value = None
        delta_temp_value = None

        if tempo_inicio and tempo_final:
            try:
                dt_inicio = self._parse_datetime(tempo_inicio)
                dt_final = self._parse_datetime(tempo_final)
                delta_minutes = (dt_final - dt_inicio).total_seconds() / 60.0
                delta_tempo_value = round(delta_minutes, 2)
            except ValueError:
                delta_tempo_value = None

        if temperatura_inicial and temperatura_final:
            try:
                delta_temp_value = round(
                    float(temperatura_final.replace(",", ".")) - float(temperatura_inicial.replace(",", ".")),
                    2,
                )
            except ValueError:
                delta_temp_value = None

        self._set_disabled_field("delta_tempo", delta_tempo_value)
        self._set_disabled_field("delta_temperatura", delta_temp_value)

    def _set_disabled_field(self, key: str, value: float | None) -> None:
        entry = self._entries[key]
        entry.configure(state="normal")
        entry.delete(0, "end")
        if value is not None:
            entry.insert(0, str(value))
        entry.configure(state="disabled")
