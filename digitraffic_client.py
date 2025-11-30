import requests
from typing import List, Tuple, Optional, Dict, Any

# --------------------------------------------------------------------
# 1. APUFUNKTIOT
# --------------------------------------------------------------------

def get_bounds(route_coords: List[Tuple[float, float]], margin: float = 0.1) -> Optional[Tuple[float, float, float, float]]:
    if not route_coords: return None
    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]
    return (min(lats) - margin, min(lons) - margin, max(lats) + margin, max(lons) + margin)

def calculate_bbox(route_coords: List[Tuple[float, float]]) -> Optional[str]:
    bounds = get_bounds(route_coords, margin=0.05)
    if not bounds: return None
    return f"{bounds[1]},{bounds[0]},{bounds[3]},{bounds[2]}"

def extract_single_coordinate(geometry: Dict[str, Any]) -> Tuple[float, float]:
    coords = geometry.get("coordinates", [])
    if not coords: return 0.0, 0.0
    try:
        if isinstance(coords[0], (float, int)): return float(coords[1]), float(coords[0])
        if isinstance(coords[0], list) and isinstance(coords[0][0], (float, int)): return float(coords[0][1]), float(coords[0][0])
    except: pass
    return 0.0, 0.0

# --------------------------------------------------------------------
# 2. LIIKENNETIEDOTTEET
# --------------------------------------------------------------------

def traffic_messages_near_route(coords: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
    url = "https://tie.digitraffic.fi/api/traffic-message/v1/messages"
    params = {"inactiveHours": 0, "situationType": "TRAFFIC_ANNOUNCEMENT", "includeAreaGeometry": "false"}
    headers = {"User-Agent": "StreamlitApp/1.0 (gzip)"}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        messages = []
        bounds = get_bounds(coords)
        for feature in data.get("features", []):
            geometry = feature.get("geometry", {})
            props = feature.get("properties", {})
            msg_lat, msg_lon = extract_single_coordinate(geometry)
            if bounds and msg_lat != 0.0:
                min_lat, min_lon, max_lat, max_lon = bounds
                if not (min_lat <= msg_lat <= max_lat and min_lon <= msg_lon <= max_lon): continue
            announcements = props.get("announcements", [])
            first_ann = announcements[0] if announcements else {}
            messages.append({
                "otsikko": first_ann.get("title", "Liikennetiedote"),
                "kuvaus": first_ann.get("comment", "") or first_ann.get("description", ""),
                "sijainti": first_ann.get("location", {}).get("description", "Alue"),
                "aika": props.get("announcementUpdateTime"),
                "lat": msg_lat,
                "lon": msg_lon
            })
        return messages
    except: return []

# --------------------------------------------------------------------
# 3. KELIKAMERAT
# --------------------------------------------------------------------

def get_weather_cameras(route_coords: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
    url = "https://tie.digitraffic.fi/api/weathercam/v1/stations"
    headers = { "User-Agent": "StreamlitApp/1.0 (gzip)" }
    bounds = get_bounds(route_coords, margin=0.15)
    if not bounds: return []
    min_lat, min_lon, max_lat, max_lon = bounds
    cameras = []
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        for feature in data.get("features", []):
            coords_raw = feature.get("geometry", {}).get("coordinates", [])
            if not coords_raw or len(coords_raw) < 2: continue
            lon, lat = float(coords_raw[0]), float(coords_raw[1])
            
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                props = feature.get("properties", {})
                station_id = props.get("id")
                presets = props.get("presets", [])
                
                # PARANNETTU URL-LOGIIKKA
                # Oletus: asemaID + "01" (yleisin pääkamera)
                image_url = f"https://weathercam.digitraffic.fi/{station_id}01.jpg"
                
                # Jos API kertoo tarkemman URLin, käytetään sitä
                if presets:
                    # Etsitään ID, joka sisältää "01"
                    best_preset = next((p for p in presets if "01" in p.get("id", "")), presets[0])
                    if "imageUrl" in best_preset:
                        image_url = best_preset["imageUrl"]

                cameras.append({
                    "id": station_id,
                    "name": props.get("names", {}).get("fi", "Kelikamera"),
                    "lat": lat,
                    "lon": lon,
                    "imageUrl": image_url
                })
        return cameras
    except Exception as e:
        print(f"Camera error: {e}")
        return []

def tms_near_route(coords): return []