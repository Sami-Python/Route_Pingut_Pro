import requests
import json

try:
    resp = requests.get('https://tie.digitraffic.fi/api/weather/v1/stations')
    data = resp.json()
    # Print first 2 stations properties
    for i in range(2):
        print(json.dumps(data['features'][i]['properties'], indent=2))
except Exception as e:
    print(e)
