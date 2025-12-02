import requests
from typing import List, Tuple, Optional, Dict, Any
from shapely.geometry import LineString, shape, Point

# --------------------------------------------------------------------
# 1. LIIKENNETIEDOTTEET (SHAPELY)
# --------------------------------------------------------------------

def traffic_messages_near_route(coords: List[Tuple[float, float]], buffer_meters: int = 500) -> List[Dict[str, Any]]:
    """
    Hakee liikennehäiriöt ja suodattaa ne tarkasti reitin perusteella käyttäen Shapelyä.
    """
    if not coords:
        return []

    # HUOM: Otetaan vain lat ja lon (indeksit 0 ja 1 tai 1 ja 0), ei korkeutta
    # Shapely vaatii järjestyksen (lon, lat) eli (x, y)
    path_coords_xy = [(p[1], p[0]) for p in coords]
    
    route_line = LineString(path_coords_xy)

    # Lasketaan Bounding Box API-hakua varten
    min_x, min_y, max_x, max_y = route_line.bounds
    
    # KORJAUS 1: Pyöristetään koordinaatit 4 desimaaliin (f-string :.4f), 
    # jotta API ei kaadu liian pitkiin desimaaleihin.
    bbox_str = f"{min_x-0.2:.4f},{min_y-0.2:.4f},{max_x+0.2:.4f},{max_y+0.2:.4f}"

    url = "https://tie.digitraffic.fi/api/traffic-message/v1/messages"
    headers = {"User-Agent": "StreamlitApp/1.0 (gzip)"}
    
    params = {
        "inactiveHours": 0,
        "situationType": "TRAFFIC_ANNOUNCEMENT",
        "includeAreaGeometry": "false",
        "bbox": bbox_str
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        
        # KORJAUS 2: Jos API valittaa (esim. alue liian iso 400/413), 
        # yritetään hakea ilman bbox-rajausta (koko Suomi) ja suodatetaan itse.
        if resp.status_code in [400, 413, 414]:
            print("Digitraffic bbox fail, fetching all messages...")
            del params["bbox"]
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Digitraffic API error: {e}")
        return []

    messages = []
    
    # Muunnetaan metrit asteiksi (karkea arvio: 1 aste ~ 111km)
    buffer_degrees = buffer_meters / 111000.0

    for feature in data.get("features", []):
        try:
            # Luodaan geometria häiriöstä
            geom = shape(feature.get("geometry"))
            
            # TARKISTUS: Onko häiriö riittävän lähellä reittiä?
            if route_line.distance(geom) < buffer_degrees:
                
                props = feature.get("properties", {})
                announcements = props.get("announcements", [])
                first_ann = announcements[0] if announcements else {}

                # Koordinaattien haku turvallisesti
                msg_lat = 0.0
                msg_lon = 0.0
                if "coordinates" in feature["geometry"]:
                    c = feature["geometry"]["coordinates"]
                    # Käsitellään pisteet ja viivat
                    if isinstance(c[0], float): 
                        msg_lon, msg_lat = c[0], c[1]
                    elif isinstance(c[0], list):
                        msg_lon, msg_lat = c[0][0], c[0][1]

                messages.append({
                    "otsikko": first_ann.get("title", "Liikennetiedote"),
                    "kuvaus": first_ann.get("comment", "") or first_ann.get("description", ""),
                    "sijainti": first_ann.get("location", {}).get("description", "Alue"),
                    "aika": props.get("announcementUpdateTime"),
                    "lat": msg_lat,
                    "lon": msg_lon
                })
        except Exception:
            continue

    return messages

# --------------------------------------------------------------------
# 2. KELIKAMERAT (SHAPELY)
# --------------------------------------------------------------------

def get_weather_cameras(route_coords: List[Tuple[float, float]], buffer_meters: int = 1000) -> List[Dict[str, Any]]:
    """
    Hakee kelikamerat, jotka ovat lähellä reittiä.
    """
    if not route_coords:
        return []

    # Shapely (lon, lat)
    path_coords_xy = [(p[1], p[0]) for p in route_coords]
    
    route_line = LineString(path_coords_xy)

    min_x, min_y, max_x, max_y = route_line.bounds
    
    # KORJAUS: Pyöristys tässäkin, Digitrafficin sääkamera-API voi olla tarkka
    # Kamerat voivat olla kauempana tiestä, isompi marginaali
    # Emme käytä bboxia API-kutsussa suoraan kaikissa endpointseissa, 
    # mutta jos käyttäisimme, se pitäisi olla näin:
    # bbox_str = f"{min_x-0.2:.4f},{min_y-0.2:.4f},{max_x+0.2:.4f},{max_y+0.2:.4f}"

    url = "https://tie.digitraffic.fi/api/weathercam/v1/stations"
    headers = { "User-Agent": "StreamlitApp/1.0 (gzip)" }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
    except Exception as e:
        print(f"Camera API error: {e}")
        return []

    cameras = []
    buffer_degrees = buffer_meters / 111000.0

    # Optimointi: Laske bbox-rajat floatteina valmiiksi
    b_min_x = min_x - 0.2
    b_max_x = max_x + 0.2
    b_min_y = min_y - 0.2
    b_max_y = max_y + 0.2

    for feature in data.get("features", []):
        try:
            geom = feature.get("geometry", {})
            coords_raw = geom.get("coordinates", [])
            
            if not coords_raw or len(coords_raw) < 2: 
                continue
            
            lon, lat = float(coords_raw[0]), float(coords_raw[1])
            cam_point = Point(lon, lat)

            # 2. Nopea bbox-tarkistus (Python-puolella)
            if not (b_min_x <= lon <= b_max_x and b_min_y <= lat <= b_max_y):
                continue

            # 3. Tarkka etäisyystarkistus Shapelyllä
            if route_line.distance(cam_point) < buffer_degrees:
                
                props = feature.get("properties", {})
                station_id = props.get("id")
                presets = props.get("presets", [])
                
                image_url = f"https://weathercam.digitraffic.fi/{station_id}01.jpg"
                
                if presets:
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
        except Exception:
            continue

    return cameras