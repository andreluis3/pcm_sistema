class SensorBuffer:

    def __init__(self, max_size=120):

        self.max_size = max_size

        self.buffer = []

    def add(self, value):

        self.buffer.append(value)

        if len(self.buffer) > self.max_size:
            self.buffer = self.buffer[-self.max_size:]

    def get_all(self):

        return self.buffer

    def clear(self):

        self.buffer.clear()