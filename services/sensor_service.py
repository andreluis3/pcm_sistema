from controller.serial_controller import SerialController


class SensorService:

    def __init__(self):
        self.serial = SerialController()

    def read_temperature(self):

        data = self.serial.read_data()

        try:
            temperature = float(data)
            return temperature
        except:
            return None