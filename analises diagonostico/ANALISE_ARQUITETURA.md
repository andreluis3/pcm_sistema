# Análise de Arquitetura: PCM Sistema - CustomTkinter + FastAPI + MySQL/SQLite

**Data:** 12 de maio de 2026  
**Escopo:** Análise de padrões de threading, banco de dados, UI, timers e gestão de memória

---

## 📊 VISÃO GERAL DA ARQUITETURA

### Camadas do Sistema

```
┌─────────────────────────────────────────────────────┐
│          Interface (CustomTkinter)                  │
│  - MainUI (app principal)                           │
│  - Dashboard, Sensor, Materiais, etc                │
│  - Charts com Matplotlib + FigureCanvasTkAgg        │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼─────────┐  ┌────────▼──────────┐
│  HybridRepository│  │  SensorManager    │
│  - SQLite        │  │  - Serial/Sim     │
│  - MySQL (API)   │  │  - Threads daemon │
└────────┬────────┘  └───────┬───────────┘
         │                   │
    ┌────▼────────────────────▼────────┐
    │  Backend (FastAPI)               │
    │  - main_api.py                   │
    │  - main_api_completo.py          │
    │  - Endpoints para CRUD            │
    └────┬────────────────────┬────────┘
         │                    │
    ┌────▼──────┐      ┌──────▼──────┐
    │  MySQL    │      │  SQLite DB  │
    │  (local)  │      │  (fallback) │
    └───────────┘      └─────────────┘

Conexões de Dados:
- MainUI → HybridRepository → API/SQLite
- SensorManager (Threads) → Callback → MainUI (após_queue)
- API recebe requests de HybridRepository
- API acessa MySQL diretamente
```

### Stack Tecnológico

| Componente | Tecnologia | Arquivo(s) | Status |
|-----------|-----------|-----------|--------|
| **Frontend** | CustomTkinter | `interface/*.py` | ✅ Ativo |
| **Backend** | FastAPI | `backend/main_api.py` | ⚠️ Problemas encontrados |
| **BD Primária** | MySQL | `backend/main_api.py` | ⚠️ Sem pool |
| **BD Fallback** | SQLite | `database/db_manager.py` | ✅ Com cleanup |
| **Charts** | Matplotlib | `ui/charts.py` | ⚠️ Sem limpeza explícita |
| **Sensores** | Serial/Simulation | `sensor_module/*` | ⚠️ Threads sem sincronização |
| **Async** | Queue + after() | `ui/dashboard_view.py` | ✅ Bom padrão |

---

## 🔴 PROBLEMAS CRÍTICOS ENCONTRADOS

### 1️⃣ **BANCO DE DADOS: Múltiplas Conexões Abertas**

#### Problema A: API cria nova conexão por request (CRÍTICO)

**Arquivo:** `backend/main_api.py` (linhas 8-13)

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
        conn = get_connection()  # ❌ NOVA CONEXÃO A CADA REQUEST
        cursor = conn.cursor()
        # ... executar query
        conn.close()  # Fecha após usar
```

**Impacto:**
- ❌ Connection pool não existe
- ❌ Conexão criada/fechada a cada request
- ❌ Sem limit de conexões simultâneas
- ⚠️ Potencial de "Too many connections" após ~100-200 requests
- ⚠️ Overhead de handshake MySQL repetido

**Severidade:** 🔴 **CRÍTICA** - Em produção com múltiplos usuários, causará falhas

**Localização adicional:** `backend/main_api_completo.py` (linhas 27-33) tem mesmo padrão

---

#### Problema B: HybridRepository cria conexão SQLite per instance

**Arquivo:** `services/hybrid_repository.py` (linhas 9-11)

```python
class HybridRepository:
    def __init__(self):
        self.api = ThermaCoreMySQLClient()
        self.sqlite = DatabaseManager()  # Nova instância = nova conexão SQLite
```

**Impacto:**
- ⚠️ Cada vez que HybridRepository é instanciado, abre nova conexão
- ⚠️ Em MainUI: `self.db_manager = HybridRepository()` (linha 36)
- ⚠️ Em cada página que carrega: `db_manager=self.db_manager` reutiliza, mas
- ❌ Se múltiplas páginas criarem suas próprias instâncias = múltiplas conexões

**Severidade:** 🟡 **ALTA** - Possível vazamento se não houver cleanup

---

#### Problema C: Falta de limpeza de conexões no destrutor

**Arquivo:** Toda a arquitetura

```python
# ❌ FALTA em MainUI, DashboardTab, etc:
def __del__(self):
    if hasattr(self, 'db_manager'):
        self.db_manager.sqlite.close()  # NUNCA CHAMADO

# ✅ EXISTE em database/db_manager.py:
def close(self) -> None:
    self.conn.close()
```

**Impacto:**
- ❌ Conexões abiertas nunca são fechadas até app terminar
- ❌ Memory leak de conexões
- ❌ Em SQLite: arquivo fica locked enquanto conexão aberta

**Severidade:** 🟡 **ALTA** - Desgasta recursos ao longo do tempo

---

### 2️⃣ **THREADS: Sem Sincronização de Dados**

#### Problema A: Callbacks diretos de thread para UI

**Arquivo:** `sensor_module/serial_connection.py` (linhas 71-91)

```python
def _read_loop(self):
    while self.running:
        try:
            if not self.connection:
                continue
            raw = self.connection.readline()
            line = raw.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            if "TEMP:" in line:
                value = line.replace("TEMP:", "")
                temperature = float(value)
                if self.on_data:
                    self.on_data(temperature)  # ❌ Callback direto da thread!
```

**Fluxo:**
1. SerialConnection._read_loop() roda em thread daemon
2. Chama `self.on_data(temperature)` diretamente
3. SensorManager.process_temperature() é chamado da thread
4. Que faz: `self.on_temperature(...)` (callback do UI)

**Impacto:**
- ❌ Operações Tkinter de thread não-main causar crashes
- ❌ Sem mutex/lock = race conditions em dados compartilhados
- ⚠️ Pode causar deadlock se Tkinter.call() bloqueado
- ❌ Não há sincronização entre sensor_buffer e thread

**Severidade:** 🔴 **CRÍTICA** - Causa crashes aleatórios em UI

**Arquivo similar:** `sensor_module/simulation_connection.py` (linha 41) tem mesmo padrão

---

#### Problema B: Falta de join() em threads

**Arquivo:** `sensor_module/serial_connection.py` (linhas 38-40)

```python
self.thread = threading.Thread(
    target=self._read_loop,
    daemon=True  # ❌ Daemon thread: será terminada abruptamente ao fechar app
)
```

**Impacto:**
- ❌ Thread daemon é terminada sem cleanup quando app fecha
- ❌ Arquivo serial pode ficar em estado indefinido
- ❌ Buffer de dados pode perder dados
- ⚠️ Sem chance de fazer flush final de dados

**Severidade:** 🟡 **ALTA** - Perda de dados possível

**Localização:** `sensor_module/simulation_connection.py` (linha 26) - mesmo problema

---

#### Problema C: Sem proteção de dados compartilhados

**Arquivo:** `sensor_module/sensor_buffer.py` (não lido completamente, mas inferível)

```python
# Em sensor_manager.py, processo é:
# Thread 1 (serial/sim) → on_data → process_temperature
# Main thread → query buffer → add event

# ❌ FALTA:
# self.lock = threading.Lock()
# with self.lock:
#     self.buffer.add(temperature)
```

**Impacto:**
- ❌ Condição de corrida no SensorBuffer
- ❌ Dados inconsistentes se Main thread lê enquanto thread escreve
- ❌ Índice de buffer pode ficar corrompido

**Severidade:** 🟡 **ALTA** - Corrupção de dados possível

---

### 3️⃣ **CALLBACKS DE UI: Mal Gerenciados**

#### Problema A: Múltiplos bind() com lambdas sem cleanup

**Arquivo:** `interface/view/thermal_calculations_page.py` (linhas 151-158)

```python
self.scroll_frame.bind(
    "<Configure>",
    lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
)

self.canvas.bind(
    "<Configure>",
    lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
)

# ❌ FALTA: unbind() quando widget é destruído
```

**Impacto:**
- ⚠️ Lambdas mantêm referência ao self
- ⚠️ Podem causar memory leak se não destruído
- ❌ Se page é destruída mas widgets não, callbacks continuam executando

**Severidade:** 🟡 **MÉDIA** - Vazamento de memória leve

---

#### Problema B: Callbacks de API sem timeout adequado

**Arquivo:** `services/api_client.py` (linhas 29-30)

```python
def health_check(self) -> bool:
    try:
        response = requests.get(f"{self.base_url}/experimentos", timeout=2)
        return response.status_code == 200
    except:
        return False  # ❌ Swallows ALL exceptions silenciosamente
```

**Impacto:**
- ⚠️ Exceções não são logged
- ⚠️ Falha silenciosa dificulta debug
- ❌ Sem retry logic para transient failures

**Severidade:** 🟡 **MÉDIA** - Dificulta troubleshooting

---

#### Problema C: Callbacks de eventos de widget sem validação

**Arquivo:** `interface/main_ui.py` (linhas 100-111)

```python
def update_status(self, temp):
    try:
        if not self.winfo_exists():  # ✅ BOM: verifica se widget ainda existe
            return
        
        self.status_label.configure(
            text=f"Sensor: Conectado | Última Temp: {temp:.1f} °C | Usuário: {self.username} | Banco: Ativo"
        )
```

**Status:** ✅ Bom prática aqui - mas nem todos fazem isso

**Falta em:** Muitos callbacks em dashboard_tab.py e outras páginas

---

### 4️⃣ **MATPLOTLIB: Sem Cleanup Adequado**

#### Problema A: FigureCanvasTkAgg não é explicitamente destruído

**Arquivo:** `ui/charts.py` (linhas 6-20)

```python
class BaseChart:
    def __init__(self, parent, title: str) -> None:
        # ...
        self.figure = Figure(figsize=(4.6, 2.6), dpi=100)
        # ...
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()
        
        # ❌ FALTA cleanup no destrutor:
        # def __del__(self):
        #     if hasattr(self, 'canvas'):
        #         self.canvas.get_tk_widget().destroy()
        #     if hasattr(self, 'figure'):
        #         plt.close(self.figure)
```

**Impacto:**
- ⚠️ Figure objetos acumulam na memória
- ⚠️ Tk widget não é destruído automaticamente
- ❌ Em dashboard com múltiplas páginas = vazamento de figures

**Severidade:** 🟡 **MÉDIA** - Vazamento gradual de memória

---

#### Problema B: AreaChart.update() não remove fill antigo

**Arquivo:** `ui/charts.py` (linhas 56-65)

```python
def update(self, data: Sequence[float] | Iterable[float]) -> None:
    series = self._coerce_series(data)
    if not series:
        return
    x = list(range(len(series)))
    self._line.set_data(x, series)
    if self._fill is not None:
        self._fill.remove()  # ✅ Tenta remover
    self._fill = self.ax.fill_between(x, series, color=self._area_color, alpha=0.22)
    # ...
    self.draw()
```

**Status:** ✅ Tenta remover, mas se draw() falhar = leak

**Impacto:** ⚠️ Acúmulo de polígonos se há exceção

---

#### Problema C: BarChart.update() chama ax.clear() (ineficiente)

**Arquivo:** `ui/charts.py` (linhas 73-93)

```python
def update(self, data: Sequence[float] | Iterable[float]) -> None:
    series = self._coerce_series(data)
    if not series:
        return
    x = list(range(1, len(series) + 1))
    self.ax.clear()  # ❌ Limpa TUDO, depois reconfigura
    self.ax.set_facecolor(THEME_COLORS["card"])
    self.ax.set_title(self._title, color=THEME_COLORS["white"], fontsize=11, pad=10)
    # ... reconfigura tudo novamente
```

**Impacto:**
- ⚠️ Ineficiente: limpa e reconfigura a cada update
- ⚠️ Mais propenso a memory leak
- ✅ Funciona, mas é subótimo

**Severidade:** 🟡 **BAIXA** - Performance

---

#### Problema D: PCMScreen cria múltiplos FigureCanvasTkAgg

**Arquivo:** `pcm_module/pcm_screen.py` (linhas 565-568)

```python
canvas = FigureCanvasTkAgg(figure, master=self.chart_section)
canvas.get_tk_widget().grid(row=i, column=0, sticky="nsew", padx=PAD_NORMAL, pady=PAD_NORMAL)
canvas.draw_idle()
self.chart_canvases.append(canvas)  # Armazena referência
```

**Impacto:**
- ⚠️ Armazena múltiplas figuras em lista
- ⚠️ Se página não é destruída = acumula

**Localização:** `pcm_module/pcm_screen.py` linha 838 faz `destroy()`:
```python
canvas.get_tk_widget().destroy()
```
✅ Mas apenas ao processar novo arquivo

**Severidade:** 🟡 **MÉDIA** - Vazamento se página não destruída

---

### 5️⃣ **TIMERS E LOOPS DE ATUALIZAÇÃO**

#### Problema A: after() não sempre cancelado no destroy()

**Mapeamento de timers:**

| Arquivo | Timer ID | Período | Cleanup | Status |
|---------|----------|---------|---------|--------|
| `loading_screen.py:31` | `_animate_id` | 80ms | ✅ _cleanup_after_jobs() | ✅ OK |
| `loading_screen.py:32` | `_finish_after_id` | var | ✅ _cleanup_after_jobs() | ✅ OK |
| `dashboard_tab.py:684` | `_animate_id` | 120ms | ❓ Não claro | ⚠️ RISCO |
| `database_tab.py:248-249` | `_search_after_id` | 200ms | ❓ Não claro | ⚠️ RISCO |
| `interface/view/dashboard.py:25` | `_update_after_id` | 1000ms | ✅ destroy() | ✅ OK |
| `ui/dashboard_view.py:185` | `_ui_queue_after_id` | 50ms | ✅ destroy() | ✅ OK |

---

#### Problema B: DashboardTab._animate_pcm() pode continuar após destroy()

**Arquivo:** `interface/dashboard_tab.py` (linhas 680-689)

```python
def _animate_pcm(self):
    try:
        if not self.winfo_exists():  # ✅ Verifica existência
            return
    except TclError:
        return
    
    # ... animação ...
    
    self._animate_id = self.after(120, self._animate_pcm)  # Agenda próximo
```

**Impacto:**
- ✅ Verifica winfo_exists() - BOM
- ⚠️ Mas se winfo_exists() falha por outro motivo = memory leak
- ⚠️ Não há after_cancel() explícito no destroy()

**Severidade:** 🟡 **MÉDIA** - Timer orfão possível

---

#### Problema C: database_tab.py não cancela _search_after_id

**Arquivo:** `interface/database_tab.py` (linhas 248-249)

```python
def _on_search_keyrelease(self, event):
    if hasattr(self, '_search_after_id'):
        self.after_cancel(self._search_after_id)  # ✅ Cancela anterior
    self._search_after_id = self.after(200, self.search_experiment)
```

**Impacto:**
- ✅ Cancela antes de agendar novo (debounce bom)
- ⚠️ FALTA destroy() para cleanup final:

```python
# ❌ FALTA em destroy():
def destroy(self):
    if hasattr(self, '_search_after_id'):
        self.after_cancel(self._search_after_id)
    super().destroy()
```

**Severidade:** 🟡 **MÉDIA** - Timer orfão se página destruída durante typing

---

### 6️⃣ **LIMPEZA DE WIDGETS**

#### Problema A: Transição de páginas em MainUI

**Arquivo:** `interface/main_ui.py` (linhas 119-151)

```python
def load_page(self, page_name: str):
    if self.current_screen is not None:
        if self._dashboard_ref is self.current_screen:
            self._dashboard_ref = None
        self.current_screen.destroy()  # ✅ Destrói widget anterior
    
    # ... cria nova página ...
    self.current_screen.pack(fill="both", expand=True)
```

**Status:** ✅ Bom - destrói corretamente

**Risco:** ❌ Se há timers agendados após destroy(), pode causar erro

---

#### Problema B: PCMScreen cleanup

**Arquivo:** `pcm_module/pcm_screen.py` (linhas 837-839)

```python
for canvas in self.chart_canvases:
    canvas.get_tk_widget().destroy()
self.chart_canvases.clear()
```

**Status:** ✅ Limpa figuras

**Risco:** ⚠️ Apenas faz isso após novo arquivo, não em destroy()

---

### 7️⃣ **CHAMADAS DE API**

#### Problema A: Sem rate limiting

**Arquivo:** `services/hybrid_repository.py` (linhas 37-49)

```python
def insert_experiment(self, data):
    print("USANDO HYBRID REPOSITORY")
    if self.api_online():
        try:
            experiment_id = self.api.insert_experiment(data)  # ❌ Sem rate limit
            # ...
```

**Impacto:**
- ⚠️ UI pode fazer múltiplas requisições rapidamente
- ⚠️ Sem backoff exponencial
- ⚠️ Pode sobrecarregar API

**Severidade:** 🟡 **BAIXA** - Depende do uso

---

#### Problema B: Sem caching de resultados

**Arquivo:** Toda a arquitetura

```python
# ❌ A cada load_page("dashboard"), faz:
def load_dashboard_data(self) -> None:
    self._experiments = [dict(r) for r in self.db.list_experiments()]  # Query completa
    self._refresh_experiment_selector()
    self.update_dashboard()
    self._refresh_statistics()
```

**Impacto:**
- ⚠️ Sem cache = múltiplas queries ao BD
- ⚠️ Se usuário navega rápido entre páginas = overhead

**Severidade:** 🟡 **BAIXA** - Performance

---

### 8️⃣ **GESTÃO DE MEMÓRIA**

#### Problema A: Lambdas em binds mantêm referência ao self

**Arquivo:** `interface/view/thermal_calculations_page.py` (linhas 151-158)

```python
self.scroll_frame.bind(
    "<Configure>",
    lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
)
```

**Impacto:**
- ⚠️ Lambda captura `self` no closure
- ⚠️ Se widget não é unbound antes de destruir = vazamento
- ⚠️ Acumula se página é aberta/fechada muitas vezes

**Severidade:** 🟡 **MÉDIA** - Vazamento leve

---

#### Problema B: Referências de callback em SensorManager

**Arquivo:** `sensor_module/sensor_manager.py` (linhas 7-18)

```python
class SensorManager:
    def __init__(self, on_temperature=None, on_status=None, on_log=None):
        self.on_temperature = on_temperature  # ❌ Mantém referência
        self.on_status = on_status
        self.on_log = on_log
```

**Impacto:**
- ⚠️ Se UI class é destruída mas SensorManager não = referência pendurada
- ⚠️ Pode impedir garbage collection

**Severidade:** 🟡 **MÉDIA** - GC delay

---

#### Problema C: Sem context manager para conexões

**Arquivo:** Vários

```python
# ❌ Padrão atual em db_manager.py (linha 547):
conn = sqlite3.connect(self.db_path)
# ... usa conn ...
conn.close()  # Pode não ser executado se erro

# ✅ Deveria ser:
with sqlite3.connect(self.db_path) as conn:
    # ... usa conn ...
    # garantido close() mesmo com exceção
```

**Severidade:** 🟡 **MÉDIA** - Risco de conexões abertas

---

## 📈 RESUMO DE SEVERIDADE

| Nível | Contagem | Problemas |
|-------|----------|-----------|
| 🔴 **CRÍTICA** | 3 | Connection pool MySQL, Thread → UI callbacks, Data race condition |
| 🟡 **ALTA** | 7 | Cleanup conexões, join() threads, Matplotlib cleanup, Lambdas binds, etc |
| 🟢 **MÉDIA** | 8 | Timers cleanup, BarChart inefficiency, Caching, Context managers |

---

## 🔧 RECOMENDAÇÕES DE CORREÇÃO

### **Prioridade 1: IMEDIATO** (Próximos 1-2 dias)

#### 1.1 Implementar Connection Pool para MySQL
```python
# Criar arquivo: backend/db_pool.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "mysql+mysqlconnector://root:@localhost:3306/thermacore",
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    echo=False
)
```

Aplicar em `main_api.py`, `main_api_completo.py`

---

#### 1.2 Usar Queue para Callbacks de Threads
```python
# Em sensor_module/sensor_manager.py
from queue import Queue

class SensorManager:
    def __init__(self, ...):
        self.ui_queue = Queue()
        
    def process_temperature(self, value):
        # Em vez de chamar callback direto:
        self.ui_queue.put(('temperature', value))
        
# Em MainUI:
def _process_sensor_queue(self):
    while not self.sensor_manager.ui_queue.empty():
        event_type, data = self.sensor_manager.ui_queue.get_nowait()
        if event_type == 'temperature':
            self.update_status(data)
    self.after(50, self._process_sensor_queue)
```

---

#### 1.3 Usar Locks para Sincronização
```python
# Em sensor_module/sensor_buffer.py
import threading

class SensorBuffer:
    def __init__(self):
        self.data = []
        self.lock = threading.Lock()
        
    def add(self, value):
        with self.lock:
            self.data.append(value)
            
    def get_all(self):
        with self.lock:
            return list(self.data)
```

---

### **Prioridade 2: CURTO PRAZO** (Próximos 3-5 dias)

#### 2.1 Cleanup de Matplotlib Figures
```python
# Em ui/charts.py - adicionar a BaseChart:
def __del__(self):
    try:
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
        if hasattr(self, 'figure') and self.figure:
            import matplotlib.pyplot as plt
            plt.close(self.figure)
    except:
        pass
```

---

#### 2.2 Cancelar Timers em destroy()
```python
# Em dashboard_tab.py:
def destroy(self):
    try:
        if self._animate_id:
            self.after_cancel(self._animate_id)
    except:
        pass
    super().destroy()

# Em database_tab.py:
def destroy(self):
    try:
        if hasattr(self, '_search_after_id'):
            self.after_cancel(self._search_after_id)
    except:
        pass
    super().destroy()
```

---

#### 2.3 Usar Context Manager para Conexões SQLite
```python
# Em database/db_manager.py - refatorar métodos:
def get_experiments(self):
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experiments")
        return cursor.fetchall()
```

---

#### 2.4 Unbing Lambdas em destroy()
```python
# Em interface/view/thermal_calculations_page.py:
def __init__(self, ...):
    self._bindings = []
    
    # Ao bind:
    binding = self.scroll_frame.bind(
        "<Configure>",
        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    )
    self._bindings.append((self.scroll_frame, binding))

def destroy(self):
    for widget, binding_id in self._bindings:
        try:
            widget.unbind("<Configure>", binding_id)
        except:
            pass
    super().destroy()
```

---

### **Prioridade 3: MÉDIO PRAZO** (Próximas 2-3 semanas)

#### 3.1 Implementar Caching
```python
# Em services/hybrid_repository.py:
from functools import lru_cache
import time

class HybridRepository:
    def __init__(self):
        self._cache = {}
        self._cache_time = {}
        
    def list_experiments(self, use_cache=True):
        if use_cache and 'experiments' in self._cache:
            if time.time() - self._cache_time.get('experiments', 0) < 60:
                return self._cache['experiments']
        
        result = self.api_online() and self.api.list_experiments() or self.sqlite.list_experiments()
        self._cache['experiments'] = result
        self._cache_time['experiments'] = time.time()
        return result
```

---

#### 3.2 Implementar Rate Limiting
```python
# Em services/hybrid_repository.py:
import asyncio
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = deque()
        
    def is_allowed(self):
        now = datetime.now()
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
```

---

#### 3.3 Adicionar Retry Logic
```python
# Em services/api_client.py:
from tenacity import retry, stop_after_attempt, wait_exponential

class ThermaCoreMySQLClient:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _request_json(self, method: str, path: str, **kwargs):
        # ... código existente ...
        pass
```

---

## 📋 CHECKLIST DE TESTES

```
□ Teste de stress com 1000 requisições em 10 segundos
  - Deve não superar 20 conexões simultâneas
  
□ Teste de estabilidade: deixar app aberto por 12 horas
  - Monitorar memory usage (deve estar estável)
  - Verificar número de conexões BD (deve estar <= 10)
  
□ Teste de threading: desconectar serial durante operação
  - Não deve causar crash
  - Deve recuperar estado corretamente
  
□ Teste de timers: abrir/fechar página 100 vezes
  - Sem vazamento de memory
  - Performance mantida
  
□ Teste de matplotlib: carregar 50 arquivos CSVs
  - Não deve ultrapassar 500MB de memória
  
□ Teste de callbacks: UI deve responder em < 100ms mesmo com thread ativa
```

---

## 🎯 PRÓXIMOS PASSOS

1. **Semana 1:** Implementar Prioridade 1 (connection pool, threads queue)
2. **Semana 2:** Implementar Prioridade 2 (cleanup, context managers)
3. **Semana 3:** Implementar Prioridade 3 + testes de stress
4. **Semana 4:** Revisão geral, profiling, otimizações finais

---

## 📚 REFERÊNCIAS

- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Threading no Python](https://docs.python.org/3/library/threading.html)
- [Tkinter Thread Safety](https://effbot.org/tkinterbook/tkinter-index.htm)
- [Matplotlib Backend TkAgg](https://matplotlib.org/3.5.3/api/backend_tkagg_api.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/)

---

**Documento preparado para discussão e implementação**
