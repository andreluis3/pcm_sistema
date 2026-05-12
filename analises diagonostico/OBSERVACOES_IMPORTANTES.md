# ✅ CHECKLIST E PRÓXIMOS PASSOS

## 📦 O QUE FOI CRIADO

### Arquivos Criados:

1. **`backend/main_api_completo.py`** ✅
   - API FastAPI completa com 15+ endpoints
   - Pronta para usar, apenas execute
   - Inclui documentação automática em `/docs`

2. **`GUIA_API.md`** ✅
   - Como executar a API
   - Exemplos de todos os endpoints
   - Exemplos de uso em Python
   - Checklist de configuração

3. **`MAPEAMENTO_MIGRACAO.md`** ✅
   - Mapeamento de cada função SQLite → Endpoint API
   - Prioridades de migração
   - Classe intermediária `ThermaCoreMySQLClient` para transição segura

4. **`OBSERVACOES_IMPORTANTES.md`** (este arquivo) ✅


## 🚀 PRÓXIMOS PASSOS (POR ORDEM)

### PASSO 1: Preparar MySQL ✅ (Você já fez?)
```sql
-- Execute no MySQL:
CREATE DATABASE thermacore;
USE thermacore;

-- Crie estas tabelas:
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE experiments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    material VARCHAR(100),
    operador VARCHAR(100),
    capsula VARCHAR(100),
    massa FLOAT,
    calor_especifico FLOAT DEFAULT 2.0,
    tempo_inicio VARCHAR(50),
    tempo_final VARCHAR(50),
    delta_tempo FLOAT,
    temperatura_inicial FLOAT,
    temperatura_final FLOAT,
    delta_temperatura FLOAT,
    FOREIGN KEY (id_usuario) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE calculos_termicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_experimento INT,
    temperatura_inicial FLOAT,
    temperatura_final FLOAT,
    delta_temperatura FLOAT,
    calor_latente FLOAT,
    calor_sensivel FLOAT,
    energia_armazenada FLOAT,
    densidade_energetica FLOAT,
    eficiencia FLOAT,
    calculation_type VARCHAR(100),
    data_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_experimento) REFERENCES experiments(id) ON DELETE CASCADE
);

-- Dados iniciais para teste:
INSERT INTO users (username, password_hash) VALUES ('Camila', 'senha123');
INSERT INTO experiments (id_usuario, material, operador) 
VALUES (1, 'Cera de coco', 'Camila');
```

### PASSO 2: Testar a API 🧪
```bash
# 1. Certifique-se que MySQL está rodando
# 2. Navegue até pasta backend:
cd backend

# 3. Execute a API:
python -m uvicorn main_api_completo:app --reload

# 4. Abra no navegador:
# http://localhost:8000/docs

# 5. Teste alguns endpoints:
#    - POST /api/experimentos
#    - GET /api/experimentos
#    - GET /api/experimentos/1/metricas
```

### PASSO 3: Integrar na Interface 🎨

**Opção A: Transição Segura (Recomendado)**

Crie arquivo: `services/api_client.py`
(Copie a classe `ThermaCoreMySQLClient` do MAPEAMENTO_MIGRACAO.md)

Depois na interface, substitua:
```python
# ANTES:
from database.database_manager import DatabaseManager
self.db = DatabaseManager()

# DEPOIS:
from services.api_client import ThermaCoreMySQLClient
self.db = ThermaCoreMySQLClient()
```

**Opção B: Mantém ambos funcionando**
- SQLite continua em paralelo
- Ativa API apenas quando necessário
- Mais seguro para testes

### PASSO 4: Migre Arquivo por Arquivo 📋

**Ordem recomendada:**

1. **`interface/experiment_tab.py`** (Salvar experimentos)
   - Troque `self.db.insert_experiment()` por API
   - Troque `self.db.update_experiment()` por API

2. **`interface/dashboard_tab.py`** (Dashboard)
   - Substitua 5 chamadas por 1: `/metricas`
   - Mais eficiente!

3. **`interface/database_tab.py`** (Visualização)
   - Migre buscas e deletions

4. **`interface/view/thermal_calculations_page.py`** (Cálculos)
   - Cálculos térmicos via API

### PASSO 5: Validar e Remover SQLite 🗑️

Quando estiver 100% confiante:
1. Faça backup do banco SQLite
2. Remova importações do `DatabaseManager`
3. Remova pasta `database/` se não precisar mais
4. Teste tudo novamente


## ⚡ RESUMO RÁPIDO

**O que você tem AGORA:**
- ✅ API pronta para usar (`main_api_completo.py`)
- ✅ 15+ endpoints funcionais
- ✅ Documentação completa
- ✅ Exemplos de código

**O que você precisa fazer:**
1. Criar tabelas no MySQL
2. Executar `uvicorn main_api_completo:app --reload`
3. Testar em `http://localhost:8000/docs`
4. Integrar classe `ThermaCoreMySQLClient` na interface
5. Migrar arquivo por arquivo

**Tempo estimado:**
- MySQL setup: 10 min
- Testar API: 5 min
- Integrar interface: 30-60 min (depende de quantos arquivos)
- Total: ~1-2 horas


## ⚠️ CUIDADOS

### ❌ NÃO FAÇA:
- Não delete SQLite enquanto está testando
- Não execute ambos (SQLite + MySQL) simultaneamente no mesmo experimento
- Não esqueça de instalar: `pip install fastapi uvicorn mysql-connector-python`

### ✅ FAÇA:
- Mantenha backups do banco SQLite
- Teste cada endpoint em `/docs` antes de integrar
- Use a classe `ThermaCoreMySQLClient` para transição segura
- Valide os dados em MySQL após cada migração

## 🐛 TROUBLESHOOTING

### Erro: "Connection refused"
- MySQL não está rodando
- Solução: `sudo service mysql start` (Linux/Mac) ou iniciar MySQL Workbench

### Erro: "Access denied for user 'root'"
- Senha incorreta em `get_connection()`
- Solução: Verifique senha no `main_api_completo.py` linha 17

### Erro: "Table doesn't exist"
- Tabelas não foram criadas
- Solução: Execute o SQL do PASSO 1

### API retorna 404 em alguns endpoints
- Pode ser URL incorreta
- Solução: Use documentação em `http://localhost:8000/docs`

### Dados não aparecem na interface
- API está offline
- SQLite e MySQL desincronizados
- Solução: Confirme que `uvicorn` está rodando e que você está usando `ThermaCoreMySQLClient`


## 📞 DÚVIDAS FREQUENTES

**P: Preciso criar um endpoint novo?**
R: Sim, para `tabela_calculos`. Abra o `main_api_completo.py` e adicione endpoints similares aos de `calculos_termicos`.

**P: Posso usar SQLite e MySQL juntos?**
R: Não recomendo para mesmos dados. Use `ThermaCoreMySQLClient` para chamar apenas a API.

**P: Como faço rollback se algo der errado?**
R: Mantenha backup do SQLite, deixe API desligada, volta a usar DatabaseManager.

**P: Preciso mudar credenciais do MySQL?**
R: Sim, edite linha 17 do `main_api_completo.py`: `get_connection()`

**P: Consigo rodar API em outra porta?**
R: Sim, `uvicorn main_api_completo:app --port 9000`


## ✨ BENEFÍCIOS DA MIGRAÇÃO

- ✅ Escalabilidade: MySQL aguenta bem mais dados
- ✅ Multi-usuário: Vários usuários acessando simultaneamente
- ✅ Segurança: Acesso controlado via API
- ✅ Análise: Banco estruturado facilita relatórios
- ✅ Backup: Backups centralizados do MySQL
- ✅ Integração: Fácil conectar outras aplicações


---

**Você está pronto para começar! Qual passo quer fazer primeiro?**
