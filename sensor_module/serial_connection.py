import threading
import serial


class SerialConnection:

    def __init__(
        self,
        port,
        baudrate,
        on_data=None,
        on_log=None
    ):

        self.port = port
        self.baudrate = baudrate

        self.on_data = on_data
        self.on_log = on_log

        self.connection = None

        self.running = False
        self.thread = None

    def connect(self):

        try:

            self.connection = serial.Serial(
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

            if self.on_log:
                self.on_log(
                    f"Serial conectada {self.port}"
                )

        except Exception as e:

            if self.on_log:
                self.on_log(
                    f"Erro serial: {e}"
                )

    def disconnect(self):

        self.running = False

        try:

            if self.connection:
                self.connection.close()

        except:
            pass

        if self.on_log:
            self.on_log(
                "Serial desconectada"
            )

    def _read_loop(self):

        while self.running:

            try:

                if not self.connection:
                    continue

                raw = self.connection.readline()

                line = raw.decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                if not line:
                    continue

                if "TEMP:" in line:

                    value = line.replace(
                        "TEMP:",
                        ""
                    )

                    temperature = float(value)

                    if self.on_data:
                        self.on_data(temperature)

            except Exception as e:

                if self.on_log:
                    self.on_log(
                        f"Erro leitura serial: {e}"
                    )