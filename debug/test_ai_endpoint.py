"""
Test the AI route analysis endpoint directly
"""

import requests
import json

# Test data matching what Flutter sends
test_route_data = {
    "distance_km": 150.5,
    "duration_hours": 2.5,
    "incidents": [
        {"tyyppi": "Ruuhka", "kuvaus": "Ruuhkaa moottoritiellä", "taso": "keskivaikea"}
    ]
}

url = "http://localhost:8000/maps/analyze/route"

print(f"Testing endpoint: {url}")
print(f"Sending data: {json.dumps(test_route_data, indent=2)}")

try:
    response = requests.post(url, json=test_route_data, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"\nError: {e}")
