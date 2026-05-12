import requests


class APIConnection:

    def __init__(self, url, on_data=None, on_log=None):

        self.url = url

        self.on_data = on_data
        self.on_log = on_log

    def send_temperature(self, temperature):

        try:

            payload = {
                "temperatura": temperature
            }

            response = requests.post(
                self.url,
                json=payload,
                timeout=5
            )

            if self.on_log:
                self.on_log(
                    f"API HTTP {response.status_code}"
                )

        except Exception as e:

            if self.on_log:
                self.on_log(
                    f"Erro API: {e}"
                )