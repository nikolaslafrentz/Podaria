import ee
import json
import os
import time

def main():
    print("Starting background download of Galicia data...")
    
    # Authenticate and initialize Earth Engine
    try:
        ee.Initialize(project="ee-nikolaslafrentz")
        print("Earth Engine initialized successfully")
    except Exception as e:
        print(f"Error initializing Earth Engine: {e}")
        ee.Authenticate()
        ee.Initialize(project="ee-nikolaslafrentz")
        print("Earth Engine initialized after authentication")
    
    # Define the Galicia region boundaries (approximate coordinates)
    galicia = ee.Geometry.Polygon([
        [[-9.301758, 41.862611],
         [-9.301758, 43.789203],
         [-6.767578, 43.789203],
         [-6.767578, 41.862611]]
    ])
    
    # Define time periods (monthly from 2018-2023)
    time_periods = []
    
    # Generate monthly periods for multiple years
    years = [2018, 2019, 2020, 2021, 2022, 2023]
    months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    
    for year in years:
        for month in months:
            # Determine last day of month
            if month in [4, 6, 9, 11]:
                last_day = 30
            elif month == 2:
                # Simple leap year check
                if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                    last_day = 29
                else:
                    last_day = 28
            else:
                last_day = 31
            
            # Format month and create period
            month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month-1]
            period = {
                'start': f'{year}-{month:02d}-01',
                'end': f'{year}-{month:02d}-{last_day}',
                'name': f'{month_name} {year}'
            }
            time_periods.append(period)
    
    # Define spectral indices with descriptions
    spectral_indices = [
        {
            'id': 'rgb',
            'name': 'True Color (RGB)',
            'description': 'Natural color representation as seen by human eyes.',
            'vis_params': {'min': 0, 'max': 3000, 'bands': ['B4', 'B3', 'B2']}
        },
        {
            'id': 'ndvi',
            'name': 'NDVI (Vegetation Health)',
            'description': 'Normalized Difference Vegetation Index: Measures vegetation health and density.',
            'vis_params': {'min': -0.2, 'max': 0.8, 'palette': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850']}
        },
        {
            'id': 'ndwi',
            'name': 'NDWI (Water Bodies)',
            'description': 'Normalized Difference Water Index: Highlights water bodies and moisture content.',
            'vis_params': {'min': -0.5, 'max': 0.5, 'palette': ['#a52a2a', '#fcf8e3', '#86c4ec', '#0d47a1']}
        },
        {
            'id': 'ndbi',
            'name': 'NDBI (Built-up Areas)',
            'description': 'Normalized Difference Built-up Index: Highlights urban and built-up areas.',
            'vis_params': {'min': -0.5, 'max': 0.5, 'palette': ['#1a9641', '#a6d96a', '#f4f466', '#d7191c']}
        },
        {
            'id': 'nbr',
            'name': 'NBR (Burn Scars)',
            'description': 'Normalized Burn Ratio: Detects burn scars and fire damage.',
            'vis_params': {'min': -1, 'max': 1, 'palette': ['#1a9850', '#66bd63', '#a6d96a', '#d9ef8b', '#fee08b', '#fdae61', '#f46d43', '#d73027']}
        }
    ]
    
    # Create data directory if it doesn't exist
    data_dir = "galicia_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Process each time period
    for period in time_periods:
        print(f"Processing {period['name']}...")
        
        # Check if this period already exists in saved data
        period_filename = os.path.join(data_dir, f"galicia_{period['start']}_{period['end']}.json")
        if os.path.exists(period_filename):
            print(f"  Data for {period['name']} already exists, skipping")
            continue
        
        # Get Sentinel-2 surface reflectance data for the period
        sentinel = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterBounds(galicia) \
            .filterDate(period['start'], period['end']) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
        
        image_count = sentinel.size().getInfo()
        print(f"  Found {image_count} Sentinel-2 images")
        
        # Skip if no images found
        if image_count == 0:
            print(f"  No images found for {period['name']}, skipping")
            continue
        
        # Create a median composite for this period
        composite = sentinel.median()
        
        # Initialize period data
        period_data = {
            'name': period['name'],
            'start': period['start'],
            'end': period['end'],
            'imageCount': image_count,
            'indices': []
        }
        
        # Process each spectral index
        for index in spectral_indices:
            print(f"  Processing {index['name']} for {period['name']}...")
            try:
                if index['id'] == 'rgb':
                    # RGB true color image
                    index_image = composite
                    # Calculate average RGB values across the region
                    rgb_stats = composite.select(['B4', 'B3', 'B2']).reduceRegion({
                        'reducer': ee.Reducer.mean(),
                        'geometry': galicia,
                        'scale': 1000,
                        'maxPixels': 1e9
                    }).getInfo()
                    
                    # Calculate a simple RGB score (0-100 scale)
                    r_val = rgb_stats['B4'] / 3000 * 100 if 'B4' in rgb_stats else 0
                    g_val = rgb_stats['B3'] / 3000 * 100 if 'B3' in rgb_stats else 0
                    b_val = rgb_stats['B2'] / 3000 * 100 if 'B2' in rgb_stats else 0
                    rgb_score = round((r_val + g_val + b_val) / 3)
                    
                    # Store the numerical score
                    metric_score = {
                        'value': rgb_score,
                        'description': f'Average RGB brightness: {rgb_score}/100'
                    }
                    
                elif index['id'] == 'ndvi':
                    # NDVI - Normalized Difference Vegetation Index
                    # (NIR - Red) / (NIR + Red)
                    index_image = composite.normalizedDifference(['B8', 'B4']).rename('NDVI')
                    
                    # Calculate average NDVI across the region
                    ndvi_stats = index_image.reduceRegion({
                        'reducer': ee.Reducer.mean(),
                        'geometry': galicia,
                        'scale': 1000,
                        'maxPixels': 1e9
                    }).getInfo()
                    
                    # Get the NDVI value and convert to 0-100 scale
                    ndvi_value = ndvi_stats.get('NDVI', 0)
                    # NDVI typically ranges from -1 to 1, with healthy vegetation > 0.2
                    ndvi_score = round(((ndvi_value + 0.2) / 1.2) * 100)
                    ndvi_score = max(0, min(100, ndvi_score))  # Clamp to 0-100
                    
                    # Store the numerical score
                    metric_score = {
                        'value': ndvi_score,
                        'description': f'Vegetation Health Score: {ndvi_score}/100 (Raw NDVI: {ndvi_value:.3f})'
                    }
                    
                elif index['id'] == 'ndwi':
                    # NDWI - Normalized Difference Water Index
                    # (Green - NIR) / (Green + NIR)
                    index_image = composite.normalizedDifference(['B3', 'B8']).rename('NDWI')
                    
                    # Calculate average NDWI across the region
                    ndwi_stats = index_image.reduceRegion({
                        'reducer': ee.Reducer.mean(),
                        'geometry': galicia,
                        'scale': 1000,
                        'maxPixels': 1e9
                    }).getInfo()
                    
                    # Get the NDWI value and convert to 0-100 scale (water presence)
                    ndwi_value = ndwi_stats.get('NDWI', 0)
                    # NDWI typically ranges from -1 to 1, with water bodies > 0
                    ndwi_score = round(((ndwi_value + 0.5) / 1.0) * 100)
                    ndwi_score = max(0, min(100, ndwi_score))  # Clamp to 0-100
                    
                    # Store the numerical score
                    metric_score = {
                        'value': ndwi_score,
                        'description': f'Water Presence Score: {ndwi_score}/100 (Raw NDWI: {ndwi_value:.3f})'
                    }
                    
                elif index['id'] == 'ndbi':
                    # NDBI - Normalized Difference Built-up Index
                    # (SWIR - NIR) / (SWIR + NIR)
                    index_image = composite.normalizedDifference(['B11', 'B8']).rename('NDBI')
                    
                    # Calculate average NDBI across the region
                    ndbi_stats = index_image.reduceRegion({
                        'reducer': ee.Reducer.mean(),
                        'geometry': galicia,
                        'scale': 1000,
                        'maxPixels': 1e9
                    }).getInfo()
                    
                    # Get the NDBI value and convert to 0-100 scale (built-up area)
                    ndbi_value = ndbi_stats.get('NDBI', 0)
                    # NDBI typically ranges from -1 to 1, with built areas > 0
                    ndbi_score = round(((ndbi_value + 0.5) / 1.0) * 100)
                    ndbi_score = max(0, min(100, ndbi_score))  # Clamp to 0-100
                    
                    # Store the numerical score
                    metric_score = {
                        'value': ndbi_score,
                        'description': f'Urban/Built-up Score: {ndbi_score}/100 (Raw NDBI: {ndbi_value:.3f})'
                    }
                    
                elif index['id'] == 'nbr':
                    # NBR - Normalized Burn Ratio
                    # (NIR - SWIR) / (NIR + SWIR)
                    index_image = composite.normalizedDifference(['B8', 'B12']).rename('NBR')
                    
                    # Calculate average NBR across the region
                    nbr_stats = index_image.reduceRegion({
                        'reducer': ee.Reducer.mean(),
                        'geometry': galicia,
                        'scale': 1000,
                        'maxPixels': 1e9
                    }).getInfo()
                    
                    # Get the NBR value and convert to 0-100 scale (burn detection)
                    nbr_value = nbr_stats.get('NBR', 0)
                    # NBR typically ranges from -1 to 1, with burned areas having lower values
                    # Invert the scale so higher scores mean less burned area (healthier)
                    nbr_score = round(((nbr_value + 1.0) / 2.0) * 100)
                    nbr_score = max(0, min(100, nbr_score))  # Clamp to 0-100
                    
                    # Store the numerical score
                    metric_score = {
                        'value': nbr_score,
                        'description': f'Burn Assessment Score: {nbr_score}/100 (Raw NBR: {nbr_value:.3f})'
                    }
                
                # Get map ID for visualization
                mapid = index_image.getMapId(index['vis_params'])
                
                # Add index data to the period
                period_data['indices'].append({
                    'id': index['id'],
                    'tileUrl': mapid['tile_fetcher'].url_format,
                    'score': metric_score
                })
                
                print(f"    Successfully processed {index['name']}")
                
            except Exception as e:
                print(f"    Error processing {index['name']}: {str(e)}")
        
        # Save period data to JSON file if any indices were processed successfully
        if period_data['indices']:
            with open(period_filename, 'w') as f:
                json.dump(period_data, f, indent=2)
            print(f"  Successfully processed and saved {period['name']}")
            
            # Add a small delay to avoid hitting API rate limits
            time.sleep(2)
    
    print("\nAll data has been downloaded and processed!")
    print(f"Data is stored in the '{data_dir}' directory")

if __name__ == "__main__":
    main()
