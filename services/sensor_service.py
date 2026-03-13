from controller.serial_controller import SerialController


class SensorService:
    def __init__(self, on_temperature_callback):
        self.callback = on_temperature_callback
        self.last_temperature = None
        self.serial = SerialController(self._on_temperature)

    def _on_temperature(self, value: float):
        self.last_temperature = value
        self.callback(value)  # chama a função no MainUI
        print(f"[SENSOR] Temperatura recebida: {value:.2f} °C")

    def start(self, root):
        self.serial.start(root)

    def stop(self):
        self.serial.stop()