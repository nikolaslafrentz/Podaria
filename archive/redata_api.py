import requests
import pandas as pd
import json
import os

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Function to fetch data from REData API
def fetch_data(url, params, filename):
    print(f"Fetching data from {url} with params: {params}")

    try:
        response = requests.get(url, params=params)
        
        # Check if the response is valid
        if response.status_code != 200:
            print(f"Error: API request failed with status code {response.status_code}")
            print("Response text:", response.text)
            return None
        
        # Print raw response for debugging
        print("Raw API Response:", response.text[:200])  # Print first 200 characters

        # Try parsing JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("Error: Failed to parse JSON. Response might be empty.")
            return None

        # Save raw response
        raw_filepath = f'data/{filename}_raw.json'
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Raw data saved to {raw_filepath}")

        # Check if data contains expected keys
        if 'included' not in data or not data['included']:
            print("Warning: No relevant data found in API response.")
            return None

        # Extract the relevant data
        values = data['included'][0]['attributes']['values']
        df = pd.DataFrame(values)

        # Convert datetime strings to pandas datetime objects
        df['datetime'] = pd.to_datetime(df['datetime'])

        # Save to CSV
        csv_filepath = f'data/{filename}.csv'
        df.to_csv(csv_filepath, index=False)
        print(f"Processed data saved to {csv_filepath}")

        return df

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# Define API endpoints and parameters
api_endpoints = {
    "transmission_lines": "https://apidatos.ree.es/en/datos/transporte/kilometros-lineas",
    "substations": "https://apidatos.ree.es/en/datos/transporte/capacidad-transformacion",
    "outages": "https://apidatos.ree.es/en/datos/indisponibilidades/tasa-indisponibilidad",
}

common_params = {
    "start_date": "2024-01-01T00:00",  # Use current or past year instead of future
    "end_date": "2024-12-31T23:59",
    "time_trunc": "month",
    "geo_trunc": "electric_system",
    "geo_limit": "ccaa",
    "geo_ids": "17",  # Galicia region ID
}

# Fetch each dataset
def main():
    print("\nFetching REData API data for Galicia electrical grid and outages...\n")

    results = {}
    for name, url in api_endpoints.items():
        print(f"\nFetching {name.replace('_', ' ')}...")
        results[name] = fetch_data(url, common_params, name)

    # Summary
    print("\n===== Data Fetching Summary =====")
    for name, result in results.items():
        print(f"{name.replace('_', ' ').title()}: {'Success' if result is not None else 'Failed'}")

    print("\nData fetching complete. Check the 'data' directory for results.")

if __name__ == "__main__":
    main()
