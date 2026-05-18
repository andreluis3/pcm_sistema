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

        self.running = False
        self.thread = None
        self.serial = None
        
    # sensor_manager.py - MÉTODO CORRIGIDO
    def connect(self, mode, config=None):
        self.disconnect()
        self.mode = mode
        config = config or {}

        try:
            if mode == "Serial":
                # ✅ CORREÇÃO: usar process_temperature e log
                self.connection = SerialConnection(
                    port=config.get("port", "COM3"),
                    baudrate=config.get("baudrate", 115200),
                    on_data=self.process_temperature,    # ✅ método que existe
                    on_log=self.log                      # ✅ método que existe
                )

            elif mode == "API":
                self.connection = APISensorDriver(
                    host=config.get("host", "192.168.200.227"),
                    port=config.get("port", 8080),
                    endpoint=config.get("endpoint", "/sensor/temperature"),
                    poll_interval=config.get("poll_interval", 2.0),
                    timeout=config.get("timeout", 5.0),
                    on_data=self.process_temperature,    # ✅ método que existe
                    on_log=self.log                      # ✅ método que existe
                )

            elif mode == "Simulação":
                self.connection = SimulationConnection(
                    on_data=self.process_temperature,    # ✅ método que existe
                    on_log=self.log                      # ✅ método que existe
                )
            else:
                self.log(f"Modo {mode} ainda não implementado")
                return

            self.connection.connect()

            if self.on_status:
                self.on_status(f"🟢 {mode} conectado", True)

        except Exception as e:
            if self.on_status:
                self.on_status("🔴 Falha conexão", False)
            self.log(f"🔴 Falha conexão: {e}")

    def disconnect(self):
        self.running = False

        try:
            if self.connection:
                self.connection.disconnect()
        except Exception as e:
            self.log(f"Erro ao desconectar: {e}")

        # Remova a tentativa de fechar self.serial diretamente
        # pois isso agora é responsabilidade da SerialConnection
        
        self.log("🔴 Conexão encerrada")
        
        if self.on_status:
            self.on_status("🔴 Desconectado", False)
        
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
        
        