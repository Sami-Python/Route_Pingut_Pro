"""
Test traffic messages on Turku-Kotka route
"""

import requests

# Turku-Kotka route coordinates
test_coords = [
    (60.4518, 22.2666),  # Turku
    (60.7, 24.5),        # Midpoint 1
    (60.8, 26.0),        # Midpoint 2
    (60.4664, 26.9458)   # Kotka
]

coords_str = ";".join([f"{lat},{lon}" for lat, lon in test_coords])

url = "http://localhost:8000/maps/digitraffic/messages"
params = {
    "route_coords": coords_str,
    "radius": 50.0
}

print(f"Testing Turku -> Kotka route")
print(f"Coordinates: {len(test_coords)} points")
print(f"URL: {url}\n")

try:
    resp = requests.get(url, params=params, timeout=10)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        messages = data.get("messages", [])
        print(f"Found {len(messages)} traffic messages\n")
        
        if messages:
            for i, msg in enumerate(messages):
                print(f"{i+1}. {msg.get('otsikko', 'No title')}")
                print(f"   Location: {msg.get('sijainti', 'N/A')}")
                print(f"   Coords: ({msg.get('lat', 0):.4f}, {msg.get('lon', 0):.4f})\n")
        else:
            print("✓ API works but no active incidents on this route right now")
            print("This is normal - Digitraffic only returns active incidents")
    else:
        print(f"ERROR: {resp.text}")
        
except Exception as e:
    print(f"Exception: {e}")
