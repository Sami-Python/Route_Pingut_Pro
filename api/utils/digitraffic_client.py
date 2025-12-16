import requests
from typing import List, Tuple, Optional, Dict, Any
from shapely.geometry import LineString, shape, Point
import datetime

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
    
    # KORJAUS 1: Pyöristetään koordinaatit
    bbox_str = f"{min_x-0.2:.4f},{min_y-0.2:.4f},{max_x+0.2:.4f},{max_y+0.2:.4f}"

    # KORJAUS 3: Tarkistetaan alueen koko. Jos liian iso, ei käytetä bboxia ollenkaan.
    # Digitrafficilla on rajat, ja isoilla alueilla on varmempaa hakea kaikki.
    bbox_too_large = (max_x - min_x) > 1.5 or (max_y - min_y) > 1.5

    url = "https://tie.digitraffic.fi/api/traffic-message/v1/messages"
    headers = {"User-Agent": "StreamlitApp/1.0 (gzip)"}
    
    params = {
        "inactiveHours": 0,
        "situationType": "TRAFFIC_ANNOUNCEMENT",
        "includeAreaGeometry": "false"
    }
    
    # Käytetään bboxia vain jos alue on järkevän kokoinen
    if not bbox_too_large:
        params["bbox"] = bbox_str

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        
        # Jos bbox failaa silti, yritetään ilman (fallback)
        if resp.status_code in [400, 413, 414] and "bbox" in params:
            # print("Digitraffic bbox fail, fetching all messages...") # Hiljennetään printti
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
                # Koordinaattien haku turvallisesti
                def get_first_point(coords):
                    if not coords: return 0.0, 0.0
                    # If first element is float/int, we are at the point level [lon, lat]
                    if isinstance(coords[0], (float, int)):
                         return coords[0], coords[1]
                    # Recurse down
                    return get_first_point(coords[0])

                msg_lon, msg_lat = 0.0, 0.0
                if "coordinates" in feature["geometry"]:
                    c = feature["geometry"]["coordinates"]
                    msg_lon, msg_lat = get_first_point(c)

                messages.append({
                    "otsikko": first_ann.get("title", "Liikennetiedote"),
                    "kuvaus": first_ann.get("comment", "") or first_ann.get("description", ""),
                    "sijainti": first_ann.get("location", {}).get("description", "Alue"),
                    "aika": props.get("announcementUpdateTime"),
                    "lat": msg_lat,
                    "lon": msg_lon,
                    "id": feature.get("id")
                })
        except Exception:
            continue

    return messages

def traffic_messages_near_point(lat: float, lon: float, radius: float = 50.0) -> List[Dict[str, Any]]:
    """Hakee liikennetiedotteet tietyn pisteen ympäriltä (säde km)."""
    # 1 deg ~ 111km
    radius_deg = radius / 111.0
    min_lat, max_lat = lat - radius_deg, lat + radius_deg
    min_lon, max_lon = lon - (radius_deg * 2), lon + (radius_deg * 2)
    
    bbox_str = f"{min_lon:.4f},{min_lat:.4f},{max_lon:.4f},{max_lat:.4f}" # x,y,x,y

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
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Digitraffic Message API error: {e}")
        return []

    messages = []
    center = Point(lon, lat)
    
    for feature in data.get("features", []):
        try:
            # Luodaan geometria
            geom = shape(feature.get("geometry"))
            # Jos geometria on kaukana keskipisteestä, skipataan (tarkempi tsekkaus)
            # Yksinkertaistus: jos se on bboxissa, se on mukana.
            # Mutta voidaan laskea etäisyys jos halutaan tarkka radius.
            
            props = feature.get("properties", {})
            announcements = props.get("announcements", [])
            first_ann = announcements[0] if announcements else {}

            # Koordinaattien selvitys
            # Koordinaattien selvitys
            def get_first_point(coords):
                if not coords: return 0.0, 0.0
                if isinstance(coords[0], (float, int)):
                        return coords[0], coords[1]
                return get_first_point(coords[0])

            msg_lon, msg_lat = 0.0, 0.0
            if "coordinates" in feature["geometry"]:
                c = feature["geometry"]["coordinates"]
                msg_lon, msg_lat = get_first_point(c)

            messages.append({
                "otsikko": first_ann.get("title", "Liikennetiedote"),
                "kuvaus": first_ann.get("comment", "") or first_ann.get("description", ""),
                "sijainti": first_ann.get("location", {}).get("description", "Alue"),
                "aika": props.get("announcementUpdateTime"),
                "lat": msg_lat,
                "lon": msg_lon,
                "id": feature.get("id")
            })
        except Exception:
            continue

    return messages

# --------------------------------------------------------------------
# 2. KELIKAMERAT (SHAPELY)
# --------------------------------------------------------------------

def fetch_weather_cam_data() -> Dict[str, Any]:
    """Hakee kelikameroiden metatiedot API:sta."""
    url = "https://tie.digitraffic.fi/api/weathercam/v1/stations"
    headers = { "User-Agent": "StreamlitApp/1.0 (gzip)", "Accept-Encoding": "gzip" }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"Camera API error: {e}")
        return {}

def filter_weather_cameras(route_coords: List[Tuple[float, float]], data: Dict[str, Any], buffer_meters: int = 1000) -> List[Dict[str, Any]]:
    """Suodattaa haetut kelikamerat reitin perusteella."""
    if not route_coords or not data:
        return []

    path_coords_xy = [(p[1], p[0]) for p in route_coords]
    route_line = LineString(path_coords_xy)
    min_x, min_y, max_x, max_y = route_line.bounds
    
    cameras = []
    buffer_degrees = buffer_meters / 111000.0

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

            if not (b_min_x <= lon <= b_max_x and b_min_y <= lat <= b_max_y):
                continue

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

def get_weather_cameras(route_coords: List[Tuple[float, float]], buffer_meters: int = 1000) -> List[Dict[str, Any]]:
    data = fetch_weather_cam_data()
    return filter_weather_cameras(route_coords, data, buffer_meters)

def get_weather_cameras_by_point(lat: float, lon: float, radius: float = 50.0) -> List[Dict[str, Any]]:
    """Hakee kelikamerat tietyn pisteen ympäriltä (säde km)."""
    data = fetch_weather_cam_data()
    if not data: return []
    
    cameras = []
    # Karkea laatikkorajaus optimointia varten (1 deg lat ~ 111km)
    radius_deg = radius / 111.0
    min_lat, max_lat = lat - radius_deg, lat + radius_deg
    min_lon, max_lon = lon - (radius_deg * 2), lon + (radius_deg * 2) # Lon vaihtelee enemmän
    
    center = Point(lon, lat)
    
    for feature in data.get("features", []):
        try:
            geom = feature.get("geometry", {})
            coords_raw = geom.get("coordinates", [])
            if not coords_raw or len(coords_raw) < 2: continue
            
            c_lon, c_lat = float(coords_raw[0]), float(coords_raw[1])
            
            if not (min_lon <= c_lon <= max_lon and min_lat <= c_lat <= max_lat):
                continue
                
            p = Point(c_lon, c_lat)
            # Distance in degrees approx
            if center.distance(p) * 111.0 <= radius:
                 props = feature.get("properties", {})
                 station_id = props.get("id")
                 presets = props.get("presets", [])
                 image_url = f"https://weathercam.digitraffic.fi/{station_id}01.jpg"
                 if presets:
                     best = next((p for p in presets if "01" in p.get("id", "")), presets[0])
                     if "imageUrl" in best: image_url = best["imageUrl"]
                     
                 cameras.append({
                    "id": station_id,
                    "name": props.get("names", {}).get("fi", "Kelikamera"),
                    "lat": c_lat,
                    "lon": c_lon,
                    "imageUrl": image_url
                 })
        except:
            continue
    return cameras

# --------------------------------------------------------------------
# 3. TIESÄÄ (Road Weather)
# --------------------------------------------------------------------

def fetch_road_weather_data() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    url_meta = "https://tie.digitraffic.fi/api/weather/v1/stations"
    url_data = "https://tie.digitraffic.fi/api/weather/v1/stations/data"
    headers = { "User-Agent": "StreamlitApp/1.0 (gzip)", "Accept-Encoding": "gzip" }
    try:
        resp_meta = requests.get(url_meta, headers=headers, timeout=10)
        resp_data = requests.get(url_data, headers=headers, timeout=10)
        return resp_meta.json(), resp_data.json()
    except Exception as e:
        print(f"Road Weather API error: {e}")
        return {}, {}

def filter_road_weather_stations(route_coords: List[Tuple[float, float]], meta_json: Dict, data_json: Dict, buffer_meters: int = 2000) -> List[Dict[str, Any]]:
    if not route_coords or not meta_json:
        return []

    path_coords_xy = [(p[1], p[0]) for p in route_coords]
    route_line = LineString(path_coords_xy)
    
    data_lookup = {}
    for st_data in data_json.get("stations", []):
        sid = st_data.get("id")
        vals = {}
        for s in st_data.get("sensorValues", []):
            if s["id"] == 1: vals["air_temp"] = s["value"]
            if s["id"] == 3: vals["road_temp"] = s["value"]
        data_lookup[sid] = vals

    stations = []
    buffer_degrees = buffer_meters / 111000.0
    
    for feature in meta_json.get("features", []):
        try:
            geom = feature.get("geometry", {})
            coords_raw = geom.get("coordinates", [])
            if not coords_raw or len(coords_raw) < 2: continue
            
            lon, lat = float(coords_raw[0]), float(coords_raw[1])
            point = Point(lon, lat)

            if route_line.distance(point) < buffer_degrees:
                props = feature.get("properties", {})
                sid = props.get("id")
                vals = data_lookup.get(sid, {})
                
                raw_name = props.get("name", "Sääasema")
                clean_name = raw_name.replace("_", " ")
                
                parts = raw_name.split("_")
                municipality = ""
                road_num = ""
                if len(parts) >= 2:
                    if parts[0].lower().startswith(("vt", "kt", "st")) or parts[0].isdigit():
                        road_num = parts[0]
                        municipality = parts[1]
                
                stations.append({
                    "id": sid,
                    "name": clean_name,
                    "lat": lat,
                    "lon": lon,
                    "air_temp": vals.get("air_temp"),
                    "road_temp": vals.get("road_temp"),
                    "municipality": municipality,
                    "road_number": road_num
                })
        except:
            continue

    return stations

def get_road_weather_stations(route_coords: List[Tuple[float, float]], buffer_meters: int = 2000) -> List[Dict[str, Any]]:
    m, d = fetch_road_weather_data()
    return filter_road_weather_stations(route_coords, m, d, buffer_meters)

def get_road_weather_stations_by_point(lat: float, lon: float, radius: float = 50.0) -> List[Dict[str, Any]]:
    """Hakee tiesääasemat tietyn pisteen ympäriltä."""
    m, d = fetch_road_weather_data()
    if not m: return []
    
    data_lookup = {}
    for st_data in d.get("stations", []):
        sid = st_data.get("id")
        vals = {}
        for s in st_data.get("sensorValues", []):
            if s["id"] == 1: vals["air_temp"] = s["value"]
            if s["id"] == 3: vals["road_temp"] = s["value"]
        data_lookup[sid] = vals

    stations = []
    radius_deg = radius / 111.0
    min_lat, max_lat = lat - radius_deg, lat + radius_deg
    min_lon, max_lon = lon - (radius_deg * 2), lon + (radius_deg * 2)
    center = Point(lon, lat)

    for feature in m.get("features", []):
        try:
            geom = feature.get("geometry", {})
            coords_raw = geom.get("coordinates", [])
            if not coords_raw or len(coords_raw) < 2: continue
            
            c_lon, c_lat = float(coords_raw[0]), float(coords_raw[1])
            if not (min_lon <= c_lon <= max_lon and min_lat <= c_lat <= max_lat):
                continue
            
            p = Point(c_lon, c_lat)
            if center.distance(p) * 111.0 <= radius:
                props = feature.get("properties", {})
                sid = props.get("id")
                vals = data_lookup.get(sid, {})
                
                raw_name = props.get("name", "Sääasema")
                clean_name = raw_name.replace("_", " ")
                
                parts = raw_name.split("_")
                municipality = ""
                road_num = ""
                if len(parts) >= 2:
                    if parts[0].lower().startswith(("vt", "kt", "st")) or parts[0].isdigit():
                        road_num = parts[0]
                        municipality = parts[1]

                stations.append({
                    "id": sid,
                    "name": clean_name,
                    "lat": c_lat,
                    "lon": c_lon,
                    "air_temp": vals.get("air_temp"),
                    "road_temp": vals.get("road_temp"),
                    "municipality": municipality,
                    "road_number": road_num
                })
        except:
             continue
    return stations

def fetch_vms_data() -> Dict[str, Any]:
    url = "https://tie.digitraffic.fi/api/variable-sign/v1/signs"
    headers = { "User-Agent": "StreamlitApp/1.0 (gzip)", "Accept-Encoding": "gzip" }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"VMS API error: {e}")
        return {}

def filter_vms_stations(route_coords: List[Tuple[float, float]], data: Dict[str, Any], buffer_meters: int = 1000) -> List[Dict[str, Any]]:
    if not route_coords or not data: return []
    
    path_coords_xy = [(p[1], p[0]) for p in route_coords]
    route_line = LineString(path_coords_xy)
    buffer_degrees = buffer_meters / 111000.0

    vms_points = []
    for feature in data.get("features", []):
        try:
            geom = feature.get("geometry", {})
            c = geom.get("coordinates", [])
            if not c or len(c) < 2: continue
            
            lon, lat = float(c[0]), float(c[1])
            point = Point(lon, lat)
            
            if route_line.distance(point) < buffer_degrees:
                props = feature.get("properties", {})
                sid = props.get("id")
                
                display_value = props.get("displayValue")
                if not display_value:
                    rows = props.get("textRows", [])
                    if rows:
                        display_value = " | ".join([r.get("screenText", "") for r in rows])
                
                if not display_value:
                    display_value = props.get("type", "VMS")

                vms_points.append({
                    "id": sid,
                    "lat": lat,
                    "lon": lon,
                    "name": f"{display_value}",
                    "type": props.get("type", "UNKNOWN")
                })
        except:
            continue
            
    return vms_points

def get_vms_stations(route_coords: List[Tuple[float, float]], buffer_meters: int = 1000) -> List[Dict[str, Any]]:
    d = fetch_vms_data()
    return filter_vms_stations(route_coords, d, buffer_meters)

# --------------------------------------------------------------------
# 5. KUNNOSSAPITO (Maintenance)
# --------------------------------------------------------------------

def get_maintenance_data(route_coords: List[Tuple[float, float]], buffer_meters: int = 5000) -> List[Dict[str, Any]]:
    """
    Hakee kunnossapitotiedot (esim. auraus) reitin alueelta.
    """
    if not route_coords: return []
    
    path_coords_xy = [(p[1], p[0]) for p in route_coords]
    route_line = LineString(path_coords_xy)
    min_x, min_y, max_x, max_y = route_line.bounds
    
    import time
    end_time = int(time.time() * 1000)
    start_time = end_time - (12 * 3600 * 1000) 
    
    url = f"https://tie.digitraffic.fi/api/maintenance/v1/tracking/routes?endFrom={start_time}&endBefore={end_time}&xMin={min_x-0.1}&yMin={min_y-0.1}&xMax={max_x+0.1}&yMax={max_y+0.1}"
    headers = { 
        "User-Agent": "StreamlitApp/1.0 (gzip)",
        "Accept-Encoding": "gzip"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
    except Exception as e:
        print(f"Maintenance API error: {e}")
        return []
        
    tasks = []
    for feature in data.get("features", []):
        try:
            # Maintenance data on usein MultiLineString
            geom = shape(feature.get("geometry"))
            if route_line.distance(geom) < (buffer_meters / 111000.0):
                props = feature.get("properties", {})
                tasks.append({
                    "id": props.get("id"),
                    "task": props.get("tasks", ["Huolto"])[0],
                    "time": props.get("endTime"),
                    "geometry": feature.get("geometry")
                })
        except:
            continue
            
    return tasks

# --------------------------------------------------------------------
# 6. LAM (Liikennemäärät)
# --------------------------------------------------------------------

def fetch_lam_data() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    url_meta = "https://tie.digitraffic.fi/api/tms/v1/stations"
    url_data = "https://tie.digitraffic.fi/api/tms/v1/stations/data"
    headers = { "User-Agent": "StreamlitApp/1.0 (gzip)", "Accept-Encoding": "gzip" }
    try:
        resp_meta = requests.get(url_meta, headers=headers, timeout=10)
        resp_data = requests.get(url_data, headers=headers, timeout=10)
        return resp_meta.json(), resp_data.json()
    except Exception as e:
        print(f"LAM API error: {e}")
        return {}, {}

def filter_lam_stations(route_coords: List[Tuple[float, float]], meta_json: Dict, data_json: Dict, buffer_meters: int = 1000) -> List[Dict[str, Any]]:
    if not route_coords or not meta_json: return []
    
    path_coords_xy = [(p[1], p[0]) for p in route_coords]
    route_line = LineString(path_coords_xy)
    buffer_degrees = buffer_meters / 111000.0

    data_lookup = {}
    for st_data in data_json.get("stations", []):
        sid = st_data.get("id")
        vals = {}
        for s in st_data.get("sensorValues", []):
            if s["id"] in [5122, 5169]: vals["speed"] = s["value"]
            if s["id"] in [5116, 5163]: vals["volume"] = s["value"]
        data_lookup[sid] = vals

    results = []
    for feature in meta_json.get("features", []):
        try:
            geom = feature.get("geometry", {})
            c = geom.get("coordinates", [])
            if not c or len(c) < 2: continue
            
            lon, lat = float(c[0]), float(c[1])
            point = Point(lon, lat)
            
            if route_line.distance(point) < buffer_degrees:
                props = feature.get("properties", {})
                sid = props.get("id")
                vals = data_lookup.get(sid, {})
                
                results.append({
                    "id": sid,
                    "name": props.get("names", {}).get("fi", "LAM"),
                    "lat": lat,
                    "lon": lon,
                    "speed": vals.get("speed"),
                    "volume": vals.get("volume")
                })
        except:
            continue
        
    return results

def get_lam_stations(route_coords: List[Tuple[float, float]], buffer_meters: int = 1000) -> List[Dict[str, Any]]:
    m, d = fetch_lam_data()
    return filter_lam_stations(route_coords, m, d, buffer_meters)

def get_lam_stations_by_point(lat: float, lon: float, radius: float = 50.0) -> List[Dict[str, Any]]:
    """Hakee LAM-asemat säteen sisällä pisteestä geo-etäisyyden perusteella."""
    m, d = fetch_lam_data()
    if not m: return []

    data_lookup = {}
    for st_data in d.get("stations", []):
        sid = st_data.get("id")
        vals = {}
        for s in st_data.get("sensorValues", []):
            if s["id"] in [5122, 5169]: vals["speed"] = s["value"]
            if s["id"] in [5116, 5163]: vals["volume"] = s["value"]
        data_lookup[sid] = vals

    results = []
    center_point = Point(lon, lat)
    # Radius in degrees approx (1 deg ~ 111km)
    buffer_degrees = radius / 111.0 

    for feature in m.get("features", []):
        try:
            geom = feature.get("geometry", {})
            c = geom.get("coordinates", [])
            if not c or len(c) < 2: continue
            
            p_lon, p_lat = float(c[0]), float(c[1])
            station_point = Point(p_lon, p_lat)
            
            if center_point.distance(station_point) <= buffer_degrees:
                props = feature.get("properties", {})
                sid = props.get("id")
                vals = data_lookup.get(sid, {})
                results.append({
                    "id": sid,
                    "name": props.get("names", {}).get("fi", "LAM"),
                    "lat": p_lat,
                    "lon": p_lon,
                    "speed": vals.get("speed"),
                    "volume": vals.get("volume")
                })
        except:
            continue
            
    return results

def get_road_weather_history(station_id: int) -> List[Dict[str, Any]]:
    """
    Hakee tiesääaseman historiatiedot (viimeiset 12h).
    """
    import datetime
    
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(hours=12)
    
    # ISO format for API
    from_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = f"https://tie.digitraffic.fi/api/weather/v1/stations/{station_id}/data/history?from={from_str}"
    headers = { "User-Agent": "StreamlitApp/1.0 (gzip)", "Accept-Encoding": "gzip" }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        history = []
        for item in data:
            ts = item.get("measuredTime")
            air = None
            road = None
            for s in item.get("sensorValues", []):
                if s["id"] == 1: air = s["value"]
                if s["id"] == 3: road = s["value"]
            
            if air is not None or road is not None:
                history.append({
                    "time": ts,
                    "air_temp": air,
                    "road_temp": road
                })
        return history
    except Exception as e:
        print(f"History API error: {e}")
        return []