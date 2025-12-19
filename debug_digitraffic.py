import requests
import json

def test_digitraffic():
    url = "https://tie.digitraffic.fi/api/traffic-message/v1/messages"
    params = {
        "inactiveHours": 0,
        "situationType": "TRAFFIC_ANNOUNCEMENT",
        "includeAreaGeometry": "false"
    }
    headers = {
        "User-Agent": "TestScript/1.0"
    }

    try:
        print(f"Fetching from {url}...")
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            print(f"Found {len(features)} active traffic messages.")
            if features:
                print("First message example:")
                print(json.dumps(features[0]['properties'], indent=2, ensure_ascii=False))
        else:
            print("Failed to fetch data.")
            print(resp.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_digitraffic()
