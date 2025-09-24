import network
from machine import Pin, RTC
import machine
from unit import EarthUnit
from umqtt.simple import MQTTClient
import ujson
import gc
import ssl
import urandom  # For generating random values
import ntptime
import time
import utime
import M5

# MQTT Configuration
MQTT_BROKER = 'l5820bb1.ala.asia-southeast1.emqxsl.com'
MQTT_PORT = 8883
MQTT_CLIENT_ID = "plant_monitor_" + str(machine.unique_id())
MQTT_USER = "heet434"
MQTT_PASSWORD = "heet434"
MQTT_TOPIC_PREFIX = "mqtt/"

# Topic for receiving the moisture threshold
THRESHOLD_TOPIC = MQTT_TOPIC_PREFIX + "optimal_moisture_threshold"

# WiFi Configuration
WIFI_SSID = "Ifone 15"
WIFI_PASSWORD = "sierra3003"

# Schedule Configuration
SCHEDULE_TIMES = [
    {"hour": 19, "minute": 20, "name": "Morning"},   # 8:00 AM
    {"hour": 14, "minute": 0, "name": "Afternoon"},  # 2:00 PM
    {"hour": 20, "minute": 0, "name": "Evening"}   # 8:00 PM
]

# Threshold monitoring configuration
THRESHOLD_CHECK_INTERVAL = 80  # 3 minutes in seconds

# Global variables
mqtt_client = None
rtc = RTC()
threshold_monitoring_active = False
moisture_threshold = None
last_threshold_check_time = 0
threshold_cross_reported = False
env_data = {
        "temperature": 28,
        "air_humidity": 55,
        "soil_ph": 6.5,
        "nitrogen_content": 0 
    }
last_publish_time = 0

# Define colors
BLACK = 0x000000
WHITE = 0xFFFFFF
GREEN = 0x00FF00
YELLOW = 0xFFFF00
RED = 0xFF0000
BLUE = 0x0000FF
CYAN = 0x00FFFF
ORANGE = 0xFFA500
GREY = 0x808080

# Add global variables for display
PUMP_RATE = 10  # mL per minute - Add this if not already defined

# Global variables for tracking watering
water_quantity_added = 0.0
last_watering_timestamp = 0
is_watering = False
watering_start_time = 0
start_soil_moisture = 0
soil_moisture = 0

def setup_display():
    """Initialize the M5 display"""
    try:
        # Initialize M5 display
        M5.begin()
        
        # Clear the display
        M5.Display.clear(BLACK)
        
        # Set text color and size for title
        M5.Display.setTextColor(BLUE, BLACK)
        M5.Display.setTextSize(2)
        
        # Draw header
        M5.Display.setCursor(20, 10)
        M5.Display.print("PLANT WATERING SYSTEM")
        
        # Draw divider line
        M5.Display.drawLine(0, 40, 320, 40, WHITE)
        
        # Show initialization message
        M5.Display.setTextColor(GREEN, BLACK)
        M5.Display.setTextSize(1)
        M5.Display.setCursor(10, 60)
        M5.Display.print("Initializing system...")
        
        print("Display initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing display: {e}")
        return False

def update_connection_status(wifi_connected, mqtt_connected):
    """Update connection status indicators on display"""
    # Clear status area
    M5.Display.fillRect(10, 45, 300, 20, BLACK)
    
    # WiFi status
    M5.Display.setTextSize(1)
    M5.Display.setCursor(10, 50)
    if wifi_connected:
        M5.Display.setTextColor(GREEN, BLACK)
        M5.Display.print("WiFi: Connected")
    else:
        M5.Display.setTextColor(RED, BLACK)
        M5.Display.print("WiFi: Disconnected")
    
    # MQTT status
    M5.Display.setCursor(160, 50)
    if mqtt_connected:
        M5.Display.setTextColor(GREEN, BLACK)
        M5.Display.print("MQTT: Connected")
    else:
        M5.Display.setTextColor(RED, BLACK)
        M5.Display.print("MQTT: Disconnected")

def display_all_data(moisture, env_data, threshold=None, is_watering=False):
    """Display all sensor data on a single screen"""
    # Clear display area
    M5.Display.fillRect(5, 75, 310, 165, BLACK)
    
    # Current moisture with larger display
    M5.Display.setTextColor(WHITE, BLACK)
    M5.Display.setTextSize(1)
    M5.Display.setCursor(10, 75)
    M5.Display.print("SOIL MOISTURE:")
    
    # Determine color based on moisture level
    if threshold is not None:
        if moisture > threshold:
            moisture_color = GREEN
        elif moisture > threshold * 0.7:
            moisture_color = YELLOW
        else:
            moisture_color = RED
    else:
        moisture_color = BLUE
    
    # Show moisture value
    M5.Display.setTextColor(moisture_color, BLACK)
    M5.Display.setTextSize(2)
    M5.Display.setCursor(10, 90)
    M5.Display.print(f"{moisture}%")
    
    # Draw moisture bar
    bar_width = int((moisture / 100) * 170)  # Scale to 170px width
    M5.Display.drawRect(110, 90, 170, 15, WHITE)  # Bar outline
    M5.Display.fillRect(110, 90, bar_width, 15, moisture_color)  # Fill bar
    
    # Show threshold if available
    if threshold is not None:
        # Draw threshold marker
        threshold_x = 110 + int((threshold / 100) * 170)
        M5.Display.drawLine(threshold_x, 85, threshold_x, 105, YELLOW)
        
        M5.Display.setTextColor(YELLOW, BLACK)
        M5.Display.setTextSize(1)
        M5.Display.setCursor(threshold_x - 10, 110)
        M5.Display.print(f"{threshold}%")
    
    # Watering status
    M5.Display.setTextColor(WHITE, BLACK)
    M5.Display.setTextSize(1)
    M5.Display.setCursor(10, 125)
    M5.Display.print("WATERING:")
    
    if is_watering:
        M5.Display.setTextColor(BLUE, BLACK)
        M5.Display.print(" ACTIVE")
        # Draw water drop when watering
        M5.Display.fillCircle(280, 125, 5, BLUE)
    else:
        M5.Display.setTextColor(WHITE, BLACK)
        M5.Display.print(" INACTIVE")
    
    # Environment data with compact display
    # Temperature
    M5.Display.setTextColor(ORANGE, BLACK)
    M5.Display.setTextSize(1)
    M5.Display.setCursor(10, 145)
    M5.Display.print("TEMP:")
    M5.Display.setCursor(50, 145)
    M5.Display.print(f"{env_data['temperature']}°C")
    
    # Humidity
    M5.Display.setTextColor(CYAN, BLACK)
    M5.Display.setCursor(120, 145)
    M5.Display.print("HUMIDITY:")
    M5.Display.setCursor(180, 145)
    M5.Display.print(f"{env_data['air_humidity']}%")
    
    # Soil pH
    M5.Display.setTextColor(YELLOW, BLACK)
    M5.Display.setCursor(10, 165)
    M5.Display.print("SOIL pH:")
    M5.Display.setCursor(65, 165)
    M5.Display.print(f"{env_data['soil_ph']}")
    
    # Nitrogen
    M5.Display.setTextColor(GREEN, BLACK)
    M5.Display.setCursor(120, 165)
    M5.Display.print("NITROGEN:")
    M5.Display.setCursor(180, 165)
    M5.Display.print(f"{env_data['nitrogen_content']} ppm")
    
    # Water data
    M5.Display.setTextColor(BLUE, BLACK)
    M5.Display.setCursor(10, 185)
    M5.Display.print("WATER ADDED TODAY:")
    M5.Display.setCursor(145, 185)
    M5.Display.print(f"{water_quantity_added:.1f} mL")
    
    # Last watering time
    if last_watering_timestamp > 0:
        last_time = format_timestamp(last_watering_timestamp)
        if len(last_time) > 19:  # Truncate if too long
            last_time = last_time[:19]
        M5.Display.setTextColor(WHITE, BLACK)
        M5.Display.setCursor(10, 205)
        M5.Display.print("LAST WATERING:")
        M5.Display.setCursor(110, 205)
        M5.Display.print(last_time)
    
    # Next scheduled reading
    current_datetime = machine.RTC().datetime()
    next_time = find_next_schedule_time(current_datetime)
    if next_time:
        M5.Display.setTextColor(GREEN, BLACK)
        M5.Display.setCursor(10, 225)
        M5.Display.print("NEXT READING:")
        M5.Display.setCursor(110, 225)
        M5.Display.print(next_time)

# Helper function to find next scheduled time
def find_next_schedule_time(current_datetime):
    """Find the next scheduled reading time"""
    current_hour = current_datetime[4]
    current_minute = current_datetime[5]
    current_minutes = current_hour * 60 + current_minute
    
    min_wait_time = 24 * 60  # Default to 24 hours (in minutes)
    next_hour = 0
    next_minute = 0
    
    for schedule in SCHEDULE_TIMES:
        # Calculate minutes from current time to this schedule
        schedule_minutes = schedule["hour"] * 60 + schedule["minute"]
        
        # If schedule is later today
        if schedule_minutes > current_minutes:
            wait_minutes = schedule_minutes - current_minutes
            if wait_minutes < min_wait_time:
                min_wait_time = wait_minutes
                next_hour = schedule["hour"]
                next_minute = schedule["minute"]
        
        # If schedule is tomorrow
        elif schedule_minutes < current_minutes:
            wait_minutes = (24 * 60) - current_minutes + schedule_minutes
            if wait_minutes < min_wait_time:
                min_wait_time = wait_minutes
                next_hour = schedule["hour"]
                next_minute = schedule["minute"]
    
    return f"{next_hour:02d}:{next_minute:02d}"

def set_time():
    """Synchronize time with NTP server"""
    try:
        ntptime.timeout = 30
        ntptime.settime()
        
        # Adjust time to IST (UTC+5:30 = 19800 seconds)
        t = utime.localtime(utime.mktime(utime.localtime()) + 19800)
        machine.RTC().datetime((t[0], t[1], t[2], 0, t[3], t[4], t[5], 0))
        print("Time set to:", t)
        return True
    except Exception as e:
        print(f"NTP time sync failed: {e}")
        # Set default time as fallback
        rtc.datetime((2025, 4, 15, 0, 12, 0, 0, 0))
        print(f"Default time set: {format_time(rtc.datetime())}")
        return False
    
def format_time(datetime_tuple):
    """Format RTC datetime tuple into readable string"""
    year, month, day, weekday, hour, minute, second, _ = datetime_tuple
    return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

def format_timestamp(timestamp):
    """Format timestamp into human-readable string"""
    try:
        # Convert timestamp to tuple
        time_tuple = time.localtime(timestamp)
        
        # Format as string: YYYY-MM-DD HH:MM:SS
        formatted = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            time_tuple[0], time_tuple[1], time_tuple[2], 
            time_tuple[3], time_tuple[4], time_tuple[5]
        )
        return formatted
    except:
        return "Unknown time"

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    print("wlan: ", wlan)
    wlan.active(True)  # Activate the WiFi interface

    if not wlan.isconnected():
        print(f"Connecting to WiFi network: {ssid}...")
        wlan.connect(ssid, password)

        timeout = 10  # Timeout in seconds
        for _ in range(timeout * 10):  # Check connection every 100ms
            if wlan.isconnected():
                break
            time.sleep(0.1)

    if wlan.isconnected():
        print("Connected to WiFi!")
        print("IP Address:", wlan.ifconfig()[0])
        return True
    else:
        print("Failed to connect to WiFi.")
        return False

# First, let's update the on_mqtt_message function to properly initialize the threshold checking timer
def on_mqtt_message(topic, msg):
    """Callback for receiving MQTT messages"""
    global moisture_threshold, threshold_monitoring_active, threshold_cross_reported, last_threshold_check_time
    
    topic_str = topic.decode('utf-8')
    msg_str = msg.decode('utf-8')
    
    print(f"Message received on topic {topic_str}: {msg_str}")
    
    # Handle threshold messages
    if topic_str == THRESHOLD_TOPIC:
        try:
            # Try to parse as JSON first
            try:
                threshold_data = ujson.loads(msg_str)
                if "threshold" in threshold_data:
                    new_threshold = float(threshold_data["threshold"])
                else:
                    new_threshold = float(msg_str)
            except:
                # If not JSON, try to parse as a direct number
                new_threshold = float(msg_str)
            
            print(f"New moisture threshold set: {new_threshold}")
            moisture_threshold = new_threshold
            threshold_monitoring_active = True
            threshold_cross_reported = False
            
            # Initialize the last check time to current time
            last_threshold_check_time = time.time()
            print(f"Starting 3-minute threshold check cycle at {format_timestamp(last_threshold_check_time)}")
            
            # Show threshold received message
            M5.Display.fillRect(30, 235, 260, 25, YELLOW)
            M5.Display.setTextColor(BLACK, YELLOW)
            M5.Display.setTextSize(1)
            M5.Display.setCursor(50, 245)
            M5.Display.print(f"NEW THRESHOLD SET: {new_threshold}%")
            
            # Update the display with the new threshold
            display_all_data(soil_moisture, env_data, moisture_threshold, is_watering)
            
            # Perform an immediate check
            check_moisture_threshold()
            
        except Exception as e:
            print(f"Error processing threshold message: {e}")
            
            # Show error on display
            M5.Display.fillRect(30, 235, 260, 25, RED)
            M5.Display.setTextColor(WHITE, RED)
            M5.Display.setTextSize(1)
            M5.Display.setCursor(50, 245)
            M5.Display.print(f"THRESHOLD ERROR: {str(e)}")

def connect_mqtt():
    global mqtt_client
    
    print(f"Connecting to MQTT Broker: {MQTT_BROKER}...")
    
    try:
        # Create a new MQTT client instance
        client_id = MQTT_CLIENT_ID
        
        # Try multiple approaches to establish a connection
        
        # Approach 1: Try with no certificate verification (least secure but most likely to work)
        try:
            print("Attempting connection with no certificate verification...")
            mqtt_client = MQTTClient(
                client_id=client_id,
                server=MQTT_BROKER,
                port=MQTT_PORT,
                user=MQTT_USER,
                password=MQTT_PASSWORD,
                ssl=True,
                ssl_params={"cert_reqs": ssl.CERT_NONE}
            )
            
            # Set the message callback
            mqtt_client.set_callback(on_mqtt_message)
            
            mqtt_client.connect()
            
            # Subscribe to the threshold topic
            mqtt_client.subscribe(THRESHOLD_TOPIC)
            print(f"Subscribed to {THRESHOLD_TOPIC}")
            
            print("Connected to MQTT Broker without certificate verification!")
            print("Warning: This connection is not fully secure but works for testing")
            return True
            
        except Exception as e1:
            print(f"First connection attempt failed: {e1}")
            
            # Approach 2: Try with server hostname but optional verification
            try:
                print("Attempting connection with optional certificate verification...")
                mqtt_client = MQTTClient(
                    client_id=client_id,
                    server=MQTT_BROKER,
                    port=MQTT_PORT,
                    user=MQTT_USER,
                    password=MQTT_PASSWORD,
                    ssl=True,
                    ssl_params={
                        "cert_reqs": ssl.CERT_OPTIONAL,
                        "server_hostname": MQTT_BROKER
                    }
                )
                
                # Set the message callback
                mqtt_client.set_callback(on_mqtt_message)
                
                mqtt_client.connect()
                
                # Subscribe to the threshold topic
                mqtt_client.subscribe(THRESHOLD_TOPIC)
                print(f"Subscribed to {THRESHOLD_TOPIC}")
                
                print("Connected to MQTT Broker with optional verification!")
                return True
                
            except Exception as e2:
                print(f"Second connection attempt failed: {e2}")
                
                # Approach 3: Try non-SSL connection if possible
                try:
                    print("Last resort: Attempting non-SSL connection...")
                    print("Note: This may fail if the broker requires SSL")
                    
                    # Use port 1883 for non-SSL connection
                    mqtt_client = MQTTClient(
                        client_id=client_id,
                        server=MQTT_BROKER,
                        port=1883,  # Standard non-SSL MQTT port
                        user=MQTT_USER,
                        password=MQTT_PASSWORD,
                        ssl=False
                    )
                    
                    # Set the message callback
                    mqtt_client.set_callback(on_mqtt_message)
                    
                    mqtt_client.connect()
                    
                    # Subscribe to the threshold topic
                    mqtt_client.subscribe(THRESHOLD_TOPIC)
                    print(f"Subscribed to {THRESHOLD_TOPIC}")
                    
                    print("Connected to MQTT Broker without SSL!")
                    return True
                    
                except Exception as e3:
                    print(f"All connection attempts failed!")
                    raise Exception(f"Cannot establish MQTT connection after multiple attempts")
                    
    except Exception as e:
        print(f"Failed to connect to MQTT Broker: {e}")
        return False

def publish_mqtt_data(topic, data):
    """Publish data to MQTT broker"""
    global mqtt_client, last_publish_time
    
    if mqtt_client is None:
        print("MQTT client not connected")
        return False
    
    try:
        # Convert data to JSON string if it's a dictionary
        if isinstance(data, dict):
            message = ujson.dumps(data)
        else:
            message = str(data)
        
        # Construct the full topic
        full_topic = MQTT_TOPIC_PREFIX + topic
        
        # Publish the message
        mqtt_client.publish(full_topic, message)
        print(f"Published to {full_topic}: {message}")
        
        # If this is publishing to the optimal_moisture topic, update the timestamp
        if topic == "get_optimal_moisture":
            last_publish_time = time.time()
            print(f"Updated last publish time to {format_timestamp(last_publish_time)}")
            print(f"Next possible threshold update after: {format_timestamp(last_publish_time + 60)}")
        
        return True
        
    except Exception as e:
        print(f"Failed to publish MQTT message: {e}")
        return False

def generate_random_data():
    """Generate random environmental data based on realistic distributions"""
    # Use normally distributed random values based on the provided statistics
    
    # Ambient Temperature: mean=23.87, std=3.65, range=[18.02-29.99]
    temperature = urandom.getrandbits(16) / 65535.0  # Random value between 0 and 1
    temperature = 23.87 + (temperature * 2 - 1) * 3.65  # Apply normal distribution around mean
    temperature = max(18.02, min(29.99, temperature))  # Constrain to the valid range
    
    # Humidity: mean=57.21, std=9.03, range=[41.39-69.69]
    humidity = urandom.getrandbits(16) / 65535.0
    humidity = 57.21 + (humidity * 2 - 1) * 9.03
    humidity = max(41.39, min(69.69, humidity))
    
    # Soil pH: mean=6.56, std=0.57, range=[5.56-7.50]
    soil_ph = urandom.getrandbits(16) / 65535.0
    soil_ph = 6.56 + (soil_ph * 2 - 1) * 0.57
    soil_ph = max(5.56, min(7.50, soil_ph))
    
    # Nitrogen Level: mean=37.22, std=8.96, range=[21.98-49.30]
    nitrogen = urandom.getrandbits(16) / 65535.0
    nitrogen = 37.22 + (nitrogen * 2 - 1) * 8.96
    nitrogen = max(21.98, min(49.30, nitrogen))
    
    return {
        "temperature": round(temperature, 1),
        "air_humidity": round(humidity, 1),
        "soil_ph": round(soil_ph, 2),
        "nitrogen_content": round(nitrogen, 1)
    }

def read_soil_moisture():
    """
    Read soil moisture and update display with current readings
    """
    global water_quantity_added, last_watering_timestamp, is_watering, watering_start_time, start_soil_moisture, soil_moisture
    
    try:
        # Initialize the Earth Unit sensor
        earth_unit = EarthUnit((33, 32))
        
        # Read soil moisture values
        soil_moisture = earth_unit.humidity()
        moisture_analog = earth_unit.get_analog_value()
        moisture_digital = earth_unit.get_digital_value()  # True if dry, False if wet
        soil_moisture = soil_moisture*45
        
        current_timestamp = time.time()
        formatted_time = format_timestamp(current_timestamp)
        
        print(f"Soil Moisture Reading: {soil_moisture}% at {formatted_time}")
        print(f"Analog value: {moisture_analog}, Digital value: {moisture_digital}")
        #soil_moisture += 20
        
        # Update the display with all data
        display_all_data(soil_moisture, env_data, moisture_threshold, is_watering)
        
        # Check if we need to water based on moisture threshold
        if moisture_threshold is not None and soil_moisture < moisture_threshold:
            # Plant needs water
            if not is_watering:
                # Start watering cycle
                is_watering = True
                watering_start_time = current_timestamp
                start_soil_moisture = soil_moisture
                
                print(f"Starting watering cycle at {formatted_time}")
                
                # Update display
                display_all_data(soil_moisture, env_data, moisture_threshold, True)
                
                # Show watering started message
                M5.Display.fillRect(30, 235, 260, 25, BLUE)
                M5.Display.setTextColor(WHITE, BLUE)
                M5.Display.setTextSize(1)
                M5.Display.setCursor(80, 245)
                M5.Display.print("AUTO WATERING STARTED")
                
                # Activate pump (simulate this with a print statement)
                print("PUMP ON: Watering the plant")
                
            else:
                # Continue watering - calculate current amount
                watering_duration = current_timestamp - watering_start_time
                current_water_quantity = (watering_duration / 60) * PUMP_RATE  # mL
    
                print(f"Watering in progress: {watering_duration:.1f} seconds, ~{current_water_quantity:.1f} mL delivered")
        else:
            # Check if we were watering and need to stop
            if is_watering:
                # Stop watering cycle
                watering_duration = current_timestamp - watering_start_time
                water_added = (watering_duration / 60) * PUMP_RATE  # mL
                
                water_quantity_added += water_added
                last_watering_timestamp = current_timestamp
                
                print(f"Stopping watering cycle. Added {water_added:.1f} mL")
                print(f"Total water added today: {water_quantity_added:.1f} mL")
                
                # Update display
                display_all_data(soil_moisture, env_data, moisture_threshold, False)
                
                # Show watering complete message
                M5.Display.fillRect(30, 235, 260, 25, GREEN)
                M5.Display.setTextColor(BLACK, GREEN)
                M5.Display.setTextSize(1)
                M5.Display.setCursor(50, 245)
                M5.Display.print(f"WATERING COMPLETE: {water_added:.1f} mL")
                
                # Turn off pump (simulate this with a print statement)
                print("PUMP OFF: Watering complete")
                
                # In real application:
                # pump_pin.value(0)  # Turn pump off
                
                is_watering = False
                
                # Publish watering data to MQTT
                watering_data = {
                    "plant_id": 1,
                    "temp": env_data["temperature"],
                    "humidity": env_data["air_humidity"],
                    "nitrogen": env_data["nitrogen_content"],
                    "pH": env_data["soil_ph"],
                    "formatted_time": formatted_time,
                    "duration_seconds": watering_duration,
                    "water_quantity": water_added,
                    "total_water_quantity": water_quantity_added,
                    "optimal_moisture": moisture_threshold,
                    "soil_moisture_now": soil_moisture,
                    "initial_moisture": start_soil_moisture,
                    "watering_type": "automatic"
                }
                
                publish_mqtt_data("moisture_alert", watering_data)
        
        return soil_moisture
        
    except Exception as e:
        print(f"Error reading soil moisture: {e}")
        import sys
        sys.print_exception(e)  # Print full exception traceback
        
        # Show error on display
        M5.Display.fillRect(10, 75, 300, 120, BLACK)
        M5.Display.setTextColor(RED, BLACK)
        M5.Display.setTextSize(1)
        M5.Display.setCursor(10, 90)
        M5.Display.print("ERROR READING MOISTURE SENSOR:")
        M5.Display.setCursor(10, 105)
        M5.Display.print(str(e))
        
        return None

# Function to reset water quantity (useful to call at midnight for daily tracking)
def reset_water_quantity():
    """Reset the water quantity counter (e.g., at the start of a new day)"""
    global water_quantity_added
    
    previous_quantity = water_quantity_added
    water_quantity_added = 0.0
    
    print(f"Water quantity counter reset. Previous value: {previous_quantity:.1f} mL")
    
    return previous_quantity

# Function to check if moisture has crossed above the threshold
def check_moisture_threshold():
    """Check if soil moisture has crossed above the threshold"""
    global threshold_monitoring_active, moisture_threshold, threshold_cross_reported
    
    if not threshold_monitoring_active or moisture_threshold is None:
        return False
    
    # Read current soil moisture
    current_moisture = read_soil_moisture()
    if current_moisture is None:
        print("Failed to read moisture for threshold check")
        return False
    
    print(f"Threshold check: Current moisture: {current_moisture}%, Threshold: {moisture_threshold}%")
    
    # Check if moisture has crossed ABOVE the threshold
    if current_moisture > moisture_threshold and not threshold_cross_reported:
        print(f"ALERT: Soil moisture ({current_moisture}%) above threshold ({moisture_threshold}%)")
        
        # Publish threshold crossing alert
        alert_data = {
            "current_moisture": current_moisture,
            "threshold": moisture_threshold,
            "status": "above_threshold",
            "timestamp": time.time()
        }
        
        #publish_mqtt_data("moisture_alert", alert_data)
        threshold_cross_reported = True
        
        return True
    
    return False

def read_sensor_and_publish(period_name=""):
    """Read sensor data and publish to MQTT"""
    global threshold_monitoring_active, threshold_cross_reported, start_soil_moisture, env_data
    
    try:
        # Initialize the Earth Unit sensor
        earth_unit = EarthUnit((33, 32))
        
        # Read soil moisture values
        soil_moisture = earth_unit.humidity()
        moisture_analog = earth_unit.get_analog_value()
        moisture_voltage = earth_unit.get_voltage_mv()
        moisture_digital = earth_unit.get_digital_value()
        soil_moisture = soil_moisture*45
        start_soil_moisture = soil_moisture
        # Generate realistic environmental data based on provided statistics
        env_data = generate_random_data()
        
        
        # Display readings
        print(f"--- {period_name} Readings ---")
        print(f"Soil Moisture analog: {moisture_analog}")
        print(f"Voltage: {moisture_voltage} mV")
        print(f"Digital: {moisture_digital}")
        print(f"Moisture humidity: {soil_moisture}%")
        print(f"Temperature: {env_data['temperature']}°C")
        print(f"Air Humidity: {env_data['air_humidity']}%")
        print(f"Soil pH: {env_data['soil_ph']}")
        print(f"Nitrogen Content: {env_data['nitrogen_content']} ppm")
        
        # Prepare combined data for MQTT
        sensor_data = {
            "period": period_name,
            "soil_moisture_percent": soil_moisture,
            "soil_moisture_analog": moisture_analog,
            "voltage_mv": moisture_voltage,
            "is_dry": moisture_digital,  # True if dry, False if wet
            "temp": env_data['temperature'],
            "humidity": env_data['air_humidity'],
            "pH": env_data['soil_ph'],
            "nitrogen": env_data['nitrogen_content'],
            "timestamp": time.time(),
            "plant_id":1
        }
        
        # Add threshold information if monitoring is active
        if threshold_monitoring_active and moisture_threshold is not None:
            sensor_data["moisture_threshold"] = moisture_threshold
            sensor_data["threshold_status"] = "above" if soil_moisture > moisture_threshold else "below"
            
            # Reset threshold monitoring after scheduled reading
            threshold_cross_reported = False
        
        # Publish data
        publish_mqtt_data("get_optimal_moisture", sensor_data)
        
        # Also publish individual values to separate topics if needed
        publish_mqtt_data("check_moisture", soil_moisture)
        publish_mqtt_data("temperature", env_data['temperature'])
        publish_mqtt_data("air_humidity", env_data['air_humidity'])
        publish_mqtt_data("nitrogen", env_data['nitrogen_content'])
        publish_mqtt_data("soil_ph", env_data['soil_ph'])
        
        # Memory management (important for long-running applications)
        gc.collect()
        
        print(f"--- {period_name} Readings Published Successfully ---")
        
        # Update the display
        display_all_data(soil_moisture, env_data, moisture_threshold, is_watering)
        
        # Show publishing notification
        M5.Display.fillRect(30, 235, 260, 25, GREEN)
        M5.Display.setTextColor(BLACK, GREEN)
        M5.Display.setTextSize(1)
        M5.Display.setCursor(80, 245)
        M5.Display.print(f"{period_name.upper()} DATA PUBLISHED")
        
    except Exception as e:
        print(f"Error reading sensor or publishing data: {e}")
        
        # Show error on display
        M5.Display.fillRect(30, 235, 260, 25, RED)
        M5.Display.setTextColor(WHITE, RED)
        M5.Display.setTextSize(1)
        M5.Display.setCursor(50, 245)
        M5.Display.print(f"SENSOR ERROR: {str(e)}")

def reconnect_if_needed():
    """Check connections and reconnect if necessary"""
    global mqtt_client
    
    # Check WiFi connection
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("WiFi disconnected. Reconnecting...")
        
        # Show reconnecting message
        M5.Display.fillRect(30, 235, 260, 25, YELLOW)
        M5.Display.setTextColor(BLACK, YELLOW)
        M5.Display.setTextSize(1)
        M5.Display.setCursor(80, 245)
        M5.Display.print("RECONNECTING WIFI...")
        
        if not connect_wifi(WIFI_SSID, WIFI_PASSWORD):
            print("Failed to reconnect WiFi")
            
            # Show error on display
            M5.Display.fillRect(30, 235, 260, 25, RED)
            M5.Display.setTextColor(WHITE, RED)
            M5.Display.setTextSize(1)
            M5.Display.setCursor(80, 245)
            M5.Display.print("WIFI RECONNECT FAILED")
            
            return False
    
    # Check MQTT connection
    try:
        # Ping the broker (this will raise an exception if disconnected)
        mqtt_client.ping()
    except:
        print("MQTT disconnected. Reconnecting...")
        
        # Show reconnecting message
        M5.Display.fillRect(30, 235, 260, 25, YELLOW)
        M5.Display.setTextColor(BLACK, YELLOW)
        M5.Display.setTextSize(1)
        M5.Display.setCursor(80, 245)
        M5.Display.print("RECONNECTING MQTT...")
        
        if not connect_mqtt():
            print("Failed to reconnect MQTT")
            
            # Show error on display
            M5.Display.fillRect(30, 235, 260, 25, RED)
            M5.Display.setTextColor(WHITE, RED)
            M5.Display.setTextSize(1)
            M5.Display.setCursor(80, 245)
            M5.Display.print("MQTT RECONNECT FAILED")
            
            return False
    
    # Update connection status
    update_connection_status(wlan.isconnected(), mqtt_client is not None)
    return True

def calculate_sleep_time():
    """Calculate time until next scheduled reading or threshold check"""
    global threshold_monitoring_active, last_threshold_check_time
    
    current_datetime = machine.RTC().datetime()
    current_hour = current_datetime[4]
    current_minute = current_datetime[5]
    current_second = current_datetime[6]
    
    # Calculate time to next scheduled reading
    min_wait_time = 24 * 60  # Default to 24 hours (in minutes)
    next_period = "Unknown"
    
    for schedule in SCHEDULE_TIMES:
        # Calculate minutes from current time to this schedule
        schedule_minutes = schedule["hour"] * 60 + schedule["minute"]
        current_minutes = current_hour * 60 + current_minute
        
        # If schedule is later today
        if schedule_minutes > current_minutes:
            wait_minutes = schedule_minutes - current_minutes
            if wait_minutes < min_wait_time:
                min_wait_time = wait_minutes
                next_period = schedule["name"]
        
        # If schedule is tomorrow
        elif schedule_minutes < current_minutes:
            wait_minutes = (24 * 60) - current_minutes + schedule_minutes
            if wait_minutes < min_wait_time:
                min_wait_time = wait_minutes
                next_period = schedule["name"]
        
        # If we're exactly at a scheduled time but with seconds > 0,
        # we should wait for the next scheduled time
        elif schedule_minutes == current_minutes and current_second > 0:
            continue
    
    # If active threshold monitoring and not already reported crossing
    if threshold_monitoring_active and not threshold_cross_reported:
        # Calculate time since last threshold check
        current_time = time.time()
        time_since_last_check = current_time - last_threshold_check_time
        
        # If it's time for a threshold check
        if time_since_last_check >= THRESHOLD_CHECK_INTERVAL:
            # Do an immediate check (return a very short sleep time)
            return 1
        else:
            # Calculate time until next threshold check
            time_to_next_check = THRESHOLD_CHECK_INTERVAL - time_since_last_check
            
            # Return the shorter of the two waiting times
            if time_to_next_check < (min_wait_time * 60):
                print(f"Next threshold check in {time_to_next_check} seconds")
                return time_to_next_check
    
    # Otherwise, wait until the next scheduled reading
    sleep_seconds = min_wait_time * 60
    
    next_check_time = time.time() + sleep_seconds
    current_time_str = format_time(current_datetime)
    next_time = time.localtime(next_check_time)
    next_time_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        next_time[0], next_time[1], next_time[2], next_time[3], next_time[4], next_time[5]
    )
    
    print(f"Current time: {current_time_str}")
    print(f"Sleeping until {next_period} reading")
    print(f"Next schedule in {sleep_seconds} seconds ({min_wait_time} minutes)")
    print(f"Next reading at: {next_time_str}")
    
    return sleep_seconds

def check_schedule():
    """Check if it's time to publish based on schedule"""
    current_datetime = rtc.datetime()
    current_hour = current_datetime[4]
    current_minute = current_datetime[5]
    current_second = current_datetime[6]
      

    for schedule in SCHEDULE_TIMES:
        if current_hour == schedule["hour"] and current_minute == schedule["minute"]:
            print(f"It's time for {schedule['name']} readings!")
            current_time = time.time()
            time_since_last_publish = current_time - last_publish_time              

            if time_since_last_publish < 60:
                print(f"Skipping scheduled reading - too soon after last publish ({time_since_last_publish:.1f} seconds)")
                return False
                
            print(f"It's time for {schedule['name']} readings!")

            # Show schedule notification
            M5.Display.fillRect(30, 235, 260, 25, BLUE)
            M5.Display.setTextColor(WHITE, BLUE)
            M5.Display.setTextSize(1)
            M5.Display.setCursor(40, 245)
            M5.Display.print(f"SCHEDULED {schedule['name'].upper()} READING")
            
            
            if reconnect_if_needed():
                read_sensor_and_publish(schedule["name"])
            return True
    
    return False

def check_for_mqtt_messages():
    """Check for any pending MQTT messages"""
    global mqtt_client
    
    try:
        mqtt_client.check_msg()
    except Exception as e:
        print(f"Error checking MQTT messages: {e}")

def main():
    global last_threshold_check_time, threshold_cross_reported
    
    # Initialize the M5 display
    setup_display()
    
    # Set the time
    set_time()
    
    # Display time on screen
    current_datetime = rtc.datetime()
    time_str = format_time(current_datetime)
    M5.Display.setTextColor(WHITE, BLACK)
    M5.Display.setTextSize(1)
    M5.Display.setCursor(190, 50)
    M5.Display.print(time_str)
    
    # Initial connections
    M5.Display.setCursor(10, 100)
    M5.Display.print("Connecting to WiFi...")
    wifi_connected = connect_wifi(WIFI_SSID, WIFI_PASSWORD)
    
    M5.Display.setCursor(10, 120)
    if wifi_connected:
        M5.Display.setTextColor(GREEN, BLACK)
        M5.Display.print("WiFi connected successfully!")
    else:
        M5.Display.setTextColor(RED, BLACK)
        M5.Display.print("WiFi connection failed.")
        time.sleep(3)
        # Don't exit, keep trying
    
    M5.Display.setCursor(10, 140)
    M5.Display.setTextColor(WHITE, BLACK)
    M5.Display.print("Connecting to MQTT broker...")
    mqtt_connected = connect_mqtt()
    
    M5.Display.setCursor(10, 160)
    if mqtt_connected:
        M5.Display.setTextColor(GREEN, BLACK)
        M5.Display.print("MQTT connected successfully!")
    else:
        M5.Display.setTextColor(RED, BLACK)
        M5.Display.print("MQTT connection failed.")
        time.sleep(3)
        # Don't exit, keep trying
    
    time.sleep(2)
    
    # Update connection status indicators
    update_connection_status(wifi_connected, mqtt_connected)
    
    # Initialize display with all data
    display_all_data(soil_moisture, env_data, moisture_threshold, is_watering)
    
    print("Starting scheduled plant monitoring with threshold checks...")
    print("Scheduled times:")
    for schedule in SCHEDULE_TIMES:
        print(f"- {schedule['name']}: {schedule['hour']:02d}:{schedule['minute']:02d}")
    
    print(f"Listening for threshold settings on {THRESHOLD_TOPIC}")
    print(f"Threshold check interval: {THRESHOLD_CHECK_INTERVAL} seconds (every 3 minutes)")
    
    # Show startup complete notification
    M5.Display.fillRect(30, 235, 260, 25, GREEN)
    M5.Display.setTextColor(BLACK, GREEN)
    M5.Display.setTextSize(1)
    M5.Display.setCursor(80, 245)
    M5.Display.print("SYSTEM INITIALIZED")
    
    try:
        while True:
            # Check for MQTT messages (including threshold settings)
            check_for_mqtt_messages()
            
            # Check if it's time for a scheduled reading
            schedule_triggered = check_schedule()
            
            # Update connection status periodically
            if time.time() % 60 < 1:  # Check roughly once per minute
                update_connection_status(
                    network.WLAN(network.STA_IF).isconnected(),
                    mqtt_client is not None
                )
            
            # Check if it's time to do a threshold check (every 3 minutes)
            current_time = time.time()
            
            if threshold_monitoring_active and not threshold_cross_reported:
                # Calculate time since last threshold check
                time_since_last_check = current_time - last_threshold_check_time
                
                # Display countdown to next check
                seconds_to_next_check = THRESHOLD_CHECK_INTERVAL - time_since_last_check
                if seconds_to_next_check > 0 and seconds_to_next_check < THRESHOLD_CHECK_INTERVAL:
                    # Only print occasionally to avoid log spam
                    if int(seconds_to_next_check) % 30 == 0 or seconds_to_next_check < 5:
                        print(f"Next threshold check in {int(seconds_to_next_check)} seconds")
                
                # If it's time for a threshold check (3 minutes have passed)
                if time_since_last_check >= THRESHOLD_CHECK_INTERVAL:
                    print(f"\n==== THRESHOLD CHECK TIME ({format_timestamp(current_time)}) ====")
                    print(f"Last check was {time_since_last_check:.1f} seconds ago")
                    print(f"Current threshold: {moisture_threshold}%")
                    
                    # Show threshold check notification
                    M5.Display.fillRect(30, 235, 260, 25, YELLOW)
                    M5.Display.setTextColor(BLACK, YELLOW)
                    M5.Display.setTextSize(1)
                    M5.Display.setCursor(80, 245)
                    M5.Display.print("CHECKING THRESHOLD")
                    
                    if reconnect_if_needed():
                        threshold_crossed = check_moisture_threshold()
                        last_threshold_check_time = current_time  # Update the last check time
                        print(f"Threshold check complete. Next check at: {format_timestamp(current_time + THRESHOLD_CHECK_INTERVAL)}")
                        
                        if threshold_crossed:
                            print("Threshold crossed - will stop monitoring until next scheduled reading")
                            
                            # Show threshold crossed message
                            M5.Display.fillRect(30, 235, 260, 25, GREEN)
                            M5.Display.setTextColor(BLACK, GREEN)
                            M5.Display.setTextSize(1)
                            M5.Display.setCursor(80, 245)
                            M5.Display.print("THRESHOLD REACHED")
            
            # Update time display periodically
            if current_time % 60 < 1:  # Update roughly once per minute
                current_datetime = rtc.datetime()
                time_str = format_time(current_datetime)
                M5.Display.fillRect(190, 50, 130, 15, BLACK)
                M5.Display.setTextColor(WHITE, BLACK)
                M5.Display.setTextSize(1)
                M5.Display.setCursor(190, 50)
                M5.Display.print(time_str)
            
            # Calculate time to next event (scheduled reading or threshold check)
            sleep_time = min(calculate_sleep_time(), 10)  # Max 10 seconds sleep for responsiveness
            
            # If we just did a reading, update display and add delay
            if schedule_triggered:
                display_all_data(soil_moisture, env_data, moisture_threshold, is_watering)
                time.sleep(5)
            
            # Sleep for a short time to maintain responsiveness
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print("Monitoring stopped by user")
    finally:
        # Clean disconnect
        if mqtt_client:
            mqtt_client.disconnect()
        
        # Show shutdown message
        M5.Display.fillScreen(BLACK)
        M5.Display.setTextColor(WHITE, BLACK)
        M5.Display.setTextSize(2)
        M5.Display.setCursor(60, 100)
        M5.Display.print("SYSTEM SHUTDOWN")
        
        print("Monitoring stopped")

if __name__ == "__main__":
    main()