from sensor_module.serial_connection import SerialConnection
from sensor_module.simulation_connection import SimulationConnection
from sensor_module.api_sensor_driver import APISensorDriver
from sensor_module.sensor_buffer import SensorBuffer
from sensor_module.sensor_repository import SensorRepository
import serial
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
        
        # ✅ CORREÇÃO: Inicializar atributos que são usados em disconnect()
        self.running = False
        self.thread = None
        self.serial = None

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

            elif mode == "API":
                
                # ✅ NOVO: Integração com APISensorDriver
                self.connection = APISensorDriver(
                    host=config.get("host", "192.168.200.227"),
                    port=config.get("port", 8080),
                    endpoint=config.get("endpoint", "/sensor/temperature"),
                    poll_interval=config.get("poll_interval", 2.0),
                    timeout=config.get("timeout", 5.0),
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

            if self.on_status:
                self.on_status(
                    f"🟢 {mode} conectado",
                    True
                )

        except Exception as e:

            # ✅ CORREÇÃO: Chamar self.on_status() em vez de self.status()
            if self.on_status:
                self.on_status(
                    "🔴 Falha conexão",
                    False
                )

            self.log(
                f"🔴 Falha conexão: {e}"
)

            self.log(
                str(e)
            )

    def disconnect(self):

        self.running = False

        # ✅ CORREÇÃO: Desconectar a conexão atual (seja qual for)
        try:

            if self.connection:
                self.connection.disconnect()

        except Exception as e:
            self.log(f"Erro ao desconectar: {e}")

        # ✅ Limpeza de atributos legacy (compatibilidade)
        try:

            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1)

        except Exception:
            pass

        try:

            if self.serial and self.serial.is_open:
                self.serial.close()

        except Exception:
            pass

        self.log("🔴 Conexão encerrada")

        if self.on_status:
            self.on_status(
                "🔴 Desconectado",
                False
            )

    def process_temperature(self, data):
        try:

            temperature = float(
                data["temperature"]
            )

            minutes = float(
                data["minutes"]
            )

            timestamp_ms = int(
                data["timestamp_ms"]
            )

            #
            # BUFFER
            #
            self.buffer.add(temperature)

            #
            # REPOSITORY
            #
            self.repository.save(
                temperature,
                self.mode
            )

            #
            # CALLBACK UI
            #
            if self.on_temperature:

                self.on_temperature({

                    "temperature": temperature,

                    "minutes": minutes,

                    "timestamp_ms": timestamp_ms
                })

        except Exception as e:

            self.log(
                f"Erro processamento: {e}"
            )

    def log(self, text):

        if self.on_log:
            self.on_log(text)
            
    def get_serial_ports(self):

        try:

            ports = serial.tools.list_ports.comports()

            return [port.device for port in ports]

        except Exception as e:

            self.log(f"Erro listando portas: {e}")

            return ["COM3"]