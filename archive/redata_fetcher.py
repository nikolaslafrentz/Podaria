import requests
import json
import os
from datetime import datetime, timedelta

# REData API Base URL
BASE_URL = 'https://apidatos.ree.es/en/datos'

# Function to fetch electrical grid data
def fetch_grid_data():
    print("Fetching electrical grid data from REData API...")
    
    try:
        # Endpoint for transmission grid information
        endpoint = '/red-transporte/mapa-red'
        
        # Get grid data (no specific date needed)
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            # Save raw data for reference
            with open('data/redata_grid_raw.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Process into GeoJSON format
            grid_geojson = convert_grid_to_geojson(data)
            
            # Save processed GeoJSON
            with open('data/electrical_grid.geojson', 'w', encoding='utf-8') as f:
                json.dump(grid_geojson, f, ensure_ascii=False, indent=2)
            
            print(f"Grid data saved to data/electrical_grid.geojson")
            return grid_geojson
        else:
            print(f"Error fetching grid data: {response.status_code}")
            print(response.text)
            return None
    
    except Exception as e:
        print(f"Error fetching grid data: {str(e)}")
        return None

# Function to fetch power outage data
def fetch_outage_data():
    print("Fetching power outage data from REData API...")
    
    try:
        # Endpoint for incidents information
        endpoint = '/indisponibilidades/incidencias'
        
        # Set date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # Request parameters
        params = {
            'start_date': start_str,
            'end_date': end_str,
            'time_trunc': 'day'
        }
        
        # Make the request
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            # Save raw data for reference
            with open('data/redata_outages_raw.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Process into GeoJSON format
            outage_geojson = convert_outages_to_geojson(data)
            
            # Save processed GeoJSON
            with open('data/power_outages.geojson', 'w', encoding='utf-8') as f:
                json.dump(outage_geojson, f, ensure_ascii=False, indent=2)
            
            print(f"Outage data saved to data/power_outages.geojson")
            return outage_geojson
        else:
            print(f"Error fetching outage data: {response.status_code}")
            print(response.text)
            return None
    
    except Exception as e:
        print(f"Error fetching outage data: {str(e)}")
        return None

# Convert grid data to GeoJSON format
def convert_grid_to_geojson(data):
    # This is a placeholder - we need to adapt this based on the actual API response structure
    # Here we're assuming the API returns some kind of network structure that we convert to GeoJSON
    
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    # We would need to parse the actual API response and extract features
    # For now, let's create a simple placeholder with expected format
    # This will need to be updated once we have actual API response samples
    
    try:
        # Extract features based on the actual API response
        # This is a placeholder and will need adaptation
        if 'included' in data and isinstance(data['included'], list):
            for item in data['included']:
                if 'type' in item and item['type'] == 'line':
                    # Process transmission lines
                    if 'attributes' in item and 'coordinates' in item['attributes']:
                        coords = item['attributes']['coordinates']
                        feature = {
                            "type": "Feature",
                            "properties": {
                                "id": item.get('id', ''),
                                "name": item['attributes'].get('name', ''),
                                "voltage": item['attributes'].get('voltage', ''),
                                "type": "transmission_line"
                            },
                            "geometry": {
                                "type": "LineString",
                                "coordinates": coords
                            }
                        }
                        geojson["features"].append(feature)
                elif 'type' in item and item['type'] == 'substation':
                    # Process substations
                    if 'attributes' in item and 'coordinates' in item['attributes']:
                        coord = item['attributes']['coordinates']
                        feature = {
                            "type": "Feature",
                            "properties": {
                                "id": item.get('id', ''),
                                "name": item['attributes'].get('name', ''),
                                "type": "substation"
                            },
                            "geometry": {
                                "type": "Point",
                                "coordinates": coord
                            }
                        }
                        geojson["features"].append(feature)
    except Exception as e:
        print(f"Error processing grid data: {str(e)}")
    
    return geojson

# Convert outage data to GeoJSON format
def convert_outages_to_geojson(data):
    # This is a placeholder - we need to adapt this based on the actual API response structure
    
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    try:
        # Extract features based on the actual API response
        # This is a placeholder and will need adaptation
        if 'included' in data and isinstance(data['included'], list):
            for item in data['included']:
                if 'type' in item and item['type'] == 'incident':
                    # Process incidents/outages
                    if 'attributes' in item and 'coordinates' in item['attributes']:
                        coord = item['attributes']['coordinates']
                        feature = {
                            "type": "Feature",
                            "properties": {
                                "id": item.get('id', ''),
                                "name": item['attributes'].get('name', ''),
                                "start_date": item['attributes'].get('start_date', ''),
                                "end_date": item['attributes'].get('end_date', ''),
                                "status": item['attributes'].get('status', ''),
                                "type": "outage"
                            },
                            "geometry": {
                                "type": "Point",
                                "coordinates": coord
                            }
                        }
                        geojson["features"].append(feature)
    except Exception as e:
        print(f"Error processing outage data: {str(e)}")
    
    return geojson

def main():
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Fetch data from REData API
    grid_data = fetch_grid_data()
    outage_data = fetch_outage_data()
    
    print("\nData fetching complete!")
    print("You can now integrate this data with your map using the layers.")

if __name__ == "__main__":
    main()
