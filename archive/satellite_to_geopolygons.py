import ee
import numpy as np
import cv2
import os
import json
import logging
import requests
import tempfile
from shapely.geometry import Polygon, mapping
import matplotlib.pyplot as plt
import geojson
from pyproj import Transformer

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', 
                   handlers=[logging.StreamHandler(), logging.FileHandler('geo_polygons_process.log')])

def initialize_ee():
    """Initialize Google Earth Engine"""
    try:
        ee.Initialize(project="ee-nikolaslafrentz")
        logging.info("Earth Engine initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing Earth Engine: {e}")
        ee.Authenticate()
        ee.Initialize(project="ee-nikolaslafrentz")
        logging.info("Earth Engine initialized after authentication")


def get_satellite_image(coords, start_date, end_date, cloud_cover_max=30):
    """
    Retrieve satellite imagery for a region defined by coordinates
    
    Args:
        coords: List of [lon, lat] coordinates defining a polygon
        start_date: Start date for imagery (YYYY-MM-DD)
        end_date: End date for imagery (YYYY-MM-DD)
        cloud_cover_max: Maximum cloud cover percentage
        
    Returns:
        ee.Image: Median composite of Sentinel-2 imagery
    """
    # Create a geometry from the coordinates
    geometry = ee.Geometry.Polygon([coords])
    
    # Get Sentinel-2 surface reflectance data
    sentinel = ee.ImageCollection('COPERNICUS/S2_SR') \
        .filterBounds(geometry) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover_max))
    
    # Count images
    count = sentinel.size().getInfo()
    logging.info(f"Found {count} Sentinel-2 images")
    
    if count == 0:
        logging.error("No images found for the specified criteria")
        return None
    
    # Create a median composite
    median = sentinel.median()
    
    return median


def download_satellite_image(image, geometry, scale=10, vis_params=None):
    """
    Download a satellite image as a GeoTIFF file
    
    Args:
        image: ee.Image object
        geometry: ee.Geometry defining the region
        scale: Resolution in meters per pixel
        vis_params: Visualization parameters (e.g., bands, min, max)
        
    Returns:
        str: Path to downloaded image
    """
    if vis_params is None:
        # Default to true color RGB
        vis_params = {'min': 0, 'max': 3000, 'bands': ['B4', 'B3', 'B2']}
    
    # Get a URL to download the image
    url = image.visualize(**vis_params).getThumbURL({
        'region': geometry,
        'dimensions': 1024,
        'format': 'png'
    })
    
    # Download the image
    response = requests.get(url)
    if response.status_code != 200:
        logging.error(f"Failed to download image: {response.status_code}")
        return None
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    with open(temp_file.name, 'wb') as f:
        f.write(response.content)
    
    logging.info(f"Downloaded image to {temp_file.name}")
    return temp_file.name


def image_to_polygons(image_path, threshold_min=100, threshold_max=200, min_area=100, save_contours=True):
    """
    Extract polygons from an image using edge detection and contour finding
    
    Args:
        image_path: Path to the image file
        threshold_min: Lower threshold for Canny edge detection
        threshold_max: Upper threshold for Canny edge detection
        min_area: Minimum contour area to consider
        save_contours: Whether to save an image showing the detected contours
        
    Returns:
        list: List of Shapely polygons
    """
    logging.debug(f"Processing image: {image_path}")
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            logging.error(f"Failed to load image: {image_path}")
            return []
        
        # Save original image dimensions
        img_height, img_width = image.shape[:2]
        logging.debug(f"Image dimensions: {img_width}x{img_height}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply edge detection
        edges = cv2.Canny(blurred, threshold_min, threshold_max)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        logging.info(f"Found {len(contours)} raw contours")
        
        # Filter contours by area
        filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
        logging.info(f"Filtered to {len(filtered_contours)} contours with area > {min_area}")
        
        # Draw contours on the original image if requested
        if save_contours:
            image_with_contours = image.copy()
            cv2.drawContours(image_with_contours, filtered_contours, -1, (0, 255, 0), 2)
            
            # Save the image with contours
            output_image_path = f"{os.path.splitext(image_path)[0]}_contours.png"
            cv2.imwrite(output_image_path, image_with_contours)
            logging.info(f"Image with contours saved to {output_image_path}")
        
        # Convert contours to polygons (in pixel coordinates)
        pixel_polygons = []
        for contour in filtered_contours:
            if len(contour) >= 3:  # Need at least 3 points for a polygon
                # Approximate the contour to simplify
                epsilon = 0.01 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Convert to Shapely polygon
                polygon = Polygon(approx.reshape(-1, 2))
                if polygon.is_valid:
                    pixel_polygons.append({
                        'polygon': polygon,
                        'area': polygon.area,
                        'centroid': (polygon.centroid.x, polygon.centroid.y),
                        'img_dims': (img_width, img_height)
                    })
        
        logging.info(f"Created {len(pixel_polygons)} valid Shapely polygons")
        return pixel_polygons
    except Exception as e:
        logging.error(f"Error processing image {image_path}: {e}")
        return []


def pixels_to_geo_coords(pixel_polygons, bounds):
    """
    Convert pixel coordinates to geographic coordinates
    
    Args:
        pixel_polygons: List of dictionaries containing pixel polygons and metadata
        bounds: Geographic bounds [west, south, east, north]
        
    Returns:
        list: List of Shapely polygons with geographic coordinates
    """
    west, south, east, north = bounds
    
    geo_polygons = []
    for pp in pixel_polygons:
        polygon = pp['polygon']
        img_width, img_height = pp['img_dims']
        
        # Create a transformer function to convert from pixel to geo coordinates
        def transform_point(x, y):
            # Convert from pixel coordinates to 0-1 range
            x_ratio = x / img_width
            y_ratio = y / img_height
            
            # Convert to geographic coordinates (longitude, latitude)
            lon = west + (east - west) * x_ratio
            # Note: Y is inverted in images (0 at top)
            lat = north - (north - south) * y_ratio
            
            return lon, lat
        
        # Transform all polygon vertices
        geo_coords = [transform_point(x, y) for x, y in polygon.exterior.coords]
        
        # Create a new Shapely polygon with geographic coordinates
        geo_polygon = Polygon(geo_coords)
        if geo_polygon.is_valid:
            geo_polygons.append(geo_polygon)
    
    return geo_polygons


def save_polygons_to_geojson(polygons, output_file):
    """
    Save polygons to GeoJSON file
    
    Args:
        polygons: List of Shapely polygons with geographic coordinates
        output_file: Path to output GeoJSON file
    """
    features = []
    for i, polygon in enumerate(polygons):
        feature = geojson.Feature(
            id=i,
            geometry=mapping(polygon),
            properties={'id': i}
        )
        features.append(feature)
    
    feature_collection = geojson.FeatureCollection(features)
    
    with open(output_file, 'w') as f:
        geojson.dump(feature_collection, f)
    
    logging.info(f"Saved {len(polygons)} polygons to {output_file}")


def visualize_results(original_image_path, geojson_file, output_image_path):
    """
    Create a visualization of the extracted polygons on the original image
    
    Args:
        original_image_path: Path to the original satellite image
        geojson_file: Path to the GeoJSON file containing polygons
        output_image_path: Path to save the visualization
    """
    # Load original image
    img = plt.imread(original_image_path)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Display the original image
    ax.imshow(img)
    
    # Load GeoJSON data
    with open(geojson_file, 'r') as f:
        data = geojson.load(f)
    
    # Display each polygon with a random color
    for feature in data['features']:
        polygon = feature['geometry']['coordinates'][0]
        xs, ys = zip(*polygon)
        ax.plot(xs, ys, '-', linewidth=2, alpha=0.7)
    
    ax.set_title('Extracted Polygons')
    ax.axis('off')
    
    # Save the visualization
    plt.savefig(output_image_path, bbox_inches='tight', dpi=300)
    plt.close()
    
    logging.info(f"Visualization saved to {output_image_path}")


def main(coords, start_date, end_date, output_dir="output"):
    """
    Main function to process satellite imagery and extract polygons
    
    Args:
        coords: List of [lon, lat] coordinates defining a polygon
        start_date: Start date for imagery (YYYY-MM-DD)
        end_date: End date for imagery (YYYY-MM-DD)
        output_dir: Directory to save output files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize Earth Engine
    initialize_ee()
    
    # Create geometry from coordinates
    geometry = ee.Geometry.Polygon([coords])
    
    # Get geographic bounds
    bounds_dict = geometry.bounds().getInfo()['coordinates'][0]
    west = min(p[0] for p in bounds_dict)
    east = max(p[0] for p in bounds_dict)
    south = min(p[1] for p in bounds_dict)
    north = max(p[1] for p in bounds_dict)
    bounds = [west, south, east, north]
    
    # Get satellite image
    logging.info(f"Fetching satellite imagery from {start_date} to {end_date}")
    image = get_satellite_image(coords, start_date, end_date)
    
    if image is None:
        logging.error("Failed to get satellite imagery")
        return
    
    # Process the same area with different indices to extract different features
    indices = [
        {
            'name': 'rgb',
            'description': 'True Color (RGB)',
            'vis_params': {'min': 0, 'max': 3000, 'bands': ['B4', 'B3', 'B2']}
        },
        {
            'name': 'ndvi',
            'description': 'Vegetation Index',
            'vis_params': {'min': -0.2, 'max': 0.8, 'palette': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850']}
        },
        {
            'name': 'ndwi',
            'description': 'Water Index',
            'vis_params': {'min': -0.5, 'max': 0.5, 'palette': ['#a52a2a', '#fcf8e3', '#86c4ec', '#0d47a1']}
        }
    ]
    
    for index in indices:
        logging.info(f"Processing {index['name']} - {index['description']}")
        
        # Apply appropriate calculation for indices
        if index['name'] == 'ndvi':
            index_image = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        elif index['name'] == 'ndwi':
            index_image = image.normalizedDifference(['B3', 'B8']).rename('NDWI')
        else:  # RGB
            index_image = image
        
        # Download the image
        image_path = download_satellite_image(index_image, geometry, vis_params=index['vis_params'])
        if image_path is None:
            continue
        
        # Extract polygons (in pixel coordinates)
        # Adjust thresholds based on the index
        if index['name'] == 'rgb':
            pixel_polygons = image_to_polygons(image_path, threshold_min=100, threshold_max=200, min_area=100)
        else:  # For calculated indices, use different thresholds
            pixel_polygons = image_to_polygons(image_path, threshold_min=50, threshold_max=150, min_area=50)
        
        # Convert to geographic coordinates
        geo_polygons = pixels_to_geo_coords(pixel_polygons, bounds)
        
        # Save as GeoJSON
        output_file = os.path.join(output_dir, f"{index['name']}_polygons.geojson")
        save_polygons_to_geojson(geo_polygons, output_file)
        
        # Create visualization
        viz_file = os.path.join(output_dir, f"{index['name']}_visualization.png")
        visualize_results(image_path, output_file, viz_file)
    
    logging.info("Processing complete!")


if __name__ == "__main__":
    # Example usage
    # Define the area of interest with [lon, lat] coordinates
    galicia_coords = [
        [-9.301758, 41.862611],  # Southwest
        [-9.301758, 43.789203],  # Northwest
        [-6.767578, 43.789203],  # Northeast
        [-6.767578, 41.862611]   # Southeast
    ]
    
    # You can replace this with your own coordinates and date range
    main(galicia_coords, "2023-06-01", "2023-06-30", output_dir="geo_polygons")
