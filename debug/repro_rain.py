import requests
import sys
import os

# Add current directory to path so we can import the client
sys.path.append(os.getcwd())

from weather_client import get_rainviewer_data

def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            return True
        else:
            print("Failed.")
            return False
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return False

try:
    print("Fetching data using updated client...")
    host, timestamps = get_rainviewer_data()
    print(f"Host: {host}")
    print(f"Found {len(timestamps)} timestamps.")
    
    if not timestamps:
        print("No timestamps found!")
        sys.exit(1)
        
    # Test the last timestamp
    ts = sorted(list(timestamps.keys()))[-1]
    path = timestamps[ts]
    
    print(f"Testing timestamp: {ts}")
    print(f"Path: {path}")
    
    # Construct URL using the logic from app.py
    url = f"{host}{path}/256/6/32/21/6/1_1.png"
    
    if check_url(url):
        print("\nVERIFICATION PASSED: URL is valid.")
    else:
        print("\nVERIFICATION FAILED: URL is invalid.")
        sys.exit(1)

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
