from sensor_module.serial_connection import SerialConnection
from sensor_module.simulation_connection import SimulationConnection
from sensor_module.sensor_buffer import SensorBuffer
from sensor_module.sensor_repository import SensorRepository
import serial as pyserial
import serial.tools.list_ports


class SensorManager:

    def __init__(
        self,
        on_temperature=None,
        on_status=None,
        on_log=None
    ):

        self.on_temperature = on_temperature
        self.on_status = on_status
        self.on_log = on_log

        self.connection = None

        self.buffer = SensorBuffer()
        self.repository = SensorRepository()

        self.mode = None

    def connect(self, mode, config=None):

        self.disconnect()

        self.mode = mode

        config = config or {}

        try:

            if mode == "Serial":

                self.connection = SerialConnection(
                    port=config.get("port", "COM3"),
                    baudrate=config.get("baudrate", 115200),
                    on_data=self.process_temperature,
                    on_log=self.log
                )

            elif mode == "Simulação":

                self.connection = SimulationConnection(
                    on_data=self.process_temperature,
                    on_log=self.log
                )

            else:

                self.log(
                    f"Modo {mode} ainda não implementado"
                )

                return

            self.connection.connect()

            self.status(
                f"🟢 {mode} conectado"
            )

        except Exception as e:

            self.status(
                "🔴 Falha conexão"
            )

            self.log(
                str(e)
            )

    def disconnect(self):

        try:

            if self.connection:
                self.connection.disconnect()

        except:
            pass

        self.status(
            "🔴 Desconectado"
        )

    def process_temperature(self, value):

        try:

            temperature = float(value)

            self.buffer.add(temperature)

            self.repository.save(
                temperature,
                self.mode
            )

            if self.on_temperature:
                self.on_temperature(
                    temperature
                )

        except Exception as e:

            self.log(
                f"Erro processamento: {e}"
            )

    def status(self, text):

        if self.on_status:
            self.on_status(text)

    def log(self, text):

        if self.on_log:
            self.on_log(text)
            
    def get_serial_ports(self):

        try:

            ports = pyserial.tools.list_ports.comports()

            return [port.device for port in ports]

        except Exception as e:

            self.log(f"Erro listando portas: {e}")

            return ["COM3"]