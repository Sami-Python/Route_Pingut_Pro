import requests
import json

def check_routes():
    base_url = "http://localhost:8000"
    
    print("--- Checking Main API Docs ---")
    try:
        resp = requests.get(f"{base_url}/openapi.json")
        if resp.status_code == 200:
            data = resp.json()
            paths = list(data.get("paths", {}).keys())
            print(f"Main API Paths ({len(paths)}):")
            for p in paths:
                print(f"  {p}")
        else:
            print(f"Failed to get main openapi.json: {resp.status_code}")
    except Exception as e:
        print(f"Error fetching main docs: {e}")

    print("\n--- Checking Maps API Docs ---")
    try:
        resp = requests.get(f"{base_url}/maps/openapi.json")
        if resp.status_code == 200:
            data = resp.json()
            paths = list(data.get("paths", {}).keys())
            print(f"Maps API Paths ({len(paths)}):")
            for p in paths:
                print(f"  {p}")
        else:
            print(f"Failed to get maps openapi.json: {resp.status_code}")
            # Try /maps/api/openapi.json just in case?
    except Exception as e:
        print(f"Error fetching maps docs: {e}")

    print("\n--- Checking Geocode Explicitly ---")
    test_urls = [
        "/maps/geocode",
        "/maps/api/geocode",
        "/api/maps/geocode",
        "/geocode"
    ]
    for url in test_urls:
        full_url = f"{base_url}{url}"
        try:
            resp = requests.get(full_url, params={"address": "Helsinki"})
            print(f"{url}: {resp.status_code}")
        except:
            print(f"{url}: Error")

if __name__ == "__main__":
    check_routes()
