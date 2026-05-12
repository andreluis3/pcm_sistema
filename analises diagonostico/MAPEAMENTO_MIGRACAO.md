# 🔍 MAPEAMENTO DE OPERAÇÕES SQLite → Endpoints API

## 📁 Arquivos Afetados e Operações

### 1. `interface/experiment_tab.py`
**O que faz:** Formulário para criar/atualizar experimentos

| Operação | Função | Linha | SQLite | API Endpoint |
|----------|--------|-------|--------|-------------|
| Criar | `_save_experiment()` | ~120 | `self.db.insert_experiment()` | `POST /api/experimentos` |
| Atualizar | `_save_experiment()` | ~130 | `self.db.update_experiment()` | `PUT /api/experimentos/{id}` |
| Listar | `_load_experiments()` | ~150 | `self.db.list_experiments()` | `GET /api/experimentos` |
| Deletar | `_delete_experiment()` | ~160 | `self.db.delete_experiment()` | `DELETE /api/experimentos/{id}` |

**Ação necessária:** Criar classe proxy que chama API ao invés de DB


### 2. `interface/dashboard_tab.py`
**O que faz:** Dashboard com métricas e gráficos

| Operação | Função | Método DB | API Endpoint |
|----------|--------|-----------|-------------|
| Carregar dados | `load_dashboard_data()` | `self.db.list_experiments()` | `GET /api/experimentos` |
| Temperatura média | `update_dashboard()` | `self.db.get_temperatura_media()` | `GET /api/experimentos/{id}/metricas` |
| Delta T | `update_dashboard()` | `self.db.get_delta_t()` | `GET /api/experimentos/{id}/metricas` |
| Taxa aquecimento | `update_dashboard()` | `self.db.get_heating_rate()` | `GET /api/experimentos/{id}/metricas` |
| Energia | `update_dashboard()` | `self.db.get_energia_armazenada()` | `GET /api/experimentos/{id}/metricas` |

**Ação necessária:** Substituir 5 chamadas por 1 chamada a `/metricas`


### 3. `interface/database_tab.py`
**O que faz:** Visualização e gerenciamento de banco de dados

| Operação | Função | Método DB | API Endpoint |
|----------|--------|-----------|-------------|
| Listar | `load_experiments()` | `self.db.list_experiments()` | `GET /api/experimentos` |
| Buscar por material | `_search_experiments()` | `self.db.search_experiments()` | `GET /api/experimentos/buscar/por-material` |
| Buscar flexível | `_search_experiments()` | `self.db.search_experiments_flexible()` | `GET /api/experimentos/buscar/texto-livre` |
| Atualizar campo | `_edit_cell()` | `self.db.update_experiment()` | `PUT /api/experimentos/{id}` |
| Deletar | `_delete_selected()` | `self.db.delete_experiment()` | `DELETE /api/experimentos/{id}` |

**Ação necessária:** Maior número de chamadas para migrar


### 4. `interface/view/thermal_calculations_page.py`
**O que faz:** Cálculos térmicos e visualizações

| Operação | Função | Método DB | API Endpoint |
|----------|--------|-----------|-------------|
| Listar cálculos | `load_thermal_data()` | `self.db.list_thermal_calculations()` | `GET /api/calculos-termicos` |
| Inserir cálculo | `save_calculation()` | `self.db.insert_thermal_calculation()` | `POST /api/calculos-termicos` |
| Tabela calculos | `upsert()` | `self.db.upsert_tabela_calculos()` | `POST /api/tabela-calculos` (novo) |

**Ação necessária:** Criar endpoint para tabela_calculos


### 5. `database/db_manager.py`
**Métodos que precisam de endpoints na API:**

```python
# EXPERIMENTOS
insert_experiment()          → POST /api/experimentos
update_experiment()          → PUT /api/experimentos/{id}
delete_experiment()          → DELETE /api/experimentos/{id}
get_experiment_by_id()       → GET /api/experimentos/{id}
list_experiments()           → GET /api/experimentos
search_experiments()         → GET /api/experimentos/buscar/por-material
search_experiments_flexible()→ GET /api/experimentos/buscar/texto-livre

# CÁLCULOS TÉRMICOS
insert_thermal_calculation() → POST /api/calculos-termicos
list_thermal_calculations()  → GET /api/calculos-termicos

# TABELA CALCULOS (FALTANDO)
upsert_tabela_calculos()     → POST/PUT /api/tabela-calculos
get_calculo_by_experimento() → GET /api/tabela-calculos/experimento/{id}
list_tabela_calculos()       → GET /api/tabela-calculos
```

**STATUS:**
- ✅ Experimentos: COMPLETO
- ✅ Cálculos Térmicos: COMPLETO
- ⏳ Tabela Calculos: FALTANDO (criar)


## 🎯 PRIORIDADE DE MIGRAÇÃO

### PRIORIDADE 1 (Crítica)
1. `experiment_tab.py` - Criar/salvar experimentos
   - POST/PUT `/api/experimentos`

2. `dashboard_tab.py` - Dashboard funcionar
   - GET `/api/experimentos`
   - GET `/api/experimentos/{id}/metricas`

### PRIORIDADE 2 (Alta)
3. `database_tab.py` - Gerenciamento completo
   - GET `/api/experimentos/buscar/*`
   - DELETE `/api/experimentos/{id}`

4. `thermal_calculations_page.py` - Cálculos
   - POST/GET `/api/calculos-termicos`

### PRIORIDADE 3 (Depois)
5. `tabela_calculos` - Tabela auxiliar
   - Criar endpoints faltantes


## 💾 SQL para TABELA_CALCULOS

Se precisar adicionar endpoint para tabela_calculos:

```sql
CREATE TABLE IF NOT EXISTS tabela_calculos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    experimento_id INT,
    massa FLOAT,
    calor_especifico FLOAT,
    delta_t FLOAT,
    resultado FLOAT,
    tipo_calculo VARCHAR(100),
    data_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (experimento_id) REFERENCES experiments(id) ON DELETE CASCADE
);
```


## 🔗 CLASSE INTERMEDIÁRIA (Para migração segura)

Crie `services/api_client.py`:

```python
import requests
from typing import List, Dict, Optional

class ThermaCoreMySQLClient:
    """Cliente para chamar API MySQL ao invés de SQLite"""
    
    def __init__(self, base_url="http://localhost:8000/api", use_api=True):
        self.base_url = base_url
        self.use_api = use_api  # Toggle para SQLite/MySQL
    
    # ==================== EXPERIMENTOS ====================
    
    def insert_experiment(self, data: Dict) -> int:
        """Insere experimento e retorna ID"""
        response = requests.post(f"{self.base_url}/experimentos", json=data)
        return response.json()["id"]
    
    def update_experiment(self, exp_id: int, data: Dict) -> None:
        """Atualiza experimento"""
        requests.put(f"{self.base_url}/experimentos/{exp_id}", json=data)
    
    def delete_experiment(self, exp_id: int) -> None:
        """Deleta experimento"""
        requests.delete(f"{self.base_url}/experimentos/{exp_id}")
    
    def get_experiment_by_id(self, exp_id: int) -> Optional[Dict]:
        """Busca experimento por ID"""
        response = requests.get(f"{self.base_url}/experimentos/{exp_id}")
        if response.status_code == 200:
            return response.json()
        return None
    
    def list_experiments(self, limit: Optional[int] = None) -> List[Dict]:
        """Lista todos os experimentos"""
        params = {"limit": limit} if limit else {}
        response = requests.get(f"{self.base_url}/experimentos", params=params)
        return response.json() if response.status_code == 200 else []
    
    def search_experiments(self, material: Optional[str] = None, 
                          date: Optional[str] = None) -> List[Dict]:
        """Busca experimentos por material ou data"""
        if material:
            response = requests.get(
                f"{self.base_url}/experimentos/buscar/por-material",
                params={"material": material}
            )
        elif date:
            response = requests.get(
                f"{self.base_url}/experimentos/buscar/por-data",
                params={"data": date}
            )
        else:
            return []
        return response.json() if response.status_code == 200 else []
    
    def search_experiments_flexible(self, query: str) -> List[Dict]:
        """Busca flexível em todos os campos"""
        response = requests.get(
            f"{self.base_url}/experimentos/buscar/texto-livre",
            params={"q": query}
        )
        return response.json() if response.status_code == 200 else []
    
    # ==================== MÉTRICAS ====================
    
    def get_temperatura_media(self, exp_id: int) -> Optional[float]:
        """Obter temperatura média"""
        response = requests.get(f"{self.base_url}/experimentos/{exp_id}/metricas")
        if response.status_code == 200:
            return response.json().get("temperatura_media")
        return None
    
    def get_delta_t(self, exp_id: int) -> Optional[float]:
        """Obter delta temperatura"""
        response = requests.get(f"{self.base_url}/experimentos/{exp_id}/metricas")
        if response.status_code == 200:
            return response.json().get("delta_temperatura")
        return None
    
    def get_heating_rate(self, exp_id: int) -> Optional[float]:
        """Obter taxa de aquecimento"""
        response = requests.get(f"{self.base_url}/experimentos/{exp_id}/metricas")
        if response.status_code == 200:
            return response.json().get("heating_rate")
        return None
    
    def get_energia_armazenada(self, exp_id: int) -> Optional[float]:
        """Obter energia armazenada"""
        response = requests.get(f"{self.base_url}/experimentos/{exp_id}/metricas")
        if response.status_code == 200:
            return response.json().get("energia_armazenada")
        return None
    
    # ==================== CÁLCULOS ====================
    
    def insert_thermal_calculation(self, data: Dict) -> int:
        """Insere cálculo térmico"""
        response = requests.post(f"{self.base_url}/calculos-termicos", json=data)
        return response.json()["id"]
    
    def list_thermal_calculations(self, limit: Optional[int] = None) -> List[Dict]:
        """Lista cálculos térmicos"""
        params = {"limit": limit} if limit else {}
        response = requests.get(f"{self.base_url}/calculos-termicos", params=params)
        return response.json() if response.status_code == 200 else []
```

**Como usar:**
```python
# Na interface, substitua:
from database.database_manager import DatabaseManager

# Por:
from services.api_client import ThermaCoreMySQLClient

# E use igual:
self.db = ThermaCoreMySQLClient()  # Ao invés de DatabaseManager()
```


---

**Resumo:** 
- ✅ API **PRONTA** com 15+ endpoints
- 📋 Mapeamento **COMPLETO** de migrações
- 🔗 Cliente intermediário para **TRANSIÇÃO SEGURA**
- ⏭️ Próxima etapa: Testar API e depois integrar interface
