# 📑 MATRIZ DE REFERÊNCIA RÁPIDA - GUIA DE IMPLEMENTAÇÃO

## Tabela de Problemas com Soluções Diretas

| ID | Problema | Arquivo | Linha | Solução Rápida | Esforço | Impacto |
|:--:|----------|---------|-------|---|---|---|
| **C1** | ❌ MySQL sem pool | `backend/main_api.py` | 1-20 | `DBUtils.PooledDB(size=15)` | 1h | 🔴🔴🔴 |
| **C2** | ❌ Threads → UI direto | `sensor_module/serial_connection.py` | 50-80 | `queue.Queue()` | 1-2h | 🔴🔴🔴 |
| **C3** | ❌ Daemon sem join() | `sensor_module/serial_connection.py` | 27-33 | `thread.join(timeout=5)` | 30min | 🔴🔴🔴 |
| **A4** | ❌ after() não cancel | `interface/dashboard_tab.py` | 684 | `after_cancel()` antes | 1-2h | 🟠🟠 |
| **A4** | ❌ after() não cancel | `interface/database_tab.py` | 249 | `after_cancel()` antes | 1-2h | 🟠🟠 |
| **A4** | ❌ after() não cancel | `interface/loading_screen.py` | 31-32 | `after_cancel()` antes | 1-2h | 🟠🟠 |
| **A5** | ❌ Matplotlib leak | `interface/view/charts.py` | 1-40 | `plt.close(figure)` em destroy | 1h | 🟠🟠 |
| **A5** | ❌ Matplotlib leak | `interface/dashboard_tab.py` | 200-220 | `clear()` + `draw_idle()` | 1h | 🟠🟠 |
| **A6** | ❌ SQLite não fecha | `database/db_manager.py` | 35-40 | Context manager + `.close()` | 30min | 🟠🟠 |
| **A7** | ❌ API health check | `services/hybrid_repository.py` | 20-50 | Cache com TTL 60s | 1h | 🟠🟠 |
| **A8** | ❌ Search lento | `interface/database_tab.py` | 249 | Debounce 500ms + índices | 2h | 🟠🟠 |
| **A9** | ❌ Update loops | `interface/dashboard_tab.py` | 70-150 | Queue centralizada | 2-3h | 🟠🟠 |
| **M10** | ❌ Lambdas circulares | `interface/main_ui.py` | 80-150 | Usar método ao invés de lambda | 1h | 🟡 |
| **M11** | ❌ Widgets não destroy | `interface/main_ui.py` | 130-150 | Destruir explicitamente | 1h | 🟡 |
| **M12** | ❌ FastAPI sem validação | `backend/main_api.py` | 20-55 | Adicionar try/except | 1-2h | 🟡 |
| **M13** | ❌ Simulation CPU | `sensor_module/simulation_connection.py` | 40-55 | Aumentar sleep para 2s | 15min | 🟡 |
| **M14** | ❌ Dashboard metrics | `interface/dashboard_tab.py` | 75-130 | Cache de resultados | 1h | 🟡 |
| **M15** | ❌ Sensor buffer | `sensor_module/sensor_buffer.py` | ? | Adicionar `.maxlen=1000` | 15min | 🟡 |
| **M16** | ❌ Sem pagination | `services/hybrid_repository.py` | 30-50 | Adicionar `limit=500` | 1h | 🟡 |
| **M17** | ❌ MySQL password | `backend/main_api.py` | 5-10 | Usar `.env` ou config | 30min | 🟡 |
| **M18** | ❌ Exception genérico | `services/hybrid_repository.py` | 14-18 | Excepts específicos | 1h | 🟡 |

---

## 📍 Mapa de Localização dos Problemas

### Problema Crítico 1: MySQL Pool
```
📂 backend/
  └─ main_api.py
     ├─ Linha 5-10: get_connection() ❌
     ├─ Linha 20: criar_experimento() ← usa get_connection()
     └─ Linha 40: listar_experimentos() ← usa get_connection()

SOLUÇÃO:
1. Instalar: pip install DBUtils
2. Adicionar no inicio do arquivo:
   from DBUtils.PooledDB import PooledDB
   
3. Criar pool único:
   db_pool = PooledDB(
       mysql.connector,
       size=15,  # Manter 15 conexões abertas
       host="localhost",
       user="root",
       password="",
       database="thermacore"
   )
   
4. Substituir get_connection():
   def get_connection():
       return db_pool.connection()
```

### Problema Crítico 2: Thread Safety
```
📂 sensor_module/
  └─ serial_connection.py
     └─ _read_loop() (linha 50-80) ❌
        └─ Chama on_data() diretamente

SOLUÇÃO:
1. Adicionar no __init__:
   self.queue = queue.Queue()
   
2. Modificar _read_loop():
   ❌ Antes: self.on_data(temperature)
   ✅ Depois: self.queue.put(temperature)
   
3. Na UI, processar queue:
   def _process_sensor_queue(self):
       while not self.queue.empty():
           temp = self.queue.get_nowait()
           if self.on_data:
               self.on_data(temp)
       self.after(50, _process_sensor_queue)
```

### Problema Crítico 3: Daemon Join
```
📂 sensor_module/
  └─ serial_connection.py
     ├─ connect() (linha 27-33) ❌
     └─ disconnect() (linha 43-50) ❌

SOLUÇÃO:
No disconnect(), adicionar:
```python
def disconnect(self):
    self.running = False
    
    if self.thread:
        self.thread.join(timeout=5)  # ✅ NOVO
        self.thread = None  # ✅ NOVO
    
    try:
        if self.connection:
            self.connection.close()
    except:
        pass
```

### Problema Alto 4: Timer Cleanup
```
📂 interface/
  ├─ dashboard_tab.py (linha 684) ❌
  ├─ database_tab.py (linha 249) ❌
  └─ loading_screen.py (linha 31-32) ❌

SOLUÇÃO PADRÃO:
❌ Antes:
    def load_dashboard(self):
        self._animate_id = self.after(120, self._animate_pcm)

✅ Depois:
    def load_dashboard(self):
        if self._animate_id:  # ← Adicionar
            self.after_cancel(self._animate_id)  # ← Adicionar
        self._animate_id = self.after(120, self._animate_pcm)

E no destroy():
    def destroy(self):
        if self._animate_id:  # ← Adicionar
            self.after_cancel(self._animate_id)  # ← Adicionar
        super().destroy()
```

### Problema Alto 5: Matplotlib Cleanup
```
📂 interface/
  ├─ view/charts.py (linha 1-40) ❌
  └─ dashboard_tab.py (linha 200-220) ❌

SOLUÇÃO:
Em LineChart class:
```python
def cleanup(self):  # ← Adicionar método
    if self.widget:
        self.widget.destroy()
    self.figure.clear()
    import matplotlib.pyplot as plt
    plt.close(self.figure)

# Chamar em DashboardTab.destroy():
def destroy(self):
    if hasattr(self, 'temp_chart'):
        self.temp_chart.cleanup()
    # ... outros charts
    super().destroy()
```

### Problema Alto 6: SQLite Context Manager
```
📂 database/
  └─ db_manager.py (linha 35-40) ❌

SOLUÇÃO:
```python
# ❌ Antes
class DatabaseManager:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(self.db_path)
    # Ninguém chama close()

# ✅ Depois
class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.conn = None
        self._connect()
    
    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()

# Usar:
with DatabaseManager() as db:
    db.list_experiments()
# Fecha automaticamente
```

### Problema Alto 7: API Health Check Cache
```
📂 services/
  └─ hybrid_repository.py (linha 20-50) ❌

SOLUÇÃO:
```python
import time

class HybridRepository:
    def __init__(self):
        self._api_online_cache = None
        self._api_check_time = 0
        self._api_check_ttl = 60  # 60 segundos

    def api_online(self):
        now = time.time()
        if (self._api_online_cache is not None and 
            now - self._api_check_time < self._api_check_ttl):
            return self._api_online_cache
        
        self._api_online_cache = self.api.health_check()
        self._api_check_time = now
        return self._api_online_cache
```

### Problema Alto 8: Search Debounce + Índices
```
📂 interface/
  └─ view/database_tab.py (linha 249) ❌

SOLUÇÃO:
```python
# ❌ Antes: debounce 200ms
def _on_search_keyrelease(self, _event=None):
    if self._search_after_id:
        self.after_cancel(self._search_after_id)
    self._search_after_id = self.after(200, self.search_experiment)

# ✅ Depois: debounce 500ms
def _on_search_keyrelease(self, _event=None):
    if self._search_after_id:
        self.after_cancel(self._search_after_id)
    self._search_after_id = self.after(500, self.search_experiment)  # ← 500ms
```

E adicionar índices no banco (em db_manager.py):
```python
def create_tables(self):
    # ... tabelas ...
    self._create_indices()  # ← Adicionar

def _create_indices(self):
    # Índices para search
    self.conn.execute("CREATE INDEX IF NOT EXISTS idx_material ON experiments(material)")
    self.conn.execute("CREATE INDEX IF NOT EXISTS idx_operador ON experiments(operador)")
    self.conn.execute("CREATE INDEX IF NOT EXISTS idx_capsula ON experiments(capsula)")
    self.conn.commit()
```

### Problema Alto 9: Update Loop Centralizado
```
📂 interface/
  └─ dashboard_tab.py (linha 70-150) ❌

SOLUÇÃO: Centralizar em fila de eventos
```python
import queue

class DashboardTab(ctk.CTkFrame):
    def __init__(self, ...):
        self._update_queue = queue.Queue()
    
    def _process_ui_queue(self):
        try:
            while True:
                action, *args = self._update_queue.get_nowait()
                
                if action == "temperature":
                    self._update_temperature(args[0])
                elif action == "metrics":
                    self._update_metrics(*args)
                elif action == "graph":
                    self.plot_temperature_graph(args[0])
        except queue.Empty:
            pass
        
        self._queue_after_id = self.after(50, self._process_ui_queue)

# Threads/callbacks colocam na fila:
def on_temperature(self, temp):
    self._update_queue.put(("temperature", temp))
    # Não chama update direto!
```

---

## 🔄 Ordem Recomendada de Implementação

### DIA 1
- [ ] MySQL Pool (C1) - 1h
- [ ] Test: `curl -X GET http://localhost:8000/api/experimentos` × 100

### DIA 2
- [ ] Thread Safety (C2) - 1-2h
- [ ] Test: Sensor conectado 1h contínuo

### DIA 3
- [ ] Daemon Join (C3) - 30min
- [ ] Test: Conecta/desconecta 50 vezes

### DIA 4
- [ ] Timer Cleanup em 3 arquivos (A4) - 2h
- [ ] Test: Troca aba 100 vezes, CPU deve estar <10%

### DIA 5
- [ ] Matplotlib Cleanup (A5) - 1h
- [ ] Test: Dashboard aberto 8h, RAM <250 MB

### DIA 6
- [ ] SQLite Context Manager (A6) - 30min
- [ ] API Health Cache (A7) - 1h
- [ ] Test: Sem "database locked" errors

### DIA 7
- [ ] Search Debounce + Índices (A8) - 2h
- [ ] Test: Search <200ms para 100 items

### Semanas 2-3
- [ ] Update Loop Centralizado (A9) e médios (M10-M18)

---

## 🧪 Testes de Validação

### Teste 1: MySQL Pool
```bash
# Terminal 1: rodar app
python main.py

# Terminal 2: disparar 100 requisições paralelas
for i in {1..100}; do
    curl -X GET http://localhost:8000/api/experimentos &
done
wait
# Resultado esperado: Todas 200 OK em ~2-3s
```

### Teste 2: Thread Safety
```python
# Rodar sensor serial 1 hora, nenhum crash esperado
python -m sensor_module.sensor_manager
# Monitorar: sem "Tcl error", sem freeze
```

### Teste 3: Memory Leak
```bash
# Rodar 8 horas, monitorar RAM
watch -n 10 'ps aux | grep python | grep main.py'
# Esperado: RAM cresce lentamente (<20 MB/hora)
# Antes: +200 MB/hora
```

### Teste 4: Performance
```python
import timeit

# Dashboard load
t = timeit.timeit(lambda: db.list_experiments(), number=1)
print(f"Dashboard load: {t*1000:.0f}ms")  # Esperado: <700ms

# Search
t = timeit.timeit(
    lambda: db.search_experiments_flexible("material"),
    number=10
) / 10
print(f"Search avg: {t*1000:.0f}ms")  # Esperado: <200ms
```

---

## 📊 Status Esperado Após Cada Fase

| Fase | Problemas Corrigidos | Ganho | Status |
|------|---|---|---|
| Inicial | 0/18 | 0% | 🔴 Crítico |
| Dia 3 (C1-C3) | 3/18 | 50% | 🟠 Instável |
| Dia 7 (C1-A4) | 9/18 | 70% | 🟡 Viável |
| Semana 2 (C1-A9) | 14/18 | 85% | 🟢 Robusto |
| Semana 3 (Todos) | 18/18 | 100% | ✅ Produção |

---

## 📞 Checklist Final

Antes de ir para produção:

- [ ] Todos os críticos (C1-C3) implementados
- [ ] Todos os altos (A4-A9) implementados
- [ ] Teste 24h contínuo sem restart ✓
- [ ] Teste com 50 usuários simultâneos ✓
- [ ] Teste com 10.000 experimentos no BD ✓
- [ ] Nenhum "database locked" error ✓
- [ ] Nenhum crash em 24h ✓
- [ ] RAM estável (<300 MB após 8h) ✓
- [ ] CPU idle <5% (não lendo sensor) ✓
- [ ] Documentação atualizada ✓

**Status após tudo:** 90-95% produção ready

---

Generated: 2026-05-12
Status: Guia pronto para implementação
