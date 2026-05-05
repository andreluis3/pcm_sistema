# 🏗️ ARQUITETURA E FLUXO DE MIGRAÇÃO

## Situação ATUAL (SQLite)

```
┌─────────────────────────────────────┐
│        Interface do Sistema          │
│  (experiment_tab.py, dashboard, etc) │
└────────────────┬────────────────────┘
                 │
                 │ DatabaseManager
                 ↓
┌─────────────────────────────────────┐
│      SQLite (pcmdata.db)             │
│  - experiments                        │
│  - thermal_calculations              │
│  - tabela_calculos                   │
│  - users                              │
└─────────────────────────────────────┘
```

**Problema:** Tudo localmente, sem escalabilidade, sem multi-usuário


## Situação DESEJADA (MySQL via API)

```
┌─────────────────────────────────────┐
│        Interface do Sistema          │
│  (experiment_tab.py, dashboard, etc) │
└────────────────┬────────────────────┘
                 │
                 │ ThermaCoreMySQLClient
                 │ (HTTP requests)
                 ↓
    ┌────────────────────────┐
    │   FastAPI (main_api)   │
    │   localhost:8000       │
    │                        │
    │  - POST /experimentos  │
    │  - GET /experimentos   │
    │  - PUT /experimentos   │
    │  - DELETE /experimentos│
    │  - GET /metricas       │
    │  - etc...              │
    └────────────────────────┘
                 │
                 │ mysql.connector
                 ↓
    ┌────────────────────────┐
    │   MySQL (ThermaCore)   │
    │   localhost:3306       │
    │                        │
    │  - experiments         │
    │  - calculos_termicos   │
    │  - users               │
    └────────────────────────┘
```

**Benefício:** Escalável, multi-usuário, seguro


## FASE DE TRANSIÇÃO (SQLite + MySQL)

```
┌─────────────────────────────────────────────────────────────┐
│              Interface do Sistema                            │
│  (gradualmente usando ThermaCoreMySQLClient)                │
└─────────────────┬─────────────────────────────────────────┘
                  │
      ┌───────────┴────────────┐
      │                        │
      │ (SELECT)       (SELECT)│
      ↓                        ↓
  ┌────────────┐         ┌──────────────┐
  │  SQLite    │         │  API+MySQL   │
  │(Backup)    │         │(Principal)   │
  └────────────┘         └──────────────┘

Estratégia:
- API está rodando (MySQL)
- Interface testando com API
- SQLite ainda disponível como fallback
- Quando tiver confiança: remova SQLite
```


## DIAGRAMA DE ENDPOINTS

```
API ROOT: http://localhost:8000/api

EXPERIMENTOS:
├── POST   /experimentos             → Criar novo
├── GET    /experimentos             → Listar todos
├── GET    /experimentos/{id}        → Obter um
├── PUT    /experimentos/{id}        → Atualizar
├── DELETE /experimentos/{id}        → Deletar
├── GET    /experimentos/{id}/metricas       → Dashboard
├── GET    /experimentos/buscar/por-material → Buscar
├── GET    /experimentos/buscar/por-data     → Buscar
└── GET    /experimentos/buscar/texto-livre  → Busca flexível

CÁLCULOS TÉRMICOS:
├── POST   /calculos-termicos        → Criar
├── GET    /calculos-termicos        → Listar
├── GET    /calculos-termicos/{id}   → Obter um
├── PUT    /calculos-termicos/{id}   → Atualizar
└── GET    /calculos-termicos/experimento/{exp_id} → Por experimento

SAÚDE:
└── GET    /health                   → Status da API
```


## MAPEAMENTO DE MÉTODOS DatabaseManager → API

```
SQLite Method                          → API Endpoint

insert_experiment(data)                → POST /api/experimentos
update_experiment(id, data)            → PUT /api/experimentos/{id}
delete_experiment(id)                  → DELETE /api/experimentos/{id}
get_experiment_by_id(id)               → GET /api/experimentos/{id}
list_experiments(limit)                → GET /api/experimentos?limit=N
search_experiments(material, date)     → GET /api/experimentos/buscar/*
search_experiments_flexible(query)     → GET /api/experimentos/buscar/texto-livre?q=X

get_temperatura_media(id)              → GET /api/experimentos/{id}/metricas
get_delta_t(id)                        → GET /api/experimentos/{id}/metricas
get_heating_rate(id)                   → GET /api/experimentos/{id}/metricas
get_energia_armazenada(id)             → GET /api/experimentos/{id}/metricas

insert_thermal_calculation(data)       → POST /api/calculos-termicos
list_thermal_calculations(limit)       → GET /api/calculos-termicos
```


## TIMELINE DE MIGRAÇÃO RECOMENDADA

```
SEMANA 1 - Preparação
├─ ✅ Criação de API (PRONTO)
├─ ✅ Documentação (PRONTO)
├─ ⏳ Criar banco MySQL (PRONTO)
├─ ⏳ Criar tabelas     (PRONTO)
└─ ⏳ Testar endpoints 

SEMANA 2 - Integração
├─ ⏳ Criar ThermaCoreMySQLClient
├─ ⏳ Testar com interface
├─ ⏳ Validar dados
└─ ⏳ Testes de carga

SEMANA 3 - Migração
├─ ⏳ Migrar experiment_tab.py
├─ ⏳ Migrar dashboard_tab.py
├─ ⏳ Migrar database_tab.py
└─ ⏳ Migrar thermal_calculations_page.py

SEMANA 4 - Finalização
├─ ⏳ Testes completos
├─ ⏳ Validação de backups
├─ ⏳ Remover SQLite
└─ ⏳ Deploy
```


## ESTRUTURA DO PROJETO APÓS MIGRAÇÃO

```
pcm_sistema/
├── backend/
│   ├── main_api_completo.py    ← API principal (NOVO)
│   ├── main_api.py             ← Versão anterior (REMOVER)
│   └── Untitled-1.py
│
├── interface/
│   ├── experiment_tab.py        ← Usa ThermaCoreMySQLClient
│   ├── dashboard_tab.py         ← Usa ThermaCoreMySQLClient
│   ├── database_tab.py          ← Usa ThermaCoreMySQLClient
│   └── view/
│       └── thermal_calculations_page.py ← Usa ThermaCoreMySQLClient
│
├── services/
│   ├── api_client.py            ← NOVO: Interface para API
│   ├── auth_service.py
│   ├── calculation_service.py
│   └── controller_calculos.py
│
├── database/                    ← REMOVER (SQLite)
│   ├── database_manager.py      (SQL oqui não será mais usado)
│   └── db_manager.py
│
├── GUIA_API.md                  ← NOVO
├── MAPEAMENTO_MIGRACAO.md       ← NOVO
└── OBSERVACOES_IMPORTANTES.md   ← NOVO
```


## COMPARAÇÃO: DatabaseManager vs ThermaCoreMySQLClient

| Aspecto | DatabaseManager | ThermaCoreMySQLClient |
|---------|-----------------|----------------------|
| Tipo | Local DB | API Client |
| Localização | Arquivo SQLite | Servidor MySQL |
| Velocidade | Muito rápido | Rápido (~100ms) |
| Multi-usuário | Não | Sim |
| Escalabilidade | Limitada | Excelente |
| Sincronização | Automática | Via HTTP |
| Backup | Arquivo | Banco centralizado |
| Segurança | Nenhuma | JWT/Auth (future) |


## FLUXO DE REQUISIÇÃO COM API

```
1. Interface chama:
   client.criar_experimento(data)
   
2. ThermaCoreMySQLClient faz:
   POST http://localhost:8000/api/experimentos
   { "material": "...", "operador": "...", ... }
   
3. FastAPI (main_api) recebe:
   Valida com Pydantic
   Chama mysql.connector
   
4. MySQL executa:
   INSERT INTO experiments (...)
   
5. Response volta:
   {"status": "ok", "id": 123, ...}
   
6. Interface recebe e continua normalmente
```


## GARANTIAS DE SEGURANÇA NA MIGRAÇÃO

```
✅ Backup automático
   - SQLite fica intacto durante transição
   - Pode fazer rollback a qualquer momento

✅ Validação de dados
   - Pydantic valida entrada
   - Tipos verificados antes de INSERT

✅ Tratamento de erros
   - HTTPException com status codes
   - Mensagens claras de erro

✅ Transações
   - FOREIGN KEYS ativadas
   - ON DELETE CASCADE configurado

✅ Testes
   - Endpoint /health para monitoramento
   - Documentação automática em /docs
```


## PRÓXIMAS FEATURES (Depois da migração)

```
┌─────────────────────────────────────┐
│        Versão Atual (v1.0)          │
│  - CRUD básico de experimentos      │
│  - Cálculos térmicos                │
│  - Dashboard simples                │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│      Versão Futura (v2.0)           │
│  - Autenticação (JWT)               │
│  - Permissões por usuário           │
│  - Histórico de alterações          │
│  - Cache com Redis                  │
│  - Notificações em tempo real       │
│  - WebSocket para dados em tempo real│
│  - Relatórios avançados             │
└─────────────────────────────────────┘
```


---

**Visualização pronta! Agora é só executar o plano.**
