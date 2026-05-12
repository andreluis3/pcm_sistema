import csv


class CSVExportService:

    @staticmethod
    def export(filepath, data):

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

            for row in data:
                writer.writerow(row)