class CycleDetector:

    def __init__(self):

        self.buffer = []
        self.cycle_active = False

    def add_temperature(self, temp):

        self.buffer.append(temp)

        if len(self.buffer) < 5:
            return None

        t1 = self.buffer[-1]
        t2 = self.buffer[-2]

        if t1 > t2:
            trend = "rising"
        elif t1 < t2:
            trend = "falling"
        else:
            trend = "stable"

        return trend