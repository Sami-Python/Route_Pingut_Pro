
import sys
import os
from fastapi.testclient import TestClient

# Ensure we can import from 'api'
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'api'))

try:
    from api.main import app
    client = TestClient(app)
    
    print("\n--- TEST: HERE Traffic Tile Endpoint ---")
    url = "/maps/tiles/here_traffic/7/75/33"
    print(f"Requesting: {url}")
    response = client.get(url)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text}")
    else:
        print("Success! (Binary data received)")

    print("\n--- TEST: Digitraffic Messages Endpoint ---")
    # Test with a dummy polyline or lat/lon
    url_dt = "/maps/digitraffic/messages?lat=60.1&lon=24.9&radius=10"
    print(f"Requesting: {url_dt}")
    resp_dt = client.get(url_dt)
    print(f"Status: {resp_dt.status_code}")
    print(f"Body: {resp_dt.text[:200]}...")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
