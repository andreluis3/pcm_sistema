import requests
import threading
import time
from typing import Optional, Callable


class APISensorDriver:
    """
    Driver para leitura de sensores via HTTP API (Wi-Fi/ESP32).
    
    Implementa polling contínuo com:
    - Reconexão automática
    - Retry logic
    - Heartbeat
    - Tratamento de timeouts
    - Thread-safe callbacks
    
    Uso:
        driver = APISensorDriver(
            host="192.168.200.227",
            port=8080,
            endpoint="/sensor/temperature",
            on_data=self.on_temperature_received,
            on_log=self.on_log_message
        )
        driver.connect()
    """

    def __init__(
        self,
        host: str = "192.168.200.227",
        port: int = 8080,
        endpoint: str = "/sensor/temperature",
        poll_interval: float = 2.0,
        timeout: float = 5.0,
        max_retries: int = 3,
        on_data: Optional[Callable] = None,
        on_log: Optional[Callable] = None,
    ):
        """
        Inicializa o driver de API.
        
        Args:
            host: IP do ESP32
            port: Porta HTTP
            endpoint: Endpoint para GET da temperatura
            poll_interval: Intervalo de polling em segundos
            timeout: Timeout para requisições HTTP
            max_retries: Tentativas de reconexão
            on_data: Callback quando temperatura recebida
            on_log: Callback para logs
        """
        
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.on_data = on_data
        self.on_log = on_log
        
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # ==========================================
        # ESTADO DE CONEXÃO
        # ==========================================
        
        self.connected = False
        self.last_successful_read = None
        self.consecutive_failures = 0
        self.last_temperature = None

    # =====================================================
    # URL BASE
    # =====================================================

    def _get_url(self) -> str:
        """Retorna URL base do ESP32."""
        return f"http://{self.host}:{self.port}{self.endpoint}"

    # =====================================================
    # CONNECT
    # =====================================================

    def connect(self) -> bool:
        """
        Inicia a conexão e thread de polling.
        
        Returns:
            bool: True se conexão iniciada com sucesso
        """
        
        if self.running:
            self._log("⚠️ Já conectado")
            return False
        
        self.running = True
        self.consecutive_failures = 0
        
        # Testar conexão inicial
        if not self._test_connection():
            self._log("❌ ESP32 não responde")
            self.running = False
            return False
        
        # Iniciar thread de polling
        self.thread = threading.Thread(
            target=self._polling_loop,
            daemon=True
        )
        self.thread.start()
        
        self._log(f"✅ Conectado a {self._get_url()}")
        return True

    # =====================================================
    # DISCONNECT
    # =====================================================

    def disconnect(self) -> None:
        """Para a thread de polling e encerra conexão."""
        
        self.running = False
        
        try:
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)
        except Exception as e:
            self._log(f"⚠️ Erro ao parar thread: {e}")
        
        self.connected = False
        self._log("🛑 Desconectado")

    # =====================================================
    # TESTE DE CONEXÃO
    # =====================================================

    def _test_connection(self) -> bool:
        """
        Testa se ESP32 está acessível.
        
        Returns:
            bool: True se responde
        """
        
        try:
            response = requests.get(
                self._get_url(),
                timeout=self.timeout
            )
            self.connected = response.status_code == 200
            return self.connected
        except Exception as e:
            self._log(f"⚠️ Teste falhou: {e}")
            self.connected = False
            return False

    # =====================================================
    # POLLING LOOP (THREAD)
    # =====================================================

    def _polling_loop(self) -> None:
        """Loop principal de polling (executado em thread)."""
        
        while self.running:
            try:
                self._fetch_temperature()
                time.sleep(self.poll_interval)
                
            except Exception as e:
                self._log(f"❌ Erro em polling: {e}")
                self.consecutive_failures += 1
                
                # Reconectar se muitas falhas
                if self.consecutive_failures >= self.max_retries:
                    self._log("🔄 Tentando reconectar...")
                    if self._test_connection():
                        self.consecutive_failures = 0
                    else:
                        time.sleep(5)  # Esperar antes de tentar novamente
                else:
                    time.sleep(self.poll_interval)

    # =====================================================
    # FETCH TEMPERATURA
    # =====================================================

    def _fetch_temperature(self) -> None:
        """
        Faz requisição GET para obter temperatura.
        
        Espera resposta JSON com:
        {
            "temperatura": 28.5,
            "umidade": 45.0,
            "timestamp": 1715600000000,
            "status": "ok"
        }
        """
        
        try:
            response = requests.get(
                self._get_url(),
                timeout=self.timeout
            )
            
            # ✅ Sucesso
            if response.status_code == 200:
                data = response.json()
                temperature = data.get("temperatura")
                
                if temperature is not None:
                    self.last_temperature = temperature
                    self.last_successful_read = time.time()
                    self.consecutive_failures = 0
                    self.connected = True
                    
                    # Chamar callback
                    if self.on_data:
                        self.on_data(temperature)
                else:
                    self._log("⚠️ Resposta JSON sem 'temperatura'")
            
            # ❌ Erro HTTP
            else:
                self._log(f"❌ HTTP {response.status_code}")
                self.consecutive_failures += 1
                
        except requests.Timeout:
            self._log("⏱️ Timeout na requisição")
            self.consecutive_failures += 1
            
        except requests.ConnectionError:
            self._log("🔴 Conexão recusada")
            self.consecutive_failures += 1
            
        except Exception as e:
            self._log(f"❌ Erro ao processar resposta: {e}")
            self.consecutive_failures += 1

    # =====================================================
    # UTILITIES
    # =====================================================

    def get_last_temperature(self) -> Optional[float]:
        """Retorna última temperatura lida."""
        return self.last_temperature

    def get_last_read_time(self) -> Optional[float]:
        """Retorna timestamp da última leitura bem-sucedida."""
        return self.last_successful_read

    def is_connected(self) -> bool:
        """Retorna status da conexão."""
        return self.connected

    def ping(self) -> Optional[float]:
        """
        Faz ping para medir latência.
        
        Returns:
            float: Latência em ms, ou None se falhar
        """
        
        try:
            start = time.time()
            response = requests.get(
                self._get_url(),
                timeout=self.timeout
            )
            latency_ms = (time.time() - start) * 1000
            
            if response.status_code == 200:
                self._log(f"🏓 Ping: {latency_ms:.1f}ms")
                return latency_ms
        except Exception:
            pass
        
        return None

    # =====================================================
    # LOG
    # =====================================================

    def _log(self, text: str) -> None:
        """Envia log para callback."""
        if self.on_log:
            self.on_log(text)
