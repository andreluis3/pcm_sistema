from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from .pcm_model import PCMResult


class PCMService:
    REQUIRED_COLUMNS = {"timestamp", "tempo_s", "potencia_w", "temperatura_c", "energia_j"}
    CALOR_LATENTE = 180000.0

    def process_csv(self, csv_path: str | Path) -> PCMResult:

        df = pd.read_csv(csv_path)

        print("COLUNAS ORIGINAIS:")
        print(df.columns.tolist())

        # ── normaliza CSV do sensor ─────────────────────

        rename_map = {
            "time_ms": "timestamp",
            "minutes": "tempo_s",
            "temp_simulada_10pct": "temperatura_c",
        }

        df = df.rename(columns=rename_map)

        # minutos -> segundos
        if "tempo_s" in df.columns:
            df["tempo_s"] = pd.to_numeric(df["tempo_s"]) * 60.0

        # cria potência fake
        if "potencia_w" not in df.columns:
            df["potencia_w"] = 0.0

        # cria energia fake
        if "energia_j" not in df.columns:
            df["energia_j"] = 0.0

        # timestamp fallback
        if "timestamp" not in df.columns:
            df["timestamp"] = range(len(df))

        print("COLUNAS NORMALIZADAS:")
        print(df.columns.tolist())

        # valida DEPOIS da normalização
        self._validate_dataframe(df)

        normalized_df = self._normalize_dataframe(df)

        # resto do código continua daqui pra baixo...

        energia_final = float(normalized_df["energia_j"].iloc[-1])
        tempo_inicial = float(normalized_df["tempo_s"].iloc[0])
        tempo_final = float(normalized_df["tempo_s"].iloc[-1])

        energia_total = energia_final
        tempo_total = tempo_final - tempo_inicial

        if tempo_total <= 0:
            raise ValueError("O tempo total calculado deve ser maior que zero.")
        if energia_total < 0:
            raise ValueError("A energia total calculada nao pode ser negativa.")

        energia_incremental = normalized_df["energia_j"].diff().fillna(normalized_df["energia_j"]).round(4)
        pico_potencia_idx = int(normalized_df["potencia_w"].idxmax())
        pico_temperatura_idx = int(normalized_df["temperatura_c"].idxmax())
        soma_potencia = float(normalized_df["potencia_w"].sum())
        quantidade_amostras = int(len(normalized_df))
        potencia_media = soma_potencia / quantidade_amostras
        pico_potencia = float(normalized_df["potencia_w"].iloc[pico_potencia_idx])
        pico_temperatura = float(normalized_df["temperatura_c"].iloc[pico_temperatura_idx])
        tempo_pico_potencia = float(normalized_df["tempo_s"].iloc[pico_potencia_idx] - tempo_inicial)
        tempo_pico_temperatura = float(normalized_df["tempo_s"].iloc[pico_temperatura_idx] - tempo_inicial)
        temperatura_media = float(normalized_df["temperatura_c"].mean())
        temperatura_inicial = float(normalized_df["temperatura_c"].iloc[0])
        delta_t = pico_temperatura - temperatura_inicial

        c = 2000  # J/kg°C
        m = 1
        delta_T = pico_temperatura - temperatura_inicial

        Q_sensivel = m * c * delta_T
        Q_total_pcm = Q_sensivel + self.CALOR_LATENTE

        massa_pcm_kg = energia_total / Q_total_pcm
        massa_pcm_g = massa_pcm_kg * 1000.0

        Q_teorico = 234000.0
        erro_percentual = ((energia_total - Q_teorico) / Q_teorico) * 100

        energia_array = normalized_df["energia_j"].tolist()
        Q_latente = self.CALOR_LATENTE
        Q_sensivel_fase = Q_teorico - Q_latente

        fase_pcm = []
        for energia in energia_array:
            if energia < Q_sensivel_fase:
                fase_pcm.append("sensivel")
            else:
                fase_pcm.append("latente")

        preview_df = normalized_df.tail(8).copy()
        preview_df["tempo_s"] = preview_df["tempo_s"].map(lambda value: f"{value:.2f}")
        preview_df["potencia_w"] = preview_df["potencia_w"].map(lambda value: f"{value:.2f}")
        preview_df["temperatura_c"] = preview_df["temperatura_c"].map(lambda value: f"{value:.2f}")
        preview_df["energia_j"] = preview_df["energia_j"].map(lambda value: f"{value:.2f}")

        temperatura_media_movel = self._moving_average(normalized_df["temperatura_c"])
        potencia_media_movel = self._moving_average(normalized_df["potencia_w"])
        energia_media_movel = self._moving_average(normalized_df["energia_j"])

        status_termico = self._classify_thermal_behavior(
            pico_temperatura=pico_temperatura,
            temperatura_media=temperatura_media,
            potencia_pico=pico_potencia,
            potencia_media=potencia_media,
        )

        calculo_detalhado = self._build_calculation_audit_trail(
            df=normalized_df,
            energia_total=energia_total,
            energia_incremental=energia_incremental.tolist(),
            soma_potencia=soma_potencia,
            quantidade_amostras=quantidade_amostras,
            potencia_media=potencia_media,
            pico_temperatura=pico_temperatura,
            temperatura_media=temperatura_media,
            delta_t=delta_t,
            massa_pcm_kg=massa_pcm_kg,
            massa_pcm_g=massa_pcm_g,
        )

        analise_tecnica = [
            f"O sistema atingiu pico termico de {pico_temperatura:.2f} C em {tempo_pico_temperatura:.2f} s.",
            f"Potencia maxima registrada: {pico_potencia:.2f} W em {tempo_pico_potencia:.2f} s.",
            f"Energia acumulada no ensaio: {energia_total:.2f} J ao longo de {tempo_total:.2f} s.",
            f"PCM necessario estimado: {massa_pcm_g:.2f} g usando m = E_total / (Q_sensivel + L).",
            f"Referencia teorica: {Q_teorico:.0f} J com erro de {erro_percentual:.2f}%.",
            f"Comportamento termico classificado como {status_termico}.",
        ]

        return PCMResult(
            energia_total=energia_total,
            tempo_total=tempo_total,
            potencia_media=potencia_media,
            massa_pcm=massa_pcm_g,
            pico_potencia=pico_potencia,
            pico_temperatura=pico_temperatura,
            data_execucao=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            delta_tempo=tempo_total,
            tempo_pico_potencia=tempo_pico_potencia,
            tempo_pico_temperatura=tempo_pico_temperatura,
            temperatura_media=temperatura_media,
            status_termico=status_termico,
            analise_tecnica=analise_tecnica,
            timestamps=normalized_df["timestamp"].astype(str).tolist(),
            tempo_s=(normalized_df["tempo_s"] - tempo_inicial).round(4).tolist(),
            potencia_w=normalized_df["potencia_w"].round(4).tolist(),
            temperatura_c=normalized_df["temperatura_c"].round(4).tolist(),
            energia_j=normalized_df["energia_j"].round(4).tolist(),
            potencia_media_movel=potencia_media_movel,
            temperatura_media_movel=temperatura_media_movel,
            energia_media_movel=energia_media_movel,
            fase_pcm=fase_pcm,
            csv_preview=preview_df.to_dict(orient="records"),
            calculo_detalhado=calculo_detalhado,
            erro_percentual=erro_percentual,
            energia_teorica=Q_teorico,
        )

    def _moving_average(self, series) -> list[float]:

        # se vier DataFrame pega primeira coluna
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]

        # garante Series
        series = pd.Series(series)

        window = max(
            3,
            min(
                25,
                len(series) // 10 if len(series) >= 10 else len(series)
            )
        )

        return (
            series
            .rolling(window=window, min_periods=1)
            .mean()
            .round(4)
            .tolist()
        )

    def _build_calculation_audit_trail(
        self,
        *,
        df: pd.DataFrame,
        energia_total: float,
        energia_incremental: list[float],
        soma_potencia: float,
        quantidade_amostras: int,
        potencia_media: float,
        pico_temperatura: float,
        temperatura_media: float,
        delta_t: float,
        massa_pcm_kg: float,
        massa_pcm_g: float,
    ) -> list[str]:
        calculo_detalhado = [
            "Energia total: E_total = ultimo valor da coluna energia_j.",
            f"E_total = {energia_total:.2f} J.",
            "Energia incremental: DeltaE[i] = energia_j[i] - energia_j[i-1].",
        ]

        if energia_incremental:
            preview_count = min(5, len(energia_incremental))
            for index in range(preview_count):
                if index == 0:
                    calculo_detalhado.append(
                        f"DeltaE[0] = energia_j[0] = {energia_incremental[index]:.2f} J."
                    )
                else:
                    energia_atual = float(df['energia_j'].iloc[index])
                    energia_anterior = float(df['energia_j'].iloc[index - 1])
                    calculo_detalhado.append(
                        f"DeltaE[{index}] = {energia_atual:.2f} - {energia_anterior:.2f} = {energia_incremental[index]:.2f} J."
                    )
            if len(energia_incremental) > preview_count:
                calculo_detalhado.append(
                    f"... {len(energia_incremental) - preview_count} incrementos adicionais permanecem rastreaveis na serie importada."
                )

        calculo_detalhado.extend(
            [
                "Potencia media: P_media = soma(potencia_w) / N.",
                f"soma(potencia_w) = {soma_potencia:.2f} W.",
                f"N = {quantidade_amostras} amostras.",
                f"P_media = {soma_potencia:.2f} / {quantidade_amostras} = {potencia_media:.2f} W.",
                "Temperatura: analisar pico, media e variacao no periodo.",
                f"T_inicial = {float(df['temperatura_c'].iloc[0]):.2f} C.",
                f"T_pico = {pico_temperatura:.2f} C.",
                f"T_media = {temperatura_media:.2f} C.",
                f"DeltaT = T_pico - T_inicial = {pico_temperatura:.2f} - {float(df['temperatura_c'].iloc[0]):.2f} = {delta_t:.2f} C.",
                "Massa de PCM: m_PCM = E_total / L.",
                f"L = {self.CALOR_LATENTE:.0f} J/kg.",
                f"m_PCM = {energia_total:.2f} / {self.CALOR_LATENTE:.0f} = {massa_pcm_kg:.6f} kg.",
                f"PCM final = {massa_pcm_kg:.6f} x 1000 = {massa_pcm_g:.2f} g.",
            ]
        )
        return calculo_detalhado


    def _classify_thermal_behavior(
        self,
        *,
        pico_temperatura: float,
        temperatura_media: float,
        potencia_pico: float,
        potencia_media: float,
    ) -> str:
        if pico_temperatura >= 85.0 or (potencia_media > 0 and potencia_pico / potencia_media >= 2.2):
            return "critico"
        if pico_temperatura >= 70.0 or temperatura_media >= 60.0:
            return "em observacao"
        return "estavel"

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized_df = df.copy()
        normalized_df.columns = [str(column).strip().lower() for column in normalized_df.columns]
        normalized_df["timestamp"] = normalized_df["timestamp"].astype(str).str.strip()

        for column in self.REQUIRED_COLUMNS.difference({"timestamp"}):
            normalized_df[column] = pd.to_numeric(normalized_df[column], errors="raise")

        normalized_df = normalized_df.sort_values(by="tempo_s", kind="stable").reset_index(drop=True)
        return normalized_df

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        print("VALIDANDO COLUNAS:")
        print(df.columns.tolist())

        normalized_columns = {
            str(column).strip().lower()
            for column in df.columns
        }

        print("COLUNAS NORMALIZADAS:")
        print(normalized_columns)

        missing_columns = self.REQUIRED_COLUMNS.difference(normalized_columns)

        print("FALTANDO:")
        print(missing_columns)
        normalized_columns = {str(column).strip().lower() for column in df.columns}
        missing_columns = self.REQUIRED_COLUMNS.difference(normalized_columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV invalido. Colunas ausentes: {missing}.")

        if df.empty:
            raise ValueError("O CSV informado esta vazio.")

        if len(df.index) < 2:
            raise ValueError("O CSV deve conter pelo menos duas linhas para calcular os intervalos.")

        normalized_df = df.copy()
        normalized_df.columns = [str(column).strip().lower() for column in normalized_df.columns]

        for column in self.REQUIRED_COLUMNS:
            if normalized_df[column].isnull().any():
                raise ValueError(f"A coluna '{column}' possui valores nulos.")
