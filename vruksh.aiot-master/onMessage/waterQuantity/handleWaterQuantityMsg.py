# Send water quantity data to the database

# from pymongo import MongoClient
# from config import mongo_uri, mongo_db, mongo_collection

# Use sqlite3 to store the data
import sqlite3

def send_water_quantity_data(payload):
    """
    Function to send water quantity data to the database.
    """
    
    # Connect to the SQLite database
    conn = sqlite3.connect('water_quantity.db')
    cursor = conn.cursor()
    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_quantity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            water_quantity REAL,
            temp REAL,
            humidity REAL,
            pH REAL,
            nitrogen REAL,
            plant_id TEXT,
            initial_moisture REAL,
            soil_moisture_now REAL
        )
    ''')
    # Commit the changes
    conn.commit()
    
    # Prepare the data to be inserted
    data = {
        "water_quantity": payload.get("water_quantity"),
        "temp": payload.get("temp"),
        "humidity": payload.get("humidity"),
        "pH": payload.get("pH"),
        "nitrogen": payload.get("nitrogen"),
        "plant_id": payload.get("plant_id"),
        "initial_moisture": payload.get("initial_moisture"),
        "soil_moisture_now": payload.get("soil_moisture_now")
    }
        
    # Insert the data into the database
    cursor.execute('''
        INSERT INTO water_quantity (water_quantity, temp, humidity, pH, nitrogen, plant_id, initial_moisture, soil_moisture_now)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data["water_quantity"], data["temp"], data["humidity"], data["pH"], data["nitrogen"], data["plant_id"], data["initial_moisture"], data["soil_moisture_now"]))
    # Commit the changes
    conn.commit()
    # Close the connection
    conn.close()
    
    # return the inserted data
    return data