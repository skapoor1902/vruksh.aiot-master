import joblib
import numpy as np


model = joblib.load("model1/soil_moisture_rf_model.pkl")

def recommend_soil_moisture(temp, humidity, pH, nitrogen, plant_id):
    input_data = np.array([[temp, humidity, pH, nitrogen, plant_id]])
    predicted_moisture = model.predict(input_data)[0]
    return predicted_moisture


# if __name__ == "__main__":
#     print(" Soil Moisture Recommender\n")
    
#     temp = float(input("Enter Ambient Temperature (°C): "))
#     humidity = float(input("Enter Humidity (%): "))
#     pH = float(input("Enter Soil pH: "))
#     nitrogen = float(input("Enter Nitrogen Level: "))
#     plant_id = int(input("Enter Plant ID: "))

#     moisture = recommend_soil_moisture(temp, humidity, pH, nitrogen, plant_id)
#     print(moisture)
    