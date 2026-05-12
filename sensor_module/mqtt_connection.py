class MQTTConnection:

    def __init__(
        self,
        host,
        port,
        topic,
        on_data=None,
        on_log=None
    ):

        self.host = host
        self.port = port
        self.topic = topic

        self.on_data = on_data
        self.on_log = on_log

    def connect(self):

        if self.on_log:
            self.on_log(
                "MQTT ainda não implementado"
            )

    def disconnect(self):

        if self.on_log:
            self.on_log(
                "MQTT desconectado"
            )