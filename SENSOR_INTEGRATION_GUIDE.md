# 🔬 GUIA COMPLETO DE INTEGRAÇÃO DE SENSORES
## PCM Thermal Manager - Arquitetura Profissional

---

## 📋 SUMÁRIO EXECUTIVO

Este documento descreve a arquitetura completa de integração de sensores no PCM Thermal Manager, com suporte a **4 protocolos diferentes**: Serial (PySerial), HTTP API, MQTT e Simulação.

**Status atual**: ⚠️ Parcialmente implementado
- ✅ Serial (funciona)
- ✅ Simulação (funciona)
- ❌ HTTP API (não está integrada)
- ❌ MQTT (não implementada)
- ❌ UI Dinâmica (widgets estáticos)
- ❌ Threading seguro (callbacks de thread direta)

---

## 🏗️ ARQUITETURA ATUAL (COM PROBLEMAS)

```
┌─────────────────────────────────────────────────────┐
│ ESP32 (MLX90614 + Wi-Fi)                            │
├─────────────────────────────────────────────────────┤
│ Serial (115200 baud)  │  HTTP API (Wi-Fi)           │
└──────────┬──────────────────────────┬───────────────┘
           │                          │
      ❌ PROBLEMA: API não está implementada
           │                          │
           ▼                          ▼
┌──────────────────────┐   ┌──────────────────────┐
│ SerialConnection     │   │ APIConnection        │
│ ✅ Funciona          │   │ ❌ Só envia dados    │
│ ⚠️ Sem retry         │   │ ❌ Sem polling       │
│ ⚠️ Sem reconexão     │   │ ❌ Sem handler       │
└──────────┬───────────┘   └──────────────────────┘
           │
           ▼ on_data callback (DE THREAD)
┌─────────────────────────────────────────┐
│ SensorManager.process_temperature()     │
│ ⚠️ Recebe de thread                     │
└──────────┬────────────────────────────┘
           │ callback (AINDA EM THREAD)
           ▼ ❌ PROBLEMA: Acesso direto a widgets
┌─────────────────────────────────────────────────────────┐
│ SensorPage.update_temperature()                         │
│ ❌ Modifica StringVar de thread                         │
│ ❌ Modifica gráfico de thread                           │
│ ❌ Sem sincronização                                    │
└──────────┬────────────────────────────────────────────┘
           │
           ▼
      UI CustomTkinter (inseguro!)
           │
           ▼
      Dashboard
           │
           ▼
      Banco de dados
```

---

## 🔧 PROBLEMAS ESPECÍFICOS ENCONTRADOS

### 1. **SensorManager.py** (Crítico)

#### Problema 1.1: Atributos não inicializados
```python
# ❌ Linha ~88 em disconnect()
try:
    if self.thread and self.thread.is_alive():  # ❌ self.thread não existe!
        self.thread.join(timeout=1)
except Exception:
    pass

try:
    if self.serial and self.serial.is_open:  # ❌ self.serial não existe!
        self.serial.close()
except Exception:
    pass
```

#### Problema 1.2: Método não existe
```python
# ❌ Linha ~81 em connect()
self.status("🔴 Falha conexão")  # ❌ self.status() não existe!
# Deveria ser:
# self.on_status("🔴 Falha conexão")
```

#### Problema 1.3: Modo API não implementado
```python
elif mode == "API":
    # ❌ Não faz nada!
    self.log(f"Modo {mode} ainda não implementado")
    return
```

---

### 2. **SensorPage.py** (Crítico)

#### Problema 2.1: UI não é dinâmica
- Painel de conexão sempre mostra todos os controles
- Não muda conforme o modo selecionado
- Serial, API, MQTT, Simulação aparecem juntos

#### Problema 2.2: Threading inseguro
```python
# ❌ Chamado de thread (serial_connection._read_loop)
def update_temperature(self, value):
    # Modifica StringVar de thread ❌
    self.sensor_temperature_var.set(f"{value:.1f} °C")
    
    # Modifica gráfico de thread ❌
    if self._chart:
        self._chart.update(self.temperature_history)
    
    # Modifica textbox de thread ❌
    self.add_log(f"🌡 Temperatura: {value:.2f} °C")
```

---

### 3. **APIConnection.py** (Não implementado)

- Só tem método `send_temperature()` (POST)
- Não faz **polling** contínuo
- Não está integrada no `SensorManager`
- Não trata reconexão
- Sem retry logic

---

### 4. **MQTT** (Não implementado)

Classe `MQTTConnection` vazia.

---

## ✅ ARQUITETURA PROPOSTA (CORRIGIDA)

```
┌──────────────────────────────────────────────────────────┐
│ ESP32 (MLX90614 + Wi-Fi)                                 │
├───────────────┬──────────────────┬─────────────────┐────┤
│ Serial (USB)  │ HTTP API (Wi-Fi)  │ MQTT (Wi-Fi)    │Sim │
└───────┬───────┴────────┬──────────┴─────────┬───────┴──┬─┘
        │                │                    │          │
        ▼                ▼                    ▼          ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐ ┌──────┐
│ SerialDriver │  │ APIDriver    │  │ MQTTDriver   │ │ SimD │
│ (thread)     │  │ (thread)     │  │ (thread)     │ │      │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘ └──┬───┘
       │                 │                 │            │
       └─────────────────┴─────────────────┴────────────┘
                         │
         ✅ Interface unificada (on_data callback)
                         │
                         ▼
         ┌──────────────────────────────────────┐
         │ SensorManager (thread-safe)          │
         │ - Queue para dados                   │
         │ - Processa de forma segura           │
         │ - Chama .after() na UI               │
         └──────────┬───────────────────────────┘
                    │
         ✅ .after() chamado da main thread
                    │
                    ▼
         ┌──────────────────────────────────────┐
         │ SensorPage.update_ui_from_queue()    │
         │ ✅ Executado na main thread          │
         │ ✅ Seguro para widgets               │
         └──────────┬───────────────────────────┘
                    │
                    ▼
            UI CustomTkinter ✅
                    │
                    ▼
               Dashboard ✅
                    │
                    ▼
            Banco de dados ✅
```

---

## 📊 PAINEL DINÂMICO PROPOSTO

### Estado: Modo = "Serial"
```
┌─────────────────────────────────────────┐
│ Central de Conexão                      │
│                                         │
│ Modo de conexão: [Serial ▼]            │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ ⚙️ Conexão Serial (VISIBLE)          │ │
│ │                                      │ │
│ │ Porta COM: [COM3 ▼]                 │ │
│ │ Baudrate: [115200 ▼]                │ │
│ │                                      │ │
│ │ [Conectar] [Desconectar]            │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Logs do Sensor (VISIBLE)             │ │
│ │ [Textbox...]                         │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Estado: Modo = "API"
```
┌─────────────────────────────────────────┐
│ Central de Conexão                      │
│                                         │
│ Modo de conexão: [API ▼]               │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ ⚙️ Conexão HTTP/Wi-Fi (VISIBLE)     │ │
│ │                                      │ │
│ │ IP ESP32: [192.168.200.xxx]         │ │
│ │ Porta: [8080]                        │ │
│ │ Endpoint: [/sensor/temperature]     │ │
│ │ Timeout: [5 segundos]                │ │
│ │                                      │ │
│ │ 🔍 Ping: -- ms  [Testar]            │ │
│ │ 📶 Sinal: -- %                       │ │
│ │                                      │ │
│ │ [Conectar] [Desconectar]            │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Logs do Sensor (VISIBLE)             │ │
│ │ [Textbox...]                         │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Estado: Modo = "MQTT"
```
┌─────────────────────────────────────────┐
│ Central de Conexão                      │
│                                         │
│ Modo de conexão: [MQTT ▼]              │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ ⚙️ Conexão MQTT (VISIBLE)           │ │
│ │                                      │ │
│ │ Broker: [mqtt.local]                │ │
│ │ Porta: [1883]                        │ │
│ │ Tópico: [sensors/pcm/temp]          │ │
│ │ Usuário: [usuario]                   │ │
│ │ Senha: [••••••]                      │ │
│ │                                      │ │
│ │ [Conectar] [Desconectar]            │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Logs do Sensor (VISIBLE)             │ │
│ │ [Textbox...]                         │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Estado: Modo = "Simulação"
```
┌─────────────────────────────────────────┐
│ Central de Conexão                      │
│                                         │
│ Modo de conexão: [Simulação ▼]         │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🧪 Simulação Térmica (VISIBLE)      │ │
│ │                                      │ │
│ │ Intervalo: [1.0 segundo]            │ │
│ │ Temperatura Máx: [82 °C]            │ │
│ │ Temperatura Min: [28 °C]            │ │
│ │ Trigger PCM: [45 °C]                │ │
│ │ Ruído: [✓] Habilitado               │ │
│ │                                      │ │
│ │ [Iniciar] [Parar]                   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Logs do Sensor (VISIBLE)             │ │
│ │ [Textbox...]                         │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 🔌 PROTOCOLO ESP32 PROPOSTO

### Serial (PySerial)
**Formato**: Uma temperatura por linha
```
28.5
28.6
28.7
29.0
...
```

### HTTP API

#### Endpoint: GET /sensor/temperature
```
GET http://192.168.200.227:8080/sensor/temperature
```

**Resposta**:
```json
{
  "temperatura": 28.5,
  "umidade": 45.0,
  "timestamp": 1715600000000,
  "status": "ok"
}
```

#### Endpoint: POST /experimento/dados (Dados do experimento)
```
POST http://192.168.200.227:8080/experimento/dados
Content-Type: application/json

{
  "id_experimento": 1,
  "temperatura_inicial": 28.0,
  "temperatura_final": 45.5,
  "duracao_segundos": 120,
  "timestamp": 1715600000000
}
```

### MQTT

**Tópicos**:
- `sensors/pcm/temperature` → Temperatura em tempo real
- `sensors/pcm/status` → Status do sensor
- `sensors/pcm/heartbeat` → Keep-alive (a cada 30s)

**Payload**:
```json
{
  "temperatura": 28.5,
  "timestamp": 1715600000000,
  "dispositivo": "ESP32-MLX90614"
}
```

---

## 🚀 CÓDIGO ESP32 MELHORADO

```cpp
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <PubSubClient.h>

// ==========================================
// CONFIGURAÇÕES
// ==========================================

LiquidCrystal_I2C lcd(0x27, 20, 4);
Adafruit_MLX90614 mlx = Adafruit_MLX90614();
WiFiClient espClient;
PubSubClient mqtt_client(espClient);

const char* SSID = "Joao";
const char* PASSWORD = "stefany1511";
const char* API_SERVER = "192.168.200.227";
const int API_PORT = 8000;
const char* MQTT_BROKER = "192.168.200.200";
const int MQTT_PORT = 1883;

// ==========================================
// ESTADO
// ==========================================

unsigned long last_api_post = 0;
unsigned long last_mqtt_publish = 0;
unsigned long last_heartbeat = 0;
const unsigned long API_INTERVAL = 30000;     // 30 segundos
const unsigned long MQTT_INTERVAL = 5000;     // 5 segundos
const unsigned long HEARTBEAT_INTERVAL = 30000; // 30 segundos

int connection_attempts = 0;
const int MAX_RECONNECT_ATTEMPTS = 5;

// ==========================================
// SETUP
// ==========================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Inicializar sensor
  if (!mlx.begin()) {
    Serial.println("MLX90614 não encontrado!");
    while (1);
  }
  
  // Inicializar LCD
  lcd.init();
  lcd.backlight();
  lcd.print("Iniciando...");
  
  // Conectar Wi-Fi
  wifi_connect();
  
  // Conectar MQTT
  mqtt_client.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt_client.setCallback(mqtt_callback);
  mqtt_connect();
  
  Serial.println("Sistema pronto!");
  lcd.clear();
  lcd.print("PCM Ready");
}

// ==========================================
// CONECTAR Wi-Fi
// ==========================================

void wifi_connect() {
  Serial.println("\n[WiFi] Conectando...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\n[WiFi] Conectado! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Falha ao conectar!");
  }
}

// ==========================================
// CONECTAR MQTT
// ==========================================

void mqtt_connect() {
  Serial.println("[MQTT] Conectando...");
  
  int attempts = 0;
  while (!mqtt_client.connected() && attempts < MAX_RECONNECT_ATTEMPTS) {
    if (mqtt_client.connect("ESP32-PCM")) {
      Serial.println("[MQTT] Conectado!");
      mqtt_client.subscribe("sensors/pcm/config");
    } else {
      Serial.print("[MQTT] Falha (");
      Serial.print(mqtt_client.state());
      Serial.println("), tentando novamente...");
      delay(2000);
      attempts++;
    }
  }
}

// ==========================================
// CALLBACK MQTT
// ==========================================

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("[MQTT] Mensagem recebida em ");
  Serial.println(topic);
}

// ==========================================
// PUBLICAR VIA MQTT
// ==========================================

void mqtt_publish_temperature(float temp) {
  if (!mqtt_client.connected()) {
    mqtt_connect();
  }
  
  if (mqtt_client.connected()) {
    char payload[100];
    snprintf(payload, sizeof(payload), 
             "{\"temperatura\":%.2f,\"timestamp\":%lu}",
             temp, millis());
    
    mqtt_client.publish("sensors/pcm/temperature", payload);
    Serial.print("[MQTT] Publicado: ");
    Serial.println(payload);
  }
}

// ==========================================
// ENVIAR DADOS VIA API
// ==========================================

void api_post_experiment(float temp_inicial, float temp_final) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[API] Wi-Fi desconectado!");
    return;
  }
  
  HTTPClient http;
  http.setTimeout(5000);
  
  char url[150];
  snprintf(url, sizeof(url), 
           "http://%s:%d/experimento/dados",
           API_SERVER, API_PORT);
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  char payload[250];
  snprintf(payload, sizeof(payload),
           "{\"id_experimento\":1,\"temperatura_inicial\":%.2f,\"temperatura_final\":%.2f,\"duracao_segundos\":120,\"timestamp\":%lu}",
           temp_inicial, temp_final, millis());
  
  Serial.print("[API] POST para ");
  Serial.println(url);
  Serial.print("[API] Payload: ");
  Serial.println(payload);
  
  int httpResponseCode = http.POST(payload);
  Serial.print("[API] Response: ");
  Serial.println(httpResponseCode);
  
  http.end();
}

// ==========================================
// ENVIAR TEMPERATURA (Serial)
// ==========================================

void serial_send_temperature(float temp) {
  Serial.print("[SERIAL] ");
  Serial.println(temp);
}

// ==========================================
// LOOP PRINCIPAL
// ==========================================

void loop() {
  unsigned long now = millis();
  
  // Ler temperatura
  float temp_obj = mlx.readObjectTempC();
  float temp_amb = mlx.readAmbientTempC();
  
  // Atualizar LCD
  lcd.setCursor(0, 0);
  lcd.print("Obj:");
  lcd.print(temp_obj);
  lcd.print("C");
  
  lcd.setCursor(0, 1);
  lcd.print("Amb:");
  lcd.print(temp_amb);
  lcd.print("C");
  
  // Enviar Serial (contínuo)
  serial_send_temperature(temp_obj);
  
  // Publicar MQTT (a cada 5 segundos)
  if (now - last_mqtt_publish >= MQTT_INTERVAL) {
    mqtt_publish_temperature(temp_obj);
    last_mqtt_publish = now;
  }
  
  // Enviar API (a cada 30 segundos)
  if (now - last_api_post >= API_INTERVAL) {
    api_post_experiment(temp_amb, temp_obj);
    last_api_post = now;
  }
  
  // Heartbeat MQTT (a cada 30 segundos)
  if (now - last_heartbeat >= HEARTBEAT_INTERVAL) {
    mqtt_client.publish("sensors/pcm/heartbeat", "{\"status\":\"alive\"}");
    last_heartbeat = now;
  }
  
  // Reconectar MQTT se desconectado
  if (!mqtt_client.connected()) {
    mqtt_connect();
  }
  mqtt_client.loop();
  
  delay(1000);
}
```

---

## 🛠️ CHECKLIST DE INTEGRAÇÃO

### ✅ Fase 1: Correções Críticas
- [ ] Corrigir `SensorManager.__init__` (adicionar atributos)
- [ ] Corrigir `SensorManager.connect()` (chamar método correto)
- [ ] Corrigir `SensorManager.disconnect()` (verificar existência)
- [ ] Melhorar tratamento de threading

### ✅ Fase 2: Drivers de Sensor
- [ ] Criar `BaseSensorDriver` (interface abstrata)
- [ ] Melhorar `SerialSensorDriver` (com retry)
- [ ] Criar `APISensorDriver` (polling contínuo)
- [ ] Criar `MQTTSensorDriver` (inscrições)
- [ ] Melhorar `SimulationDriver`

### ✅ Fase 3: Thread Safety
- [ ] Usar `queue.Queue` para dados
- [ ] Usar `.after()` para atualizar UI
- [ ] Remover callbacks diretos de thread
- [ ] Sincronizar acessos ao banco

### ✅ Fase 4: UI Dinâmica
- [ ] Fazer painel de configuração dinâmico
- [ ] Mostrar/esconder widgets por modo
- [ ] Adicionar controles para cada modo
- [ ] Validar entradas

### ✅ Fase 5: Documentação
- [ ] Este arquivo (SENSOR_INTEGRATION_GUIDE.md) ✅
- [ ] Docstrings em todas as classes
- [ ] Exemplos de uso
- [ ] Troubleshooting

---

## 🐛 TROUBLESHOOTING

### Problema: "AttributeError: 'SensorManager' object has no attribute 'thread'"
**Causa**: `__init__` não inicializa `self.thread`
**Solução**: Ver correção em Fase 1

### Problema: "Widget inválido" ou "Tkinter error"
**Causa**: Atualizar widgets de thread diferente da main
**Solução**: Usar `.after()` para atualizar de main thread

### Problema: "WiFi desconectado, conexão API falhando"
**Causa**: ESP32 sem reconexão automática
**Solução**: Implementar retry logic no `APISensorDriver`

### Problema: "Serial desconecta aleatoriamente"
**Causa**: Sem tratamento de exceção em `_read_loop`
**Solução**: Adicionar reconexão automática em `SerialSensorDriver`

### Problema: "Temperatura não atualiza no dashboard"
**Causa**: Callback perde contexto da view
**Solução**: Usar queue e polling em vez de callbacks diretos

---

## 📚 REFERÊNCIAS

- [CustomTkinter Threading](https://github.com/TomSchimansky/CustomTkinter)
- [PySerial Documentation](https://pyserial.readthedocs.io/)
- [Requests HTTP Client](https://docs.python-requests.org/)
- [PubSubClient MQTT](https://pubsubclient.knolleary.net/)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/en/docs/advanced/websockets/)

---

## 👤 AUTOR & HISTÓRICO

- **Criado**: 13/05/2026
- **Status**: Auditoria Completa
- **Versão**: 1.0.0

---

**Próximo passo**: Execute o checklist de integração fase por fase.
