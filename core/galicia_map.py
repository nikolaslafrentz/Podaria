import ee

def main():
    try:
        # Step 1: Initialize Earth Engine
        print("Initializing Earth Engine...")
        try:
            ee.Initialize(project="ee-nikolaslafrentz")
            print("Earth Engine initialized successfully!")
        except Exception as e:
            print(f"Error initializing: {e}")
            print("Attempting to authenticate...")
            ee.Authenticate()
            ee.Initialize(project="ee-nikolaslafrentz")
            print("Earth Engine initialized after authentication")
        
        # Step 2: Define the Galicia region
        print("Defining Galicia region...")
        galicia = ee.Geometry.Polygon([
            [[-9.301758, 41.862611],
             [-9.301758, 43.789203],
             [-6.767578, 43.789203],
             [-6.767578, 41.862611]]
        ])
        
        # Step 3: Get Sentinel-2 surface reflectance data
        print("Fetching Sentinel-2 data for the region...")
        sentinel = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterBounds(galicia) \
            .filterDate('2023-01-01', '2023-12-31') \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            
        print(f"Found {sentinel.size().getInfo()} Sentinel-2 images for the specified time period.")
        
        if sentinel.size().getInfo() == 0:
            print("No images found! Try expanding the date range or relaxing cloud coverage restriction.")
            return
        
        # Step 4: Create a composite image
        print("Creating a median composite from all images...")
        composite = sentinel.median()
        
        # Step 5: Generate map URL
        print("Generating map URL...")
        # RGB visualization parameters
        rgb_vis = {'min': 0, 'max': 3000, 'bands': ['B4', 'B3', 'B2']}
        
        # Get map ID and URL
        map_id = composite.getMapId(rgb_vis)
        mapurl = map_id['tile_fetcher'].url_format
        
        print("\nMap URL generated successfully!")
        print("\nYou can use this tile URL in web mapping applications:")
        print(mapurl)
        print("\nVisualization parameters:")
        print(rgb_vis)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have authenticated with Google Earth Engine")
        print("2. Verify that your Google account has access to Earth Engine")
        print("3. Check your internet connection")
        print("4. Verify that your project ID is correct: ee-nikolaslafrentz")

if __name__ == "__main__":
    main()
