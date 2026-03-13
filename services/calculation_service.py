class CalculationService:

    def calculate_average(self, data):

        if not data:
            return 0

        return sum(data) / len(data)

    def calculate_delta(self, data):

        if len(data) < 2:
            return 0

        return max(data) - min(data)