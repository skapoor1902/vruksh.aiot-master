
![PHOTO-2025-04-16-18-27-36](https://github.com/user-attachments/assets/8d950d0e-1d4e-4203-9a91-7d66a9c02429)


# 🌱 vruksh.aiot - Automated Plant Watering System

This project implements a smart, automated plant watering system using an IoT device and a Python-based backend. The system uses sensor data to predict and manage optimal watering quantities for plants, helping ensure efficient water usage.

## 🚀 Project Overview

- **IoT Device**: M5Stack Core2 with an ESP32 processor
- **Backend Language**: Python
- **MQTT Broker**: [EMQX Cloud](https://www.emqx.com/en/cloud)
- **MQTT Client Library**: `paho-mqtt`
- **Database**: SQLite for local logging of water dispensed, useful for training water quantity prediction models.
- **Device Firmware**: MicroPython
- **ML Models**: Random forest regressors are used for moisture level and water quantity prediction based on live soil and weather conditions.

## 🧰 Prerequisites

- Python 3.8+
- M5Stack Core2 flashed with MicroPython
- An EMQX Cloud MQTT broker instance

## 🔧 Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/heet434/vruksh.aiot.git
   cd vruksh.aiot
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server**
   ```bash
   python server.py
   ```

5. **Client side - ESP32 (upide)**
   Run the .py file in upide. It contains the code for reading the soil moisture sensor data and then after processing, publishes data to the MQTT broker on the topics "mqtt/get_optimal_moisture" and "mqtt/moisture_alert" and subscribes to another topic from the other client to get the optimal threshold. It has scheduled times for reading 3 times a day. 

## 📡 IoT Device

- **Platform**: M5Stack Core2
- **Firmware**: MicroPython
- **Broker**: EMQX Cloud

The IoT device reads the soil moisture sensor, publishes the readings via MQTT, and receives watering commands from the backend.

## 📊 Features

- Real-time soil moisture data collection
- Smart water quantity prediction using trained ML models
- MQTT-based bi-directional communication
- Local database logging of water dispensed
  
![PHOTO-2025-04-16-18-24-28](https://github.com/user-attachments/assets/e6ca8af1-5f55-425b-a140-e67fa9635b52)
![PHOTO-2025-04-16-18-29-39](https://github.com/user-attachments/assets/0d54abc0-6fef-41a2-9ce8-fb48e7e66ae8)


