from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from .pcm_model import PCMResult


class PCMService:
    REQUIRED_COLUMNS = {"energia_j", "tempo_s", "potencia_w", "temperatura_c"}
    CALOR_ESPECIFICO = 2000.0
    TEMPERATURA_FUSAO = 52.0
    TEMPERATURA_REFERENCIA = 25.0
    CALOR_LATENTE = 180000.0

    def process_csv(self, csv_path: str | Path) -> PCMResult:
        df = pd.read_csv(csv_path)
        self._validate_dataframe(df)
        df = self._normalize_dataframe(df)

        energia_inicial = float(df["energia_j"].iloc[0])
        energia_final = float(df["energia_j"].iloc[-1])
        tempo_inicial = float(df["tempo_s"].iloc[0])
        tempo_final = float(df["tempo_s"].iloc[-1])

        energia_total = energia_final - energia_inicial
        tempo_total = tempo_final - tempo_inicial

        if tempo_total <= 0:
            raise ValueError("O tempo total calculado deve ser maior que zero.")
        if energia_total < 0:
            raise ValueError("A energia total calculada nao pode ser negativa.")

        potencia_media = energia_total / tempo_total
        pico_potencia = float(df["potencia_w"].max())
        pico_temperatura = float(df["temperatura_c"].max())

        delta_t = self.TEMPERATURA_FUSAO - self.TEMPERATURA_REFERENCIA
        q_total = (self.CALOR_ESPECIFICO * delta_t) + self.CALOR_LATENTE
        massa_pcm_kg = energia_total / q_total
        massa_pcm_g = massa_pcm_kg * 1000.0

        return PCMResult(
            energia_total=energia_total,
            tempo_total=tempo_total,
            potencia_media=potencia_media,
            massa_pcm=massa_pcm_g,
            pico_potencia=pico_potencia,
            pico_temperatura=pico_temperatura,
            data_execucao=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized_df = df.copy()

        for column in self.REQUIRED_COLUMNS:
            normalized_df[column] = pd.to_numeric(normalized_df[column], errors="raise")

        return normalized_df

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        missing_columns = self.REQUIRED_COLUMNS.difference(df.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV invalido. Colunas ausentes: {missing}.")

        if df.empty:
            raise ValueError("O CSV informado esta vazio.")

        for column in self.REQUIRED_COLUMNS:
            if df[column].isnull().any():
                raise ValueError(f"A coluna '{column}' possui valores nulos.")

        if len(df.index) < 2:
            raise ValueError("O CSV deve conter pelo menos duas linhas para calcular os intervalos.")
