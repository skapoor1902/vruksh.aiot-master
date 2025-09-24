
from config import broker, port, username, password
from paho.mqtt import client as mqtt_client
# generate client ID with pub prefix randomly
import random

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("=====================")
            print("=====================")
            print("=====================")
            print("Connected to MQTT Broker!")
            print("=====================")
        else:
            print("!!!!!!!!!!!!!!!!!!!!!!")
            print("Failed to connect, return code %d\n", rc)
            print("!!!!!!!!!!!!!!!!!!!!!!")
            
    client_id = f'python-mqtt-{random.randint(0, 1000)}'

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id)
    client.tls_set(ca_certs='./emqxsl-ca.crt')
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client