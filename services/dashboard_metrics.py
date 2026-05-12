def calcular_metricas_globais(experimentos, db):
    """
    Calcula métricas gerais de TODOS os experimentos.
    """

    if not experimentos:
        return None

    temperaturas = []
    energias = []
    tempos = []
    eficiencias = []

    for exp in experimentos:
        exp_id = exp.get("id")

        temp = db.get_temperatura_media(exp_id)
        energia = db.get_energia_armazenada(exp_id)
        tempo = exp.get("delta_tempo")

        if temp is not None:
            temperaturas.append(temp)

        if energia is not None:
            energias.append(energia)

        if tempo is not None:
            tempos.append(tempo)

    calculos = db.list_thermal_calculations()

    for calc in calculos:
        eficiencia = calc.get("eficiencia")

        if eficiencia is not None:
            eficiencias.append(eficiencia)

    return {
        "media_temperatura": round(sum(temperaturas) / len(temperaturas), 1) if temperaturas else 0,

        "media_energia": round(sum(energias) / len(energias), 1) if energias else 0,

        "media_tempo": round(sum(tempos) / len(tempos), 1) if tempos else 0,

        "media_eficiencia": round(sum(eficiencias) / len(eficiencias), 1) if eficiencias else 0,

        "total_experimentos": len(experimentos),
    }