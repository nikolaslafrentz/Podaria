import os
import webbrowser
import subprocess
import time
from core.authenticate_ee import authenticate_earth_engine
import core.galicia_satellite as galicia_satellite
from core.transmission_lines_to_geojson import create_transmission_lines_geojson
from core.generate_ee_tiles import generate_tile_urls

def main():
    print("\n===== Galicia Map Launcher =====\n")
    
    # Step 1: Generate satellite imagery data
    print("Step 1: Authenticating with Earth Engine...")
    authenticate_earth_engine()
    
    # Step 2: Generate fresh satellite tile URLs
    print("\nStep 2: Generating satellite tile URLs...")
    generate_tile_urls()
    
    # Step 3: Generate electrical grid data
    print("\nStep 3: Generating electrical grid data...")
    create_transmission_lines_geojson()
    
    # Step 4: Start a local web server
    print("\nStep 4: Starting local web server...")
    server_process = None
    
    try:
        # Use Python's built-in HTTP server
        cmd = ['python', '-m', 'http.server', '8000']
        server_process = subprocess.Popen(cmd)
        
        # Give the server a moment to start
        time.sleep(1)
        
        # Step 5: Open the map in the default browser
        print("\nStep 5: Opening map in browser...")
        # Default to the integrated map, but allow choosing others
        map_url = "http://localhost:8000/mapping/galicia_integrated_map.html"
        webbrowser.open(map_url)
        
        print("\n===== Launcher Complete =====\n")
        print("The Galicia map application is now running.")
        print("If the browser didn't open automatically, please manually open:")
        print("mapping/galicia_integrated_map.html")
        
        # Keep the server running until the user interrupts with Ctrl+C
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down the server...")
    
    finally:
        # Clean up the server process when done
        if server_process:
            server_process.terminate()

if __name__ == "__main__":
    main()
