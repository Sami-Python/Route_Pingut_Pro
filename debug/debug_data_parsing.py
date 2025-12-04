import requests
import json

def debug_endpoint(name, url):
    print(f"--- DEBUGGING {name} ---")
    try:
        resp = requests.get(url, headers={"User-Agent": "StreamlitApp/1.0 (gzip)", "Accept-Encoding": "gzip"})
        if resp.status_code != 200:
            print(f"Failed with status {resp.status_code}")
            return

        data = resp.json()
        
        # Data endpoints usually return a list of objects or a 'dataStations' key
        if "dataStations" in data:
            items = data["dataStations"]
            print(f"Found {len(items)} data stations.")
            if items:
                print(json.dumps(items[0], indent=2))
        elif "features" in data:
             print(f"Found {len(data['features'])} features (GeoJSON).")
             if data['features']:
                 print(json.dumps(data['features'][0], indent=2))
        else:
            print("Unknown structure.")
            print(json.dumps(data, indent=2)[:500]) # Print start

    except Exception as e:
        print(f"Error: {e}")
    print("\n")

# 1. Road Weather Data
debug_endpoint("Road Weather Data", "https://tie.digitraffic.fi/api/weather/v1/stations/data")

# 2. LAM Data
debug_endpoint("LAM Data", "https://tie.digitraffic.fi/api/tms/v1/stations/data")
