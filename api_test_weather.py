
import requests
import datetime

def test_backend_weather():
    url = "http://localhost:8000/weather/route-coords"
    
    # Test parameters
    params = {
        "from_lat": 60.1699,
        "from_lon": 24.9384,
        "to_lat": 61.4978,
        "to_lon": 23.7610,
        "hours": 6,
        "start_time": datetime.datetime.utcnow().isoformat()
    }
    
    print(f"Testing URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Response JSON keys:", response.json().keys())
            print("Success! Backend supports start_time.")
        else:
            print("Error response:", response.text)
            
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Make sure the backend is running on port 8000!")

if __name__ == "__main__":
    test_backend_weather()
