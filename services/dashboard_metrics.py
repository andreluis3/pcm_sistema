def calcular_metricas_globais(experimentos, db):
    """
    Calcula métricas globais do dashboard PCM.
    """

    if not experimentos:
        return {
            "media_temperatura": 0,
            "media_energia": 0,
            "media_tempo": 0,
            "media_taxa": 0,
            "media_eficiencia": 0,
            "total_experimentos": 0,
        }

    temperaturas: list[float] = []
    energias: list[float] = []
    tempos: list[float] = []
    taxas: list[float] = []
    eficiencias: list[float] = []

    for exp in experimentos:

        exp_id = exp.get("id")

        if exp_id is None:
            continue

        # =========================
        # TEMPERATURA MÉDIA
        # =========================
        temp = db.get_temperatura_media(exp_id)

        if temp is not None:
            temperaturas.append(float(temp))

        # =========================
        # ENERGIA
        # =========================
        energia = db.get_energia_armazenada(exp_id)

        if energia is not None:
            energias.append(float(energia))

        # =========================
        # TEMPO
        # =========================
        tempo = exp.get("delta_tempo")

        if tempo is not None:
            tempos.append(float(tempo))

        # =========================
        # TAXA DE AQUECIMENTO
        # =========================
        taxa = db.get_heating_rate(exp_id)

        if taxa is not None:
            taxas.append(float(taxa))

    # =========================
    # EFICIÊNCIAS
    # =========================
    calculos = db.list_thermal_calculations()

    for calc in calculos:

        eficiencia = calc.get("eficiencia")

        if eficiencia is not None:
            eficiencias.append(float(eficiencia))

    # =========================
    # RETORNO FINAL
    # =========================
    return {

        "media_temperatura": round(
            sum(temperaturas) / len(temperaturas),
            1
        ) if temperaturas else 0,

        "media_energia": round(
            sum(energias) / len(energias),
            1
        ) if energias else 0,

        "media_tempo": round(
            sum(tempos) / len(tempos),
            1
        ) if tempos else 0,

        "media_taxa": round(
            sum(taxas) / len(taxas),
            2
        ) if taxas else 0,

        "media_eficiencia": round(
            sum(eficiencias) / len(eficiencias),
            1
        ) if eficiencias else 0,

        "total_experimentos": len(experimentos),
    }