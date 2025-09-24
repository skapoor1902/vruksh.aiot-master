import warnings
warnings.filterwarnings("ignore")
import time
from connect import connect_mqtt
from subscribe import subscribe
from onMessage.onMessage import on_message

def run():
    client = connect_mqtt()
    client.loop_start()  # Start the loop in a separate thread
    
    while True:
        try:
            subscribe(client, "mqtt/get_optimal_moisture")
            subscribe(client, "mqtt/moisture_alert")
            subscribe(client, "mqtt/get_water_quantity")
            time.sleep(1)  # Prevents excessive CPU usage
        except KeyboardInterrupt:
            print("=====================")
            print("=====================")
            print("=====================")
            print("Stopping MQTT client...")
            client.loop_stop()
            client.disconnect()
            break

if __name__ == '__main__':
    run()