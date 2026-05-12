# 🎯 GUIA RÁPIDO - MUDANÇAS EXATAS LINHA POR LINHA

## ARQUIVO 1: `sensor_module/serial_connection.py`

### Mudança 1 (LINHAS 1-2): Fix do Import

```diff
- import serial as pyserial
- import serial.tools.list_ports

+ import serial
+ from serial.tools import list_ports
```

### Mudança 2 (LINHA 33): Usar list_ports diretamente

```diff
  @staticmethod
  def get_available_ports():
      try:
-         ports = serial.tools.list_ports.comports()
+         ports = list_ports.comports()
          return [port.device for port in ports]
      except Exception:
          return []
```

### Mudança 3 (LINHA 55): Usar serial normalmente

```diff
  def connect(self):
      try:
          self.serial = serial.Serial(
              self.port,
              self.baudrate,
              timeout=1
          )
```

**✅ FIM DO ARQUIVO 1**

---

## ARQUIVO 2: `pcm_module/pcm_screen.py`

### Mudança 1 (NO `__init__`, antes de `_build_layout()`): Inicializar atributos

**Encontre a função `__init__` (por volta da LINHA 310).**

```diff
  def __init__(self, parent) -> None:
      super().__init__(parent, fg_color=self.BG_COLOR)
      self.service = PCMService()
      self.repository = PCMRepository()
      self.current_result: PCMResult | None = None
      self.chart_canvases: list[FigureCanvasTkAgg] = []
      self.kpi_values: dict[str, ctk.CTkLabel] = {}
      self.kpi_subvalues: dict[str, ctk.CTkLabel] = {}
+     
+     # === Histórico de sensor ===
+     self.sensor_temperature_history: list[float] = []
+     self.sensor_time_history: list[str] = []
+     
+     # === StringVars para UI ===
      self.sensor_current_temp = ctk.StringVar(value="-- °C")
      self.sensor_status = ctk.StringVar(value="Desconectado")
+     
+     # === Atributos matplotlib (serão criados em _build_layout) ===
+     self.sensor_figure: Figure | None = None
+     self.sensor_ax = None
+     self.sensor_line = None
+     self.sensor_canvas = None
+     self.sensor_status_label = None
+     
+     # === Layout ANTES de criar SensorManager ===
      self._build_layout()
+     
+     # === SensorManager DEPOIS de layout criado ===
      self.sensor_manager = SensorManager(
          on_temperature=self.update_sensor_temperature,
          on_status=self.update_sensor_status,
          on_log=self.add_sensor_log,
      )
-     self.sensor_temperatures = []
-     self.sensor_temperature_history = []
-     self.sensor_time_history = []
-     
-     self.sensor_current_temp = ctk.StringVar(value="-- °C")
-     self.sensor_status = ctk.StringVar(value="Desconectado")
-     
-     self._build_layout()
```

### Mudança 2 (NO FINAL DE `_build_layout()`): Adicionar seção sensor

**Encontre o final da função `_build_layout()` e adicione antes do último `return` ou `pass`:**

```python
        # ============================================================
        # SEÇÃO SENSOR REALTIME
        # ============================================================

        # Frame do sensor
        sensor_frame = ctk.CTkFrame(self.scroll_frame, fg_color=self.PANEL_COLOR, corner_radius=12)
        sensor_frame.grid(row=10, column=0, sticky="ew", padx=12, pady=(16, 16))
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

### Mudança 3 (LINHAS ~1047-1074): Corrigir método update_sensor_temperature

**DELETAR completamente a segunda definição (linhas ~1132-1142):**

```diff
- def update_sensor_temperature(self, temperature):
-
-     self.sensor_temperatures.append(temperature)
-
-     if len(self.sensor_temperatures) > 300:
-         self.sensor_temperatures = self.sensor_temperatures[-300:]
-
-     self.status_label.configure(
-         text=f"🌡 Sensor online: {temperature:.2f} °C",
-         text_color=self.SUCCESS_COLOR
-     )
```

**REESCREVER a PRIMEIRA definição (por volta de LINHA 1047):**

```diff
- def update_sensor_temperature(self, value):
-
-     timestamp = datetime.now().strftime("%H:%M:%S")
-
-     self.sensor_current_temp.set(
-         f"{value:.2f} °C"
-     )
-
-     self.sensor_temperature_history.append(value)
-
-     self.sensor_time_history.append(timestamp)
-
-     if len(self.sensor_temperature_history) > 60:
-         self.sensor_temperature_history = self.sensor_temperature_history[-60:]
-         self.sensor_time_history = self.sensor_time_history[-60:]
-
-     self.sensor_line.set_data(
-         range(len(self.sensor_temperature_history)),
-         self.sensor_temperature_history
-     )
-
-     self.sensor_ax.set_xlim(
-         0,
-         max(10, len(self.sensor_temperature_history))
-     )
-
-     self.sensor_ax.set_ylim(
-         min(self.sensor_temperature_history) - 2,
-         max(self.sensor_temperature_history) + 2
-     )
-
-     self.sensor_canvas.draw_idle()

+ def update_sensor_temperature(self, temperature):
+     """Callback chamado a cada leitura do sensor em tempo real"""
+     
+     # Armazenar temperatura no histórico
+     self.sensor_temperature_history.append(temperature)
+     
+     # Manter apenas últimas 60 leituras
+     if len(self.sensor_temperature_history) > 60:
+         self.sensor_temperature_history = self.sensor_temperature_history[-60:]
+     
+     # Atualizar label com temperatura atual
+     self.sensor_current_temp.set(f"{temperature:.2f} °C")
+     
+     # Atualizar gráfico matplotlib
+     if self.sensor_line is not None:
+         self.sensor_line.set_data(
+             range(len(self.sensor_temperature_history)),
+             self.sensor_temperature_history
+         )
+         
+         # Auto-escala o eixo Y
+         if len(self.sensor_temperature_history) > 1:
+             temps = self.sensor_temperature_history
+             margin = 2
+             self.sensor_ax.set_ylim(min(temps) - margin, max(temps) + margin)
+         
+         # Auto-escala o eixo X
+         self.sensor_ax.set_xlim(0, max(10, len(self.sensor_temperature_history)))
+         
+         # Redesenha sem bloquear UI
+         self.sensor_canvas.draw_idle()
+     
+     # Status visual do sensor
+     self.update_sensor_status("🟢 Conectado", success=True)
+
+
+ def update_sensor_status(self, text, success=False):
+     """Atualiza status do sensor (cor e texto)"""
+     color = "#00FF99" if success else "#FF4444"
+     
+     self.sensor_status.set(text)
+     
+     if hasattr(self, 'sensor_status_label') and self.sensor_status_label:
+         self.sensor_status_label.configure(text_color=color)
+
+
+ def add_sensor_log(self, text):
+     """Log de eventos do sensor"""
+     timestamp = datetime.now().strftime("%H:%M:%S")
+     print(f"[SENSOR {timestamp}] {text}")
```

### Mudança 4 (NO FINAL DA CLASSE): Adicionar métodos

**NO FINAL da classe PCMCalcScreen, adicione:**

```python
    # ============================================================
    # CONTROLE DO SENSOR
    # ============================================================
    
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

**✅ FIM DO ARQUIVO 2**

---

## 📋 RESUMO DAS MUDANÇAS

| Arquivo | Linhas | O Quê | Status |
|---------|--------|-------|--------|
| `serial_connection.py` | 1-2 | Corrigir imports | ✏️ Mudança |
| `serial_connection.py` | 33 | Usar `list_ports` | ✏️ Mudança |
| `pcm_screen.py` | ~310 (init) | Adicionar atributos | ✏️ Mudança + Adição |
| `pcm_screen.py` | ~380 (`_build_layout`) | Adicionar gráfico | ✏️ Adição |
| `pcm_screen.py` | ~1047-1074 | Reescrever método | ✏️ Mudança |
| `pcm_screen.py` | ~1132-1142 | DELETAR 2ª definição | 🗑️ Deleção |
| `pcm_screen.py` | Fim da classe | Adicionar 3 métodos | ✏️ Adição |

---

## ✅ ORDEM DE APLICAÇÃO

1. **Primeiro:** Arquivo `serial_connection.py` (3 mudanças simples)
2. **Segundo:** Arquivo `pcm_screen.py` (4 mudanças maiores)
3. **Terceiro:** Testar

---

## 🧪 TESTE RÁPIDO APÓS MUDANÇAS

```bash
# Test 1: Imports
python -c "from sensor_module.serial_connection import SerialConnection; print('✓ Import OK')"

# Test 2: Métodos
python -c "from pcm_module.pcm_screen import PCMCalcScreen; print('✓ Methods OK')"

# Test 3: Instância
python -c "import customtkinter as ctk; from pcm_module.pcm_screen import PCMCalcScreen; app = ctk.CTk(); s = PCMCalcScreen(app); print('✓ Instantiate OK'); app.destroy()"
```

**Esperado:** Todos ✓ OK

---

**Tempo estimado para aplicar:** 30-45 minutos
