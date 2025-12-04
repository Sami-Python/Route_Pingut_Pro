import requests
import sys
import os
from io import BytesIO
from PIL import Image

# Add current directory to path so we can import the client
sys.path.append(os.getcwd())

from weather_client import get_rainviewer_data

def is_tile_empty(content):
    try:
        img = Image.open(BytesIO(content))
        extrema = img.getextrema()
        if extrema:
            # For RGBA, extrema is a list of tuples. Look at Alpha channel (index 3).
            # If min and max alpha are both 0, it's fully transparent.
            if len(extrema) == 4:
                alpha_min, alpha_max = extrema[3]
                return alpha_max == 0
            # For L or P mode, it might be different.
            # But RainViewer usually returns RGBA or P with transparency.
        return False # Assume not empty if we can't tell
    except Exception:
        return True

try:
    print("Fetching metadata...")
    host, timestamps = get_rainviewer_data()
    
    if not timestamps:
        print("No timestamps found!")
        sys.exit(1)
        
    # Check the last few timestamps (nowcast)
    sorted_ts = sorted(list(timestamps.keys()))
    recent_ts = sorted_ts[-3:]
    
    print(f"Checking timestamps: {recent_ts}")
    
    # Helsinki coordinates approx: 60.17, 24.94
    # Zoom 6 tile:
    # x = 24.94 -> (24.94 + 180) / 360 * 64 = 36.4 -> 36
    # y = 60.17 -> ... approx 19
    
    # Let's check a 3x3 grid around Helsinki at zoom 6
    center_x = 36
    center_y = 19
    zoom = 6
    
    found_rain = False
    
    for ts in recent_ts:
        path = timestamps[ts]
        print(f"\nTimestamp: {ts} (Path: {path})")
        
        for x in range(center_x - 1, center_x + 2):
            for y in range(center_y - 1, center_y + 2):
                url = f"{host}{path}/256/{zoom}/{x}/{y}/6/1_1.png"
                try:
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        if not is_tile_empty(resp.content):
                            print(f"  [FOUND RAIN] Tile {x}/{y}: {len(resp.content)} bytes - URL: {url}")
                            found_rain = True
                        else:
                            # print(f"  [Empty] Tile {x}/{y}")
                            pass
                    else:
                        print(f"  [Error] Tile {x}/{y}: Status {resp.status_code}")
                except Exception as e:
                    print(f"  [Exception] {e}")

    if not found_rain:
        print("\nNo rain detected in the scanned area (Helsinki region).")
        print("This suggests RainViewer data might be empty for this region right now.")
    else:
        print("\nRain detected in some tiles!")

except Exception as e:
    print(f"Error: {e}")
