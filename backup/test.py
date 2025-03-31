import ee
import os

# Authenticate and initialize Earth Engine
ee.Authenticate()
ee.Initialize(project="trying-this-out")  # Using your project ID from the original code

# Define the Galicia region boundaries (approximate coordinates)
galicia = ee.Geometry.Polygon([
    [[-9.301758, 41.862611],
     [-9.301758, 43.789203],
     [-6.767578, 43.789203],
     [-6.767578, 41.862611]]
])

# Get Sentinel-2 surface reflectance data
sentinel = ee.ImageCollection('COPERNICUS/S2_SR') \
    .filterBounds(galicia) \
    .filterDate('2022-06-01', '2022-09-30') \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))

# Select RGB bands and create a median composite
rgb_vis = {'min': 0, 'max': 3000, 'bands': ['B4', 'B3', 'B2']}
composite = sentinel.median()

# Create output directory for imagery
output_dir = './galicia_imagery'
os.makedirs(output_dir, exist_ok=True)

# Export the image to Google Drive
print("Setting up export task for Sentinel-2 imagery of Galicia region...")
task = ee.batch.Export.image.toDrive({
    'image': composite.select(['B4', 'B3', 'B2']),
    'description': 'Galicia_Sentinel2_RGB',
    'folder': 'Earth_Engine_Exports',
    'region': galicia,
    'scale': 10,  # 10m resolution for Sentinel-2
    'maxPixels': 1e9
})

# Start the export task
task.start()
print("\nExport task started! The imagery will be available in your Google Drive")
print("Folder: Earth_Engine_Exports")
print("Filename: Galicia_Sentinel2_RGB.tif")
print("\nYou can check the status of your task in the Earth Engine Code Editor:")
print("https://code.earthengine.google.com/tasks")
