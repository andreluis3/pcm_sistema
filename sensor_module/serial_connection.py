
import serial
import serial.tools.list_ports
import threading
import time


class SerialConnection:

    def __init__(
        self,
        port="COM3",
        baudrate=115200,
        on_data=None,
        on_log=None
    ):

        self.port = port
        self.baudrate = baudrate

        self.on_data = on_data
        self.on_log = on_log

        self.serial = None

        self.running = False
        self.thread = None

    # =====================================================
    # PORTAS DISPONÍVEIS
    # =====================================================

    @staticmethod
    def get_available_ports():

        try:

            ports = serial.tools.list_ports.comports()

            return [port.device for port in ports]

        except Exception:
            return []

    # =====================================================
    # CONNECT
    # =====================================================

    def connect(self):

        try:

            self.serial = serial.Serial(
                self.port,
                self.baudrate,
                timeout=1
            )

            self.running = True

            self.thread = threading.Thread(
                target=self._read_loop,
                daemon=True
            )

            self.thread.start()

            self.log(
                f"Conectado em {self.port}"
            )

        except Exception as e:

            self.log(
                f"Erro conexão serial: {e}"
            )

    # =====================================================
    # DISCONNECT
    # =====================================================

    def disconnect(self):

        self.running = False

        try:

            if self.serial and self.serial.is_open:
                 self.serial.close()

        except:
            pass

        self.log(
            "Serial desconectada"
        )

    # =====================================================
    # LOOP LEITURA
    # =====================================================

    def _read_loop(self):

        while self.running:

            try:

                if self.serial and self.serial.in_waiting:

                    line = self.serial.readline().decode(
                        "utf-8",
                        errors="ignore"
                    ).strip()

                    if line:

                        if self.on_log and time.time() % 2 < 0.1:
                            self.log(f"RX -> {line}")

                        try:

                            value = float(line)

                            if self.on_data:
                                self.on_data(value)

                        except ValueError:

                            self.log(f"Dado inválido: {line}")

                time.sleep(0.05)

            except Exception as e:

                self.log(f"Erro leitura serial: {e}")

                self.running = False

                break
    # =====================================================
    # LOG
    # =====================================================

    def log(self, text):

        if self.on_log:
            self.on_log(text)