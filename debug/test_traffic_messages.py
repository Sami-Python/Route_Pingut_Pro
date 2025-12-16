"""
Test Digitraffic traffic messages API directly
"""

import requests

url = "https://tie.digitraffic.fi/api/traffic-message/v1/messages"
headers = {"User-Agent": "StreamlitApp/1.0 (gzip)"}
params = {
    "inactiveHours": 0,
    "situationType": "TRAFFIC_ANNOUNCEMENT",
    "includeAreaGeometry": "false"
}

print(f"Testing: {url}")
print(f"Params: {params}\n")

try:
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        features = data.get("features", [])
        print(f"Found {len(features)} traffic messages\n")
        
        if features:
            print("First 3 messages:")
            for i, feature in enumerate(features[:3]):
                props = feature.get("properties", {})
                announcements = props.get("announcements", [])
                first_ann = announcements[0] if announcements else {}
                
                print(f"\n{i+1}. {first_ann.get('title', 'No title')}")
                print(f"   Location: {first_ann.get('location', {}).get('description', 'N/A')}")
                print(f"   Geometry type: {feature.get('geometry', {}).get('type', 'N/A')}")
                
                # Try to get coordinates
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates", [])
                print(f"   Coords (raw): {coords[:2] if coords else 'None'}...")
        else:
            print("No active traffic messages found!")
    else:
        print(f"Error: {resp.text}")
        
except Exception as e:
    print(f"Exception: {e}")
