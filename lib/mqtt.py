import socket
import time
from threading import Thread

import paho.mqtt.client

_SERVER = 'bill'
_PUBLISH_CALLBACKS = {}

def start_client(service_name):
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
    mqttc = paho.mqtt.client.Client(client_name)
    mqttc.connect(_SERVER)
    mqttc.loop_start()
    Thread(target=publisher(mqttc), daemon=True).start()

def publish_forever(topic, callback):
    _PUBLISH_CALLBACKS[topic] = callback
