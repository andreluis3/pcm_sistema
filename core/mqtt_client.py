<<<<<<< HEAD
import paho.mqtt.client as mqtt


class MQTTClient:

    def __init__(self, callback):

        self.broker = "broker.hivemq.com"
        self.port = 1883
        self.topic = "pcm/esp32/temperature"

        self.callback = callback

        self.client = mqtt.Client()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def connect(self):

        self.client.connect(self.broker, self.port)

        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):

        print("MQTT conectado")

        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):

        temperatura = msg.payload.decode()

        print("Temperatura recebida:", temperatura)

        if self.callback:
            self.callback(temperatura)
=======
"""MQTT client for ESP32 telemetry integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import paho.mqtt.client as mqtt


@dataclass
class TelemetryPayload:
    temperature: float
    raw: str


class MQTTClient:
    def __init__(
        self,
        on_temperature: Callable[[float], None],
        on_log: Optional[Callable[[str], None]] = None,
        on_status: Optional[Callable[[bool], None]] = None,
        host: str = "broker.hivemq.com",
        port: int = 1883,
        topic: str = "pcm/esp32/temperature",
        client_id: Optional[str] = None,
        keepalive: int = 60,
    ) -> None:
        self._on_temperature = on_temperature
        self._on_log = on_log
        self._on_status = on_status
        self._host = host
        self._port = port
        self._topic = topic
        self._keepalive = keepalive
        self._connected = False

        self._client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message
        self._client.on_disconnect = self.on_disconnect

    def connect(self) -> None:
        self._log("Conectando ao broker MQTT...")
        self._client.connect(self._host, self._port, self._keepalive)
        self._client.loop_start()

    def stop(self) -> None:
        try:
            self._client.disconnect()
        finally:
            self._client.loop_stop()

    def on_connect(self, client, userdata, flags, rc, properties=None) -> None:
        result_code = self._coerce_reason_code(rc)
        if result_code == 0:
            self._connected = True
            self._log("Conectado ao broker")
            self._log(f"Escutando tópico {self._topic}")
            self._notify_status(True)
            client.subscribe(self._topic)
        else:
            self._connected = False
            self._notify_status(False)
            self._log(f"Falha ao conectar (código {result_code})")

    def on_disconnect(self, client, userdata, rc, properties=None) -> None:
        if self._connected:
            self._log("Desconectado do broker")
        self._connected = False
        self._notify_status(False)

    def on_message(self, client, userdata, msg) -> None:
        payload = msg.payload.decode(errors="replace").strip()
        try:
            temperature = float(payload)
        except ValueError:
            self._log(f"Payload inválido: {payload}")
            return
        self._log(f"Temperatura recebida: {temperature:.1f} °C")
        self._on_temperature(temperature)

    def _log(self, message: str) -> None:
        if self._on_log:
            self._on_log(message)

    def _notify_status(self, connected: bool) -> None:
        if self._on_status:
            self._on_status(connected)

    @staticmethod
    def _coerce_reason_code(rc) -> int:
        try:
            return int(rc)
        except Exception:
            return getattr(rc, "value", 1)
>>>>>>> 9ca76cd869fef6245ae18bf751e2ad8288765600
