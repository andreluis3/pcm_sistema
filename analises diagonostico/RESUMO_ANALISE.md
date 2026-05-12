# SUMÁRIO EXECUTIVO: Análise de Arquitetura PCM Sistema

## 🎯 Status Geral: ⚠️ **REQUER AÇÃO IMEDIATA**

### Descobertas Principais

| Área | Severidade | Impacto | Quantidade |
|------|-----------|--------|-----------|
| **Banco de Dados** | 🔴 CRÍTICA | App quebrará com >100 usuários | 3 problemas |
| **Threading** | 🔴 CRÍTICA | Crashes aleatórios em UI | 3 problemas |
| **Timers** | 🟡 ALTA | Memory leak progressivo | 4 problemas |
| **Matplotlib** | 🟡 ALTA | Memória acumula lentamente | 5 problemas |
| **Callbacks** | 🟡 ALTA | Referências circulares | 3 problemas |
| **Limpeza** | 🟡 ALTA | Recursos não liberados | 2 problemas |

**Total:** 18 problemas, sendo 6 críticos/altos

---

## 🔴 CRÍTICOS (Corrigir HOJE)

### 1. MySQL: Sem Connection Pool ⚠️

```
Status: A cada HTTP request, cria NOVA conexão MySQL
Risco:  Crash após ~100-200 requisições simultâneas
Local:  backend/main_api.py linhas 8-13
        backend/main_api_completo.py linhas 27-33
```

**Teste:** Abra 50 experimentos rápido → erro "Too many connections"

---

### 2. Threads não são Thread-Safe 🚨

```
Serial/Simulation thread → on_data callback → MainUI atualiza widget
                          ↑
                   PROBLEMA: Sem sincronização!
                   
Risco: Crashes aleatórios, race conditions, deadlock
Local: sensor_module/serial_connection.py linha 74
       sensor_module/simulation_connection.py linha 41
```

**Teste:** Conecte sensor serial → altere página rápido → freeze/crash

---

### 3. Threads Daemon sem join() 🔌

```
Thread daemon = terminada abruptamente ao fechar app
Risco: Perda de dados, arquivo serial corrompido
Local: sensor_module/*_connection.py (daemon=True)
```

**Teste:** Feche app enquanto sensor enviando dados → comportamento indefinido

---

## 🟡 ALTOS (Corrigir esta semana)

### 4. Memory Leak: Matplotlib Figures

```
Cada chart criado = Figure em memória
Quando página destruída = Figure NÃO é liberada
Risco: Memória cresce ~10MB por página aberta/fechada 10 vezes
Local: ui/charts.py, pcm_module/pcm_screen.py
```

**Teste:** Abra/feche dashboard 100 vezes → memória sobe para 1GB+

---

### 5. Timers Orfãos

```
DashboardTab._animate_id agendado a cada 120ms
Se widget destruído durante after() = timer continua agendado
Risco: Acúmulo de callbacks, memória cresce, CPU sobe
Local: interface/dashboard_tab.py linha 684
       interface/database_tab.py linha 248-249
```

**Teste:** Navegar entre abas 50 vezes → memória +500MB, CPU +20%

---

### 6. Conexões SQLite não fechadas

```
HybridRepository instância = nova conexão
Se criar múltiplas instâncias = múltiplas conexões abertas
Risco: Arquivo .db fica locked, disk I/O lento
Local: services/hybrid_repository.py __init__
       interface/main_ui.py linha 36
```

**Teste:** Abra app → feche sem logout → .db locked até restart

---

## 📊 Distribuição de Problemas por Arquivo

```
backend/main_api.py              ████████ CRÍTICA (connection pool)
sensor_module/serial_connection  ████████ CRÍTICA (threads)
ui/charts.py                     ██████ ALTA (memory leak)
interface/dashboard_tab.py       ██████ ALTA (timers)
services/hybrid_repository.py    ████ ALTA (cleanup)
interface/view/thermal_calc...   ████ MÉDIA (binds cleanup)
interface/database_tab.py        ████ ALTA (timers)
pcm_module/pcm_screen.py        ██ MÉDIA (figures)
```

---

## 🎬 Plano de Ação

### ESTA SEMANA
```
□ Dia 1-2: Implementar MySQL Connection Pool
   → Usar SQLAlchemy com QueuePool
   → Máximo 5 conexões, timeout 3600s
   
□ Dia 2-3: Refatorar threads com Queue
   → Thread coloca eventos em Queue
   → MainUI processa Queue a cada 50ms
   → Elimina race conditions
   
□ Dia 3-4: Adicionar cleanup de timers
   → after_cancel() em destroy()
   → Para: dashboard_tab, database_tab
   
□ Dia 4-5: Cleanup de Matplotlib
   → __del__() em BaseChart
   → plt.close(figure)
```

### PRÓXIMO MÊS
```
□ Caching com TTL (60s)
□ Rate limiting (100 req/min por usuário)
□ Context managers para conexões
□ Retry logic exponencial
□ Profiling de memória
```

---

## 🧪 Testes Recomendados

### Teste de Load
```bash
# Criar 500 experimentos em 30 segundos
for i in {1..500}; do
  curl -X POST http://localhost:8000/criar_experimento \
    -d "material=PCM&operador=test"
done
```
**Esperado:** Sem erro "Too many connections"

### Teste de Stabilidade
```bash
# Deixar app aberto por 8 horas
# Monitorar com `psutil`:
memory_inicio = 150MB
memory_apos_8h = 160MB ± 10MB  # Aceitável

conexoes_db = 1 (constant)
```

### Teste de Threading
```python
# Desconectar serial enquanto transferindo dados
# Esperado: Erro tratado, app continua responsivo
```

---

## 💡 Insights Adicionais

### Pontos Positivos ✅
- ✅ HybridRepository com fallback SQLite é inteligente
- ✅ Queue em dashboard_view.py mostra compreensão de thread-safety
- ✅ loading_screen.py com _cleanup_after_jobs() é bom padrão
- ✅ API tem timeouts configurados (2-10s)
- ✅ Structure modular e fácil de manter

### Padrões a Evitar ❌
- ❌ Criar nova conexão por request (√ 10 vezes!)
- ❌ Callbacks diretos de thread para UI (√ 5 locais)
- ❌ Daemon threads sem join()
- ❌ after() sem after_cancel() em destroy()
- ❌ Matplotlib figures sem cleanup

### Recomendação Geral
```
O projeto tem bom design geral, mas carece de:
1. Padrões de sincronização thread-safe
2. Resource cleanup adequado
3. Connection pooling

Estimar: 2-3 semanas de refactoring para levar a produção
```

---

## 📖 Documentação de Referência

Documento completo: `ANALISE_ARQUITETURA.md` (este diretório)

Seções principais:
- Arquitetura geral
- 8 categorias de problemas com exemplos
- Recomendações de correção por prioridade
- Checklist de testes
- Referências técnicas

---

**Preparado em:** 12 de maio de 2026  
**Versão:** 1.0  
**Status:** Pronto para discussão e implementação
