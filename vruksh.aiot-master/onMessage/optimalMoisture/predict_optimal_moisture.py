from model1.recommend_soil_moisture import recommend_soil_moisture as inference

def predict_optimal_moisture(payload):
    """
    Function to predict the optimal moisture level based on the given conditions.
    """
   
    conditions = {
        "temp": payload.get("temp"),
        "humidity": payload.get("humidity"),
        "pH": payload.get("pH"),
        "nitrogen": payload.get("nitrogen"),
        "plant_id": payload.get("plant_id")
    }
    
    # Call the inference function from model1
    optimal_moisture = inference(
        conditions["temp"],
        conditions["humidity"],
        conditions["pH"],
        conditions["nitrogen"],
        conditions["plant_id"]
    )
    
    return optimal_moisture