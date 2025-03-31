import ee
import json
import os

def authenticate_and_initialize():
    """Authenticate with Earth Engine and initialize"""
    try:
        # Check if already authenticated
        ee.Initialize(project="ee-nikolaslafrentz")
        print("Earth Engine already authenticated and initialized!")
        return True
    except Exception:
        try:
            # Authenticate
            ee.Authenticate()
            # Initialize
            ee.Initialize(project="ee-nikolaslafrentz")
            print("Earth Engine authenticated and initialized successfully!")
            return True
        except Exception as e:
            print(f"Error authenticating: {e}")
            return False

def get_galicia_geometry():
    """Define the Galicia region geometry"""
    return ee.Geometry.Polygon([
        [[-9.301758, 41.862611],
         [-9.301758, 43.789203],
         [-6.767578, 43.789203],
         [-6.767578, 41.862611]]
    ])

def get_sentinel_collection(start_date, end_date, region):
    """Get Sentinel-2 surface reflectance data for the region"""
    sentinel = ee.ImageCollection('COPERNICUS/S2_SR') \
        .filterBounds(region) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        
    print(f"Found {sentinel.size().getInfo()} Sentinel-2 images for the specified time period.")
    return sentinel

def create_composite(collection):
    """Create a median composite image from a collection"""
    return collection.median()

def generate_rgb_url(image, region):
    """Generate a tile URL for RGB visualization"""
    rgb_vis = {
        'min': 0,
        'max': 3000,
        'bands': ['B4', 'B3', 'B2']
    }
    map_id = image.getMapId(rgb_vis)
    return map_id['tile_fetcher'].url_format

def generate_ndvi_url(image, region):
    """Generate a tile URL for NDVI visualization"""
    # Calculate NDVI
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    
    ndvi_vis = {
        'min': -0.2,
        'max': 0.8,
        'palette': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850']
    }
    
    map_id = ndvi.getMapId(ndvi_vis)
    return map_id['tile_fetcher'].url_format

def generate_ndwi_url(image, region):
    """Generate a tile URL for NDWI visualization"""
    # Calculate NDWI
    ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI')
    
    ndwi_vis = {
        'min': -0.5,
        'max': 0.5,
        'palette': ['#a52a2a', '#fcf8e3', '#86c4ec', '#0d47a1']
    }
    
    map_id = ndwi.getMapId(ndwi_vis)
    return map_id['tile_fetcher'].url_format

def generate_tile_urls():
    """Generate all tile URLs and save to JSON"""
    # Authenticate and initialize
    if not authenticate_and_initialize():
        return False
    
    # Get the Galicia region
    galicia = get_galicia_geometry()
    
    # Define time periods
    periods = [
        {"name": "Jan-Mar 2023", "start": "2023-01-01", "end": "2023-03-31"}
    ]
    
    # This will hold all our map data
    map_data = {
        "center": [42.8, -8.0],
        "zoom": 8,
        "indices": [
            {
                "id": "rgb",
                "name": "True Color (RGB)",
                "description": "Natural color representation as seen by human eyes."
            },
            {
                "id": "ndvi",
                "name": "NDVI (Vegetation Health)",
                "description": "Normalized Difference Vegetation Index: Measures vegetation health and density."
            },
            {
                "id": "ndwi",
                "name": "NDWI (Water Bodies)",
                "description": "Normalized Difference Water Index: Highlights water bodies and moisture content."
            }
        ],
        "periods": []
    }
    
    # For each time period, generate tile URLs
    for period in periods:
        print(f"\nProcessing period: {period['name']}")
        
        # Get Sentinel data for this period
        collection = get_sentinel_collection(period["start"], period["end"], galicia)
        
        if collection.size().getInfo() > 0:
            # Create composite image
            composite = create_composite(collection)
            
            # Generate tile URLs for different indices
            period_data = {
                "name": period["name"],
                "start": period["start"],
                "end": period["end"],
                "imageCount": collection.size().getInfo(),
                "indices": [
                    {
                        "id": "rgb",
                        "tileUrl": generate_rgb_url(composite, galicia)
                    },
                    {
                        "id": "ndvi",
                        "tileUrl": generate_ndvi_url(composite, galicia)
                    },
                    {
                        "id": "ndwi",
                        "tileUrl": generate_ndwi_url(composite, galicia)
                    }
                ]
            }
            
            map_data["periods"].append(period_data)
            print(f"Successfully generated tile URLs for {period['name']}")
        else:
            print(f"No images found for period {period['name']}")
    
    # Save the map data to a JSON file
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    output_file = os.path.join(output_dir, 'satellite_tiles.json')
    
    with open(output_file, 'w') as f:
        json.dump(map_data, f, indent=2)
    
    print(f"\nTile URLs saved to {output_file}")
    return True

if __name__ == "__main__":
    generate_tile_urls()
