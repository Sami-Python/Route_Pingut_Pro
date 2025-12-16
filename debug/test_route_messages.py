"""
Test traffic messages with a specific route (Helsinki-Tampere)
"""

import requests

# Simulate a route from Helsinki to Tampere
test_coords = [
    (60.1699, 24.9384),  # Helsinki
    (60.5, 24.5),        # Midpoint
    (61.4978, 23.7610)   # Tampere
]

# Convert to polyline format for API
coords_str = ";".join([f"{lat},{lon}" for lat, lon in test_coords])

url = "http://localhost:8000/maps/digitraffic/messages"
params = {
    "route_coords": coords_str,
    "radius": 50.0
}

print(f"Testing: {url}")
print(f"Route: Helsinki -> Tampere")
print(f"Params: {params}\n")

try:
    resp = requests.get(url, params=params, timeout=10)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        messages = data.get("messages", [])
        print(f"Found {len(messages)} messages near route\n")
        
        if messages:
            print("Messages:")
            for i, msg in enumerate(messages[:5]):
                print(f"\n{i+1}. {msg.get('otsikko', 'No title')}")
                print(f"   Location: {msg.get('sijainti', 'N/A')}")
                print(f"   Lat/Lon: {msg.get('lat', 0):.4f}, {msg.get('lon', 0):.4f}")
        else:
            print("No messages found near this route!")
            print("This might be normal if there are no active incidents on this route.")
    else:
        print(f"Error: {resp.text}")
        
except Exception as e:
    print(f"Exception: {e}")
