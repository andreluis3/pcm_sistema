import math
import random
import threading
import time


class SimulationConnection:

    """
    Simulador térmico inteligente para testes do PCM.

    Simula:
    - aquecimento gradual
    - pico térmico
    - atuação do PCM
    - estabilização
    - ruído real de sensor

    Ideal para:
    ✅ testar gráficos
    ✅ validar dashboard
    ✅ validar logs
    ✅ validar exportação CSV
    ✅ validar cálculo térmico
    """

    def __init__(
        self,
        on_data=None,
        on_log=None,
        interval=1.0
    ):

        self.on_data = on_data
        self.on_log = on_log

        self.interval = interval

        self.running = False
        self.thread = None

        # =========================
        # CONTROLE DA SIMULAÇÃO
        # =========================

        self.start_time = None

        self.current_temp = 28.0

        self.ambient_temp = 27.0

        self.max_temp = 82.0

        self.pcm_trigger_temp = 45.0

        self.pcm_active = False

        self.noise_enabled = True

    # =====================================================
    # CONNECT
    # =====================================================

    def connect(self):

        if self.running:
            return

        self.running = True

        self.start_time = time.time()

        self.thread = threading.Thread(
            target=self._simulation_loop,
            daemon=True
        )

        self.thread.start()

        self._log(
            "🧪 Simulação térmica iniciada"
        )

    # =====================================================
    # DISCONNECT
    # =====================================================

    def disconnect(self):

        self.running = False

        self._log(
            "🛑 Simulação encerrada"
        )

    # =====================================================
    # MAIN LOOP
    # =====================================================

    def _simulation_loop(self):

        while self.running:

            if self.start_time is None:
                return

            elapsed = time.time() - self.start_time

            self.current_temp = self._generate_temperature(
                elapsed
            )

            temperature = round(
                self.current_temp,
                2
            )

            payload = {

                "temperature": temperature,

                "timestamp": time.time(),

                "mode": "simulation",

                "pcm_active": self.pcm_active
            }

            # CALLBACK
            if self.on_data:
                self.on_data(payload)

            # LOG
            self._log_temperature(
                temperature
            )

            time.sleep(self.interval)

    # =====================================================
    # TEMPERATURE MODEL
    # =====================================================

    def _generate_temperature(self, elapsed):

        """
        Curva térmica simulada:

        Fase 1 -> aquecimento rápido
        Fase 2 -> PCM absorvendo calor
        Fase 3 -> estabilização
        """

        # ==========================================
        # FASE 1 — AQUECIMENTO
        # ==========================================

        if elapsed < 40:

            growth = elapsed * 0.75

            temp = self.ambient_temp + growth

        # ==========================================
        # FASE 2 — PCM ATUANDO
        # ==========================================

        elif elapsed < 110:

            self.pcm_active = True

            # crescimento desacelera
            growth = 30 + ((elapsed - 40) * 0.15)

            temp = self.ambient_temp + growth

        # ==========================================
        # FASE 3 — SATURAÇÃO TÉRMICA
        # ==========================================

        else:

            self.pcm_active = False

            saturation = (
                self.max_temp
                - math.exp(-(elapsed - 110) / 30)
            )

            temp = saturation

        # ==========================================
        # RUÍDO REALISTA
        # ==========================================

        if self.noise_enabled:

            temp += random.uniform(
                -0.35,
                0.35
            )

        # ==========================================
        # LIMITES
        # ==========================================

        temp = max(
            self.ambient_temp,
            min(temp, self.max_temp)
        )

        return temp

    # =====================================================
    # LOG TEMP
    # =====================================================

    def _log_temperature(self, temperature):

        if temperature >= self.pcm_trigger_temp:

            if self.pcm_active:

                self._log(
                    f"🧊 PCM absorvendo calor | {temperature:.2f} °C"
                )

            else:

                self._log(
                    f"🔥 PCM saturado | {temperature:.2f} °C"
                )

        else:

            self._log(
                f"🌡 Temperatura: {temperature:.2f} °C"
            )

    # =====================================================
    # LOG
    # =====================================================

    def _log(self, message):

        if self.on_log:
            self.on_log(message)