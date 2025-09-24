# Script to extract water quantity data from water_quantity.db in csv format

import sqlite3
import pandas as pd
import json
import os

def extract_water_quantity_data():
    """
    Function to extract water quantity data from the SQLite database and save it as a CSV file.
    """
    
    # Connect to the SQLite database
    conn = sqlite3.connect('water_quantity.db')
    
    # Query to select all data from the water_quantity table
    query = "SELECT * FROM water_quantity"
    
    # Read the data into a pandas DataFrame
    df = pd.read_sql_query(query, conn)
    
    # Close the connection
    conn.close()
    
    # Save the DataFrame to a CSV file
    csv_file_path = 'water_quantity_data.csv'
    df.to_csv(csv_file_path, index=False)
    
    print(f"Water quantity data extracted and saved to {csv_file_path}")
    return csv_file_path

if __name__ == "__main__":
    extract_water_quantity_data()
