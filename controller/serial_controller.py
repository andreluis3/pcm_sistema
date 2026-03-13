import random
from typing import Callable

#responsavel por ler o esp32 

class SerialController:
    def __init__(self, on_temperature: Callable[[float], None], interval_ms: int = 500) -> None:
        self.on_temperature = on_temperature
        self.interval_ms = interval_ms
        self._running = False
        self._root = None

    def start(self, root) -> None:
        self._root = root
        self._running = True
        self._tick()

    def stop(self) -> None:
        self._running = False

    def _tick(self) -> None:
        if not self._running or self._root is None:
            return
        value = random.uniform(20.0, 35.0)
        self.on_temperature(value)
        self._root.after(self.interval_ms, self._tick)
