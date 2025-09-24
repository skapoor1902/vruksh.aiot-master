import pickle
import pandas as pd
import numpy as np

# Load the saved model
with open('water_prediction_model.pkl', 'rb') as file:
    model = pickle.load(file)

def predict_water_quantity(data):
    """
    Make predictions using the loaded model
    
    Parameters:
    data (dict or pd.DataFrame): Input data with required features
    
    Returns:
    float: Predicted water quantity in ml
    """
    if isinstance(data, dict):
        data = pd.DataFrame([data])
    return model.predict(data)[0]

# Test Case 1: Hot, dry summer day
test_case_1 = {
    'current_soil_moisture': 30.0,  # Low moisture
    'target_soil_moisture': 65.0,
    'soil_type': 'Sandy',
    'soil_depth_in_pot': 20.0,
    'soil_compaction_level': 3,
    'soil_pH': 6.5,
    'nitrogen_level': 5.0,
    'ambient_temperature': 32.0,  # Hot
    'relative_humidity': 40.0,    # Dry
    'sunlight_exposure': 8.0,
    'plant_size': 'Medium',
    'leaf_surface_area': 200.0,
    'plant_type': 'Tropical',
    'number_of_leaves': 20,
    'time_since_last_watering': 48.0,
    'time_of_day': 14,
    'season': 'Summer'
}

# Test Case 2: Cool, humid winter day
test_case_2 = {
    'current_soil_moisture': 55.0,  # Moderate moisture
    'target_soil_moisture': 60.0,
    'soil_type': 'Clay',
    'soil_depth_in_pot': 15.0,
    'soil_compaction_level': 4,
    'soil_pH': 7.0,
    'nitrogen_level': 4.0,
    'ambient_temperature': 18.0,  # Cool
    'relative_humidity': 70.0,    # Humid
    'sunlight_exposure': 4.0,
    'plant_size': 'Small',
    'leaf_surface_area': 100.0,
    'plant_type': 'Succulent',
    'number_of_leaves': 10,
    'time_since_last_watering': 72.0,
    'time_of_day': 10,
    'season': 'Winter'
}

# Test Case 3: Moderate spring day
test_case_3 = {
    'current_soil_moisture': 45.0,  # Moderate moisture
    'target_soil_moisture': 60.0,
    'soil_type': 'Loam',
    'soil_depth_in_pot': 25.0,
    'soil_compaction_level': 2,
    'soil_pH': 6.0,
    'nitrogen_level': 6.0,
    'ambient_temperature': 24.0,  # Moderate
    'relative_humidity': 55.0,    # Moderate
    'sunlight_exposure': 6.0,
    'plant_size': 'Large',
    'leaf_surface_area': 300.0,
    'plant_type': 'Herb',
    'number_of_leaves': 30,
    'time_since_last_watering': 24.0,
    'time_of_day': 12,
    'season': 'Spring'
}

# Test Case 4: Critical low moisture
test_case_4 = {
    'current_soil_moisture': 15.0,  # Very low moisture
    'target_soil_moisture': 70.0,
    'soil_type': 'Peat',
    'soil_depth_in_pot': 18.0,
    'soil_compaction_level': 2,
    'soil_pH': 5.5,
    'nitrogen_level': 7.0,
    'ambient_temperature': 28.0,
    'relative_humidity': 45.0,
    'sunlight_exposure': 7.0,
    'plant_size': 'Large',
    'leaf_surface_area': 400.0,
    'plant_type': 'Tropical',
    'number_of_leaves': 25,
    'time_since_last_watering': 96.0,
    'time_of_day': 16,
    'season': 'Summer'
}

# Create a function to explain the prediction
def explain_prediction(test_case, prediction):
    moisture_diff = test_case['target_soil_moisture'] - test_case['current_soil_moisture']
    
    explanation = f"""
    Prediction Analysis:
    -------------------
    Predicted water quantity: {prediction:.2f} ml
    
    Key Factors:
    - Moisture difference: {moisture_diff:.1f}% (Current: {test_case['current_soil_moisture']}%, Target: {test_case['target_soil_moisture']}%)
    - Temperature: {test_case['ambient_temperature']}°C
    - Humidity: {test_case['relative_humidity']}%
    - Soil type: {test_case['soil_type']}
    - Plant type: {test_case['plant_type']}
    - Time since last watering: {test_case['time_since_last_watering']} hours
    - Season: {test_case['season']}
    """
    return explanation

# Test all cases
test_cases = {
    "Hot Summer Day": test_case_1,
    "Cool Winter Day": test_case_2,
    "Moderate Spring Day": test_case_3,
    "Critical Low Moisture": test_case_4
}

print("Model Testing Results:")
print("=====================")

for case_name, test_case in test_cases.items():
    prediction = predict_water_quantity(test_case)
    print(f"\nTest Case: {case_name}")
    print(explain_prediction(test_case, prediction))

# Function to test custom input
def test_custom_input():
    print("\nCustom Input Test")
    print("=================")
    
    # Get user input for key parameters
    try:
        current_moisture = float(input("Enter current soil moisture (%): "))
        target_moisture = float(input("Enter target soil moisture (%): "))
        temperature = float(input("Enter temperature (°C): "))
        humidity = float(input("Enter humidity (%): "))
        soil_type = input("Enter soil type (Clay/Loam/Sandy/Silt/Peat): ")
        plant_type = input("Enter plant type (Succulent/Tropical/Herb/Flowering): ")
        
        # Create test case with default values for other parameters
        custom_case = {
            'current_soil_moisture': current_moisture,
            'target_soil_moisture': target_moisture,
            'soil_type': soil_type,
            'soil_depth_in_pot': 20.0,
            'soil_compaction_level': 3,
            'soil_pH': 6.5,
            'nitrogen_level': 5.0,
            'ambient_temperature': temperature,
            'relative_humidity': humidity,
            'sunlight_exposure': 6.0,
            'plant_size': 'Medium',
            'leaf_surface_area': 200.0,
            'plant_type': plant_type,
            'number_of_leaves': 20,
            'time_since_last_watering': 24.0,
            'time_of_day': 12,
            'season': 'Summer'
        }
        
        prediction = predict_water_quantity(custom_case)
        print(explain_prediction(custom_case, prediction))
        
    except ValueError:
        print("Invalid input. Please enter numeric values for measurements.")
    except Exception as e:
        print(f"Error: {str(e)}")

# Allow user to test custom input
while True:
    response = input("\nWould you like to test a custom input? (yes/no): ")
    if response.lower() == 'yes':
        test_custom_input()
    else:
        break

print("\nTesting completed!")