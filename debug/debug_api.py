import requests

endpoints = [
    "https://tie.digitraffic.fi/api/v1/metadata/weather-stations",
    "https://tie.digitraffic.fi/api/v3/metadata/weather-stations",
    "https://tie.digitraffic.fi/api/weather/v1/stations",
    "https://tie.digitraffic.fi/api/v1/data/variable-sign-data",
    "https://tie.digitraffic.fi/api/variable-sign/v1/signs",
    "https://tie.digitraffic.fi/api/tms/v1/stations",
    "https://tie.digitraffic.fi/api/v1/metadata/tms-stations"
]

headers = {
    "User-Agent": "StreamlitApp/1.0 (gzip)",
    "Accept": "application/json"
}

print("Testing endpoints...")
for url in endpoints:
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        print(f"{url}: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  Headers: {resp.headers}")
            print(f"  Content (first 100): {resp.text[:100]}")
    except Exception as e:
        print(f"{url}: Error {e}")
