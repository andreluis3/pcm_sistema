# 📋 Guia de Uso - API ThermaCore

## 🚀 Como Executar a API

```bash
# Navegue até a pasta backend
cd backend

# Instale dependências (se não tiver)
pip install fastapi uvicorn mysql-connector-python

# Execute a API
uvicorn main_api_completo:app --reload --host 0.0.0.0 --port 8000
```

**Acesse a documentação interativa:** http://localhost:8000/docs


## 📝 ENDPOINTS DISPONÍVEIS

### 1️⃣ EXPERIMENTOS

#### ✅ Criar Experimento
```
POST /api/experimentos
```
**Corpo (JSON):**
```json
{
  "id_usuario": 1,
  "material": "Óleo de Coco",
  "operador": "Camila",
  "capsula": "A1",
  "massa": 120.5,
  "tempo_inicio": "2026-05-05 14:30",
  "tempo_final": "2026-05-05 14:50",
  "delta_tempo": 20.0,
  "temperatura_inicial": 24.0,
  "temperatura_final": 42.0,
  "delta_temperatura": 18.0
}
```

#### ✅ Listar Todos os Experimentos
```
GET /api/experimentos
GET /api/experimentos?limit=10
GET /api/experimentos?usuario_id=1
```

#### ✅ Obter Experimento por ID
```
GET /api/experimentos/1
```

#### ✅ Atualizar Experimento
```
PUT /api/experimentos/1
```
**Corpo (envie apenas campos que quer atualizar):**
```json
{
  "temperatura_final": 45.0,
  "delta_temperatura": 21.0
}
```

#### ✅ Deletar Experimento
```
DELETE /api/experimentos/1
```

#### ✅ Buscar por Material
```
GET /api/experimentos/buscar/por-material?material=Coco
```

#### ✅ Buscar por Data
```
GET /api/experimentos/buscar/por-data?data=2026-05-05
```

#### ✅ Busca Flexível (Texto)
```
GET /api/experimentos/buscar/texto-livre?q=Camila
GET /api/experimentos/buscar/texto-livre?q=A1
GET /api/experimentos/buscar/texto-livre?q=123
```


### 2️⃣ CÁLCULOS TÉRMICOS

#### ✅ Criar Cálculo Térmico
```
POST /api/calculos-termicos
```
**Corpo:**
```json
{
  "id_experimento": 1,
  "temperatura_inicial": 24.0,
  "temperatura_final": 42.0,
  "delta_temperatura": 18.0,
  "calor_latente": 250.5,
  "calor_sensivel": 180.2,
  "energia_armazenada": 2160.0,
  "densidade_energetica": 17.95,
  "eficiencia": 92.5
}
```

#### ✅ Listar Cálculos
```
GET /api/calculos-termicos
GET /api/calculos-termicos?limit=20
```

#### ✅ Cálculos de um Experimento
```
GET /api/calculos-termicos/experimento/1
```

#### ✅ Obter Cálculo por ID
```
GET /api/calculos-termicos/5
```

#### ✅ Atualizar Cálculo
```
PUT /api/calculos-termicos/5
```


### 3️⃣ MÉTRICAS (DASHBOARD)

#### ✅ Obter Métricas do Experimento
```
GET /api/experimentos/1/metricas
```

**Resposta:**
```json
{
  "temperatura_media": 33.0,
  "delta_temperatura": 18.0,
  "heating_rate": 0.9,
  "energia_armazenada": 2160.0
}
```

| Campo | Cálculo | Descrição |
|-------|---------|-----------|
| `temperatura_media` | (T_ini + T_fin) / 2 | Temperatura média |
| `delta_temperatura` | T_fin - T_ini | Variação de temperatura |
| `heating_rate` | ΔT / Δt | Taxa de aquecimento (°C/min) |
| `energia_armazenada` | massa × 2.0 × ΔT | Energia armazenada (J) |


## 📚 EXEMPLOS COM PYTHON

### Usar API da Interface (FASE 3)

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Criar experimento
response = requests.post(f"{BASE_URL}/experimentos", json={
    "id_usuario": 1,
    "material": "Cera de Coco",
    "operador": "Camila",
    "temperatura_inicial": 24.0,
    "temperatura_final": 42.0
})
exp_id = response.json()["id"]
print(f"Experimento criado: {exp_id}")

# Listar experimentos
response = requests.get(f"{BASE_URL}/experimentos")
experimentos = response.json()
print(f"Total: {len(experimentos)} experimentos")

# Buscar por material
response = requests.get(f"{BASE_URL}/experimentos/buscar/por-material", params={"material": "Coco"})
resultados = response.json()

# Obter métricas
response = requests.get(f"{BASE_URL}/experimentos/{exp_id}/metricas")
metricas = response.json()
print(f"Temperatura média: {metricas['temperatura_media']}")

# Deletar
requests.delete(f"{BASE_URL}/experimentos/{exp_id}")
```


## 🔄 ESTRATÉGIA DE MIGRAÇÃO (SEM QUEBRAR)

### FASE 1: Criar Endpoints (JÁ FEITO ✅)
- API está pronta com todos os endpoints

### FASE 2: Testar (PRÓXIMO)
- Use http://localhost:8000/docs para testar
- Verifique se MySQL está rodando
- Confirme as credenciais

### FASE 3: Integrar na Interface (DEPOIS)
Crie um módulo intermediário:

```python
# arquivo: services/api_client.py
import requests
from typing import List, Optional

class ThermaCoreMySQLClient:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
    
    def criar_experimento(self, **kwargs):
        return requests.post(f"{self.base_url}/experimentos", json=kwargs).json()
    
    def listar_experimentos(self, limit=None):
        params = {"limit": limit} if limit else {}
        return requests.get(f"{self.base_url}/experimentos", params=params).json()
    
    def obter_metricas(self, exp_id):
        return requests.get(f"{self.base_url}/experimentos/{exp_id}/metricas").json()
    
    # ... mais métodos
```

Depois na interface, troque:
```python
# ANTES (SQLite)
self.db = DatabaseManager()
exp = self.db.get_experiment_by_id(1)

# DEPOIS (MySQL via API)
self.db = ThermaCoreMySQLClient()
exp = self.db.obter_experimento(1)
```

### FASE 4: Migração Gradual
1. Mantenha SQLite funcionando
2. Migre um módulo por vez
3. Quando tiver confiança, remova SQLite


## ❌ PROBLEMAS COMUNS

### "Erro ao conectar: Access denied for user 'root'"
- Verifique se MySQL está rodando
- Confirme usuário e senha em `get_connection()`

### "Table 'thermacore.experiments' doesn't exist"
- Crie as tabelas no MySQL com o SQL fornecido
- Verifique se está no banco correto

### "ConnectionError: Connection refused"
- API está desligada? Execute `uvicorn main_api_completo:app --reload`

### Conflito: SQLite vs MySQL
- **SOLUÇÃO:** Mantenha ambos funcionando em paralelo
- API lê/escreve no MySQL
- Interface (por enquanto) lê do SQLite
- Após confirmar, mude interface para API


## ✅ CHECKLIST

- [ ] MySQL instalado e rodando
- [ ] Banco "thermacore" criado
- [ ] Tabelas criadas (SQL fornecido)
- [ ] main_api_completo.py salvo
- [ ] FastAPI instalado
- [ ] API iniciada com sucesso
- [ ] Teste em http://localhost:8000/docs
- [ ] Endpoints retornam dados corretos

---

**Próximo Passo:** Você quer testar a API ou já começar a integração na interface?
