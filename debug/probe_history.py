import requests
import json

def get_station_id():
    url = "https://tie.digitraffic.fi/api/weather/v1/stations"
    headers = { "User-Agent": "StreamlitApp/1.0 (gzip)", "Accept-Encoding": "gzip" }
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        if features:
            return features[0]["properties"]["id"]
    except Exception as e:
        print(f"Error fetching stations: {e}")
    return None

def probe_history(station_id):
    if not station_id:
        print("No station ID found.")
        return

    print(f"Probing history for station: {station_id}")
    headers = { "User-Agent": "StreamlitApp/1.0 (gzip)", "Accept-Encoding": "gzip" }
    
    # Potential endpoints
    endpoints = [
        f"https://tie.digitraffic.fi/api/weather/v1/stations/{station_id}/data/history",
        f"https://tie.digitraffic.fi/api/weather/v1/stations/{station_id}/history",
        f"https://tie.digitraffic.fi/api/weather/v1/stations/data/history?stationId={station_id}",
        # Forecast might be interesting too
        f"https://tie.digitraffic.fi/api/weather/v1/stations/{station_id}/forecast"
    ]

    for url in endpoints:
        print(f"Testing: {url}")
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print("Success! Data keys:", data.keys())
                    # Print a snippet
                    print(json.dumps(data, indent=2)[:200])
                except:
                    print("Not JSON")
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 20)

if __name__ == "__main__":
    sid = get_station_id()
    probe_history(sid)
