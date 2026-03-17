from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import customtkinter as ctk
from tkinter import messagebox

from database.database_manager import DatabaseManager


@dataclass
class ExperimentFormData:
    material: str | None = None
    tempo_inicio: str | None = None
    end_time: str | None = None
    delta_time: float | None = None
    temperatura_inicial: float | None = None
    temperatura_final: float | None = None
    delta_temperatura: float | None = None
    massa: float | None = None
    capsula: str | None = None
    operador: str | None = None
    calor_latente: float | None = None
    calor_sensivel: float | None = None
    energia_armazenada: float | None = None
    eficiencia: float | None = None

    def as_db_dict(self) -> dict[str, Any]:
        return {
            "material": self.material,
            "tempo_inicio": self.tempo_inicio,
            "end_time": self.end_time,
            "delta_time": self.delta_time,
            "temperatura_inicial": self.temperatura_inicial,
            "temperatura_final": self.temperatura_final,
            "delta_temperatura": self.delta_temperatura,
            "massa": self.massa,
            "capsula": self.capsula,
            "operador": self.operador,
            "calor_latente": self.calor_latente,
            "calor_sensivel": self.calor_sensivel,
            "energia_armazenada": self.energia_armazenada,
            "eficiencia": self.eficiencia,
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
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(6, 12))

        form = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=18)
        form.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
        form.grid_columnconfigure(1, weight=1)

        row = 0
        row = self._field(form, row, "material", "Material", "Ex.: Óleo de Coco")
        row = self._field(form, row, "operador", "Operador", "Ex.: André")
        row = self._field(form, row, "capsula", "Cápsula", "Ex.: A1")
        row = self._field(form, row, "massa", "Massa (g)", "Ex.: 120")
        row = self._field(form, row, "tempo_inicio", "Tempo início (ISO)", "2026-03-17 10:00:00")
        row = self._field(form, row, "end_time", "Tempo fim (ISO)", "2026-03-17 10:05:00")
        row = self._field(form, row, "delta_time", "Δ tempo (s)", "Ex.: 300")
        row = self._field(form, row, "temperatura_inicial", "Temperatura inicial (°C)", "Ex.: 24.0")
        row = self._field(form, row, "temperatura_final", "Temperatura final (°C)", "Ex.: 42.0")
        row = self._field(form, row, "delta_temperatura", "Δ temperatura (°C)", "Ex.: 18.0")
        row = self._field(form, row, "calor_latente", "Calor latente (J)", "Ex.: 12000")
        row = self._field(form, row, "calor_sensivel", "Calor sensível (J)", "Ex.: 5000")
        row = self._field(form, row, "energia_armazenada", "Energia armazenada (J)", "Ex.: 17000")
        row = self._field(form, row, "eficiencia", "Eficiência (%)", "Ex.: 85")

        actions = ctk.CTkFrame(form, fg_color="transparent")
        actions.grid(row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(8, 16))

        self.btn_save = ctk.CTkButton(
            actions,
            text="Salvar Experimento",
            corner_radius=12,
            fg_color="#00F5D4",
            text_color="#0D1117",
            hover_color="#24FFE0",
            command=self.save_experiment,
        )
        self.btn_save.grid(row=0, column=0, padx=(0, 10))

        self.btn_clear = ctk.CTkButton(
            actions,
            text="Limpar",
            corner_radius=12,
            fg_color="#1E2530",
            text_color="#E5E7EB",
            hover_color="#2A3341",
            command=self.clear_form,
        )
        self.btn_clear.grid(row=0, column=1)

    def _field(self, parent, row: int, key: str, label: str, placeholder: str) -> int:
        lbl = ctk.CTkLabel(parent, text=label, text_color="#9AA0AB", font=ctk.CTkFont(size=12))
        lbl.grid(row=row, column=0, sticky="w", padx=16, pady=(12 if row == 0 else 0, 6))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder)
        entry.grid(row=row, column=1, sticky="ew", padx=16, pady=(12 if row == 0 else 0, 12))
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
        return ExperimentFormData(
            material=self._get_str("material"),
            tempo_inicio=self._get_str("tempo_inicio"),
            end_time=self._get_str("end_time"),
            delta_time=self._get_float("delta_time"),
            temperatura_inicial=self._get_float("temperatura_inicial"),
            temperatura_final=self._get_float("temperatura_final"),
            delta_temperatura=self._get_float("delta_temperatura"),
            massa=self._get_float("massa"),
            capsula=self._get_str("capsula"),
            operador=self._get_str("operador"),
            calor_latente=self._get_float("calor_latente"),
            calor_sensivel=self._get_float("calor_sensivel"),
            energia_armazenada=self._get_float("energia_armazenada"),
            eficiencia=self._get_float("eficiencia"),
        )

    def clear_form(self) -> None:
        for entry in self._entries.values():
            entry.delete(0, "end")
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
            entry.insert(0, str(value))

        self.btn_save.configure(text=f"Salvar Alterações (ID {self._editing_id})")

    def save_experiment(self) -> None:
        try:
            data = self.get_form_data().as_db_dict()
        except ValueError as e:
            messagebox.showerror("Dados inválidos", str(e), parent=self.winfo_toplevel())
            return

        if not data.get("material"):
            messagebox.showwarning("Campos obrigatórios", "Informe o material.", parent=self.winfo_toplevel())
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

