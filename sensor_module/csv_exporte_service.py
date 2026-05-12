import csv
from datetime import datetime


class CSVExportService:

    """
    Serviço responsável por:

    ✅ exportar logs do sensor
    ✅ importar experimentos CSV
    ✅ validar dados
    ✅ preparar dados para PCM Calc
    """

    # =====================================================
    # EXPORT CSV
    # =====================================================

    @staticmethod
    def export(filepath, data):

        """
        Exporta logs do sensor para CSV.

        Parameters
        ----------
        filepath : str
            Caminho do arquivo.

        data : list[dict]
            Lista de logs.
        """

        if not data:
            raise ValueError(
                "Nenhum dado encontrado para exportação."
            )

        normalized_data = []

        for row in data:

            timestamp = row.get("timestamp")

            # datetime -> string
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            normalized_data.append({

                "timestamp": timestamp,

                "temperature": row.get(
                    "temperature",
                    0
                ),

                "mode": row.get(
                    "mode",
                    "unknown"
                )
            })

        with open(
            filepath,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "timestamp",
                    "temperature",
                    "mode"
                ]
            )

            writer.writeheader()

            for row in normalized_data:
                writer.writerow(row)

    # =====================================================
    # IMPORT CSV
    # =====================================================

    @staticmethod
    def import_csv(filepath):

        """
        Importa CSV do sensor.

        Returns
        -------
        list[dict]
        """

        data = []

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                try:

                    timestamp = row.get(
                        "timestamp"
                    )

                    temperature = float(
                        row.get(
                            "temperature",
                            0
                        )
                    )

                    mode = row.get(
                        "mode",
                        "unknown"
                    )

                    data.append({

                        "timestamp": timestamp,

                        "temperature": temperature,

                        "mode": mode
                    })

                except Exception:
                    continue

        return data

    # =====================================================
    # EXTRACT TEMPERATURES
    # =====================================================

    @staticmethod
    def extract_temperatures(data):

        """
        Extrai somente temperaturas.
        """

        return [

            float(item["temperature"])

            for item in data

            if "temperature" in item
        ]

    # =====================================================
    # EXTRACT TIMESTAMPS
    # =====================================================

    @staticmethod
    def extract_timestamps(data):

        """
        Extrai timestamps.
        """

        return [

            item["timestamp"]

            for item in data

            if "timestamp" in item
        ]

    # =====================================================
    # VALIDATE CSV
    # =====================================================

    @staticmethod
    def validate_csv(filepath):

        """
        Verifica se CSV possui estrutura válida.
        """

        required_fields = {

            "timestamp",

            "temperature",

            "mode"
        }

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            fields = set(reader.fieldnames or [])

            return required_fields.issubset(fields)

    # =====================================================
    # CALCULATE BASIC METRICS
    # =====================================================

    @staticmethod
    def calculate_metrics(data):

        """
        Calcula métricas básicas térmicas.
        """

        temperatures = CSVExportService.extract_temperatures(
            data
        )

        if not temperatures:

            return {

                "max_temp": 0,

                "min_temp": 0,

                "avg_temp": 0,

                "delta_t": 0,

                "samples": 0
            }

        max_temp = max(temperatures)

        min_temp = min(temperatures)

        avg_temp = sum(temperatures) / len(
            temperatures
        )

        delta_t = max_temp - min_temp

        return {

            "max_temp": round(max_temp, 2),

            "min_temp": round(min_temp, 2),

            "avg_temp": round(avg_temp, 2),

            "delta_t": round(delta_t, 2),

            "samples": len(temperatures)
        }