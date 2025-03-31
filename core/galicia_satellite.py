import ee
import os
import sys

def main():
    try:
        # Step 1: Authenticate with Earth Engine
        print("Step 1: Authenticating with Google Earth Engine...")
        ee.Authenticate()
        
        # Step 2: Initialize Earth Engine with the correct project ID
        print("Step 2: Initializing Earth Engine...")
        ee.Initialize(project="ee-nikolaslafrentz")
        print("Earth Engine initialized successfully!")
        
        # Step 3: Define the Galicia region
        print("Step 3: Defining Galicia region...")
        galicia = ee.Geometry.Polygon([
            [[-9.301758, 41.862611],
             [-9.301758, 43.789203],
             [-6.767578, 43.789203],
             [-6.767578, 41.862611]]
        ])
        
        # Step 4: Get Sentinel-2 surface reflectance data
        print("Step 4: Fetching Sentinel-2 data for the region...")
        sentinel = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterBounds(galicia) \
            .filterDate('2022-06-01', '2022-09-30') \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            
        print(f"Found {sentinel.size().getInfo()} Sentinel-2 images for the specified time period.")
        
        if sentinel.size().getInfo() == 0:
            print("No images found! Try expanding the date range or relaxing cloud coverage restriction.")
            return
        
        # Step 5: Create a composite image
        print("Step 5: Creating a median composite from all images...")
        composite = sentinel.median()
        
        # Step 6: Export the image to Google Drive
        print("Step 6: Setting up export task to Google Drive...")
        # Select RGB bands
        rgb_image = composite.select(['B4', 'B3', 'B2'])
        
        # Create the export task
        task = ee.batch.Export.image.toDrive(
            image=rgb_image,
            description='Galicia_Sentinel2_RGB',
            folder='Earth_Engine_Exports',
            region=galicia,
            scale=10,  # 10m resolution for Sentinel-2
            maxPixels=1e9
        )
        
        # Step 7: Start the export task
        print("Step 7: Starting export task...")
        task.start()
        
        # Check and print task status
        print("\nExport task started successfully!")
        print("The imagery will be available in your Google Drive")
        print("Folder: Earth_Engine_Exports")
        print("Filename: Galicia_Sentinel2_RGB.tif")
        print("\nYou can check the status of your task in the Earth Engine Code Editor:")
        print("https://code.earthengine.google.com/tasks")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have authenticated with Google Earth Engine")
        print("2. Verify that your Google account has access to Earth Engine")
        print("3. Check your internet connection")
        print("4. Verify that your project ID is correct: ee-nikolaslafrentz")
        print("\nFor detailed information on Earth Engine setup, visit:")
        print("https://developers.google.com/earth-engine/guides/python_install")

if __name__ == "__main__":
    main()
