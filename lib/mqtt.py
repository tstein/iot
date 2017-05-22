import socket
import time
from threading import Thread

import paho.mqtt.client

_MQTTC = None
_PUBLISH_CALLBACKS = {}

server = 'bill'

def start_client(service_name):
    global _MQTTC
    def publisher(mqttc):
        def loop():
            while True:
                for topic, callback in _PUBLISH_CALLBACKS.items():
                    value = callback()
                    if value is not None:
                        mqttc.publish(topic, value)
                time.sleep(1)
        return loop

    client_name = "{}-{}".format(socket.gethostname(), service_name)
    _MQTTC = paho.mqtt.client.Client(client_name)
    _MQTTC.connect(server)
    _MQTTC.loop_start()
    Thread(target=publisher(_MQTTC), daemon=True).start()

def publish_forever(topic, callback):
    _PUBLISH_CALLBACKS[topic] = callback

def tell(whom, what, client=None):
    if not client:
        client = _MQTTC
    client.publish("tell/" + whom, what)
