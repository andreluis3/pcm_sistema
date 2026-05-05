"""
API FastAPI para ThermaCore - Banco de Dados MySQL
Endpoints para substituir operações SQLite

Executar com:
    uvicorn main_api:app --reload --host 0.0.0.0 --port 8000

Teste em: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import mysql.connector
from datetime import datetime
from contextlib import contextmanager

app = FastAPI(
    title="ThermaCore API",
    description="API para gerenciar experimentos e cálculos térmicos",
    version="1.0.0"
)

# ==================== CONFIGURAÇÃO DE CONEXÃO ====================

def get_connection():
    """Criar conexão com banco MySQL"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="thermacore",
        port=3306
    )

@contextmanager
def get_db():
    """Context manager para gerenciar conexões com segurança"""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


# ==================== MODELOS PYDANTIC ====================

class ExperimentoBase(BaseModel):
    """Base para Experimento"""
    material: str
    operador: str
    capsula: Optional[str] = None
    massa: Optional[float] = None
    tempo_inicio: Optional[str] = None
    tempo_final: Optional[str] = None
    delta_tempo: Optional[float] = None
    temperatura_inicial: Optional[float] = None
    temperatura_final: Optional[float] = None
    delta_temperatura: Optional[float] = None


class ExperimentoCreate(ExperimentoBase):
    """Para criar experimento"""
    id_usuario: int


class ExperimentoUpdate(BaseModel):
    """Para atualizar experimento (todos opcionais)"""
    material: Optional[str] = None
    operador: Optional[str] = None
    capsula: Optional[str] = None
    massa: Optional[float] = None
    tempo_inicio: Optional[str] = None
    tempo_final: Optional[str] = None
    delta_tempo: Optional[float] = None
    temperatura_inicial: Optional[float] = None
    temperatura_final: Optional[float] = None
    delta_temperatura: Optional[float] = None


class ExperimentoResponse(ExperimentoBase):
    """Resposta com experimento completo"""
    id: int
    id_usuario: int
    date_created: str


class CalculoTermicoBase(BaseModel):
    """Base para cálculo térmico"""
    temperatura_inicial: float
    temperatura_final: float
    delta_temperatura: float
    calor_latente: Optional[float] = None
    calor_sensivel: Optional[float] = None
    energia_armazenada: Optional[float] = None
    densidade_energetica: Optional[float] = None
    eficiencia: Optional[float] = None
    calculation_type: Optional[str] = None


class CalculoTermicoCreate(CalculoTermicoBase):
    """Para criar cálculo térmico"""
    id_experimento: int


class CalculoTermicoUpdate(BaseModel):
    """Para atualizar cálculo térmico"""
    temperatura_inicial: Optional[float] = None
    temperatura_final: Optional[float] = None
    delta_temperatura: Optional[float] = None
    calor_latente: Optional[float] = None
    calor_sensivel: Optional[float] = None
    energia_armazenada: Optional[float] = None
    densidade_energetica: Optional[float] = None
    eficiencia: Optional[float] = None


class CalculoTermicoResponse(CalculoTermicoBase):
    """Resposta com cálculo térmico completo"""
    id: int
    id_experimento: int
    data_calculo: str


class TabelaCalculosBase(BaseModel):
    """Base para tabela_calculos"""
    experimento_id: int
    tipo_calculo: str
    massa: float
    calor_especifico: float
    delta_t: float
    resultado: float


class TabelaCalculosResponse(TabelaCalculosBase):
    """Resposta com cálculo da tabela"""
    id: int
    data_calculo: str


class MetricasResponse(BaseModel):
    """Métricas do experimento para dashboard"""
    temperatura_media: Optional[float] = None
    delta_temperatura: Optional[float] = None
    heating_rate: Optional[float] = None
    energia_armazenada: Optional[float] = None


# ==================== ENDPOINTS: EXPERIMENTOS ====================

@app.post("/api/experimentos", response_model=dict, tags=["Experimentos"])
def criar_experimento(exp: ExperimentoCreate):
    """
    ✅ Criar novo experimento
    
    Retorna ID e status
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            query = """
            INSERT INTO experiments 
            (id_usuario, material, operador, capsula, massa, 
             tempo_inicio, tempo_final, delta_tempo,
             temperatura_inicial, temperatura_final, delta_temperatura)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                exp.id_usuario, exp.material, exp.operador, exp.capsula, exp.massa,
                exp.tempo_inicio, exp.tempo_final, exp.delta_tempo,
                exp.temperatura_inicial, exp.temperatura_final, exp.delta_temperatura
            ))
            conn.commit()
            
            return {
                "status": "ok",
                "id": cursor.lastrowid,
                "mensagem": "Experimento criado com sucesso"
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao criar experimento: {str(e)}")


@app.get("/api/experimentos", response_model=List[ExperimentoResponse], tags=["Experimentos"])
def listar_experimentos(
    limit: Optional[int] = Query(None, description="Limitar número de resultados"),
    usuario_id: Optional[int] = Query(None, description="Filtrar por usuário")
):
    """
    ✅ Listar todos os experimentos
    
    Parâmetros opcionais:
    - limit: número máximo de resultados
    - usuario_id: filtrar por usuário
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            
            query = "SELECT * FROM experiments"
            params = []
            
            if usuario_id:
                query += " WHERE id_usuario = %s"
                params.append(usuario_id)
            
            query += " ORDER BY date_created DESC"
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao listar: {str(e)}")


@app.get("/api/experimentos/{experimento_id}", response_model=ExperimentoResponse, tags=["Experimentos"])
def obter_experimento(experimento_id: int):
    """
    ✅ Obter experimento por ID
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM experiments WHERE id = %s", (experimento_id,))
            exp = cursor.fetchone()
            
            if not exp:
                raise HTTPException(status_code=404, detail="Experimento não encontrado")
            
            return exp
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro: {str(e)}")


@app.put("/api/experimentos/{experimento_id}", response_model=dict, tags=["Experimentos"])
def atualizar_experimento(experimento_id: int, exp_update: ExperimentoUpdate):
    """
    ✅ Atualizar experimento
    
    Apenas campos fornecidos serão atualizados
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Construir query dinamicamente apenas com campos não-nulos
            campos = []
            valores = []
            
            for campo, valor in exp_update.dict(exclude_unset=True).items():
                campos.append(f"{campo} = %s")
                valores.append(valor)
            
            if not campos:
                return {"status": "ok", "mensagem": "Nenhum campo para atualizar"}
            
            valores.append(experimento_id)
            query = f"UPDATE experiments SET {', '.join(campos)} WHERE id = %s"
            
            cursor.execute(query, valores)
            conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Experimento não encontrado")
            
            return {"status": "ok", "mensagem": "Experimento atualizado"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar: {str(e)}")


@app.delete("/api/experimentos/{experimento_id}", response_model=dict, tags=["Experimentos"])
def deletar_experimento(experimento_id: int):
    """
    ✅ Deletar experimento
    
    Também deleta cálculos associados (cascata)
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM experiments WHERE id = %s", (experimento_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Experimento não encontrado")
            
            return {"status": "ok", "mensagem": "Experimento deletado"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao deletar: {str(e)}")


@app.get("/api/experimentos/buscar/por-material", response_model=List[ExperimentoResponse], tags=["Experimentos"])
def buscar_por_material(material: str = Query(..., description="Nome do material")):
    """
    ✅ Buscar experimentos por material
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM experiments WHERE material LIKE %s ORDER BY date_created DESC",
                (f"%{material}%",)
            )
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro: {str(e)}")


@app.get("/api/experimentos/buscar/por-data", response_model=List[ExperimentoResponse], tags=["Experimentos"])
def buscar_por_data(data: str = Query(..., description="Data no formato YYYY-MM-DD")):
    """
    ✅ Buscar experimentos por data
    
    Formato: 2026-05-05
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM experiments WHERE DATE(date_created) = %s ORDER BY date_created DESC",
                (data,)
            )
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro: {str(e)}")


@app.get("/api/experimentos/buscar/texto-livre", response_model=List[ExperimentoResponse], tags=["Experimentos"])
def buscar_texto_livre(q: str = Query(..., description="Termo para busca")):
    """
    ✅ Busca flexível em todos os campos
    
    Busca em: operador, material, cápsula, ID
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            like = f"%{q}%"
            query = """
            SELECT * FROM experiments WHERE 
                operador LIKE %s OR 
                material LIKE %s OR 
                capsula LIKE %s OR 
                CAST(id AS CHAR) LIKE %s
            ORDER BY date_created DESC
            """
            cursor.execute(query, (like, like, like, like))
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro: {str(e)}")


# ==================== ENDPOINTS: CÁLCULOS TÉRMICOS ====================

@app.post("/api/calculos-termicos", response_model=dict, tags=["Cálculos Térmicos"])
def criar_calculo_termico(calculo: CalculoTermicoCreate):
    """
    ✅ Criar novo cálculo térmico
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            query = """
            INSERT INTO calculos_termicos
            (id_experimento, temperatura_inicial, temperatura_final, delta_temperatura,
             calor_latente, calor_sensivel, energia_armazenada, densidade_energetica, eficiencia)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                calculo.id_experimento,
                calculo.temperatura_inicial,
                calculo.temperatura_final,
                calculo.delta_temperatura,
                calculo.calor_latente,
                calculo.calor_sensivel,
                calculo.energia_armazenada,
                calculo.densidade_energetica,
                calculo.eficiencia
            ))
            conn.commit()
            
            return {
                "status": "ok",
                "id": cursor.lastrowid,
                "mensagem": "Cálculo criado com sucesso"
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro: {str(e)}")


@app.get("/api/calculos-termicos", response_model=List[CalculoTermicoResponse], tags=["Cálculos Térmicos"])
def listar_calculos_termicos(limit: Optional[int] = Query(None)):
    """
    ✅ Listar todos os cálculos térmicos
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM calculos_termicos ORDER BY data_calculo DESC"
            params = []
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro: {str(e)}")


@app.get("/api/calculos-termicos/{calculo_id}", response_model=CalculoTermicoResponse, tags=["Cálculos Térmicos"])
def obter_calculo_termico(calculo_id: int):
    """
    ✅ Obter cálculo térmico por ID
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM calculos_termicos WHERE id = %s", (calculo_id,))
            calculo = cursor.fetchone()
            
            if not calculo:
                raise HTTPException(status_code=404, detail="Cálculo não encontrado")
            
            return calculo
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro: {str(e)}")


@app.put("/api/calculos-termicos/{calculo_id}", response_model=dict, tags=["Cálculos Térmicos"])
def atualizar_calculo_termico(calculo_id: int, calculo_update: CalculoTermicoUpdate):
    """
    ✅ Atualizar cálculo térmico
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            campos = []
            valores = []
            
            for campo, valor in calculo_update.dict(exclude_unset=True).items():
                campos.append(f"{campo} = %s")
                valores.append(valor)
            
            if not campos:
                return {"status": "ok", "mensagem": "Nenhum campo para atualizar"}
            
            valores.append(calculo_id)
            query = f"UPDATE calculos_termicos SET {', '.join(campos)} WHERE id = %s"
            
            cursor.execute(query, valores)
            conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Cálculo não encontrado")
            
            return {"status": "ok", "mensagem": "Cálculo atualizado"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro: {str(e)}")


@app.get("/api/calculos-termicos/experimento/{experimento_id}", response_model=List[CalculoTermicoResponse], tags=["Cálculos Térmicos"])
def listar_calculos_por_experimento(experimento_id: int):
    """
    ✅ Listar cálculos de um experimento específico
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM calculos_termicos WHERE id_experimento = %s ORDER BY data_calculo DESC",
                (experimento_id,)
            )
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro: {str(e)}")


# ==================== ENDPOINTS: MÉTRICAS (DASHBOARD) ====================

@app.get("/api/experimentos/{experimento_id}/metricas", response_model=MetricasResponse, tags=["Dashboard"])
def obter_metricas(experimento_id: int):
    """
    ✅ Obter métricas calculadas para o dashboard
    
    Retorna:
    - temperatura_media: (T_inicial + T_final) / 2
    - delta_temperatura: T_final - T_inicial
    - heating_rate: ΔT / Δt
    - energia_armazenada: massa × 2.0 × ΔT
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM experiments WHERE id = %s", (experimento_id,))
            exp = cursor.fetchone()
            
            if not exp:
                raise HTTPException(status_code=404, detail="Experimento não encontrado")
            
            # Cálculos
            t_ini = exp.get("temperatura_inicial")
            t_fin = exp.get("temperatura_final")
            delta_t = exp.get("delta_temperatura")
            delta_tempo = exp.get("delta_tempo")
            massa = exp.get("massa")
            
            temp_media = None
            if t_ini and t_fin:
                temp_media = (float(t_ini) + float(t_fin)) / 2.0
            
            heating_rate = None
            if delta_t and delta_tempo and delta_tempo != 0:
                heating_rate = float(delta_t) / float(delta_tempo)
            
            energia = None
            if massa and delta_t:
                energia = float(massa) * 2.0 * float(delta_t)
            
            return {
                "temperatura_media": temp_media,
                "delta_temperatura": delta_t,
                "heating_rate": heating_rate,
                "energia_armazenada": energia
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro: {str(e)}")


# ==================== HEALTH CHECK ====================

@app.get("/health", tags=["Status"])
def health_check():
    """Verificar saúde da API"""
    try:
        with get_db() as conn:
            conn.ping()
        return {"status": "ok", "banco": "conectado"}
    except Exception as e:
        return {"status": "erro", "detalhe": str(e)}, 500


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
