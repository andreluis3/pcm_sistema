class ThermalProcessing:

    @staticmethod
    def calculate_delta_t(initial, final):

        return final - initial

    @staticmethod
    def calculate_average(data):

        if not data:
            return 0

        return sum(data) / len(data)

    @staticmethod
    def calculate_peak(data):

        if not data:
            return 0

        return max(data)