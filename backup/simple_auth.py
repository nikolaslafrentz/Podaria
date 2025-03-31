import ee

try:
    print("Starting Google Earth Engine authentication...")
    # This will open a browser window for authentication
    ee.Authenticate()
    print("Authentication completed. Now initializing Earth Engine...")
    
    # Try initializing without a project ID first
    try:
        ee.Initialize()
        print("Earth Engine initialized successfully!")
    except Exception as e:
        print(f"Standard initialization failed: {str(e)}")
        print("Attempting to initialize with a project ID...")
        
        # Get the project ID from the user
        project_id = input("Enter your Google Cloud project ID: ")
        if project_id:
            try:
                ee.Initialize(project=project_id)
                print(f"Earth Engine initialized successfully with project ID: {project_id}")
                print("\nSave this project ID for future use.")
            except Exception as e:
                print(f"Initialization with project ID failed: {str(e)}")
        else:
            print("No project ID provided.")
    
    print("\nTo create a new Earth Engine-enabled Google Cloud project:")
    print("1. Go to https://console.cloud.google.com/projectcreate")
    print("2. Create a new project")
    print("3. Enable the Earth Engine API for this project")
    print("   (Go to APIs & Services > Library > Search for 'Earth Engine' > Enable)")

except Exception as e:
    print(f"\nError during authentication: {str(e)}")
    print("\nTroubleshooting tips:")
    print("1. Make sure you have a Google account with Earth Engine access")
    print("2. If you haven't signed up, visit: https://signup.earthengine.google.com/")
    print("3. Check your internet connection")
