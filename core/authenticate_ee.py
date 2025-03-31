import ee
import os
import webbrowser

def authenticate_earth_engine():
    try:
        # Check if authenticated already
        print("Checking if already authenticated...")
        ee.Initialize()
        print("Already authenticated!")
        return True
    except:
        print("Not authenticated. Starting authentication process...")
    
    try:
        # Trigger the authentication flow.
        print("\n1. If a browser doesn't open automatically, copy the URL below and open it manually.")
        # Use the simpler authentication method without the problematic parameter
        ee.Authenticate()
        
        print("\n2. Follow the steps in the browser to authenticate.")
        print("3. Copy the authorization code from the browser when prompted.")
        
        # Initialize Earth Engine
        try:
            ee.Initialize(project="ee-nikolaslafrentz")
            print("Earth Engine initialized successfully!")
        except Exception as e:
            print(f"Initializing with project ID failed: {str(e)}")
            print("Trying to initialize without project ID...")
            try:
                ee.Initialize()
                print("Earth Engine initialized successfully without project ID!")
            except Exception as e:
                print(f"Initialization without project ID failed: {str(e)}")
                return False
        
        return True
    except Exception as e:
        print(f"\nAuthentication Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have a Google account with Earth Engine access enabled")
        print("2. If you haven't signed up for Earth Engine, visit: https://signup.earthengine.google.com/")
        print("3. Clear your browser cookies and try again")
        print("4. Check your internet connection")
        return False

if __name__ == "__main__":
    print("=== Google Earth Engine Authentication Process ===")
    success = authenticate_earth_engine()
    
    if success:
        print("\nAuthentication and initialization complete!")
        print("You can now use Earth Engine in your Python scripts.")
    else:
        print("\nAuthentication or initialization failed. Please try again.")
