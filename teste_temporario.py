from services.api_client import ThermaCoreMySQLClient

api = ThermaCoreMySQLClient()

dados = {
    "id_usuario": 1,
    "material": "teste",
    "operador": "andre"
}

print(api.insert_experiment(dados))