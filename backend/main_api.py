from fastapi import FastAPI
from pydantic import BaseModel
import mysql.connector

app = FastAPI()

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="thermacore",
        port=3306
    )

class Experimento(BaseModel):
    material: str
    operador: str
    id_usuario: int

@app.post("/criar_experimento")
def criar_experimento(exp: Experimento):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO experiments (id_usuario, material, operador)
        VALUES (%s, %s, %s)
        """

        cursor.execute(query, (exp.id_usuario, exp.material, exp.operador))
        conn.commit()

        cursor.close()
        conn.close()

        return {"status": "ok"}

    except Exception as e:
        print("ERRO REAL:", e)
        return {"erro": str(e)}
    
@app.get("/experimentos")
def listar_experimentos():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM experiments")
        resultados = cursor.fetchall()

        cursor.close()
        conn.close()

        return resultados

    except Exception as e:
        return {"erro": str(e)}