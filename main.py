import time

from services.sensor_service import SensorService
from database.db_manager import DatabaseManager
from core.detector_ciclo import CycleDetector


sensor = SensorService()
db = DatabaseManager()
detector = CycleDetector()

db.create_tables()


while True:

    temp = sensor.read_temperature()

    if temp:

        print("Temperatura:", temp)

        db.insert_temperature(temp)

        trend = detector.add_temperature(temp)

        if trend:
            print("Tendência:", trend)

    time.sleep(1)