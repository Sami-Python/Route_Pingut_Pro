
import requests
import json
import datetime

def test_route_http():
    url = "http://localhost:8000/maps/route"
    
    # HSL -> Oulu (Long distance to ensure polyline)
    payload = {
        "origin_lat": 60.17116,
        "origin_lon": 24.93265,
        "dest_lat": 65.01035,
        "dest_lon": 25.47357,
        "departure_time": datetime.datetime.now().isoformat()
    }
    
    print(f"Sending POST to {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        resp = requests.post(url, json=payload)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                print("SUCCESS: Route calculation successful!")
                print(f"Distance: {data.get('distance_km')} km")
                print(f"Duration: {data.get('duration_hours')} h")
                if data.get("polyline"):
                     print(f"Polyline received (len={len(data['polyline'])})")
            else:
                print(f"FAILURE: Route failed logically: {data}")
        else:
            print(f"FAILURE: HTTP Request failed: {resp.status_code}")
            print(f"Response: {resp.text}")
            
    except Exception as e:
        print(f"FAILURE: Exception: {e}")

if __name__ == "__main__":
    test_route_http()
