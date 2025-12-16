
import sys
import os
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../api")))

load_dotenv()

try:
    from api.maps_api import api_route, RouteRequest
except ImportError as e:
    print(f"ImportError: {e}")
    print(f"Sys Path: {sys.path}")
    sys.exit(1)

def test_route():
    print("Testing api_route...")
    
    # Check if API Key exists
    if not os.getenv("HERE_API_KEY"):
        print("SKIPPING: HERE_API_KEY not found in env.")
        return

    # Create dummy request (Helsinki -> Tampere)
    req = RouteRequest(
        origin_lat=60.1699,
        origin_lon=24.9384,
        dest_lat=61.4978,
        dest_lon=23.7610
    )

    try:
        response = api_route(req)
        print(f"Success: {response.success}")
        
        if response.coordinates:
            print(f"Coordinates found: {len(response.coordinates)}")
            print(f"First coord: {response.coordinates[0]}")
            print(f"Last coord: {response.coordinates[-1]}")
        else:
            print("FAILURE: No coordinates return!")
            
        if response.polyline:
            print("Polyline present.")
            
    except Exception as e:
        print(f"FAILURE: Exception occurred: {e}")

if __name__ == "__main__":
    test_route()
