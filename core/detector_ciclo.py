class CycleDetector:

    def __init__(self, ponto_de_fusao):
        self.ponto_de_fusao = ponto_de_fusao
        self.estado = "solido"
        self.cycle_count = 0

    def update(self, temperature):

        if self.estado == "solido" and temperature > self.ponto_de_fusao:
            self.estado = "melting"

        elif self.estado == "melting" and temperature < self.ponto_de_fusao:
            self.estado = "solido"
            self.cycle_count += 1
            return True

        return False