import requests
from shapely.geometry import LineString, Point
import json

# Mock route (Helsinki - Tampere approx)
mock_route = [
    (60.1699, 24.9384), # Helsinki
    (60.2000, 24.9500),
    (60.3000, 25.0000),
    (60.4000, 25.1000),
    (60.5000, 25.2000),
    (60.6000, 25.3000),
    (60.7000, 25.4000),
    (60.8000, 25.5000),
    (60.9000, 25.6000),
    (61.0000, 25.7000),
    (61.4978, 23.7610)  # Tampere
]

def test_fetch(name, func):
    print(f"Testing {name}...")
    try:
        data = func(mock_route)
        print(f"  Found {len(data)} items.")
        if data:
            print(f"  Sample: {data[0]}")
    except Exception as e:
        print(f"  Error: {e}")
    print("-" * 20)

if __name__ == "__main__":
    from digitraffic_client import (
        traffic_messages_near_route,
        get_weather_cameras,
        get_road_weather_stations,
        get_vms_stations,
        get_maintenance_data,
        get_lam_stations
    )

    test_fetch("Traffic Messages", traffic_messages_near_route)
    test_fetch("Weather Cameras", get_weather_cameras)
    test_fetch("Road Weather", get_road_weather_stations)
    test_fetch("VMS", get_vms_stations)
    test_fetch("Maintenance", get_maintenance_data)
    test_fetch("LAM", get_lam_stations)
