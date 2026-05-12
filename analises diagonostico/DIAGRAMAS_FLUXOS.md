# FLUXOS PROBLEMÁTICOS - Diagramas Visuais

## 1. 🔴 PROBLEMA: Connection Pool MySQL

### Fluxo CRÍTICO (Atual)

```
User 1: HTTP POST /criar_experimento
        ↓
    get_connection() → mysql.connector.connect()  [Conexão #1]
        ↓
    INSERT query
        ↓
    conn.close()  [Liberada]

User 2: HTTP POST /criar_experimento
        ↓
    get_connection() → mysql.connector.connect()  [Conexão #2]
        ↓
    INSERT query
        ↓
    conn.close()  [Liberada]

... (repetir 100x) ...

User 100: ⚠️ ERROR: "Too many connections (Max: 100)"
          MySQL quebrará após ~150-200 requisições simultâneas
```

### Fluxo CORRETO (Proposto)

```
       FastAPI App
           ↓
    ┌──────────────┐
    │  Connection  │ Pool de 5 conexões REUTILIZÁVEIS
    │     Pool     │ + 10 conexões extras sob demanda
    └──────────────┘
      ↙      ↓      ↘
   Conn1  Conn2  Conn3

User 1: INSERT → usa Conn1 → retorna ao pool
User 2: INSERT → usa Conn2 → retorna ao pool
User 3: INSERT → REUTILIZA Conn1 (após User 1)
                   ✅ Sem criar conexão nova!

RESULTADO: Max 15 conexões simultâneas, não 100!
```

---

## 2. 🔴 PROBLEMA: Callbacks de Thread para UI (Deadlock)

### Fluxo PERIGOSO (Atual)

```
┌─────────────────────────┐
│   THREAD DAEMON (Serial)│
│                         │
│  while running:         │
│    data = serial.read() │  ← Lê em loop, chamada BLOQUEANTE
│    if on_data:          │
│      on_data(temp)      │  ← PROBLEMA: Callback direto!
│        ↓                │
│   SensorManager.        │
│   process_temp()        │
│        ↓                │
│   on_temperature(v)     │
│        ↓                │
└────────────────────────┼────────────────┐
                         │                │
                    MAIN THREAD (Tkinter)
                         │
                    Update Status:
                    self.status_label.
                    configure(text=...)
                         │
                    ⚠️ RACE CONDITION!
                    Thread writes to widget
                    while Main thread reads
```

**Resultado possível:**
```
1. Segmentation fault (crash)
2. Tkinter deadlock (freeze)
3. Data corruption (valores errados)
4. Intermittent errors (difícil debugar)
```

---

### Fluxo SEGURO (Proposto)

```
┌──────────────────────────┐
│   THREAD DAEMON (Serial) │
│                          │
│  while running:          │
│    data = serial.read()  │
│    if on_data:           │
│      queue.put(data)     │  ← Coloca em QUEUE
│                          │  ← Thread-safe!
└──────────┬───────────────┘
           │
           │ (async, não-bloqueante)
           ↓
┌─────────────────────────────────────┐
│   MAIN THREAD (Timer-based)         │
│                                     │
│  def _process_queue():              │
│    while not queue.empty():         │
│      data = queue.get()             │
│      self.update_status(data) ← Aqui, thread-safe!
│                                     │
│    self.after(50, _process_queue)   │
└─────────────────────────────────────┘

RESULTADO:
✅ Sem deadlock
✅ Sem race conditions
✅ UI sempre responsivo
```

---

## 3. 🟡 PROBLEMA: Memory Leak de Matplotlib Figures

### Acúmulo de Figuras (Atual)

```
User abre Dashboard
    ↓
BaseChart criada
    → Figure objeto criado
    → FigureCanvasTkAgg criado
    → Widget adicionado a tela
    ↓
Memory Usage: +5MB

User navega para outra página
    ↓
DashboardTab.destroy() é chamado
    ↓
Widget é destruído
    ↓
❌ PROBLEMA:
   - Figure não é liberada
   - FigureCanvasTkAgg não é destruído
   - Matplotlib manager mantém referência
    ↓
Memory Usage: AINDA +5MB (vazada!)

User abre Dashboard novamente
    ↓
Nova Figure + Canvas criada
    ↓
Memory Usage: +10MB (2 figuras vazadas!)

... repetir 10x ...

Memory Usage final: +50MB de vazamento!
```

### Com Limpeza (Proposto)

```
User abre Dashboard
    ↓
BaseChart criada com cleanup registrado
    ↓
Memory: +5MB

User navega
    ↓
DashboardTab.destroy() chamado
    ↓
BaseChart.__del__() executado:
    - canvas.get_tk_widget().destroy()
    - plt.close(figure)
    ↓
Memory: -5MB (LIBERADA!)

User abre Dashboard novamente
    ↓
Memory: +5MB (sem vazamento!)

RESULTADO:
✅ Memory estável
✅ Sem acúmulo de figuras
✅ Limpeza automática
```

---

## 4. 🟡 PROBLEMA: Timers Orfãos (after sem cancel)

### Timeline de Timers (Atual)

```
T=0s:    DashboardTab.__init__()
         self._animate_id = self.after(120, self._animate_pcm)

T=0.12s: self._animate_pcm() chamado
         ├─ Faz animação
         └─ self._animate_id = self.after(120, self._animate_pcm)

T=0.24s: Timer executado novamente...

T=10s:   User clica "Exportar" → vai para página "export"
         ↓
         DashboardTab.destroy() chamado
         ↓
         ❌ PROBLEMA: _animate_id NÃO foi cancelado!
         Timer ainda está agendado!

T=10.12s: Timer tenta executar:
         self._animate_pcm()
         ├─ Tenta acessar self.winfo_exists()
         ├─ Widget não existe mais
         └─ ⚠️ Exceção, mas timer continua agendado

T=10.24s, 10.36s, 10.48s... : Mais timers "orfãos" agendados
                               Acumulam na fila de eventos

RESULTADO:
❌ Memória vazada (callbacks mantêm referências)
❌ CPU sobe (processando timers orfãos)
❌ Events acumulam na fila
```

### Com Cleanup (Proposto)

```
T=0s:    DashboardTab.__init__()
         self._animate_id = self.after(120, self._animate_pcm)

T=10s:   User navega para outra página
         ↓
         DashboardTab.destroy() chamado
         ↓
         try:
           self.after_cancel(self._animate_id)  ← CANCELA!
           self._animate_id = None
         except:
           pass
         
         super().destroy()

RESULTADO:
✅ Timer cancelado
✅ Memória liberada
✅ Sem callbacks orfãos
```

---

## 5. 🟡 PROBLEMA: Threads sem join()

### Daemon Threads (Problemático)

```
App startup
    ↓
SerialConnection.connect():
    thread = Thread(target=_read_loop, daemon=True)  ← DAEMON!
    thread.start()
    ↓
App rodando... dados sendo lidos...
    ↓
User fecha app
    ↓
MainUI.destroy() chamado
    ↓
Thread daemon é ABRUPTAMENTE TERMINADA
    ↓
❌ PROBLEMA:
   - _read_loop() não pode fazer cleanup
   - Buffer pode estar em estado inconsistente
   - Arquivo serial pode estar locked
   - Dados perdidos no final

RESULTADO:
- Próxima execução: arquivo serial locked
- Memória de thread não foi liberada
- Dados de último segundo perdidos
```

### Non-Daemon Threads com Join (Correto)

```
App startup
    ↓
SerialConnection.connect():
    thread = Thread(target=_read_loop, daemon=False)  ← Não daemon
    thread.start()
    ↓
App rodando...
    ↓
User fecha app
    ↓
MainUI.destroy() chamado
    ↓
SerialConnection.disconnect() chamado:
    running = False  ← Sinal para thread parar
    thread.join(timeout=2)  ← Espera até 2 segundos
    ↓
    _read_loop() vê running=False
    ├─ Executa cleanup:
    ├─ Flush final do buffer
    ├─ Close serial port
    └─ Return (thread encerra)
    ↓
    join() retorna
    ↓

RESULTADO:
✅ Cleanup gracioso
✅ Dados preservados
✅ Recurso liberado corretamente
✅ Próxima execução sem problemas
```

---

## 6. Visão Geral: Interdependências de Problemas

```
                    ┌─────────────────┐
                    │  Too Many Users │
                    │   (100+)        │
                    └────────┬────────┘
                             │
                    ┌────────▼─────────┐
                    │ Connection Pool   │  ← Problema #1
                    │ NÃO EXISTE       │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ↓              ↓              ↓
      ┌──────────────┐ ┌──────────┐ ┌────────────┐
      │ MySQL Error: │ │ UI Freeze│ │ Memory     │
      │ Too many     │ │ (Race    │ │ Leak       │
      │ connections  │ │ conditions)│ (Timers)   │
      │              │ │          │ │            │
      │ ❌ CRASH     │ │ ❌ HANG  │ │ ❌ SLOW    │
      └──────────────┘ └──────────┘ └────────────┘
```

---

## 7. Priorização de Problemas

```
Impacto vs Dificuldade

ALTO IMPACTO + FÁCIL → FAZER PRIMEIRO
├─ [#1] Connection Pool MySQL       (4 horas)
├─ [#2] Thread Queue Refactor       (6 horas)
├─ [#3] Timer Cleanup              (2 horas)
└─ [#4] Matplotlib __del__()       (1 hora)

ALTO IMPACTO + MÉDIO → FAZER DEPOIS
├─ [#5] SQLite Context Managers    (3 horas)
└─ [#6] Cleanup binds Lambda       (2 horas)

MÉDIO IMPACTO + FÁCIL → NICE-TO-HAVE
├─ [#7] Rate Limiting              (1 hora)
├─ [#8] Caching com TTL            (3 horas)
└─ [#9] Retry Logic                (2 horas)

TOTAL: ~24 horas de trabalho
       = ~3 dias de desenvolvimento
```

---

## 8. Matriz de Dependências

```
Qual problema deve ser resolvido PRIMEIRO?

Connection Pool MySQL
└─ ✅ Independente, comece AQUI
   Impacto: Alto (resolve >100 usuários)

Thread Queue Refactor
├─ Depende: SensorManager refactor
├─ Impacto: Crítico (resolve deadlocks)
└─ ✅ Independente, pode ser paralelo

Timer Cleanup
├─ Depende: Nada
├─ Impacto: Médio-Alto
└─ ✅ Independente

Matplotlib Cleanup
├─ Depende: Nada
├─ Impacto: Médio
└─ ✅ Independente

SQLite Context Manager
├─ Depende: Nada
├─ Impacto: Médio
└─ ✅ Independente

RECOMENDAÇÃO:
1. Dia 1: Connection Pool (paralelo com Thread Queue)
2. Dia 2: Thread Queue (paralelo com Timers)
3. Dia 3: Timers + Matplotlib + SQLite
4. Dia 4-5: Testes de stress
```

---

## Conclusão

| Métrica | Valor | Status |
|---------|-------|--------|
| **Problemas encontrados** | 18 | 🔴 Crítico |
| **Severidade média** | ALTA | ⚠️ Ação necessária |
| **Tempo estimado de fix** | 24h | 📅 Viável |
| **Risco em produção** | MUITO ALTO | 🚫 Não recomendado |
| **Após correções** | Production-ready | ✅ Recomendado |

**Recomendação Final:**
```
NÃO coloque em produção antes de resolver:
- Connection Pool MySQL [#1]
- Thread Safety [#2]
- Timer Cleanup [#3]

DEPOIS desses 3, o projeto fica 90% estável.
```
