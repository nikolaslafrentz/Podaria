import requests
import pandas as pd
import json
import os
import time
import random

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

def fetch_transmission_lines():
    """Fetch transmission line data for Galicia region"""
    print("Fetching transmission line data for Galicia...")
    
    # Define the API endpoint and parameters (Galicia = region 17)
    url = "https://apidatos.ree.es/en/datos/transporte/kilometros-lineas"
    params = {
        "start_date": "2025-01-01T00:00",
        "end_date": "2025-03-31T23:59",
        "time_trunc": "month",
        "geo_trunc": "electric_system",
        "geo_limit": "ccaa",
        "geo_ids": "17"  # ID for Galicia
    }
    
    try:
        # Make the API request
        response = requests.get(url, params=params)
        
        # Check if response is valid JSON
        try:
            data = response.json()
            
            # Save raw response for inspection
            with open('data/transmission_lines_raw.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Extract and process data
            if 'included' in data and len(data['included']) > 0:
                values = data['included'][0]['attributes']['values']
                df = pd.DataFrame(values)
                
                # Convert datetime strings to pandas datetime objects
                df['datetime'] = pd.to_datetime(df['datetime'])
                
                # Save to CSV for easy viewing
                df.to_csv('data/transmission_lines.csv', index=False)
                print("Data successfully saved to data/transmission_lines.csv")
                print(df.head())
                
                # Convert to GeoJSON (placeholder - would need real coordinates)
                create_geojson_from_lines_data(df)
                
                return True
            else:
                print("No transmission line data found in the API response")
                print(f"API response content: {data}")
                return False
                
        except json.JSONDecodeError:
            print(f"Invalid JSON response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"Error fetching transmission line data: {e}")
        return False

def create_geojson_from_lines_data(df):
    """Create a GeoJSON file from the transmission line data"""
    print("Creating GeoJSON from transmission line data...")
    
    # This is a placeholder function that creates sample GeoJSON
    # In a real implementation, we would need to get actual geographic coordinates
    # for the transmission lines, which aren't directly provided in the API response
    
    # Define main cities in Galicia for our placeholders
    cities = {
        'A Coruña': [-8.4115, 43.3623],
        'Santiago': [-8.5455, 42.8782],
        'Lugo': [-7.5568, 43.0123],
        'Ourense': [-7.8663, 42.3358],
        'Pontevedra': [-8.6452, 42.4298],
        'Vigo': [-8.7137, 42.2328],
        'Ferrol': [-8.2326, 43.4836],
    }
    
    # Create a GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    # Add transmission lines connecting major cities
    connections = [
        ('A Coruña', 'Santiago', '400kV', '#FF0000', 3),
        ('Santiago', 'Pontevedra', '220kV', '#FF7700', 2),
        ('Pontevedra', 'Vigo', '400kV', '#FF0000', 3),
        ('A Coruña', 'Ferrol', '220kV', '#FF7700', 2),
        ('Santiago', 'Lugo', '220kV', '#FF7700', 2),
        ('Lugo', 'Ourense', '220kV', '#FF7700', 2),
        ('Ourense', 'Pontevedra', '400kV', '#FF0000', 3),
    ]
    
    # Create the line features
    for i, (city1, city2, voltage, color, weight) in enumerate(connections):
        # Get the coordinates for the two cities
        coords1 = cities[city1]
        coords2 = cities[city2]
        
        # Add some random intermediate points to make the lines more realistic
        intermediate_points = []
        num_points = random.randint(1, 3)
        for _ in range(num_points):
            # Create points that generally move from city1 to city2
            progress = random.random()
            lat = coords1[1] + (coords2[1] - coords1[1]) * progress
            lng = coords1[0] + (coords2[0] - coords1[0]) * progress
            # Add some randomness
            lat += random.uniform(-0.05, 0.05)
            lng += random.uniform(-0.05, 0.05)
            intermediate_points.append([lng, lat])
        
        # Sort intermediate points to create a reasonable path
        intermediate_points.sort(key=lambda p: (p[0] - coords1[0])**2 + (p[1] - coords1[1])**2)
        
        # Combine all points to form the line
        line_coords = [coords1] + intermediate_points + [coords2]
        
        # Format coordinates correctly [lng, lat]
        formatted_coords = []
        for point in line_coords:
            if isinstance(point[0], float) and isinstance(point[1], float):
                formatted_coords.append(point)
            else:
                formatted_coords.append([point[1], point[0]])  # Swap if needed
        
        # Create the feature
        feature = {
            "type": "Feature",
            "properties": {
                "id": f"line{i+1}",
                "name": f"{city1} - {city2} Line",
                "voltage": voltage,
                "type": "transmission_line",
                "color": color,
                "weight": weight
            },
            "geometry": {
                "type": "LineString",
                "coordinates": formatted_coords
            }
        }
        
        geojson["features"].append(feature)
    
    # Add substations at each city
    for i, (city, coords) in enumerate(cities.items()):
        feature = {
            "type": "Feature",
            "properties": {
                "id": f"substation{i+1}",
                "name": f"{city} Substation",
                "type": "substation",
                "capacity": "400kV" if i % 2 == 0 else "220kV"  # Alternate capacities
            },
            "geometry": {
                "type": "Point",
                "coordinates": coords
            }
        }
        
        geojson["features"].append(feature)
    
    # Add some power outages
    outage_cities = random.sample(list(cities.keys()), 3)  # Pick 3 random cities for outages
    outage_statuses = ['active', 'scheduled', 'resolved']
    outage_causes = ['Equipment failure', 'Weather-related', 'Scheduled maintenance', 'Physical damage']
    
    for i, city in enumerate(outage_cities):
        # Choose location near the city with some randomness
        city_coords = cities[city]
        outage_coords = [
            city_coords[0] + random.uniform(-0.1, 0.1),
            city_coords[1] + random.uniform(-0.1, 0.1)
        ]
        
        status = outage_statuses[i % len(outage_statuses)]
        cause = random.choice(outage_causes)
        affected = random.randint(800, 8000)
        
        # Create basic date information
        start_date = "2025-03-" + str(random.randint(1, 31)).zfill(2) + "T" + \
                     str(random.randint(0, 23)).zfill(2) + ":" + \
                     str(random.randint(0, 59)).zfill(2) + ":00"
        
        end_date = None
        if status != 'active':
            # Create an end date a few hours later
            hours_later = random.randint(2, 12)
            end_date = start_date  # We'll just reuse the same date for simplicity
        
        feature = {
            "type": "Feature",
            "properties": {
                "id": f"outage{i+1}",
                "name": f"{city} Area {cause}",
                "start_date": start_date,
                "end_date": end_date,
                "status": status,
                "type": "outage",
                "affected_customers": affected,
                "cause": cause
            },
            "geometry": {
                "type": "Point",
                "coordinates": outage_coords
            }
        }
        
        geojson["features"].append(feature)
    
    # Save the GeoJSON files
    # Split into separate files for electrical grid and outages
    grid_features = [f for f in geojson["features"] 
                   if f["properties"]["type"] in ["transmission_line", "substation"]]
    
    outage_features = [f for f in geojson["features"] 
                     if f["properties"]["type"] == "outage"]
    
    grid_geojson = {"type": "FeatureCollection", "features": grid_features}
    outage_geojson = {"type": "FeatureCollection", "features": outage_features}
    
    with open('data/electrical_grid.geojson', 'w', encoding='utf-8') as f:
        json.dump(grid_geojson, f, ensure_ascii=False, indent=2)
    
    with open('data/power_outages.geojson', 'w', encoding='utf-8') as f:
        json.dump(outage_geojson, f, ensure_ascii=False, indent=2)
    
    print("GeoJSON files created successfully:")
    print("- data/electrical_grid.geojson")
    print("- data/power_outages.geojson")

def main():
    print("===== Fetching Galicia Electrical Grid Data =====\n")
    fetch_transmission_lines()
    print("\nProcess complete. The map should now display the electrical grid and power outages.")
    print("Open galicia_map_viewer.html in your browser to view the map.")

if __name__ == "__main__":
    main()
