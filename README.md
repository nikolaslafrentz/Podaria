# Galicia Earth Engine & Mapping Project

## Project Overview
A Python-based project that uses Google Earth Engine to access and visualize satellite imagery and geographic data for the Galicia region in Spain. The project includes tools for satellite image processing and web-based visualization.

## Project Structure

### `/core`
Core functionality and authentication scripts:
- `authenticate_ee.py` - Google Earth Engine authentication
- `galicia_map.py` - Core script for fetching and processing satellite data
- `simple_auth.py` - Simplified authentication utilities
- `redata_api.py` - Script for fetching electrical grid and outage data from REData API

### `/mapping`
Web-based visualization tools:
- `galicia_map_viewer.html` - Basic map viewer for displaying satellite imagery
- `galicia_unified_map.html` - Advanced map viewer with multiple layers and data visualization

### `/data`
Data files generated and used by the application:
- Contains GeoJSON files, CSV data, and processing logs
- Includes electrical grid and power outage information

### `/archive`
Archived/backup scripts that are not currently in active use.

### `/backup`
Backup copies of original files before major modifications.

## Getting Started

1. First, authenticate with Google Earth Engine using `core/authenticate_ee.py`
2. Run `core/galicia_map.py` to fetch satellite imagery for the Galicia region
3. Open `mapping/galicia_map_viewer.html` in a web browser to view the results

## Data Sources
- Sentinel-2 satellite imagery from Google Earth Engine
- REData API for electrical grid and power outage information (when available)

## Notes
- The REData API integration is currently experiencing issues (500 Internal Server Error)
- For REData API access, a custom User-Agent header is being used to attempt to bypass access restrictions
