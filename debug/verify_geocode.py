import requests
import sys

def test_geocode():
    url = "http://localhost:8000/maps/geocode"
    params = {"address": "Helsinki"}
    try:
        print(f"Requesting {url} with params {params}...")
        resp = requests.get(url, params=params)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                print("✅ Geocoding successful!")
            else:
                print("❌ Geocoding failed (success=False).")
        else:
            print("❌ Request failed.")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_geocode()
