# EXEMPLOS DE CÓDIGO CORRIGIDO

## 1. Connection Pool para MySQL (CRÍTICA)

### ❌ ANTES: backend/main_api.py

```python
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="thermacore",
        port=3306
    )

@app.post("/criar_experimento")
def criar_experimento(exp: Experimento):
    try:
        conn = get_connection()  # ❌ NOVA conexão a cada request!
        cursor = conn.cursor()
        # ...
        conn.close()
    except Exception as e:
        return {"erro": str(e)}
```

### ✅ DEPOIS: Usar SQLAlchemy com Pool

**Arquivo: backend/db_pool.py (NOVO)**

```python
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import os

# Configuração centralizada
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "thermacore")

# Pool de conexões
engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    poolclass=QueuePool,
    pool_size=5,              # Manter 5 conexões abertas
    max_overflow=10,          # Até 10 conexões extras se necessário
    pool_recycle=3600,        # Reciclar a cada 1 hora
    pool_pre_ping=True,       # Verificar conexão antes de usar
    echo=False                # Sem logs SQL (mudar para True se debug)
)

def get_connection():
    """Retorna conexão do pool (não cria nova!)"""
    return engine.connect()

def execute_query(query: str, params: dict = None):
    """Helper para executar query com pool"""
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        conn.commit()
        return result

# Teste de saúde
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except:
        return False
```

**Arquivo: backend/main_api.py (REFATORADO)**

```python
from fastapi import FastAPI
from pydantic import BaseModel
from backend.db_pool import engine, execute_query, health_check
from sqlalchemy import text

app = FastAPI()

class Experimento(BaseModel):
    material: str
    operador: str
    id_usuario: int

@app.get("/health")
def health():
    return {"status": "ok" if health_check() else "error"}

@app.post("/criar_experimento")
def criar_experimento(exp: Experimento):
    """✅ Usa pool em vez de criar nova conexão"""
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO experiments (id_usuario, material, operador)
                VALUES (:id_usuario, :material, :operador)
            """)
            
            result = conn.execute(query, {
                "id_usuario": exp.id_usuario,
                "material": exp.material,
                "operador": exp.operador
            })
            
            conn.commit()
            
            return {
                "status": "ok",
                "id": result.lastrowid
            }
            
    except Exception as e:
        print(f"ERRO: {e}")
        return {"erro": str(e)}, 500

@app.get("/experimentos")
def listar_experimentos():
    """✅ Usa pool"""
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM experiments")
            result = conn.execute(query)
            return [dict(row) for row in result]
    except Exception as e:
        return {"erro": str(e)}, 500
```

---

## 2. Sincronização de Threads com Queue (CRÍTICA)

### ❌ ANTES: sensor_module/serial_connection.py

```python
def _read_loop(self):
    while self.running:
        try:
            raw = self.connection.readline()
            line = raw.decode("utf-8", errors="ignore").strip()
            if "TEMP:" in line:
                value = line.replace("TEMP:", "")
                temperature = float(value)
                if self.on_data:
                    self.on_data(temperature)  # ❌ Callback direto de thread!
        except Exception as e:
            if self.on_log:
                self.on_log(f"Erro leitura serial: {e}")
```

### ✅ DEPOIS: Com Queue Thread-Safe

**Arquivo: sensor_module/sensor_connection_safe.py (NOVO)**

```python
import threading
import serial
from queue import Queue
import time

class SerialConnectionSafe:
    """Versão thread-safe com Queue"""
    
    def __init__(self, port, baudrate, on_log=None):
        self.port = port
        self.baudrate = baudrate
        self.on_log = on_log
        
        # ✅ Use Queue para comunicação thread-safe
        self.data_queue = Queue(maxsize=100)
        
        self.connection = None
        self.running = False
        self.thread = None
        
    def connect(self):
        """Inicia thread de leitura"""
        try:
            self.connection = serial.Serial(
                self.port,
                self.baudrate,
                timeout=1
            )
            
            self.running = True
            
            # ✅ NÃO é daemon - vamos fazer join()
            self.thread = threading.Thread(
                target=self._read_loop,
                daemon=False  # IMPORTANTE: permite join() gracioso
            )
            
            self.thread.start()
            
            self._log(f"Serial conectada {self.port}")
            
        except Exception as e:
            self._log(f"Erro serial: {e}")
            self.running = False
            
    def disconnect(self):
        """Para thread de leitura"""
        self.running = False
        
        # ✅ Espera thread terminar (máx 2 segundos)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        
        try:
            if self.connection:
                self.connection.close()
        except:
            pass
        
        self._log("Serial desconectada")
        
    def get_temperature(self):
        """Lê temperatura da queue (non-blocking)"""
        try:
            return self.data_queue.get_nowait()
        except:
            return None
    
    def _read_loop(self):
        """Thread loop - SEGURO para colocar em queue"""
        while self.running:
            try:
                if not self.connection:
                    time.sleep(0.1)
                    continue
                
                raw = self.connection.readline()
                
                if not raw:
                    continue
                
                line = raw.decode("utf-8", errors="ignore").strip()
                
                if not line:
                    continue
                
                if "TEMP:" in line:
                    value = line.replace("TEMP:", "")
                    temperature = float(value)
                    
                    # ✅ Coloca na queue (thread-safe)
                    try:
                        self.data_queue.put_nowait(temperature)
                    except:  # Queue cheia
                        self.data_queue.get()  # Remove antigo
                        self.data_queue.put_nowait(temperature)
                        
            except Exception as e:
                self._log(f"Erro leitura serial: {e}")
                if not self.running:
                    break
    
    def _log(self, msg):
        if self.on_log:
            self.on_log(msg)
```

**Arquivo: sensor_module/sensor_manager_safe.py (REFATORADO)**

```python
from sensor_module.sensor_connection_safe import SerialConnectionSafe
from sensor_module.simulation_connection import SimulationConnection
from queue import Queue

class SensorManagerSafe:
    """Gerenciador de sensores thread-safe"""
    
    def __init__(self, on_status=None, on_log=None):
        self.on_status = on_status
        self.on_log = on_log
        
        self.connection = None
        self.ui_queue = Queue()  # ✅ Queue para comunicação com UI
        
    def connect(self, mode, config=None):
        self.disconnect()
        
        config = config or {}
        
        try:
            if mode == "Serial":
                self.connection = SerialConnectionSafe(
                    port=config.get("port", "COM3"),
                    baudrate=config.get("baudrate", 115200),
                    on_log=self.log
                )
            elif mode == "Simulação":
                # Para simulação, ainda pode usar thread
                self.connection = SimulationConnection(
                    on_data=self._put_temperature_in_queue,
                    on_log=self.log
                )
            else:
                self.log(f"Modo {mode} não suportado")
                return
            
            self.connection.connect()
            self.status(f"🟢 {mode} conectado")
            
        except Exception as e:
            self.status("🔴 Falha conexão")
            self.log(str(e))
    
    def disconnect(self):
        try:
            if self.connection:
                self.connection.disconnect()
        except:
            pass
        self.status("🔴 Desconectado")
    
    def get_queued_events(self):
        """Processa todos eventos na queue (chama da MainUI)"""
        events = []
        while not self.ui_queue.empty():
            try:
                events.append(self.ui_queue.get_nowait())
            except:
                break
        return events
    
    def _put_temperature_in_queue(self, value):
        """Coloca temperatura na queue (chamado de thread)"""
        try:
            self.ui_queue.put_nowait(('temperature', value))
        except:
            pass
    
    def status(self, msg):
        if self.on_status:
            self.on_status(msg)
    
    def log(self, msg):
        if self.on_log:
            self.on_log(msg)
```

**Arquivo: interface/main_ui.py (REFATORADO)**

```python
class MainUI(ctk.CTk):
    def __init__(self, username: str = "Usuário"):
        super().__init__()
        # ...
        self.sensor_manager = SensorManagerSafe(
            on_status=self.update_sensor_status,
            on_log=self.log_sensor
        )
        
        # ✅ Inicia processamento da queue
        self._process_sensor_queue()
    
    def _process_sensor_queue(self):
        """Processa eventos do sensor (PRINCIPAL THREAD - seguro)"""
        try:
            if not self.winfo_exists():
                return
            
            # Processa todos eventos da queue de forma segura
            events = self.sensor_manager.get_queued_events()
            
            for event_type, data in events:
                if event_type == 'temperature':
                    self.update_status(data)
                elif event_type == 'error':
                    self.log_error(data)
            
        except Exception as e:
            print(f"Erro processando sensor: {e}")
        finally:
            # ✅ Agenda próxima verificação
            self.after(50, self._process_sensor_queue)
```

---

## 3. Cleanup de Timers (ALTA)

### ❌ ANTES: interface/dashboard_tab.py

```python
class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self._animate_id = None
        # ...
        self._animate_pcm()
    
    def _animate_pcm(self):
        # ... animação ...
        self._animate_id = self.after(120, self._animate_pcm)
    
    def destroy(self):  # ❌ NÃO cancela timer!
        super().destroy()
```

### ✅ DEPOIS: Com Cleanup

```python
class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self._animate_id = None
        # ...
        self._animate_pcm()
    
    def _animate_pcm(self):
        try:
            if not self.winfo_exists():
                return
        except:
            return
        
        # ... animação ...
        self._animate_id = self.after(120, self._animate_pcm)
    
    def destroy(self):
        """✅ Limpa recursos antes de destruir"""
        # Cancela todos timers pendentes
        if self._animate_id:
            try:
                self.after_cancel(self._animate_id)
            except:
                pass
            self._animate_id = None
        
        # Fecha conexões
        if hasattr(self, 'db') and self.db:
            try:
                self.db.sqlite.close()
            except:
                pass
        
        super().destroy()
```

---

## 4. Cleanup de Matplotlib (ALTA)

### ❌ ANTES: ui/charts.py

```python
class BaseChart:
    def __init__(self, parent, title: str) -> None:
        self.figure = Figure(figsize=(4.6, 2.6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()
        # ❌ Sem cleanup no destrutor!
```

### ✅ DEPOIS: Com Cleanup

```python
import matplotlib.pyplot as plt

class BaseChart:
    def __init__(self, parent, title: str) -> None:
        self.figure = Figure(figsize=(4.6, 2.6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()
    
    def destroy(self):
        """✅ Limpa recursos matplotlib"""
        try:
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None
        except:
            pass
        
        try:
            if hasattr(self, 'figure') and self.figure:
                plt.close(self.figure)
                self.figure = None
        except:
            pass
    
    def __del__(self):
        """Destrutor garante limpeza mesmo em erro"""
        self.destroy()
```

---

## 5. Context Manager para Conexões SQLite (ALTA)

### ❌ ANTES: database/db_manager.py

```python
def search_experiments(self, material: str) -> list[dict]:
    conn = sqlite3.connect(self.db_path)  # ❌ Pode não fechar se erro
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM experiments WHERE material LIKE ?",
        (f"%{material}%",)
    )
    
    results = cursor.fetchall()
    conn.close()  # Nunca executado se erro acima
    return results
```

### ✅ DEPOIS: Com Context Manager

```python
def search_experiments(self, material: str) -> list[dict]:
    """✅ Context manager garante close() mesmo com erro"""
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM experiments WHERE material LIKE ?",
            (f"%{material}%",)
        )
        
        results = cursor.fetchall()
        # ✅ conn.close() chamado automaticamente
        return [dict(row) for row in results]

# Refatorar TODAS as queries dessa forma
```

---

## 6. Rate Limiting (MÉDIA)

### ✅ NOVO: services/rate_limiter.py

```python
from collections import deque
from datetime import datetime, timedelta
import threading

class RateLimiter:
    """Rate limiter simples com janela deslizante"""
    
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = deque()
        self.lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        """Retorna True se request é permitido"""
        now = datetime.now()
        
        with self.lock:
            # Remove requests antigas
            while self.requests and self.requests[0] < now - self.window:
                self.requests.popleft()
            
            # Verifica limite
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            return False

# Uso em api_client.py:
class ThermaCoreMySQLClient:
    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
    
    def insert_experiment(self, data: Dict) -> int:
        # ✅ Verifica rate limit
        if not self.rate_limiter.is_allowed():
            raise Exception("Rate limit exceeded")
        
        return self._request_json("POST", "/experimentos", json=data)
```

---

## Resumo de Mudanças

| Problema | Solução | Arquivo |
|----------|---------|---------|
| Connection Pool MySQL | SQLAlchemy QueuePool | backend/db_pool.py |
| Thread Safety | Queue + after() | sensor_module/sensor_*_safe.py |
| Timer Cleanup | after_cancel() em destroy() | interface/dashboard_tab.py |
| Matplotlib Cleanup | __del__() + plt.close() | ui/charts.py |
| SQLite Close | with statement | database/db_manager.py |
| Rate Limiting | RateLimiter class | services/rate_limiter.py |

---

**Tempo estimado de implementação:** 2-3 dias  
**Dificuldade:** Média (refatoração, não nova feature)  
**Impacto:** Produção-ready
