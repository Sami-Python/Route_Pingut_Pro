import requests
import sys
import os

# Add current directory to path so we can import the client
sys.path.append(os.getcwd())

from weather_client import get_rainviewer_data

try:
    print("Fetching data...")
    host, timestamps = get_rainviewer_data()
    
    if not timestamps:
        print("No timestamps found!")
        sys.exit(1)
        
    ts = sorted(list(timestamps.keys()))[-1]
    path = timestamps[ts]
    
    url = f"{host}{path}/256/6/32/21/6/1_1.png"
    print(f"Testing URL: {url}")
    
    response = requests.get(url, timeout=10, allow_redirects=False)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    
    if response.status_code in [301, 302, 303, 307, 308]:
        print(f"Redirect Location: {response.headers.get('Location')}")
        
        # Follow redirect manually to see where it goes
        redirect_url = response.headers.get('Location')
        if redirect_url:
            print(f"Following redirect to: {redirect_url}")
            resp2 = requests.get(redirect_url, timeout=10)
            print(f"Final Status: {resp2.status_code}")

except Exception as e:
    print(f"Error: {e}")
