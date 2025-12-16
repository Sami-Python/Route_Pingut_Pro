import requests
import json

url = "http://127.0.0.1:8000/maps/route"
payload = {
    "origin_lat": 60.1699,
    "origin_lon": 24.9384,
    "dest_lat": 61.4978,
    "dest_lon": 23.7610,
    "alternatives": 2
}

try:
    response = requests.post(url, json=payload)
    data = response.json()
    
    print("Success:", data.get("success"))
    if "alternatives" in data:
        print(f"Alternatives count: {len(data['alternatives'])}")
        for i, alt in enumerate(data['alternatives']):
            print(f"Route {i+1}:")
            print(f"  Distance: {alt.get('distance_km')}")
            print(f"  Duration: {alt.get('duration_hours')}")
            # print(f"  Coords count: {len(alt.get('coordinates', []))}")
    else:
        print("No 'alternatives' key in response.")
        
except Exception as e:
    print(f"Error: {e}")
