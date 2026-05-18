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

    # =========================
    # PORTAS DISPONÍVEIS
    # =========================
    @staticmethod
    def get_available_ports():
        try:
            ports = serial.tools.list_ports.comports()
            return [p.device for p in ports]
        except Exception:
            return []

    # =========================
    # CONNECT
    # =========================
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

            self.log(f"Conectado em {self.port}")

        except Exception as e:
            self.log(f"Erro conexão serial: {e}")

    # =========================
    # DISCONNECT
    # =========================
    def disconnect(self):

        self.running = False

        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
        except:
            pass

        self.log("Serial desconectada")

    # =========================
    # PARSER (CORRIGIDO)
    # =========================
    # serial_connection.py - MÉTODO CORRIGIDO
    def _parse_line(self, line: str):
        """
        Parse da linha serial.
        Retorna None para dados inválidos (boot, lixo, etc)
        """
        try:
            # ✅ FILTRO 1: Ignorar linhas muito curtas
            if len(line) < 10:
                return None
            
            # ✅ FILTRO 2: Verificar formato esperado
            if "TEMP:" not in line or "TIME:" not in line:
                return None
            
            # ✅ FILTRO 3: Verificar estrutura mínima
            parts = line.split(",")
            if len(parts) < 3:
                return None
            
            # Parse dos dados
            temperature = float(parts[0].split(":")[1])
            timestamp_ms = int(parts[1].split(":")[1])
            minutes = float(parts[2].split(":")[1])
            
            # ✅ FILTRO 4: Validar ranges realistas
            if temperature < -40 or temperature > 125:
                self.log(f"⚠️ Temperatura fora do range: {temperature}°C")
                return None
            
            return {
                "temperature": temperature,
                "timestamp_ms": timestamp_ms,
                "minutes": minutes
            }
        
        except (ValueError, IndexError) as e:
            # Ignorar silenciosamente dados inválidos do boot
            return None
        except Exception as e:
            self.log(f"Parse error: {e} | line={line[:50]}...")
            return None

    # =========================
    # LOOP LEITURA
    # =========================
    def _read_loop(self):

        while self.running:

            try:

                if self.serial and self.serial.in_waiting:

                    line = (
                        self.serial.readline()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )

                    if not line:
                        continue

                    # log leve (debug)
                    if self.on_log:
                        self.log(f"RX -> {line}")
                    

                    data = self._parse_line(line)

                    if data and self.on_data:
                        self.on_data(data)

                time.sleep(0.05)

            except Exception as e:
                self.log(f"Erro leitura serial: {e}")
                self.running = False
                break

    # =========================
    # LOG
    # =========================
    def log(self, text):
        if self.on_log:
            self.on_log(text)