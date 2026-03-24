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