from paho.mqtt import client as mqtt_client
from onMessage.onMessage import on_message

def subscribe(client: mqtt_client, topic: str):
    """
    Subscribe to a topic and set the callback function for incoming messages.
    """
    client.subscribe(topic)
    client.on_message = on_message