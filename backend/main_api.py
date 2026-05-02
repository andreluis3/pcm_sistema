from fastapi import FastAPI
from pydantic import BaseModel
import mysql.connector

app = FastAPI()

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "ThermaCore"
}

class Experimento(BaseModel):
    material: str
    operador: str
    id_usuario: int

@app.post("/criar_experimento")
def criar_experimento(exp: Experimento):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    query = """
    INSERT INTO experiments (id_usuario, material, operador)
    VALUES (%s, %s, %s)
    """

    cursor.execute(query, (exp.id_usuario, exp.material, exp.operador))
    conn.commit()

    return {"status": "ok"}