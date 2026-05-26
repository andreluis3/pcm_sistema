# ✅ CORREÇÕES DEFINITIVAS - CÓDIGO PRONTO PARA COPIAR

---

## 🔧 CORREÇÃO 1: SERIAL CONNECTION - Import Fix

**Arquivo:** `sensor_module/serial_connection.py`

### ❌ ANTES (PROBLEMÁTICO):

```python
import serial as pyserial                    # ← Alias confuso
import serial.tools.list_ports

class SerialConnection:
    # ...
    
    @staticmethod
    def get_available_ports():
        try:
            ports = serial.tools.list_ports.comports()  # ← Usa 'serial', não 'pyserial'!
            return [port.device for port in ports]
        except Exception:
            return []
    
    def connect(self):
        try:
            self.serial = serial.Serial(  # ← ERRO: serial não definido!
                self.port,
                self.baudrate,
                timeout=1
            )
```

### ✅ DEPOIS (CORRIGIDO):

```python
import serial
from serial.tools import list_ports

class SerialConnection:
    # ...
    
    @staticmethod
    def get_available_ports():
        try:
            ports = list_ports.comports()  # ← Usa list_ports diretamente
            return [port.device for port in ports]
        except Exception:
            return []
    
    def connect(self):
        try:
            self.serial = serial.Serial(  # ← Usa serial normalmente
                self.port,
                self.baudrate,
                timeout=1
            )
```

### 📝 MUDANÇAS EXATAS:

**Linha 1-2:** Substituir
```python
import serial as pyserial
import serial.tools.list_ports
```

Por:
```python
import serial
from serial.tools import list_ports
```

**Linha 33:** Substituir
```python
ports = serial.tools.list_ports.comports()
```

Por:
```python
ports = list_ports.comports()
```

**Linha 55:** MANTER como está (já está correto)
```python
self.serial = serial.Serial(...)
```

---

## 🔧 CORREÇÃO 2: PCM SCREEN - Método Duplicado + Gráfico

**Arquivo:** `pcm_module/pcm_screen.py`

### PASSO 1: Remover a segunda definição (linhas 1132-1142)

#### ❌ DELETAR ISTO:

```python
def update_sensor_temperature(self, temperature):

    self.sensor_temperatures.append(temperature)

    if len(self.sensor_temperatures) > 300:
        self.sensor_temperatures = self.sensor_temperatures[-300:]

    self.status_label.configure(
        text=f"🌡 Sensor online: {temperature:.2f} °C",
        text_color=self.SUCCESS_COLOR
    )
```

### PASSO 2: Corrigir a primeira definição (linhas 1047-1074)

#### ❌ ANTES (INCOMPLETO):

```python
def update_sensor_temperature(self, value):

    timestamp = datetime.now().strftime("%H:%M:%S")

    self.sensor_current_temp.set(
        f"{value:.2f} °C"
    )

    self.sensor_temperature_history.append(value)

    self.sensor_time_history.append(timestamp)

    if len(self.sensor_temperature_history) > 60:
        self.sensor_temperature_history = self.sensor_temperature_history[-60:]
        self.sensor_time_history = self.sensor_time_history[-60:]

    self.sensor_line.set_data(
        range(len(self.sensor_temperature_history)),
        self.sensor_temperature_history
    )

    self.sensor_ax.set_xlim(
        0,
        max(10, len(self.sensor_temperature_history))
    )

    self.sensor_ax.set_ylim(
        min(self.sensor_temperature_history) - 2,
        max(self.sensor_temperature_history) + 2
    )

    self.sensor_canvas.draw_idle()
```

#### ✅ DEPOIS (COMPLETO):

```python
def update_sensor_temperature(self, temperature):
    """Callback chamado a cada leitura do sensor em tempo real"""
    
    # Armazenar temperatura no histórico
    self.sensor_temperature_history.append(temperature)
    
    # Manter apenas últimas 60 leituras
    if len(self.sensor_temperature_history) > 60:
        self.sensor_temperature_history = self.sensor_temperature_history[-60:]
    
    # Atualizar label com temperatura atual
    self.sensor_current_temp.set(f"{temperature:.2f} °C")
    
    # Atualizar gráfico matplotlib
    if self.sensor_line is not None:
        self.sensor_line.set_data(
            range(len(self.sensor_temperature_history)),
            self.sensor_temperature_history
        )
        
        # Auto-escala o eixo Y
        if len(self.sensor_temperature_history) > 1:
            temps = self.sensor_temperature_history
            margin = 2
            self.sensor_ax.set_ylim(min(temps) - margin, max(temps) + margin)
        
        # Auto-escala o eixo X
        self.sensor_ax.set_xlim(0, max(10, len(self.sensor_temperature_history)))
        
        # Redesenha sem bloquear UI
        self.sensor_canvas.draw_idle()
    
    # Status visual do sensor
    self.update_sensor_status("🟢 Conectado", success=True)


def update_sensor_status(self, text, success=False):
    """Atualiza status do sensor (cor e texto)"""
    color = "#00FF99" if success else "#FF4444"
    
    self.sensor_status.set(text)
    
    if hasattr(self, 'sensor_status_label') and self.sensor_status_label:
        self.sensor_status_label.configure(text_color=color)


def add_sensor_log(self, text):
    """Log de eventos do sensor"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[SENSOR {timestamp}] {text}")
```

### PASSO 3: Criar o gráfico matplotlib no `__init__`

#### ❌ ANTES (em `__init__`, linha ~310):

```python
def __init__(self, parent) -> None:
    super().__init__(parent, fg_color=self.BG_COLOR)
    self.service = PCMService()
    self.repository = PCMRepository()
    self.current_result: PCMResult | None = None
    self.chart_canvases: list[FigureCanvasTkAgg] = []
    self.kpi_values: dict[str, ctk.CTkLabel] = {}
    self.kpi_subvalues: dict[str, ctk.CTkLabel] = {}
    
    # ❌ Falta inicializar atributos do sensor!
    self.sensor_manager = SensorManager(
        on_temperature=self.update_sensor_temperature,
        on_status=self.update_sensor_status,
        on_log=self.add_sensor_log,
    )
    self.sensor_temperatures = []
    self.sensor_temperature_history = []
    self.sensor_time_history = []
    
    self.sensor_current_temp = ctk.StringVar(value="-- °C")
    self.sensor_status = ctk.StringVar(value="Desconectado")
    
    self._build_layout()
```

#### ✅ DEPOIS (CORRETO):

```python
def __init__(self, parent) -> None:
    super().__init__(parent, fg_color=self.BG_COLOR)
    
    # === Serviços de PCM ===
    self.service = PCMService()
    self.repository = PCMRepository()
    self.current_result: PCMResult | None = None
    self.chart_canvases: list[FigureCanvasTkAgg] = []
    self.kpi_values: dict[str, ctk.CTkLabel] = {}
    self.kpi_subvalues: dict[str, ctk.CTkLabel] = {}
    
    # === Histórico de sensor ===
    self.sensor_temperature_history: list[float] = []
    self.sensor_time_history: list[str] = []
    
    # === StringVars para UI ===
    self.sensor_current_temp = ctk.StringVar(value="-- °C")
    self.sensor_status = ctk.StringVar(value="Desconectado")
    
    # === Atributos matplotlib (serão criados em _build_layout) ===
    self.sensor_figure: Figure | None = None
    self.sensor_ax = None
    self.sensor_line = None
    self.sensor_canvas = None
    self.sensor_status_label = None
    
    # === Layout ANTES de criar SensorManager ===
    self._build_layout()
    
    # === SensorManager DEPOIS de layout criado ===
    self.sensor_manager = SensorManager(
        on_temperature=self.update_sensor_temperature,
        on_status=self.update_sensor_status,
        on_log=self.add_sensor_log,
    )
```

### PASSO 4: Adicionar seção de gráfico matplotlib em `_build_layout()`

#### Encontre a seção de layout e adicione isto (antes do final de `_build_layout`):

```python
# ============================================================
# SEÇÃO SENSOR REALTIME (ADICIONAR EM _build_layout)
# ============================================================

# Frame do sensor
sensor_frame = ctk.CTkFrame(self.scroll_frame, fg_color=self.PANEL_COLOR, corner_radius=12)
sensor_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(16, 16))  # Ajuste row se necessário
sensor_frame.grid_columnconfigure(0, weight=1)

# Header do sensor
sensor_header = ctk.CTkFrame(sensor_frame, fg_color="transparent")
sensor_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
sensor_header.grid_columnconfigure(1, weight=1)

ctk.CTkLabel(
    sensor_header,
    text="🌡 Sensor em Tempo Real",
    font=("Arial", 18, "bold"),
    text_color=self.TEXT_PRIMARY,
).grid(row=0, column=0, sticky="w")

self.sensor_status_label = ctk.CTkLabel(
    sensor_header,
    text="Desconectado",
    font=("Arial", 13),
    text_color="#FF4444",
)
self.sensor_status_label.grid(row=0, column=2, sticky="e", padx=(12, 0))

# Temperatura atual
temp_display_frame = ctk.CTkFrame(sensor_frame, fg_color=self.CARD_COLOR, corner_radius=8)
temp_display_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

ctk.CTkLabel(
    temp_display_frame,
    text="Temperatura Atual:",
    font=("Arial", 12),
    text_color=self.TEXT_SECONDARY,
).pack(side="left", padx=12, pady=8)

sensor_temp_label = ctk.CTkLabel(
    temp_display_frame,
    textvariable=self.sensor_current_temp,
    font=("Arial", 14, "bold"),
    text_color=self.TEMP_COLOR,
)
sensor_temp_label.pack(side="left", padx=12, pady=8)

# Criar gráfico matplotlib
self.sensor_figure = Figure(figsize=(8, 3), dpi=100, facecolor=self.PANEL_COLOR)
self.sensor_ax = self.sensor_figure.add_subplot(111)
self.sensor_ax.set_facecolor(self.CARD_COLOR)
self.sensor_ax.set_title("Temperatura vs Tempo", color=self.TEXT_PRIMARY, fontsize=12, pad=10)
self.sensor_ax.set_xlabel("Amostras", color=self.TEXT_SECONDARY, fontsize=10)
self.sensor_ax.set_ylabel("Temperatura (°C)", color=self.TEXT_SECONDARY, fontsize=10)
self.sensor_ax.grid(True, alpha=0.2, color=self.BORDER_COLOR)
self.sensor_ax.tick_params(colors=self.TEXT_SECONDARY, labelsize=9)

# Linha do gráfico
self.sensor_line, = self.sensor_ax.plot([], [], color="#6B7280", linewidth=2.5, marker='o', markersize=4)

# Cores dos spines
for spine in self.sensor_ax.spines.values():
    spine.set_color(self.BORDER_COLOR)
    spine.set_linewidth(0.5)

# Canvas do matplotlib
self.sensor_canvas = FigureCanvasTkAgg(self.sensor_figure, master=sensor_frame)
self.sensor_canvas.get_tk_widget().grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

# Botões de controle
sensor_controls = ctk.CTkFrame(sensor_frame, fg_color="transparent")
sensor_controls.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
sensor_controls.grid_columnconfigure(0, weight=1)

ctk.CTkButton(
    sensor_controls,
    text="🔗 Conectar Sensor",
    width=150,
    command=self.connect_sensor,
    fg_color="#4B5563",
    hover_color="#5D6F7F",
    font=("Arial", 12, "bold"),
).grid(row=0, column=0, sticky="w")

ctk.CTkButton(
    sensor_controls,
    text="💾 Exportar Dados",
    width=150,
    command=self.export_sensor_csv,
    fg_color="#4B5563",
    hover_color="#5D6F7F",
    font=("Arial", 12, "bold"),
).grid(row=0, column=1, sticky="w", padx=(12, 0))

ctk.CTkButton(
    sensor_controls,
    text="🔌 Desconectar",
    width=150,
    command=self.disconnect_sensor,
    fg_color="#663333",
    hover_color="#884444",
    font=("Arial", 12, "bold"),
).grid(row=0, column=2, sticky="w", padx=(12, 0))
```

### PASSO 5: Adicionar métodos de controle do sensor

```python
def connect_sensor(self):
    """Conecta ao sensor serial"""
    config = {
        "port": "COM3",      # Ajustar conforme necessário
        "baudrate": 115200
    }
    
    self.sensor_manager.connect("Serial", config)
    self.update_sensor_status("🟡 Conectando...", success=False)


def disconnect_sensor(self):
    """Desconecta do sensor"""
    self.sensor_manager.disconnect()
    self.update_sensor_status("🔴 Desconectado", success=False)
    self.sensor_current_temp.set("-- °C")


def export_sensor_csv(self):
    """Exporta histórico do sensor para CSV"""
    if not self.sensor_temperature_history:
        messagebox.showwarning("Aviso", "Nenhum dado para exportar")
        return
    
    filepath = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV", "*.csv"), ("Todos", "*.*")]
    )
    
    if not filepath:
        return
    
    try:
        import csv
        from datetime import datetime
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Tempo (s)", "Temperatura (°C)"])
            
            for i, temp in enumerate(self.sensor_temperature_history):
                writer.writerow([i, f"{temp:.2f}"])
        
        messagebox.showinfo("Sucesso", f"Dados exportados para:\n{filepath}")
    
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao exportar:\n{str(e)}")
```

---

## 🧪 TESTES DE VALIDAÇÃO

### Teste 1: Verificar Serial Import

```bash
# Terminal Python
python -c "
import serial
from serial.tools import list_ports

print('✓ Serial importado:', serial)
print('✓ Serial.Serial:', serial.Serial)
print('✓ list_ports:', list_ports)

# Testar get_available_ports
from sensor_module.serial_connection import SerialConnection
ports = SerialConnection.get_available_ports()
print(f'✓ Portas disponíveis: {ports}')
"
```

**Esperado:** Nenhum AttributeError, lista de portas exibida

### Teste 2: Verificar Métodos do PCMCalcScreen

```bash
python -c "
from pcm_module.pcm_screen import PCMCalcScreen
import customtkinter as ctk

# Verificar que métodos existem
print('✓ update_sensor_temperature:', hasattr(PCMCalcScreen, 'update_sensor_temperature'))
print('✓ update_sensor_status:', hasattr(PCMCalcScreen, 'update_sensor_status'))
print('✓ add_sensor_log:', hasattr(PCMCalcScreen, 'add_sensor_log'))
print('✓ connect_sensor:', hasattr(PCMCalcScreen, 'connect_sensor'))
print('✓ disconnect_sensor:', hasattr(PCMCalcScreen, 'disconnect_sensor'))
print('✓ export_sensor_csv:', hasattr(PCMCalcScreen, 'export_sensor_csv'))
"
```

**Esperado:** Todos True

### Teste 3: Instanciar PCMCalcScreen

```bash
python -c "
import customtkinter as ctk
from pcm_module.pcm_screen import PCMCalcScreen

# Criar janela
app = ctk.CTk()
screen = PCMCalcScreen(app)

# Verificar atributos
print('✓ sensor_figure:', screen.sensor_figure is not None)
print('✓ sensor_ax:', screen.sensor_ax is not None)
print('✓ sensor_line:', screen.sensor_line is not None)
print('✓ sensor_canvas:', screen.sensor_canvas is not None)
print('✓ sensor_status_label:', screen.sensor_status_label is not None)

# Testar callback
screen.update_sensor_temperature(25.5)
print(f'✓ Temperatura exibida: {screen.sensor_current_temp.get()}')

app.destroy()
"
```

**Esperado:** Todos True, temperatura exibida como "25.50 °C"

### Teste 4: Simular Leitura Sensor (se tiver hardware)

```bash
# Terminal 1: Rodar a aplicação
python main.py

# Terminal 2: Enviar dados simulados
python -c "
import serial
import time

# Simular dados sendo enviados pela serial
try:
    ser = serial.Serial('COM3', 115200, timeout=1)
    
    for i in range(10):
        temp = 25.0 + i * 0.5
        ser.write(f'TEMP:{temp:.2f}\\n'.encode())
        time.sleep(0.5)
    
    ser.close()
    print('✓ Dados simulados enviados')
except Exception as e:
    print(f'Erro: {e}')
"
```

**Esperado:** Gráfico atualiza em tempo real, temperatura exibida

---

## 🎯 CHECKLIST DE APLICAÇÃO

- [ ] **Correção 1:** Corrigir imports em `serial_connection.py`
  - [ ] Linha 1-2: Trocar imports
  - [ ] Linha 33: Trocar `serial.tools.list_ports` por `list_ports`
  
- [ ] **Correção 2:** Corrigir `pcm_screen.py`
  - [ ] Deletar segunda definição de `update_sensor_temperature` (linhas ~1132-1142)
  - [ ] Corrigir primeira definição
  - [ ] Adicionar métodos `update_sensor_status`, `add_sensor_log`, `connect_sensor`, etc
  - [ ] Modificar `__init__` para inicializar atributos matplotlib
  - [ ] Adicionar seção de gráfico em `_build_layout()`

- [ ] **Teste 1:** `python -c "...serial test..."`
  - [ ] Sem erros
  - [ ] Portas listadas corretamente

- [ ] **Teste 2:** `python -c "...method check..."`
  - [ ] Todos os métodos existem

- [ ] **Teste 3:** `python -c "...instantiate..."`
  - [ ] Instancia sem erros
  - [ ] Gráfico criado
  - [ ] Callback funciona

- [ ] **Teste 4:** Aplicação roda
  - [ ] Sem erro "no attribute"
  - [ ] Serial conecta
  - [ ] Gráfico mostra dados

---

## 📞 SUPORTE

Se encontrar erros ao aplicar:

1. **Erro em import:** Verificar se `pyserial` está instalado
   ```bash
   pip install --force-reinstall pyserial
   ```

2. **Erro em método:** Verificar se deletou a segunda definição

3. **Gráfico não aparecer:** Verificar se `_build_layout()` está sendo chamado ANTES de `sensor_manager`

4. **Sensor não conecta:** Verificar porta serial (pode não ser COM3)

---

**Status:** Pronto para aplicar ✅  
**Tempo esperado:** 30-45 minutos
