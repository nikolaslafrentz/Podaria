import ee
import os
import webbrowser

def authenticate_earth_engine():
    try:
        # Check if authenticated already
        print("Checking if already authenticated...")
        credentials = ee.ServiceAccountCredentials(None, None)
        ee.Initialize(credentials)
        print("Already authenticated!")
        return True
    except:
        print("Not authenticated. Starting authentication process...")
    
    try:
        # Trigger the authentication flow.
        print("\n1. If a browser doesn't open automatically, copy the URL below and open it manually.")
        auth_url = ee.Authenticate(code_in_console=True, quiet=False, return_auth_url=True)
        
        if auth_url:
            print(f"\n2. URL for manual authentication: {auth_url}")
            
            # Try to open browser automatically
            try:
                webbrowser.open(auth_url)
                print("\nBrowser window should open automatically.")
            except:
                print("\nCouldn't open browser automatically. Please use the URL above.")
        
        print("\n3. Follow the steps in the browser to authenticate.")
        print("4. Copy the authorization code from the browser.")
        print("5. Paste the authorization code when prompted below.")
        
        # The actual authentication happens here
        ee.Authenticate(code_in_console=True, quiet=False)
        
        print("\nAuthentication successful!")
        print("Now initializing Earth Engine...")
        
        # Initialize Earth Engine
        try:
            ee.Initialize()
            print("Earth Engine initialized successfully without project ID!")
        except Exception as e:
            print(f"Initializing without project ID failed: {str(e)}")
            print("If you have a project ID, you can specify it when initializing:")
            project_id = input("Enter your Google Cloud project ID (leave blank to skip): ")
            if project_id:
                try:
                    ee.Initialize(project=project_id)
                    print(f"Earth Engine initialized successfully with project ID: {project_id}")
                except Exception as e:
                    print(f"Initialization with project ID failed: {str(e)}")
                    return False
            else:
                print("No project ID provided. Please obtain a valid project ID from Google Cloud Console.")
                print("Visit: https://console.cloud.google.com/projectcreate")
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
