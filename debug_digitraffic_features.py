from api.utils.digitraffic_client import get_lam_stations, get_weather_cameras, get_road_weather_stations
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_features():
    # Sample route (Helsinki -> Tampere)
    route_coords = [
        (60.1699, 24.9384), # Helsinki
        (60.6, 24.8),       # Waypoint
        (61.4978, 23.7610)  # Tampere
    ]
    
    print("--- Testing Digitraffic Features ---")
    
    # 1. Weather Cameras
    print("\n1. Testing Weather Cameras...")
    start = time.time()
    try:
        cams = get_weather_cameras(route_coords)
        elapsed = time.time() - start
        print(f"Success! Found {len(cams)} cameras. Time: {elapsed:.2f}s")
        if cams:
            print(f"Sample: {cams[0]['name']}")
    except Exception as e:
        print(f"FAILED: {e}")

    # 2. Road Weather
    print("\n2. Testing Road Weather...")
    start = time.time()
    try:
        weather = get_road_weather_stations(route_coords)
        elapsed = time.time() - start
        print(f"Success! Found {len(weather)} stations. Time: {elapsed:.2f}s")
        if weather:
             print(f"Sample: {weather[0]}")
    except Exception as e:
         print(f"FAILED: {e}")

    # 3. LAM Stations
    print("\n3. Testing LAM Stations...")
    start = time.time()
    try:
        lams = get_lam_stations(route_coords)
        elapsed = time.time() - start
        print(f"Success! Found {len(lams)} LAM stations. Time: {elapsed:.2f}s")
        if lams:
             print(f"Sample: {lams[0]}")
    except Exception as e:
         print(f"FAILED: {e}")

if __name__ == "__main__":
    test_features()
