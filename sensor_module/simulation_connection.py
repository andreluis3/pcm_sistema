import random
import threading
import time


class SimulationConnection:

    def __init__(
        self,
        on_data=None,
        on_log=None
    ):

        self.on_data = on_data
        self.on_log = on_log

        self.running = False
        self.thread = None

    def connect(self):

        self.running = True

        self.thread = threading.Thread(
            target=self._simulation_loop,
            daemon=True
        )

        self.thread.start()

        if self.on_log:
            self.on_log(
                "Simulação iniciada"
            )

    def disconnect(self):

        self.running = False

        if self.on_log:
            self.on_log(
                "Simulação encerrada"
            )

    def _simulation_loop(self):

        temp = 30

        while self.running:

            temp += random.uniform(-0.5, 1.2)

            if self.on_data:
                self.on_data(round(temp, 2))

            time.sleep(1)