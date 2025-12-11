import streamlit as st
st.set_page_config(page_title="Reitti Pro", layout="wide")

import flexpolyline
from typing import Tuple, List, Optional, Dict, Any
import datetime
import time
import math
import tempfile
import json
import pydeck as pdk
from pydeck.data_utils import compute_view
from dotenv import load_dotenv, set_key
import os
from streamlit_js_eval import get_geolocation
import requests
# import streamlit_calendar  # REMOVED - causes infinite reruns
# from streamlit_calendar import calendar  # REMOVED - causes infinite reruns
import altair as alt
import pandas as pd
import numpy as np

# 1. Ladataan ympäristömuuttujat
load_dotenv()

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
pdk.settings.mapbox_api_key = MAPBOX_TOKEN
API_URL = os.getenv("API_URL", "http://localhost:8001")
API_URL_INTERNAL = "http://api:8000"
API_URL_EXTERNAL = "http://localhost:8000"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ttm-ollama-server:11434")

# 2. Tuodaan funktiot
from utils.here_client import geocode, route, parse_traffic_incidents
from utils.digitraffic_client import (
    get_weather_cameras, 
    traffic_messages_near_route, 
    get_road_weather_stations, 
    get_vms_stations, 
    get_maintenance_data, 
    get_lam_stations,
    get_road_weather_history
)
from utils.weather_client import get_rainviewer_data, get_closest_timestamp

# AI Route Analysis
from utils.route_intelligence import RouteIntelligence
from utils.ai_analyzer import GeminiRouteAnalyzer

# ====================================================================
# CALENDAR HELPERS
# ====================================================================

@st.cache_data(ttl=300)
def _add_gcal_events(token: str):
    """Hakee tapahtumat Google Calendarista."""
    events = []
    try:
        # Oletetaan, että api_server on localhost:8000
        # Huom: API_URL on määritelty ylempänä
        resp = requests.get(f"{API_URL}/gcal/events", params={"token": token}, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            for event in data:
                evt = {
                    "title": f"🗓️ {event.get('title', 'No Title')}", # Erotellaan GCal visuaalisesti
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "color": "#4285F4", # Google Blue
                    "extendedProps": {
                        "location": event.get("location"),
                        "source": "google"
                    }
                }
                if event.get("location"):
                    evt["title"] += f" (@ {event.get('location')})"
                events.append(evt)
        elif resp.status_code == 401:
            return None # Token vanhentunut
    except Exception as e:
        print(f"GCal fetch error: {e}")
    return events

@st.cache_data(ttl=600)
def _add_ical_events(url: str):
    """Hakee tapahtumat annetusta iCal-URL:sta."""
    events = []
    try:
        # Tässä oletetaan, että meillä on joku API endpoint joka palauttaa JSONia iCal URLista
        # Mutta koska api_server.py:ssä on /ical/events, käytetään sitä jos mahdollista.
        # Oletetaan, että api_server on pystyssä localhost:8000. 

        # Korjattu localhost -> api, ovat samassa verkossa dockerissa, localhost osoittaa dockerin itseensä, api on toisessa dockerissa
        resp = requests.get("http://api:8000/ical/events", params={"url": url}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            for event in data:
                evt = {
                    "title": event.get("title", "No Title"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "extendedProps": {
                        "location": event.get("location")
                    }
                }
                if event.get("location"):
                    evt["title"] += f" (@ {event.get('location')})"
                events.append(evt)
    except Exception as e:
        print(f"Calendar fetch error: {e}")
    return events

# ====================================================================
# API WRAPPERS
# ====================================================================

@st.cache_data(ttl=600)
def get_cached_route(origin: Tuple[float, float], 
                     dest: Tuple[float, float], 
                     dep_time: str = None,
                     arr_time: str = None,
                     mode: str = "fastest",
                     avoid_list: List[str] = [],
                     alternatives: int = 0):
    return route(origin, dest, departure_time=dep_time, arrival_time=arr_time, routing_mode=mode, avoid_features=avoid_list, alternatives=alternatives)

@st.cache_data(ttl=3600)
def geocode_cached(query: str):
    return geocode(query)

@st.cache_data(ttl=300)
def get_cached_weather_data():
    return get_rainviewer_data()

def extract_route_summary(route_section: Dict[str, Any]) -> Optional[Tuple[float, float, float]]:
    try:
        summary = route_section["summary"]
        # Palautetaan (pituus_km, kesto_h, kesto_ilman_liikennettä_h)
        return (
            summary["length"] / 1000.0, 
            summary["duration"] / 3600.0,
            summary.get("baseDuration", summary["duration"]) / 3600.0
        )
    except Exception:
        return None

# ====================================================================
# VISUALIZATION HELPERS (OPEN-METEO)
# ====================================================================

# Temperature color scale
TEMP_COLORS = {
    -30: [139, 0, 139], -20: [0, 0, 255], -10: [0, 191, 255],
    0: [173, 216, 230], 5: [255, 255, 255], 10: [255, 255, 200],
    15: [255, 255, 0], 20: [255, 200, 0], 25: [255, 165, 0],
    30: [255, 100, 0], 35: [255, 0, 0]
}

def get_color_for_temperature(temp):
    temps = sorted(TEMP_COLORS.keys())
    if temp <= temps[0]: return TEMP_COLORS[temps[0]]
    if temp >= temps[-1]: return TEMP_COLORS[temps[-1]]
    for i in range(len(temps) - 1):
        if temps[i] <= temp <= temps[i + 1]:
            lower, upper = TEMP_COLORS[temps[i]], TEMP_COLORS[temps[i + 1]]
            ratio = (temp - temps[i]) / (temps[i+1] - temps[i])
            return [int(lower[j] + ratio * (upper[j] - lower[j])) for j in range(3)]
    return [255, 255, 255]

def create_temperature_layer(data, visible=True):
    if not data or not visible: return None
    df = pd.DataFrame(data)
    if df.empty: return None
    
    df['color'] = df['temperature'].apply(lambda t: get_color_for_temperature(t) + [200]) # Alpha 200
    
    return pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=12000, 
        pickable=True,
        opacity=0.8,
        filled=True,
        stroked=False
    )

def create_precipitation_layer(data, visible=True):
    """Create professional contour-based precipitation visualization using GeoJsonLayer."""
    if not data or not visible: 
        return None
    
    try:
        from scipy.interpolate import griddata
        import matplotlib.pyplot as plt
        from matplotlib.path import Path
        from shapely.geometry import Polygon, MultiPolygon
        import numpy as np
    except ImportError as e:
        st.error(f"Missing library for contours: {e}")
        return None
    
    # Filter significant precipitation
    precip_data = [d for d in data if d.get('precipitation', 0) > 0.05]
    
    if len(precip_data) < 4:  # Need minimum points for interpolation
        return None
    
    # Extract coordinates and values
    lons = np.array([d['lon'] for d in precip_data])
    lats = np.array([d['lat'] for d in precip_data])
    precips = np.array([d['precipitation'] for d in precip_data])
    
    # Create regular grid for interpolation
    lon_min, lon_max = lons.min(), lons.max()
    lat_min, lat_max = lats.min(), lats.max()
    
    # Add padding to avoid edge effects
    lon_padding = (lon_max - lon_min) * 0.1
    lat_padding = (lat_max - lat_min) * 0.1
    
    # Higher resolution grid for smoother contours (150x150)
    grid_lon = np.linspace(lon_min - lon_padding, lon_max + lon_padding, 150)
    grid_lat = np.linspace(lat_min - lat_padding, lat_max + lat_padding, 150)
    grid_lon_mesh, grid_lat_mesh = np.meshgrid(grid_lon, grid_lat)
    
    # Interpolate precipitation values onto regular grid
    try:
        grid_precip = griddata(
            points=(lons, lats),
            values=precips,
            xi=(grid_lon_mesh, grid_lat_mesh),
            method='cubic',
            fill_value=0
        )
    except Exception:
        # Fallback to linear if cubic fails
        grid_precip = griddata(
            points=(lons, lats),
            values=precips,
            xi=(grid_lon_mesh, grid_lat_mesh),
            method='linear',
            fill_value=0
        )
    
    # Define contour levels and colors
    levels = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    colors = [
        [135, 206, 250, 150],  # 0.1-0.5: Light Sky Blue
        [100, 180, 240, 170],  # 0.5-1.0: Light Blue
        [70, 130, 220, 190],   # 1.0-2.0: Cornflower Blue
        [40, 90, 200, 210],    # 2.0-5.0: Medium Blue
        [20, 50, 160, 230],    # 5.0-10.0: Dark Blue
        [0, 0, 139, 250]       # >10.0: Very Dark Blue
    ]
    
    # Generate contours using matplotlib
    fig, ax = plt.subplots(figsize=(1, 1))
    contour_set = ax.contourf(grid_lon_mesh, grid_lat_mesh, grid_precip, levels=levels, extend='max')
    plt.close(fig)
    
    # Convert contours to GeoJSON features
    features = []
    
    # Use allsegs to get polygon segments for each level (works with all matplotlib versions)
    try:
        all_segments = contour_set.allsegs
    except AttributeError:
        # Fallback for very old matplotlib
        st.error("Matplotlib version not compatible. Please update: pip install --upgrade matplotlib")
        return None
    
    for level_idx, segments in enumerate(all_segments):
        # Get color for this level
        color = colors[min(level_idx, len(colors) - 1)]
        
        # Each level can have multiple polygons
        for segment in segments:
            if len(segment) < 3:
                continue
            
            try:
                # Create shapely polygon from segment
                poly = Polygon(segment)
                
                # Less aggressive simplification for smoother curves (0.005 instead of 0.01)
                poly = poly.simplify(0.005, preserve_topology=True)
                
                if not poly.is_valid or poly.is_empty:
                    continue
                
                # Get polygon centroid to determine actual precipitation level
                centroid = poly.centroid
                cent_lon, cent_lat = centroid.x, centroid.y
                
                # Find closest grid point to centroid
                lon_idx = np.argmin(np.abs(grid_lon - cent_lon))
                lat_idx = np.argmin(np.abs(grid_lat - cent_lat))
                
                # Get actual precipitation value at this location
                actual_precip = grid_precip[lat_idx, lon_idx]
                
                # Determine which level this belongs to
                actual_level_idx = 0
                for i in range(len(levels) - 1):
                    if actual_precip >= levels[i]:
                        actual_level_idx = i
                
                # Use actual level for color and range
                color = colors[min(actual_level_idx, len(colors) - 1)]
                
                # Convert to GeoJSON-like structure
                coords = list(poly.exterior.coords)
                
                # Create readable precipitation range text based on actual level
                if actual_level_idx < len(levels) - 1:
                    precip_range = f"{levels[actual_level_idx]:.1f}-{levels[actual_level_idx + 1]:.1f} mm/h"
                else:
                    precip_range = f">{levels[-1]:.1f} mm/h"
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [coords]
                    },
                    "properties": {
                        "fill_color": color,
                        "precipitation_level": levels[min(actual_level_idx, len(levels) - 1)] if actual_level_idx < len(levels) else levels[-1],
                        "precipitation_range": precip_range
                    }
                })
            except Exception:
                continue
    
    if not features:
        return None
    
    # Create GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Create GeoJsonLayer (non-interactive to allow clicks through to cameras)
    return pdk.Layer(
        "GeoJsonLayer",
        data=geojson,
        opacity=0.6,
        filled=True,
        get_fill_color="properties.fill_color"
    )



def create_map(all_routes, selected_route_index, incidents, digitraffic_incidents, car_pos, origin_coords, dest_coords, cameras, 
               road_weather, vms, maintenance, lam,
                layer_settings, map_style, weather_ts, weather_path, weather_host, weather_opacity,
                temperature_data=None, precipitation_data=None):
    layers = []

    # 0. SÄÄ (RainViewer Manual Tiling)
    if layer_settings.get("show_rainviewer") and weather_ts and weather_path and weather_host:
        def deg2num(lat_deg, lon_deg, zoom):
            lat_rad = math.radians(lat_deg)
            n = 2.0 ** zoom
            xtile = int((lon_deg + 180.0) / 360.0 * n)
            ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
            return (xtile, ytile)

        def num2deg(xtile, ytile, zoom):
            n = 2.0 ** zoom
            lon_deg = xtile / n * 360.0 - 180.0
            lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
            lat_deg = math.degrees(lat_rad)
            return (lat_deg, lon_deg)

        min_lat, max_lat = 59.0, 71.0
        min_lon, max_lon = 19.0, 33.0
        zoom = 6
        
        x_min, y_max = deg2num(min_lat, min_lon, zoom)
        x_max, y_min = deg2num(max_lat, max_lon, zoom)
        
        x_start, x_end = min(x_min, x_max), max(x_min, x_max)
        y_start, y_end = min(y_min, y_max), max(y_min, y_max)

        max_tiles = 50 
        count = 0
        
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                if count >= max_tiles: break
                
                nw_lat, nw_lon = num2deg(x, y, zoom)
                se_lat, se_lon = num2deg(x + 1, y + 1, zoom)
                
                bounds = [nw_lon, se_lat, se_lon, nw_lat]
                
                tile_url = f"{weather_host}{weather_path}/256/{zoom}/{x}/{y}/6/1_1.png"
                
                layers.append(pdk.Layer(
                    "BitmapLayer",
                    id=f"weather-tile-{x}-{y}",
                    image=tile_url,
                    bounds=bounds,
                    opacity=weather_opacity
                ))
                count += 1

    if layer_settings.get("show_weather"): # Precipitation Heatmap
        p_layer = create_precipitation_layer(precipitation_data)
        if p_layer: layers.append(p_layer)

    if layer_settings.get("show_temp"): # Temperature Grid
        t_layer = create_temperature_layer(temperature_data)
        if t_layer: layers.append(t_layer)

    # 2. REITIT (Vaihtoehtoiset ja valittu)
    if layer_settings.get("show_route") and all_routes:
        # Piirretään ensin ei-valitut reitit harmaina
        for i, r_coords in enumerate(all_routes):
            if i == selected_route_index: continue
            layers.append(pdk.Layer(
                "PathLayer",
                data=[{"path": [[p[1], p[0]] for p in r_coords]}],
                id=f"route-{i}",
                get_path="path",
                get_color=[150, 150, 150],
                width_scale=20,
                width_min_pixels=2,
                opacity=0.4,
            ))
        
        # Piirretään valittu reitti korostettuna
        if selected_route_index < len(all_routes):
            sel_coords = all_routes[selected_route_index]
            layers.append(pdk.Layer(
                "PathLayer",
                data=[{"path": [[p[1], p[0]] for p in sel_coords]}],
                id="route-selected",
                get_path="path",
                get_color=[60, 160, 255],
                width_scale=20,
                width_min_pixels=4,
                opacity=0.9,
            ))

    # 3. KELIKAMERAT (Moved to end of layers list as cameras-top for z-index)
    # if layer_settings.get("show_cameras") and cameras:
    #     layers.append(pdk.Layer(
    #         "ScatterplotLayer",
    #         data=cameras,
    #         id="cameras", 
    #         get_position="[lon, lat]",
    #         get_color=[255, 220, 0], 
    #         get_radius=800,
    #         radius_min_pixels=8, 
    #         pickable=True,       
    #         stroked=True,
    #         get_line_color=[0,0,0],
    #         line_width_min_pixels=1,
    #         auto_highlight=True
    #     ))

    # 4. PISTEET
    point_data = []
    if origin_coords: point_data.append({"pos": [origin_coords[1], origin_coords[0]], "color": [0, 255, 100], "name": "Lähtö"})
    if dest_coords: point_data.append({"pos": [dest_coords[1], dest_coords[0]], "color": [255, 50, 50], "name": "Määränpää"})
    
    if point_data:
        layers.append(pdk.Layer("ScatterplotLayer", data=point_data, id="endpoints", get_position="pos", get_color="color", get_radius=800, radius_min_pixels=6, pickable=True, stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=2))

    # 5. HERE HÄIRIÖT
    if layer_settings.get("show_incidents") and incidents:
        incident_points = [{"pos": [i['lon'], i['lat']], "color": [200, 0, 0] if 'critical' in str(i['taso']) else [255, 140, 0], "name": i['tyyppi']} for i in incidents if i.get('lat')]
        if incident_points:
            layers.append(pdk.Layer("ScatterplotLayer", data=incident_points, id="incidents", get_position="pos", get_color="color", get_radius=600, pickable=True, stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=1))

    # 6. DIGITRAFFIC HÄIRIÖT
    if layer_settings.get("show_incidents") and digitraffic_incidents:
        dt_points = []
        for d in digitraffic_incidents:
            if d.get('lat') and d.get('lon'):
                dt_points.append({
                    "pos": [d['lon'], d['lat']],
                    "color": [0, 255, 255], 
                    "name": f"FI: {d.get('otsikko', 'Tiedote')}"
                })
        
        if dt_points:
            layers.append(pdk.Layer(
                "ScatterplotLayer", 
                data=dt_points, 
                id="dt_incidents", 
                get_position="pos", 
                get_color="color", 
                get_radius=600, 
                pickable=True, 
                stroked=True, 
                get_line_color=[0,0,0], 
                line_width_min_pixels=1
            ))

    # 7. TIESÄÄ (Road Weather)
    if layer_settings.get("show_road_weather") and road_weather:
        rw_points = []
        for r in road_weather:
            temp = r.get("air_temp")
            color = [200, 200, 200]
            if temp is not None:
                if temp < 0: color = [0, 100, 255]
                elif temp > 0: color = [255, 100, 0]
            
            rw_points.append({
                "pos": [r['lon'], r['lat']],
                "color": color,
                "name": f"{r.get('name')}\nIlma: {r.get('air_temp')}°C\nTie: {r.get('road_temp')}°C",
                "id": r.get("id"),
                "air_temp": r.get("air_temp"),
                "road_temp": r.get("road_temp")
            })
        
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=rw_points,
            id="road_weather",
            get_position="pos",
            get_color="color",
            get_radius=800,
            pickable=True,
            stroked=True,
            get_line_color=[255, 255, 255],
            line_width_min_pixels=1,
            radius_min_pixels=4,
            auto_highlight=True
        ))

    # 8. VMS (Muuttuvat opasteet)
    if layer_settings.get("show_vms") and vms:
        vms_points = [{"pos": [v['lon'], v['lat']], "name": f"Opaste: {v.get('name')}", "color": [255, 0, 255]} for v in vms]
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=vms_points,
            id="vms",
            get_position="pos",
            get_color="color",
            get_radius=600,
            pickable=True,
            stroked=True,
            get_line_color=[0, 0, 0],
            line_width_min_pixels=1,
            radius_min_pixels=4
        ))

    # 9. LAM (Liikennemäärät)
    if layer_settings.get("show_lam") and lam:
        lam_points = [{"pos": [l['lon'], l['lat']], "name": f"{l.get('name')}\nNop: {l.get('speed')} km/h\nMäärä: {l.get('volume')} kpl/h", "color": [0, 255, 100]} for l in lam]
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=lam_points,
            id="lam",
            get_position="pos",
            get_color="color",
            get_radius=600,
            pickable=True,
            stroked=True,
            get_line_color=[0, 0, 0],
            line_width_min_pixels=1,
            radius_min_pixels=4
        ))

    # 10. KUNNOSSAPITO (Maintenance)
    if layer_settings.get("show_maintenance") and maintenance:
        m_paths = []
        for m in maintenance:
            geom = m.get("geometry")
            if geom and geom.get("type") == "MultiLineString":
                for line in geom.get("coordinates", []):
                    m_paths.append({"path": line, "name": f"Huolto: {m.get('task')} ({m.get('time')})"})
            elif geom and geom.get("type") == "LineString":
                m_paths.append({"path": geom.get("coordinates", []), "name": f"Huolto: {m.get('task')} ({m.get('time')})"})
        
        if m_paths:
            layers.append(pdk.Layer(
                "PathLayer",
                data=m_paths,
                id="maintenance",
                get_path="path",
                get_color=[255, 165, 0], # Oranssi
                width_scale=10,
                width_min_pixels=2,
                opacity=0.6,
                pickable=True
            ))

    # 11. AUTO
    if layer_settings.get("show_car") and car_pos:
        layers.append(pdk.Layer("ScatterplotLayer", data=[{"pos": [car_pos[1], car_pos[0]], "name": "Auto"}], id="car", get_position="pos", get_color=[0, 100, 255], get_radius=1000, radius_min_pixels=8, pickable=True, stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=2))

    # 12. KAMERAT (UUDELLEEN PÄÄLLIMMÄISEKSI) - Ensure cameras are clickable above precipitation
    if layer_settings.get("show_cameras") and cameras:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=cameras,
            id="cameras-top", 
            get_position="[lon, lat]",
            get_color=[255, 220, 0], 
            get_radius=800,
            radius_min_pixels=8, 
            pickable=True,       
            stroked=True,
            get_line_color=[0,0,0],
            line_width_min_pixels=1,
            auto_highlight=True
        ))

    if all_routes and selected_route_index < len(all_routes):
        coords = all_routes[selected_route_index]
        formatted_points = [[p[1], p[0]] for p in coords]
        view_state = compute_view(formatted_points, view_proportion=0.75)
        view_state.pitch = 0
    else:
        view_state = pdk.ViewState(latitude=61.92, longitude=25.74, zoom=6)

    tooltip = {
        "html": "<b>{name}</b>",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    }

    return pdk.Deck(map_style=map_style, initial_view_state=view_state, layers=layers, api_keys={"mapbox": MAPBOX_TOKEN}, tooltip=tooltip)

def clear_search():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.cache_data.clear()

# ====================================================================
# UI
# ====================================================================



def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css("styles.css")

keys = ["all_routes", "route_summaries", "selected_route_index", "cameras", "origin_coords", "dest_coords", "current_location", "dep_dt", "here_incidents", "digitraffic_messages", "selected_camera", "selected_station", "weather_timestamps", "weather_host", "weather_paths",
        "road_weather", "vms", "maintenance", "lam", "data_by_route", "meteo_temp", "meteo_precip"]

for key in keys:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ["all_routes", "route_summaries", "cameras", "here_incidents", "digitraffic_messages", "weather_timestamps", "road_weather", "vms", "maintenance", "lam", "data_by_route", "meteo_temp", "meteo_precip"] else None
        if key == "weather_paths": st.session_state[key] = {}
        if key == "weather_paths": st.session_state[key] = {}
        if key == "selected_route_index": st.session_state[key] = 0

# Alustetaan input-kenttien sessiomuuttujat, jos ne puuttuvat
if "dest_input" not in st.session_state:
    st.session_state.dest_input = "Tampere"
if "date_input" not in st.session_state:
    st.session_state.date_input = datetime.date.today()
if "is_arrival_mode" not in st.session_state:
    st.session_state.is_arrival_mode = False

if "ui_default_time" not in st.session_state:
    # Calculate once and store - don't recalculate on every run
    default_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
    st.session_state.ui_default_time = default_time.time()

if st.session_state.all_routes and (not st.session_state.weather_host or not st.session_state.weather_paths):
    try:
        host, ts_dict = get_cached_weather_data()
        st.session_state.weather_timestamps = sorted(list(ts_dict.keys()))
        st.session_state.weather_paths = ts_dict
        st.session_state.weather_host = host
    except Exception as e:
        print(f"Weather cache error: {e}")

# --- GOOGLE AUTH HANDLER ---
# Check for token in query params
if "gcal_access_token" in st.query_params:
    try:
        token = st.query_params["gcal_access_token"]
        # Store in session
        st.session_state["gcal_token"] = token
        st.toast("Kirjauduttu Google-tilille! ✅")
        
        # Clear the URL parameter and rerun ONCE
        st.query_params.clear()
        time.sleep(0.3)
        st.rerun()
            
    except Exception as e:
        print(f"DEBUG: Auth Error: {e}")
        st.error(f"Kirjautumisvirhe: {e}")
        st.query_params.clear()




st.title("Reitti ja Liikenne Pingut Pro 🚗")

if not MAPBOX_TOKEN:
    st.warning("⚠️ MAPBOX_TOKEN puuttuu.")

with st.sidebar:
    # --- KALENTERI ---
    with st.expander("📅 Kalenteri", expanded=True):
        env_ical = os.getenv("ICAL_URL")
        
        # Tila: Muokataanko vai näytetäänkö tallennettu
        if "edit_ical" not in st.session_state:
            st.session_state.edit_ical = False

        target_url = None
        
        # 1. iCal Configuration
        if env_ical and not st.session_state.edit_ical:
            st.success("✅ Kalenteri yhdistetty.")
            if st.button("Vaihda osoite"):
                st.session_state.edit_ical = True
                st.rerun()
            target_url = env_ical
        else:
            # Ei tallennettua tai muokkaustila
            ical_input = st.text_input("iCal URL", value=env_ical if env_ical else "", type="password", placeholder="Liitä iCal-osoite tähän...")
            
            if st.button("Tallenna"):
                if ical_input:
                    # Tallenna .env tiedostoon
                    env_path = os.path.join(os.getcwd(), ".env")
                    set_key(env_path, "ICAL_URL", ical_input)
                    os.environ["ICAL_URL"] = ical_input
                    st.session_state.edit_ical = False
                    st.success("Tallennettu!")
                    time.sleep(1)
                    st.rerun()
            
            # Preview input
            if ical_input:
                target_url = ical_input

        # 2. Google Calendar Integration
        st.divider()
        gcal_events = []
        if "gcal_token" in st.session_state and st.session_state.gcal_token:
            st.caption("✅ Google Kalenteri yhdistetty")
            if st.button("Kirjaudu ulos", key="btn_logout_gcal"):
                del st.session_state["gcal_token"]
                st.rerun()
            
            # Fetch events
            gcal_evts = _add_gcal_events(st.session_state.gcal_token)
            if gcal_evts is None:
                st.error("Istunto vanhentunut. Kirjaudu uudelleen.")
                del st.session_state["gcal_token"]
            else:
                gcal_events = gcal_evts
        else:
                login_link = f"{API_URL_EXTERNAL}/gcal/login?redirect_url=http://localhost:8501/maps_app"
                st.markdown(f"👉 **[Yhdistä Google Kalenteri]({login_link})**", unsafe_allow_html=True)

        # 3. Combine Events
        events = []
        if target_url:
            events.extend(_add_ical_events(target_url))
        
        if gcal_events:
            events.extend(gcal_events)

        # 4. Display Calendar Events
        # NOTE: streamlit-calendar component causes infinite reruns
        # Using simple list display instead
        
        if events:
            # Filter to show only future events (today onwards)
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            future_events = []
            
            for event in events:
                start = event.get("start", "")
                try:
                    if isinstance(start, str):
                        dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                        # Include events from today onwards
                        if dt.date() >= now.date():
                            future_events.append(event)
                except:
                    # If parsing fails, include the event anyway
                    future_events.append(event)
            
            if future_events:
                st.caption(f"📅 {len(future_events)} tulevaa tapahtumaa")
                for event in future_events[:10]:  # Show max 10 upcoming events
                    title = event.get("title", "Ei otsikkoa")
                    start = event.get("start", "")
                    
                    # Parse and format the date/time
                    try:
                        if isinstance(start, str):
                            dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                            date_str = dt.strftime("%d.%m %H:%M")
                        else:
                            date_str = str(start)
                    except:
                        date_str = str(start)
                    
                    # Check if event has location
                    location = event.get("extendedProps", {}).get("location")
                    if location:
                        st.markdown(f"**{date_str}** - {title}")
                        if st.button(f"📍 {location}", key=f"loc_{event.get('start')}_{title[:20]}"):
                            # Set destination
                            st.session_state["dest_input"] = location
                            
                            # Set arrival mode
                            st.session_state["is_arrival_mode"] = True
                            
                            # Set date and time from event
                            try:
                                dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                                st.session_state["date_input"] = dt.date()
                                st.session_state["time_sel"] = dt.time()  # Changed from ui_default_time to time_sel
                                
                                # Show confirmation
                                st.toast(f"✅ Määränpää: {location}")
                                st.toast(f"🕐 Saapumisaika: {dt.strftime('%d.%m.%Y %H:%M')}")
                                
                                # Rerun to update form fields
                                st.rerun()
                            except Exception as e:
                                st.toast(f"✅ Määränpää: {location}")
                                st.warning(f"Määränpää asetettu, mutta aikaa ei voitu asettaa: {e}")
                    else:
                        st.markdown(f"**{date_str}** - {title}")
            else:
                st.info("Ei tulevia tapahtumia")
        else:
            st.info("Ei tulevia tapahtumia")




    if st.session_state.selected_camera:
        cam = st.session_state.selected_camera
        st.success(f"📸 {cam.get('name', 'Kelikamera')}")
        img_url = cam.get("imageUrl")
        if img_url:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(img_url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    st.image(resp.content, width="stretch", caption=f"ID: {cam.get('id')}")
                else:
                    st.error(f"Virhe: {resp.status_code}")
            except Exception as e:
                st.error("Yhteysvirhe.")
        if st.button("Sulje kuva", type="primary"):
            st.session_state.selected_camera = None
            st.rerun()
        st.divider()

    if st.session_state.selected_station:
        st_data = st.session_state.selected_station
        st.info(f"🌡️ Sääasema: {st_data.get('name', 'Nimetön')}")
        
        c1, c2 = st.columns(2)
        c1.metric("Ilma", f"{st_data.get('air_temp')} °C")
        c2.metric("Tie", f"{st_data.get('road_temp')} °C")
        
        if st.button("Sulje sääasema", type="primary"):
            st.session_state.selected_station = None
            st.rerun()
        st.divider()

    # --- REITTIHÄLYTYKSET ---
    if "digitraffic_messages" in st.session_state and st.session_state.digitraffic_messages:
        st.subheader("⚠️ Hälytykset reitillä")
        
        # Liikennetiedotteet
        for msg in st.session_state.digitraffic_messages:
            icon = "🛑"
            st.warning(f"{icon} **{msg.get('type', 'Häiriö')}**\n{msg.get('desc')}")
            
    if "road_weather" in st.session_state and st.session_state.road_weather:
         # Filter warnings
         warnings = [w for w in st.session_state.road_weather if w.get('condition') in ['JÄINEN', 'LUMI', 'HUONO_NAKYVYYS'] or w.get('overall') == 'HUONO']
         
         if warnings:
             if "digitraffic_messages" not in st.session_state or not st.session_state.digitraffic_messages:
                 st.subheader("⚠️ Hälytykset reitillä")
             
             for w in warnings:
                 st.info(f"❄️ **{w.get('station')}**: {w.get('condition', 'Normaali')}\nTie: {w.get('road_temp')}°C")

    st.divider()

    st.header("🗺️ Asetukset")
    map_style = st.selectbox("Karttatyyli", ["mapbox://styles/mapbox/dark-v11", "mapbox://styles/mapbox/streets-v12", "mapbox://styles/mapbox/satellite-streets-v12"])
    
    st.subheader("Reititys")
    routing_mode = st.radio("Optimointi", ["fast", "short"], format_func=lambda x: "Nopein" if x=="fast" else "Lyhin")
    
    avoid_options = []
    if st.checkbox("Vältä moottoriteitä"): avoid_options.append("controlledAccessHighway")
    if st.checkbox("Vältä tietulleja"): avoid_options.append("tollRoad")
    

    
    st.divider()
    with st.expander("🛠️ Debug: Säädata"):
        if st.session_state.weather_timestamps:
            st.write(f"Ladattu {len(st.session_state.weather_timestamps)} aikaleimaa.")
            if len(st.session_state.weather_timestamps) > 0:
                ts = st.session_state.weather_timestamps[-1]
                st.write(f"Viimeisin TS: {ts}")
                
                host = st.session_state.weather_host
                path = st.session_state.weather_paths.get(ts)
                
                if host and path:
                    test_url = f"{host}{path}/256/6/36/19/6/1_1.png"
                    st.markdown(f"[Testaa tiili selaimessa]({test_url})")
                else:
                    st.warning("Host tai polku puuttuu.")
            else:
                st.warning("Ei aikaleimoja.")
        else:
            st.warning("Ei säädataa.")
        
        st.write("---")
        st.write(f"Host: {st.session_state.weather_host}")
        st.write(f"Paths count: {len(st.session_state.weather_paths) if st.session_state.weather_paths else 0}")

    # Korkeusprofiili sidebarissa
    if st.session_state.all_routes and st.session_state.selected_route_index < len(st.session_state.all_routes):
        st.divider()
        st.subheader("⛰️ Reitin korkeusprofiili")
        coords = st.session_state.all_routes[st.session_state.selected_route_index]
        chart_data = []
        has_elevation = len(coords[0]) > 2
        for p in coords:
            val = p[2] if has_elevation else 0
            chart_data.append(val)
        
        if has_elevation:
            # Get current slider pos
            slider_val = st.session_state.get("travel_slider", 0)
            
            # Calculate current index based on slider time
            current_idx = 0
            if st.session_state.route_summaries and st.session_state.selected_route_index < len(st.session_state.route_summaries):
                 summ = st.session_state.route_summaries[st.session_state.selected_route_index]
                 if summ:
                     d_t = summ[1] * 60 # hours to mins
                     if d_t > 0:
                        current_idx = int((slider_val / d_t) * len(chart_data))

            # Create DataFrame for Altair
            df_elev = pd.DataFrame({
                "index": range(len(chart_data)),
                "elevation": chart_data,
                "status": ["Mennyt" if i <= current_idx else "Tuleva" for i in range(len(chart_data))]
            })
            
            # Enable selection
            # Explicitly name the selection to avoid Default param naming issues
            # For bar chart, click on the bar itself works well.
            selection = alt.selection_point(name="travel_select", encodings=['x'], on='click') 
            
            # Use mark_bar for single-view clickability (user can click anywhere on the 'hill')
            base = alt.Chart(df_elev).mark_bar(width=2).encode(
                x=alt.X("index", title="Reittipisteet"),
                y=alt.Y("elevation", title="Korkeus (m)"),
                color=alt.Color("status", scale=alt.Scale(domain=["Mennyt", "Tuleva"], range=["#ffaa00", "#e0e0e0"]), legend=None),
                tooltip=["index", "elevation"]
            ).properties(height=200).add_params(selection)

            # Render single chart (no layers)
            chart_selection = st.altair_chart(base, theme="streamlit", on_select="rerun")
            
            # Handle selection to update slider
            if len(chart_selection["selection"]) > 0:
                try: 
                    # Look for our named selection
                    if "travel_select" in chart_selection["selection"]:
                         sel_data = chart_selection["selection"]["travel_select"]
                         
                         rows = []
                         if isinstance(sel_data, list):
                             for item in sel_data:
                                 if isinstance(item, dict) and "index" in item:
                                     rows.append(item["index"])
                                 elif isinstance(item, int):
                                     rows.append(item)
                         elif isinstance(sel_data, dict) and "index" in sel_data:
                             val = sel_data["index"]
                             if isinstance(val, list): rows = val
                             else: rows = [val]

                         if rows:
                            selected_idx = rows[0]
                            summ = st.session_state.route_summaries[st.session_state.selected_route_index]
                            d_t = summ[1] * 60
                            if len(chart_data) > 0:
                                 new_time = int((selected_idx / len(chart_data)) * d_t)
                                 
                                 current_slider = st.session_state.get("travel_slider", 0)
                                 if abs(new_time - current_slider) > 0:
                                     st.session_state["travel_slider"] = new_time
                                     st.toast(f"📍 Siirrytty kohtaan: {int(new_time)} min")
                                     st.rerun()
                except Exception as e:
                    st.error(f"Chart selection error: {e}")

            if current_idx > 0:
                 st.caption(f"📍 Sijainti profiilissa: {current_idx}/{len(chart_data)}")
        else:
            st.info("Ei korkeusdataa.")

# --- INPUTS ---
with st.container():
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 📍 Reittihaku")
    
    c1, c2, c3 = st.columns([2, 2, 2])
    search_disabled = False

    with c1:
        # Haetaan checkboxin tila session statesta
        gps_enabled = st.session_state.get("use_gps_checkbox", False)
        
        origin = st.text_input("Lähtö", "Helsinki", disabled=gps_enabled, help="Mistä lähdetään?")
        
        use_gps = st.checkbox("Käytä GPS-sijaintia", key="use_gps_checkbox")
        
        if use_gps:
            if st.session_state.current_location:
                 lat, lon = st.session_state.current_location
                 st.caption(f"✅ GPS: {lat:.4f}, {lon:.4f}")
            else:
                 loc = get_geolocation()
                 if loc and loc.get("coords"):
                     new_loc = (loc["coords"]["latitude"], loc["coords"]["longitude"])
                     if st.session_state.get("current_location") != new_loc:
                         st.session_state.current_location = new_loc
                         st.rerun()
                 else:
                     st.caption("⏳ Odotetaan GPS...")
                     search_disabled = True

    with c2:
        dest = st.text_input("Määränpää", key="dest_input", help="Minne mennään?")
        # User instruction
        st.caption("Klikkaa kalanteritapahtumaa, jossa paikkatieto asetettu")

    with c3:
        col_d, col_t = st.columns(2)
        with col_d: date_val = st.date_input("Päivä", key="date_input")
        with col_t: time_val = st.time_input("Kello", st.session_state.ui_default_time, key="time_sel")
        
        # Time mode selector - key is directly tied to session state
        is_arr = st.checkbox("Aseta saapumisaika", key="is_arrival_mode")
        
        target_dt_naive = datetime.datetime.combine(date_val, time_val)
        target_iso = target_dt_naive.astimezone().isoformat(timespec="seconds")
        
        if is_arr:
             st.caption(f"🏁 Tavoite perillä: {target_dt_naive.strftime('%H:%M')}")
        else:
             st.caption(f"🚀 Lähtöaika: {target_dt_naive.strftime('%H:%M')}")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

b1, b2 = st.columns([1, 4])
with b1:
    if st.button("Hae reitti 🚀", type="primary", disabled=search_disabled):
        with st.spinner("Suunnitellaan..."):
            o_c = st.session_state.current_location if use_gps else geocode_cached(origin)
            d_c = geocode_cached(dest)
            
            if o_c and d_c:
                st.session_state.origin_coords = o_c
                st.session_state.dest_coords = d_c
                st.session_state.dep_dt = target_dt_naive
                
                # Haetaan reitit (2 vaihtoehtoa jos fast, muuten 0)
                alternatives = 2 if routing_mode == "fast" else 0
                
                # Determine time params
                dep_param = target_iso if not st.session_state.is_arrival_mode else None
                arr_param = target_iso if st.session_state.is_arrival_mode else None
                
                r_data = get_cached_route(o_c, d_c, dep_time=dep_param, arr_time=arr_param, mode=routing_mode, avoid_list=avoid_options, alternatives=alternatives)
                
                if r_data and "routes" in r_data:
                    st.session_state.all_routes = []
                    st.session_state.route_summaries = []
                    
                    for r in r_data["routes"]:
                        for s in r["sections"]:
                            poly = s["polyline"]
                            st.session_state.all_routes.append(flexpolyline.decode(poly))
                            st.session_state.route_summaries.append(extract_route_summary(s))
                            # Huom: HERE palauttaa useita reittejä, joissa voi olla useita sektioita.
                            # Yksinkertaistuksen vuoksi oletamme tässä 1 sektio per reitti tai otamme vain ensimmäisen.
                            # Oikeampi tapa olisi yhdistää sektiot.
                            break # Otetaan vain eka sektio per reitti demo-tarkoituksiin
                    
                    st.session_state.selected_route_index = 0
                    
                    # Käytetään ekaa reittiä metadatan hakuun
                    if st.session_state.all_routes:
                        st.session_state.here_incidents = parse_traffic_incidents(r_data)

                        # Collect data for EACH route separately
                        # Collect data for EACH route separately
                        st.session_state.data_by_route = []

                        progress_bar = st.progress(0, text="Haetaan tietoja reiteille...")
                        
                        # Pre-fetch data ONCE
                        with st.spinner("Ladataan Digitraffic-dataa..."):
                            from utils.digitraffic_client import (
                                fetch_weather_cam_data, filter_weather_cameras,
                                fetch_road_weather_data, filter_road_weather_stations,
                                fetch_vms_data, filter_vms_stations,
                                fetch_lam_data, filter_lam_stations
                            )
                            # Fetch raw data
                            cam_data = fetch_weather_cam_data()
                            rw_meta, rw_data = fetch_road_weather_data()
                            vms_data = fetch_vms_data()
                            lam_meta, lam_data = fetch_lam_data()
                            
                        total_routes = len(st.session_state.all_routes)

                        for idx, route_coords in enumerate(st.session_state.all_routes):
                            # Filter locally using pre-fetched data
                            route_data = {
                                "cameras": filter_weather_cameras(route_coords, cam_data),
                                "digitraffic_messages": traffic_messages_near_route(route_coords), # Still per route (API filtered)
                                "road_weather": filter_road_weather_stations(route_coords, rw_meta, rw_data),
                                "vms": filter_vms_stations(route_coords, vms_data),
                                "maintenance": get_maintenance_data(route_coords), # Still per route (time/bbox dependent)
                                "lam": filter_lam_stations(route_coords, lam_meta, lam_data)
                            }
                            st.session_state.data_by_route.append(route_data)
                            progress_bar.progress((idx + 1) / total_routes)

                        progress_bar.empty()
                    
                    # Pre-fetch Open-Meteo Data (once per session/search)
                    with st.spinner("Haetaan sääennusteet..."):
                        try:
                             # Default full Finland BBox from api_server
                             resp_t = requests.get(f"{API_URL_INTERNAL}/maps/api/forecast/temperature", params={"hours": 6})
                             resp_p = requests.get(f"{API_URL_INTERNAL}/maps/api/forecast/weather", params={"hours": 6})
                             
                             if resp_t.status_code == 200: 
                                 st.session_state.meteo_temp = resp_t.json().get("data", [])
                                 # st.toast(f"Latasi {len(st.session_state.meteo_temp)} lämpötilapistettä")
                             else:
                                 st.error(f"Temp Error: {resp_t.status_code} - {resp_t.text}")

                             if resp_p.status_code == 200:
                                 st.session_state.meteo_precip = resp_p.json().get("data", [])
                             else:
                                 st.error(f"Precip Error: {resp_p.status_code} - {resp_p.text}")

                        except Exception as e:
                            st.error(f"Säädatan haku epäonnistui: {e}")
                            print(f"Weather fetch error: {e}")
                            st.session_state.meteo_temp = []
                            st.session_state.meteo_precip = []

                    # st.session_state.weather_timestamps removed (we filter dynamically from full list) 
                    # OR we can extract unique times from meteo_temp for slider?
                    # For now, we rely on simulation time matching closest data point.
                    
                    st.session_state.selected_camera = None
                    st.session_state.selected_station = None
                    st.rerun()
                else:
                    st.error("Ei reittiä.")
            else:
                st.error("Osoitevirhe.")

with b2:
    if st.button("Tyhjennä haku"):
        clear_search()
        st.rerun()

st.markdown("---")

# --- RESULTS ---
if st.session_state.all_routes:
    # Traffic toggle
    use_traffic = st.checkbox("Huomioi liikenne", value=True)

    # Reitin valinta
    route_opts = []
    for i, summ in enumerate(st.session_state.route_summaries):
        if summ:
            dist, dur_traffic, dur_base = summ
            dur = dur_traffic if use_traffic else dur_base
            route_opts.append(f"Reitti {i+1}: {dist:.1f} km, {int(dur)}h {int((dur%1)*60)}min")
        else:
            route_opts.append(f"Reitti {i+1}: (Tiedot puuttuvat)")
    
    selected_opt = st.radio("Valitse reitti", route_opts, index=st.session_state.selected_route_index, horizontal=True)
    st.session_state.selected_route_index = route_opts.index(selected_opt)
    
    coords = st.session_state.all_routes[st.session_state.selected_route_index]
    
    # Get data for selected route
    current_route_data = {}
    if "data_by_route" in st.session_state and len(st.session_state.data_by_route) > st.session_state.selected_route_index:
        current_route_data = st.session_state.data_by_route[st.session_state.selected_route_index]

    cameras = current_route_data.get("cameras", [])
    dt_msgs = current_route_data.get("digitraffic_messages", [])
    road_weather = current_route_data.get("road_weather", [])
    vms = current_route_data.get("vms", [])
    maintenance = current_route_data.get("maintenance", [])
    lam = current_route_data.get("lam", [])

    st.session_state.cameras = cameras
    st.session_state.digitraffic_messages = dt_msgs
    st.session_state.road_weather = road_weather # Update session state for other components using these

    if st.session_state.route_summaries[st.session_state.selected_route_index]:
        dist, dur_traffic, dur_base = st.session_state.route_summaries[st.session_state.selected_route_index]
        dur = dur_traffic if use_traffic else dur_base
    else:
        dist, dur = 0, 0
    
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Matka", f"{dist:.1f} km")
    m2.metric("Ajoaika", f"{int(dur)}h {int((dur%1)*60)}min")
    
    if st.session_state.is_arrival_mode:
        arrival_dt = st.session_state.dep_dt
        departure_dt = arrival_dt - datetime.timedelta(hours=dur)
        m3.metric("Lähtö (Arvio)", departure_dt.strftime("%H:%M"), help="Sinun pitää lähteä viimeistään tähän aikaan.")
        m4.metric("Perillä (Tavoite)", arrival_dt.strftime("%H:%M"))
    else:
        departure_dt = st.session_state.dep_dt
        arrival_dt = departure_dt + datetime.timedelta(hours=dur)
        m3.metric("Lähtö", departure_dt.strftime("%H:%M"))
        m4.metric("Perillä (Arvio)", arrival_dt.strftime("%H:%M"))

    # --- KARTTAKONTROLLIT (MAIN COLUMN) ---
    with st.expander("🗺️ Karttatasot & Näkymä", expanded=False):
        c_l1, c_l2, c_l3 = st.columns(3)
        with c_l1:
            st.caption("Data")
            l_route = st.checkbox("Reittiviiva", True, key="chk_route")
            l_weather = st.checkbox("Sade-ennuste (Heatmap)", False, key="chk_weather")
            l_rv = st.checkbox("Sade (RainViewer)", False, key="chk_rv") # Restored
            l_temp = st.checkbox("Lämpötila (Grid)", False, key="chk_temp")
            l_incidents = st.checkbox("Häiriöt", True, key="chk_incidents")
        
        with c_l2:
            st.caption("Infra")
            # Disable cameras when precipitation is active
            l_cam = st.checkbox("Kelikamerat 📷", True, key="chk_cam", disabled=l_weather)
            l_rw = st.checkbox("Tiesää 🌡️", True, key="chk_rw")
            l_vms = st.checkbox("Opasteet 🛑", True, key="chk_vms")
            
        with c_l3:
            st.caption("Muut")
            l_maint = st.checkbox("Kunnossapito 🚜", True, key="chk_maint")
            l_lam = st.checkbox("LAM-pisteet 📊", True, key="chk_lam")
            l_car = st.checkbox("Auto", True, key="chk_car")
            
        layer_settings = {
            "show_route": l_route, "show_weather": l_weather, "show_temp": l_temp, "show_rainviewer": l_rv,
            "show_incidents": l_incidents,
            "show_cameras": l_cam and not l_weather,  # Force False when precipitation is active
            "show_road_weather": l_rw, "show_vms": l_vms,
            "show_maintenance": l_maint, "show_lam": l_lam, "show_car": l_car
        }
        # DEBUG Layers
        # st.write(layer_settings)
        c_s1, c_s2 = st.columns(2)
        with c_s1:
            weather_opacity = st.slider("Sään läpinäkyvyys", 0.0, 1.0, 0.6, step=0.1) if l_weather else 0.0
        with c_s2:
            st.caption("Karttatyyli valittu asetuksista")


    # Map and sidebar layout (2/3 map, 1/3 sidebar)
    map_col, sidebar_col = st.columns([2, 1])
    
    with map_col:
        map_placeholder = st.empty()
        c_play, c_slider = st.columns([1, 4])
        with c_play: play = st.button("Play ▶️", key="play_btn")
        
        total_mins = int(dur * 60)
        if total_mins < 1: total_mins = 1
        with c_slider: t_val = st.slider("Matka etenee", 0, total_mins, label_visibility="collapsed", key="travel_slider")
        
        idx = int((t_val / total_mins) * (len(coords) - 1))
        car_pos = coords[idx]
        
        sim_dt = st.session_state.dep_dt + datetime.timedelta(minutes=t_val)
        # Filter Weather Data for Current Time
        current_temp_data = []
        current_precip_data = []
        current_temp_data = []
        current_precip_data = []
        
        # Ensure initialization
        if "meteo_temp" not in st.session_state: st.session_state.meteo_temp = []
        if "meteo_precip" not in st.session_state: st.session_state.meteo_precip = []

        if True: # Always run time filtering
             # Convert sim_dt to UTC (rough adjustment for Finland)
             # Winter time: UTC+2. Summer: UTC+3.
             target_utc = sim_dt - datetime.timedelta(hours=2) 
             target_h = target_utc.strftime('%Y-%m-%dT%H')
             
             current_temp_data = [d for d in st.session_state.meteo_temp if d.get('time', '').startswith(target_h)]
             
             # Fallback: if empty, try original target (maybe backend converted it?)
             if not current_temp_data:
                 target_h_local = sim_dt.strftime('%Y-%m-%dT%H')
                 current_temp_data = [d for d in st.session_state.meteo_temp if d.get('time', '').startswith(target_h_local)]
                 if current_temp_data: target_h = target_h_local # It matched local!

             current_precip_data = [d for d in st.session_state.meteo_precip if d.get('time', '').startswith(target_h)]

             st.caption(f"Sääennuste: {sim_dt.strftime('%H:%M')} -> UTC approx {target_h} ({len(current_temp_data)} t, {len(current_precip_data)} p)")
             
             if not current_temp_data and st.session_state.meteo_temp:
                 st.warning(f"Ei dataa! Sim: {sim_dt.isoformat()} vs Data[0]: {st.session_state.meteo_temp[0]['time']}")


        deck = create_map(st.session_state.all_routes, 
                          st.session_state.selected_route_index,
                          st.session_state.here_incidents, 
                          dt_msgs, 
                          car_pos, 
                          st.session_state.origin_coords, 
                          st.session_state.dest_coords, 
                          cameras,
                          road_weather,
                          vms,
                          maintenance,
                          lam,
                          layer_settings, 
                          map_style, 
                          st.session_state.weather_timestamps,
                          st.session_state.weather_paths.get(st.session_state.weather_timestamps[-1]) if st.session_state.weather_timestamps else None,
                          st.session_state.weather_host,
                          0.6,
                          temperature_data=current_temp_data,
                          precipitation_data=current_precip_data)
        
        selection = map_placeholder.pydeck_chart(deck, on_select="rerun", selection_mode="single-object")
        
        # Add precipitation legend below map if layer is enabled
        if layer_settings.get("show_weather") and current_precip_data:
            st.caption("🌧️ **Sade-ennuste selite:**")
            leg_cols = st.columns(4)  # Reduced from 6 to 4 for narrower map
            legend_items = [
                ("rgb(100,180,240)", "0.1-1.0"),   # Average of first two levels
                ("rgb(70,130,220)", "1.0-2.0"),
                ("rgb(40,90,200)", "2.0-5.0"),
                ("rgb(20,50,160)", "5.0-10.0")     # Show 5-10 instead of >5
            ]
            for i, (color, label) in enumerate(legend_items):
                with leg_cols[i]:
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <div style="width: 100%; height: 20px; background: {color}; border-radius: 4px; margin-bottom: 4px;"></div>
                        <small>{label} mm/h</small>
                    </div>
                    """, unsafe_allow_html=True)
        
        if selection.selection:
            found_index = None
            def get_idx(v):
                if isinstance(v, (list, tuple)) and len(v) > 0: return v[0]
                if isinstance(v, set) and len(v) > 0: return list(v)[0]
                if isinstance(v, int): return v
                return None

            if "objects" in selection.selection:
                objs = selection.selection["objects"]
                # Check both cameras and cameras-top layers
                if ("cameras" in objs and objs["cameras"]) or ("cameras-top" in objs and objs["cameras-top"]):
                    new_cam = objs.get("cameras", objs.get("cameras-top", [None]))[0]
                    if new_cam and st.session_state.selected_camera != new_cam:
                        st.session_state.selected_camera = new_cam
                        st.rerun()
                
                if "road_weather" in objs and objs["road_weather"]:
                    new_station = objs["road_weather"][0]
                    if st.session_state.selected_station != new_station:
                        st.session_state.selected_station = new_station
                        st.rerun()
            else:
                if "cameras" in selection.selection: found_index = get_idx(selection.selection["cameras"])
                if found_index is not None and found_index < len(st.session_state.cameras):
                    new_cam = st.session_state.cameras[found_index]
                    if st.session_state.selected_camera != new_cam:
                        st.session_state.selected_camera = new_cam
                        st.rerun()
                
                # Fallback for road_weather if needed (usually objects is enough for single-object selection)
                if "road_weather" in selection.selection:
                    idx = get_idx(selection.selection["road_weather"])
                    if idx is not None and idx < len(st.session_state.road_weather):
                        new_station = st.session_state.road_weather[idx]
                        if st.session_state.selected_station != new_station:
                            st.session_state.selected_station = new_station
                            st.rerun()

        if play:
            step_size = max(1, total_mins // 50)
            for t in range(0, total_mins + 1, step_size):
                idx = int((t / total_mins) * (len(coords) - 1))
                car_pos = coords[idx]
                sim_dt = st.session_state.dep_dt + datetime.timedelta(minutes=t)
                
                # Time-based filtering for Open-Meteo data (same as static view)
                target_utc = sim_dt - datetime.timedelta(hours=2)
                target_h = target_utc.strftime('%Y-%m-%dT%H')
                
                # Filter temperature data for current time
                play_temp_data = [d for d in st.session_state.meteo_temp if d.get('time', '').startswith(target_h)]
                
                # Fallback: try local time if UTC doesn't match
                if not play_temp_data:
                    target_h_local = sim_dt.strftime('%Y-%m-%dT%H')
                    play_temp_data = [d for d in st.session_state.meteo_temp if d.get('time', '').startswith(target_h_local)]
                    if play_temp_data:
                        target_h = target_h_local
                
                # Filter precipitation data for current time
                play_precip_data = [d for d in st.session_state.meteo_precip if d.get('time', '').startswith(target_h)]
                
                # RainViewer weather data
                w_ts = None
                w_path = None
                if st.session_state.weather_timestamps:
                    w_ts = get_closest_timestamp(int(sim_dt.timestamp()), st.session_state.weather_timestamps)
                    if w_ts and st.session_state.weather_paths:
                        w_path = st.session_state.weather_paths.get(w_ts)

                deck = create_map(st.session_state.all_routes, st.session_state.selected_route_index, st.session_state.here_incidents, dt_msgs, car_pos, st.session_state.origin_coords, st.session_state.dest_coords, st.session_state.cameras, 
                                  st.session_state.road_weather, st.session_state.vms, st.session_state.maintenance, st.session_state.lam,
                                  layer_settings, map_style, w_ts, w_path, st.session_state.weather_host, weather_opacity,
                                  temperature_data=play_temp_data, precipitation_data=play_precip_data)
                map_placeholder.pydeck_chart(deck)
                time.sleep(0.05)
    
    # Right sidebar panel - AI Analysis
    with sidebar_col:
        st.markdown('<div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; background: white;">', unsafe_allow_html=True)
        st.subheader("🐧 Älykäs reittianalyysi")
        
        # Dialog function for AI analysis popup
        @st.dialog("🤖 AI Reittianalyysi", width="large")
        def show_ai_analysis_popup():
            if 'ai_analysis' in st.session_state:
                st.markdown(st.session_state['ai_analysis'], unsafe_allow_html=False)
                
                if 'ai_analysis_time' in st.session_state:
                    st.caption(f"🕐 Analysoitu: {st.session_state['ai_analysis_time'].strftime('%d.%m.%Y %H:%M')}")
                
                if st.button("Sulje", type="primary", use_container_width=True):
                    st.rerun()
        
        if st.button("🚀 Analysoi", type="primary", use_container_width=True, key="ai_analyze_btn"):
            with st.spinner("Analysoidaan..."):
                try:
                    analyzer = GeminiRouteAnalyzer()
                    if not analyzer.test_connection():
                        st.error("❌ Ei yhteyttä Gemini API:in")
                    else:
                        selected_idx = st.session_state.selected_route_index
                        intelligence = RouteIntelligence(
                            st.session_state.all_routes[selected_idx],
                            st.session_state.dep_dt
                        )
                        route_data = intelligence.collect_all_data()
                        data_summary = intelligence.summarize_for_ai()
                        route_summary = st.session_state.route_summaries[selected_idx]
                        
                        analysis = analyzer.analyze_route(
                            data_summary, route_summary,
                            st.session_state.dep_dt, "", ""
                        )
                        
                        st.session_state['ai_analysis'] = analysis
                        st.session_state['ai_analysis_time'] = datetime.datetime.now()
                        st.session_state['show_ai_popup'] = True  # Trigger popup
                        st.rerun()
                except Exception as e:
                    st.error(f"Virhe: {e}")
        
        # Show popup if flag is set
        if st.session_state.get('show_ai_popup', False):
            st.session_state['show_ai_popup'] = False  # Reset flag
            show_ai_analysis_popup()
        
        if 'ai_analysis' in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state['ai_analysis'], unsafe_allow_html=False)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if 'ai_analysis_time' in st.session_state:
                    st.caption(f"🕐 {st.session_state['ai_analysis_time'].strftime('%H:%M')}")
            with col2:
                if st.button("📄 Näytä", use_container_width=True, key="ai_show_popup_btn"):
                    show_ai_analysis_popup()
            with col3:
                if st.button("🗑️", use_container_width=True, key="ai_clear_btn"):
                    del st.session_state['ai_analysis']
                    if 'ai_analysis_time' in st.session_state:
                        del st.session_state['ai_analysis_time']
                    st.rerun()
        else:
            st.info("Klikkaa 'Analysoi' saadaksesi AI-pohjaisen reittianalyysin.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    c_inc, c_dt = st.columns(2)
    
    with c_inc:
        st.subheader("⚠️ Häiriöt")
        if st.session_state.here_incidents:
            # Luodaan lista valikkoa varten
            inc_opts = []
            for inc in st.session_state.here_incidents:
                typ = inc.get("tyyppi", "Häiriö")
                desc = inc.get("kuvaus", "")
                short = (desc[:40] + "..") if len(desc) > 40 else desc
                inc_opts.append(f"{typ} - {short}")
            
            sel_inc_idx = st.selectbox("Valitse häiriö", range(len(inc_opts)), format_func=lambda x: inc_opts[x], key="inc_sel_box")
            
            if sel_inc_idx is not None:
                inc = st.session_state.here_incidents[sel_inc_idx]
                typ = inc.get("tyyppi", "Häiriö")
                desc = inc.get("kuvaus", "")
                lat_i = inc.get("lat")
                # Severity
                severity = "warning"
                if "critical" in str(inc.get("taso", "")).lower(): severity = "critical"

                st.markdown(f"""
                <div class="feed-item {severity}">
                    <div class="feed-title">{typ}</div>
                    <div class="feed-body">{desc}</div>
                    <div class="feed-meta">Sijainti: {lat_i:.4f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Ei raportoituja häiriöitä.")

    with c_dt:
        st.subheader("📢 Tiedotteet")
        if st.session_state.digitraffic_messages:
            dt_opts = []
            for msg in st.session_state.digitraffic_messages:
                title = msg.get("otsikko", "Tiedote")
                loc = msg.get("sijainti", "")
                label = f"{title} ({loc})" if loc else title
                dt_opts.append(label)
            
            sel_dt_idx = st.selectbox("Valitse tiedote", range(len(dt_opts)), format_func=lambda x: dt_opts[x], key="dt_sel_box")
            
            if sel_dt_idx is not None:
                msg = st.session_state.digitraffic_messages[sel_dt_idx]
                title = msg.get("otsikko", "Tiedote")
                desc = msg.get("kuvaus", "")
                loc = msg.get("sijainti", "")
                t_update = msg.get("aika", "")
                
                st.markdown(f"""
                <div class="feed-item">
                    <div class="feed-title">🇫🇮 {title}</div>
                    <div class="feed-body">{desc}</div>
                    <div class="feed-meta">{loc} | {t_update}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Ei aktiivisia liikennetiedotteita.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("🌤️ Sää reitillä nyt ")
    
    if st.session_state.all_routes and st.session_state.road_weather:
        route_points = st.session_state.all_routes[st.session_state.selected_route_index]
        
        # Tarkistetaan, onko summary olemassa
        summary = st.session_state.route_summaries[st.session_state.selected_route_index]
        if summary:
            dur_hours = summary[1] # Käytetään aina liikennettä sääennusteen arviointiin (tai voisi käyttää valittua)
        else:
            dur_hours = 0
            
        dep_time = st.session_state.dep_dt
        
        # Valitaan 5 pistettä reitiltä
        indices = [0, len(route_points)//4, len(route_points)//2, 3*len(route_points)//4, len(route_points)-1]
        cols = st.columns(5)
        
        for i, idx in enumerate(indices):
            point = route_points[idx]
            progress = idx / len(route_points)
            eta = dep_time + datetime.timedelta(hours=dur_hours * progress)
            
            # Etsitään lähin sääasema
            nearest_station = None
            min_dist = float("inf")
            
            for s in st.session_state.road_weather:
                # Yksinkertainen etäisyys (ei haittaa vaikka epätarkka, riittää demoon)
                d = (s['lat'] - point[0])**2 + (s['lon'] - point[1])**2
                if d < min_dist:
                    min_dist = d
                    nearest_station = s
            
            with cols[i]:
                st.caption(f"📍 {int(progress*100)}% - {eta.strftime('%H:%M')}")
                if nearest_station and min_dist < 0.1: # n. 30km säde
                    name = nearest_station.get('name', 'Asema')
                    mun = nearest_station.get('municipality')
                    road = nearest_station.get('road_number')
                    
                    loc_str = ""
                    if mun: loc_str += f"{mun}"
                    if road: loc_str += f" (Vt {road})"
                    
                    if loc_str:
                        st.markdown(f"**{loc_str}**")
                        
                    st.metric(name, f"{nearest_station.get('air_temp')} °C", delta=f"Tie: {nearest_station.get('road_temp')}°C")
                else:
                    st.info("Ei sääasemaa lähellä")