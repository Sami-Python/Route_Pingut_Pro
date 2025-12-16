
import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("HERE_API_KEY")
print(f"API Key found: {'Yes' if key else 'No'} (Length: {len(key) if key else 0})")

if not key:
    exit(1)

# Helsinki coordinates roughly z=7, x=75, y=38 (from user error)
# Note: User error URL was /7/75/38.
z, x, y = 7, 75, 38

url = f"https://traffic.ls.hereapi.com/traffic/1.0/flowtile/png/{z}/{x}/{y}/256/png8?apiKey={key}"
print(f"Testing URL: {url.replace(key, 'HIDDEN_KEY')}")

try:
    resp = requests.get(url, timeout=10)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Success! Content length: {len(resp.content)} bytes")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
