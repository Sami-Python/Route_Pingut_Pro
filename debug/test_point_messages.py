"""
Test traffic messages with point-based search (Salo area where we know there's a message)
"""

import requests

# Use Salo coordinates where we know there's a message
url = "http://localhost:8000/maps/digitraffic/messages"
params = {
    "lat": 60.38,
    "lon": 23.58,
    "radius": 10.0  # 10km radius
}

print(f"Testing: {url}")
print(f"Location: Salo area (where we know there's a message)")
print(f"Params: {params}\n")

try:
    resp = requests.get(url, params=params, timeout=10)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        messages = data.get("messages", [])
        print(f"Found {len(messages)} messages\n")
        
        if messages:
            print("Messages:")
            for i, msg in enumerate(messages):
                print(f"\n{i+1}. {msg.get('otsikko', 'No title')}")
                print(f"   Description: {msg.get('kuvaus', 'N/A')[:100]}...")
                print(f"   Location: {msg.get('sijainti', 'N/A')}")
                print(f"   Lat/Lon: {msg.get('lat', 0):.4f}, {msg.get('lon', 0):.4f}")
        else:
            print("No messages found!")
    else:
        print(f"Error: {resp.text}")
        
except Exception as e:
    print(f"Exception: {e}")
