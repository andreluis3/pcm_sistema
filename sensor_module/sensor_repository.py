from datetime import datetime


class SensorRepository:

    def __init__(self):

        self.logs = []

    def save(self, temperature, mode):

        self.logs.append({

            "timestamp": datetime.now(),

            "temperature": temperature,

            "mode": mode
        })

    def get_all(self):

        return self.logs