from paho.mqtt import client as mqtt_client

def publish(client: mqtt_client, topic: str, message: str):
    """
    Publish a message to a specific topic.
    """
    try:
        client.publish(topic, message)
        print("=====================")
        print(f"Published `{message}` to `{topic}` topic")
        print("=====================")
    except Exception as e:
        print("!!!!!!!!!!!!!!!!!!!!!!")
        print(f"Failed to publish message: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!")