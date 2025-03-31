import os
import subprocess
import time
import webbrowser

def main():
    print("\n===== Galicia Map Launcher =====\n")
    
    # Step 1: Run the map data generation script
    print("Step 1: Generating satellite imagery data...")
    try:
        subprocess.run(["python", "core/galicia_map.py"], check=True)
        print("u2713 Satellite data generated successfully!")
    except subprocess.CalledProcessError as e:
        print(f"u2717 Error generating satellite data: {e}")
        return
    
    # Step 2: Attempt to get grid data (but continue even if it fails)
    print("\nStep 2: Attempting to fetch electrical grid data...")
    try:
        # First try to fetch data from REData API
        subprocess.run(["python", "core/redata_api.py"], check=False)
        print("u2713 Grid data fetch attempt completed")
        
        # Then convert the data to GeoJSON format for map display
        subprocess.run(["python", "core/transmission_lines_to_geojson.py"], check=True)
        print("u2713 Transmission lines converted to GeoJSON format")
    except Exception as e:
        print(f"u2717 Error with grid data processing: {e}")
    
    # Step 3: Open the map viewer
    print("\nStep 3: Opening map viewer in browser...")
    try:
        # Get absolute path to the map viewer
        map_path = os.path.join(os.getcwd(), "mapping", "galicia_map_viewer.html")
        map_url = f"file:///{map_path.replace(os.path.sep, '/')}"
        
        # Open the URL in the default browser
        webbrowser.open(map_url)
        print(f"u2713 Map viewer opened at: {map_url}")
    except Exception as e:
        print(f"u2717 Error opening map viewer: {e}")
        print("  Please manually open mapping/galicia_map_viewer.html in your browser")
    
    print("\n===== Launcher Complete =====\n")
    print("The Galicia map application is now running.")
    print("If the browser didn't open automatically, please manually open:")
    print("mapping/galicia_map_viewer.html")

if __name__ == "__main__":
    main()
