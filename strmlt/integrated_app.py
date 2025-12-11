"""Integrated Road User Assistant.

Combines calendar, routing, weather, and traffic information
in a unified Streamlit interface.
"""

import streamlit as st
import requests
import json
from streamlit_calendar import calendar
import pydeck as pdk
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import flexpolyline
import os
from dotenv import load_dotenv
import math
import time

# Load environment and set Mapbox token
load_dotenv()
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
pdk.settings.mapbox_api_key = MAPBOX_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# RETRY HELPER
# ============================================================================

def retry_request(func, max_retries=3, timeout=30, backoff=1.0):
    """Retry a request function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func(timeout=timeout)
        except (requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout,
                ConnectionResetError) as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff * (2 ** attempt)
            logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
            time.sleep(wait_time)
    return None


# ============================================================================
# RAINVIEWER FUNCTIONS
# ============================================================================

@st.cache_data(ttl=300)
def get_rainviewer_data():
    """Fetch Rainviewer radar timestamps and paths."""
    try:
        response = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            host = data.get("host", "")
            radar = data.get("radar", {})
            past = radar.get("past", [])
            
            # Create timestamp -> path mapping
            ts_dict = {}
            for item in past:
                ts = item.get("time")
                path = item.get("path")
                if ts and path:
                    ts_dict[ts] = path
            
            return host, ts_dict
        return None, {}
    except Exception as e:
        logger.error(f"Rainviewer fetch failed: {e}")
        return None, {}


def get_closest_timestamp(target_ts: int, available_timestamps: List[int]) -> Optional[int]:
    """Find closest timestamp to target."""
    if not available_timestamps:
        return None
    return min(available_timestamps, key=lambda x: abs(x - target_ts))

# ============================================================================
# CONSTANTS
# ============================================================================

API_BASE_URL = "http://api:8000"
METEO_BACKEND_URL = "http://meteo-backend:8081"

TEMPERATURE_REGIONS = {
    "Etelä-Suomi": {
        "bbox": {"min_lon": 22.0, "min_lat": 59.5, "max_lon": 28.0, "max_lat": 62.5},
        "center": {"lat": 61.0, "lon": 25.0},
        "zoom": 6.5,
        "description": "Helsinki, Tampere, Turku, Lappeenranta"
    },
    "Länsi-Suomi": {
        "bbox": {"min_lon": 21.5, "min_lat": 61.0, "max_lon": 25.5, "max_lat": 64.0},
        "center": {"lat": 62.5, "lon": 23.5},
        "zoom": 6.5,
        "description": "Vaasa, Seinäjoki, Kokkola"
    },
    "Itä-Suomi": {
        "bbox": {"min_lon": 26.0, "min_lat": 61.5, "max_lon": 31.0, "max_lat": 64.5},
        "center": {"lat": 63.0, "lon": 28.5},
        "zoom": 6.5,
        "description": "Kuopio, Joensuu, Kajaani"
    },
    "Pohjois-Suomi": {
        "bbox": {"min_lon": 23.0, "min_lat": 65.0, "max_lon": 29.0, "max_lat": 68.5},
        "center": {"lat": 66.5, "lon": 26.0},
        "zoom": 6.0,
        "description": "Oulu, Rovaniemi, Kemi"
    },
}

TEMP_COLORS = {
    -30: [139, 0, 139], -20: [0, 0, 255], -10: [0, 191, 255],
    0: [173, 216, 230], 5: [255, 255, 255], 10: [255, 255, 200],
    15: [255, 255, 0], 20: [255, 200, 0], 25: [255, 165, 0],
    30: [255, 100, 0], 35: [255, 0, 0]
}

# ============================================================================
# HERE MAPS FUNCTIONS
# ============================================================================

def fetch_here_geocode(address: str) -> Optional[tuple]:
    """Geocode address using HERE Maps API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/here/geocode",
            params={"address": address},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            return (data["latitude"], data["longitude"])
        return None
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        return None


def fetch_route_weather_forecast(route_coords: List[Tuple[float, float]], 
                                  departure_time: datetime,
                                  duration_hours: float) -> Dict[str, Any]:
    """
    Fetch weather forecast for key points along route and surrounding area.
    Returns hourly forecasts for up to 6 hours ahead.
    
    Parameters
    ----------
    route_coords : List[Tuple[float, float]]
        List of (lat, lon) coordinates along route
    departure_time : datetime
        When user departs
    duration_hours : float
        Total trip duration in hours
    
    Returns
    -------
    dict
        Weather data with hourly forecasts
    """
    logger.info(f"fetch_route_weather_forecast called: {len(route_coords)} coords, duration: {duration_hours}h")
    
    if not route_coords or duration_hours <= 0:
        logger.warning("No route coords or invalid duration")
        return {"hourly_forecasts": {}, "departure_weather": None, "arrival_weather": None, "midpoint_weather": None}
    
    # Sample points along route (5 points)
    num_route_points = 5
    indices = [int(i * (len(route_coords) - 1) / (num_route_points - 1)) for i in range(num_route_points)]
    route_sample = [route_coords[i] for i in indices]
    
    # Add grid points around route for better coverage (7x7 grid for better visualization)
    lats = [coord[0] for coord in route_coords]
    lons = [coord[1] for coord in route_coords]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    # Expand by 15% for better coverage
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon
    min_lat -= lat_range * 0.15
    max_lat += lat_range * 0.15
    min_lon -= lon_range * 0.15
    max_lon += lon_range * 0.15
    
    # Create 7x7 grid around route for better heatmap
    grid_points = []
    grid_size = 7
    for i in range(grid_size):
        for j in range(grid_size):
            lat = min_lat + (max_lat - min_lat) * i / (grid_size - 1)
            lon = min_lon + (max_lon - min_lon) * j / (grid_size - 1)
            grid_points.append((lat, lon))
    
    all_sample_coords = route_sample + grid_points
    
    # Calculate times for route points (0h, 25%, 50%, 75%, 100% of trip)
    route_time_offsets = []
    for i in range(num_route_points):
        route_time_offsets.append(duration_hours * (i / (num_route_points - 1)))
    
    # Fetch hourly forecasts (0-6 hours) for each point
    hourly_forecasts = {}  # {hour: [points]}
    
    try:
        for coord_idx, coord in enumerate(all_sample_coords):
            lat = coord[0]
            lon = coord[1]
            
            # Determine if this is a route point or grid point
            is_route_point = coord_idx < num_route_points
            
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,precipitation,weather_code",
                "forecast_days": 1,
                "timezone": "Europe/Helsinki"
            }
            
            try:
                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    hourly = data.get("hourly", {})
                    times = hourly.get("time", [])
                    
                    if coord_idx == 0:  # Log first point only
                        logger.info(f"Open-Meteo API success for point 0: {len(times)} time slots")
                    
                    # Get forecasts for next 6 hours
                    for hour_offset in range(7):  # 0, 1, 2, 3, 4, 5, 6 hours
                        forecast_time = departure_time + timedelta(hours=hour_offset)
                        target_hour = forecast_time.strftime("%Y-%m-%dT%H:00")
                        
                        if target_hour in times:
                            idx = times.index(target_hour)
                            temp = hourly.get("temperature_2m", [])[idx]
                            precip = hourly.get("precipitation", [])[idx]
                            
                            is_snow = temp < 2
                            precip_type = "lunta" if is_snow else "sadetta"
                            
                            if precip > 5.0:
                                weather_desc = f"Voimakas {precip_type}"
                            elif precip > 1.0:
                                weather_desc = f"Kohtalainen {precip_type}"
                            elif precip > 0.1:
                                weather_desc = f"Kevyt {precip_type}"
                            else:
                                weather_desc = "Ei sadetta"
                            
                            point_data = {
                                "lat": lat,
                                "lon": lon,
                                "time": forecast_time,
                                "temperature": temp,
                                "precipitation": precip,
                                "is_snow": is_snow,
                                "weather_desc": weather_desc,
                                "is_route_point": is_route_point
                            }
                            
                            if hour_offset not in hourly_forecasts:
                                hourly_forecasts[hour_offset] = []
                            hourly_forecasts[hour_offset].append(point_data)
                else:
                    logger.error(f"Open-Meteo API error: {resp.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error fetching weather for point {coord_idx}: {e}")
                continue
        
        # Create summary points for the 3-box display (departure, midpoint, arrival)
        points_at_departure = hourly_forecasts.get(0, [])
        route_points_at_departure = [p for p in points_at_departure if p.get("is_route_point")]
        
        result = {
            "hourly_forecasts": hourly_forecasts,  # {hour: [points]}
            "departure_weather": route_points_at_departure[0] if route_points_at_departure else None,
            "midpoint_weather": route_points_at_departure[len(route_points_at_departure)//2] if len(route_points_at_departure) > 2 else None,
            "arrival_weather": route_points_at_departure[-1] if route_points_at_departure else None
        }
        
        logger.info(f"Weather forecast completed: {len(hourly_forecasts)} hours with data")
        for hour, points in hourly_forecasts.items():
            logger.info(f"  Hour {hour}: {len(points)} points")
        
        return result
    
    except Exception as e:
        logger.error(f"Weather forecast fetch failed: {e}")
        return {"hourly_forecasts": {}, "departure_weather": None, "arrival_weather": None, "midpoint_weather": None}


def fetch_here_route(origin_lat: float, origin_lon: float, 
                     dest_lat: float, dest_lon: float,
                     departure_time: Optional[str] = None,
                     routing_mode: str = "fast",
                     avoid_features: List[str] = None,
                     alternatives: int = 2) -> Optional[Dict]:
    """Fetch route from HERE Maps API with alternatives."""
    try:
        payload = {
            "origin_lat": origin_lat,
            "origin_lon": origin_lon,
            "dest_lat": dest_lat,
            "dest_lon": dest_lon,
            "routing_mode": routing_mode,
            "alternatives": alternatives
        }
        if departure_time:
            payload["departure_time"] = departure_time
        if avoid_features:
            payload["avoid_features"] = avoid_features
        
        response = requests.post(
            f"{API_BASE_URL}/here/route",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Route fetch failed: {e}")
        return None


def fetch_digitraffic_cameras(route_coords: List[tuple]) -> List[Dict]:
    """Fetch weather cameras near route with retry logic."""
    try:
        # Sample max 100 points to avoid URL length issues
        if len(route_coords) > 100:
            step = len(route_coords) // 100
            sampled_coords = route_coords[::step][:100]
        else:
            sampled_coords = route_coords
        
        coords_str = ";".join([f"{coord[0]},{coord[1]}" for coord in sampled_coords])
        
        def make_request(timeout):
            response = requests.get(
                f"{API_BASE_URL}/here/cameras",
                params={"route_coords": coords_str, "radius_km": 30},
                timeout=timeout
            )
            response.raise_for_status()
            return response
        
        response = retry_request(make_request, max_retries=3, timeout=30)
        if response:
            data = response.json()
            return data.get("cameras", [])
        return []
    except Exception as e:
        logger.error(f"Camera fetch failed: {e}")
        return []


def fetch_digitraffic_road_weather(route_coords: List[tuple]) -> List[Dict]:
    """Fetch road weather stations near route with retry logic."""
    try:
        # Sample max 100 points to avoid URL length issues
        if len(route_coords) > 100:
            step = len(route_coords) // 100
            sampled_coords = route_coords[::step][:100]
        else:
            sampled_coords = route_coords
        
        coords_str = ";".join([f"{coord[0]},{coord[1]}" for coord in sampled_coords])
        
        def make_request(timeout):
            response = requests.get(
                f"{API_BASE_URL}/here/road-weather",
                params={"route_coords": coords_str, "radius_km": 30},
                timeout=timeout
            )
            response.raise_for_status()
            return response
        
        response = retry_request(make_request, max_retries=3, timeout=30)
        if response:
            data = response.json()
            return data.get("stations", [])
        return []
    except Exception as e:
        logger.error(f"Road weather fetch failed: {e}")
        return []


def fetch_digitraffic_vms(route_coords: List[tuple]) -> List[Dict]:
    """Fetch VMS (variable message signs) near route with retry logic."""
    try:
        # Sample max 100 points to avoid URL length issues
        if len(route_coords) > 100:
            step = len(route_coords) // 100
            sampled_coords = route_coords[::step][:100]
        else:
            sampled_coords = route_coords
        
        coords_str = ";".join([f"{coord[0]},{coord[1]}" for coord in sampled_coords])
        
        def make_request(timeout):
            response = requests.get(
                f"{API_BASE_URL}/here/vms",
                params={"route_coords": coords_str, "radius_km": 30},
                timeout=timeout
            )
            response.raise_for_status()
            return response
        
        response = retry_request(make_request, max_retries=3, timeout=30)
        if response:
            data = response.json()
            return data.get("signs", [])
        return []
    except Exception as e:
        logger.error(f"VMS fetch failed: {e}")
        return []


def fetch_digitraffic_maintenance(route_coords: List[tuple]) -> List[Dict]:
    """Fetch maintenance tasks near route with retry logic."""
    try:
        # Sample max 100 points to avoid URL length issues
        if len(route_coords) > 100:
            step = len(route_coords) // 100
            sampled_coords = route_coords[::step][:100]
        else:
            sampled_coords = route_coords
        
        coords_str = ";".join([f"{coord[0]},{coord[1]}" for coord in sampled_coords])
        
        def make_request(timeout):
            response = requests.get(
                f"{API_BASE_URL}/here/maintenance",
                params={"route_coords": coords_str, "radius_km": 30},
                timeout=timeout
            )
            response.raise_for_status()
            return response
        
        response = retry_request(make_request, max_retries=3, timeout=30)
        if response:
            data = response.json()
            return data.get("tasks", [])
        return []
    except Exception as e:
        logger.error(f"Maintenance fetch failed: {e}")
        return []


def fetch_digitraffic_lam(route_coords: List[tuple]) -> List[Dict]:
    """Fetch LAM stations near route with retry logic."""
    try:
        # Sample max 100 points to avoid URL length issues
        if len(route_coords) > 100:
            step = len(route_coords) // 100
            sampled_coords = route_coords[::step][:100]
        else:
            sampled_coords = route_coords
        
        coords_str = ";".join([f"{coord[0]},{coord[1]}" for coord in sampled_coords])
        
        def make_request(timeout):
            response = requests.get(
                f"{API_BASE_URL}/here/lam",
                params={"route_coords": coords_str, "radius_km": 30},
                timeout=timeout
            )
            response.raise_for_status()
            return response
        
        response = retry_request(make_request, max_retries=3, timeout=30)
        if response:
            data = response.json()
            return data.get("stations", [])
        return []
    except Exception as e:
        logger.error(f"LAM fetch failed: {e}")
        return []


def fetch_digitraffic_messages(route_coords: List[tuple]) -> List[Dict]:
    """Fetch traffic messages near route with retry logic."""
    try:
        # Sample max 100 points to avoid URL length issues
        if len(route_coords) > 100:
            step = len(route_coords) // 100
            sampled_coords = route_coords[::step][:100]
        else:
            sampled_coords = route_coords
        
        coords_str = ";".join([f"{coord[0]},{coord[1]}" for coord in sampled_coords])
        
        def make_request(timeout):
            response = requests.get(
                f"{API_BASE_URL}/here/messages",
                params={"route_coords": coords_str, "radius_km": 30},
                timeout=timeout
            )
            response.raise_for_status()
            return response
        
        response = retry_request(make_request, max_retries=3, timeout=30)
        if response:
            data = response.json()
            return data.get("messages", [])
        return []
    except Exception as e:
        logger.error(f"Messages fetch failed: {e}")
        return []


@st.cache_data(ttl=300)
def get_cached_weather_data():
    """Fetch Rainviewer weather radar data."""
    try:
        return None, {}
    except Exception as e:
        logger.error(f"Rainviewer fetch failed: {e}")
        return None, {}


# ============================================================================
# MAP CREATION
# ============================================================================

def create_route_map(route_polyline: str, origin_coords: tuple, dest_coords: tuple,
                     cameras: List[Dict] = None, road_weather: List[Dict] = None,
                     vms: List[Dict] = None, maintenance: List[Dict] = None, 
                     lam: List[Dict] = None, incidents: List[Dict] = None,
                     messages: List[Dict] = None,
                     layer_settings: Dict = None,
                     car_position: tuple = None,
                     all_routes: List[str] = None,
                     selected_route_index: int = 0,
                     map_style: str = "mapbox://styles/mapbox/dark-v11",
                     weather_ts: int = None,
                     weather_path: str = None,
                     weather_host: str = None,
                     weather_opacity: float = 0.6,
                     selected_hour: int = 0):
    """Create PyDeck map with route and all Digitraffic layers.
    
    Parameters
    ----------
    selected_hour : int
        Hour offset from departure (0-6) for weather visualization
    """
    layers = []
    
    if layer_settings is None:
        layer_settings = {}
    
    # Rainviewer precipitation layer (only show for first hour - real-time data)
    show_rainviewer = layer_settings.get("show_rainviewer", False) and selected_hour == 0
    if show_rainviewer and weather_ts and weather_path and weather_host:
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
                if count >= max_tiles:
                    break
                
                nw_lat, nw_lon = num2deg(x, y, zoom)
                se_lat, se_lon = num2deg(x + 1, y + 1, zoom)
                
                bounds = [nw_lon, se_lat, se_lon, nw_lat]
                tile_url = f"{weather_host}{weather_path}/256/{zoom}/{x}/{y}/6/1_1.png"
                
                layers.append(pdk.Layer(
                    "BitmapLayer",
                    id=f"rainviewer-tile-{x}-{y}",
                    image=tile_url,
                    bounds=bounds,
                    opacity=weather_opacity
                ))
                count += 1
    
    # Route layers
    if layer_settings.get("show_route", True):
        if all_routes and len(all_routes) > 1:
            for i, polyline in enumerate(all_routes):
                if i == selected_route_index:
                    continue
                
                try:
                    route_coords = flexpolyline.decode(polyline)
                    path_data = [[coord[1], coord[0]] for coord in route_coords]
                    
                    layers.append(pdk.Layer(
                        "PathLayer",
                        data=[{"path": path_data}],
                        get_path="path",
                        get_color=[150, 150, 150],
                        width_scale=20,
                        width_min_pixels=2,
                        opacity=0.4,
                    ))
                except Exception as e:
                    logger.error(f"Failed to decode alternative route {i}: {e}")
            
            if selected_route_index < len(all_routes):
                try:
                    selected_polyline = all_routes[selected_route_index]
                    route_coords = flexpolyline.decode(selected_polyline)
                    path_data = [[coord[1], coord[0]] for coord in route_coords]
                    
                    layers.append(pdk.Layer(
                        "PathLayer",
                        data=[{"path": path_data}],
                        get_path="path",
                        get_color=[60, 160, 255],
                        width_scale=20,
                        width_min_pixels=4,
                        opacity=0.9,
                    ))
                except Exception as e:
                    logger.error(f"Failed to decode selected route: {e}")
                    route_coords = []
        elif route_polyline:
            try:
                route_coords = flexpolyline.decode(route_polyline)
                path_data = [[coord[1], coord[0]] for coord in route_coords]
                
                layers.append(pdk.Layer(
                    "PathLayer",
                    data=[{"path": path_data}],
                    get_path="path",
                    get_color=[60, 160, 255],
                    width_scale=20,
                    width_min_pixels=4,
                    opacity=0.9,
                ))
            except Exception as e:
                logger.error(f"Route decode failed: {e}")
                route_coords = []
        else:
            route_coords = []
    else:
        route_coords = []
    
    # Start/end markers
    point_data = []
    if origin_coords:
        point_data.append({
            "pos": [origin_coords[1], origin_coords[0]],
            "color": [0, 255, 100],
            "name": "Lähtö"
        })
    if dest_coords:
        point_data.append({
            "pos": [dest_coords[1], dest_coords[0]],
            "color": [255, 50, 50],
            "name": "Määränpää"
        })
    
    if point_data:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=point_data,
            get_position="pos",
            get_color="color",
            get_radius=1000,
            radius_min_pixels=8,
            pickable=True,
            stroked=True,
            get_line_color=[255, 255, 255],
            line_width_min_pixels=2
        ))
    
    # Weather cameras
    if layer_settings.get("show_cameras", False) and cameras:
        logger.info(f"Rendering {len(cameras)} cameras on map")
        if cameras:
            logger.info(f"First camera data: {cameras[0]}")
        
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            id="cameras",
            data=cameras,
            get_position="[lon, lat]",
            get_color=[255, 220, 0],
            get_radius=800,
            radius_min_pixels=8,
            pickable=True,
            stroked=True,
            get_line_color=[0, 0, 0],
            line_width_min_pixels=1,
            auto_highlight=True
        ))
    
    # Road weather stations
    if layer_settings.get("show_road_weather", False) and road_weather:
        rw_points = []
        for r in road_weather:
            temp = r.get("air_temp")
            color = [200, 200, 200]
            if temp is not None:
                if temp < 0:
                    color = [0, 100, 255]
                elif temp > 0:
                    color = [255, 100, 0]
            
            rw_points.append({
                "pos": [r['lon'], r['lat']],
                "color": color,
                "name": f"{r.get('name')}\nIlma: {r.get('air_temp')}°C\nTie: {r.get('road_temp')}°C",
                "air_temp": r.get("air_temp"),
                "road_temp": r.get("road_temp")
            })
        
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=rw_points,
            get_position="pos",
            get_color="color",
            get_radius=800,
            pickable=True,
            stroked=True,
            get_line_color=[255, 255, 255],
            line_width_min_pixels=1,
            radius_min_pixels=6,
            auto_highlight=True
        ))
    
    # VMS
    if layer_settings.get("show_vms", False) and vms:
        vms_points = []
        for v in vms:
            vms_points.append({
                "pos": [v['lon'], v['lat']],
                "name": f"Opaste: {v.get('name')}",
                "color": [255, 0, 255]
            })
        
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=vms_points,
            get_position="pos",
            get_color="color",
            get_radius=600,
            pickable=True,
            stroked=True,
            get_line_color=[0, 0, 0],
            line_width_min_pixels=1,
            radius_min_pixels=4
        ))
    
    # LAM stations
    if layer_settings.get("show_lam", False) and lam:
        lam_points = []
        for l in lam:
            lam_points.append({
                "pos": [l['lon'], l['lat']],
                "name": f"{l.get('name')}\nNop: {l.get('speed')} km/h\nMäärä: {l.get('volume')} kpl/h",
                "color": [0, 255, 100]
            })
        
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=lam_points,
            get_position="pos",
            get_color="color",
            get_radius=600,
            pickable=True,
            stroked=True,
            get_line_color=[0, 0, 0],
            line_width_min_pixels=1,
            radius_min_pixels=4
        ))
    
    # Maintenance
    if layer_settings.get("show_maintenance", False) and maintenance:
        m_paths = []
        for m in maintenance:
            geom = m.get("geometry")
            if geom and geom.get("type") == "MultiLineString":
                for line in geom.get("coordinates", []):
                    m_paths.append({
                        "path": line,
                        "name": f"Huolto: {m.get('task')} ({m.get('time')})"
                    })
            elif geom and geom.get("type") == "LineString":
                m_paths.append({
                    "path": geom.get("coordinates", []),
                    "name": f"Huolto: {m.get('task')} ({m.get('time')})"
                })
        
        if m_paths:
            layers.append(pdk.Layer(
                "PathLayer",
                data=m_paths,
                get_path="path",
                get_color=[255, 165, 0],
                width_scale=10,
                width_min_pixels=2,
                opacity=0.6,
                pickable=True
            ))
    
    # Incidents
    if layer_settings.get("show_incidents", False) and incidents:
        incident_points = []
        for i in incidents:
            if i.get('lat') and i.get('lon'):
                incident_points.append({
                    "pos": [i['lon'], i['lat']],
                    "color": [200, 0, 0] if 'critical' in str(i.get('taso', '')) else [255, 140, 0],
                    "name": i.get('tyyppi', 'Häiriö')
                })
        
        if incident_points:
            layers.append(pdk.Layer(
                "ScatterplotLayer",
                data=incident_points,
                get_position="pos",
                get_color="color",
                get_radius=600,
                pickable=True,
                stroked=True,
                get_line_color=[255, 255, 255],
                line_width_min_pixels=1
            ))
    
    # Traffic messages
    if layer_settings.get("show_incidents", False) and messages:
        dt_points = []
        for d in messages:
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
                get_position="pos",
                get_color="color",
                get_radius=600,
                pickable=True,
                stroked=True,
                get_line_color=[0, 0, 0],
                line_width_min_pixels=1
            ))
    
    # Temperature forecast - use selected hour
    if layer_settings.get("show_temperature", False):
        forecast_data = st.session_state.get("weather_forecast", {})
        hourly_forecasts = forecast_data.get("hourly_forecasts", {})
        
        # Get forecast points for selected hour (cap at 6)
        selected_hour_capped = min(selected_hour, 6)
        forecast_points = hourly_forecasts.get(selected_hour_capped, [])
        
        if forecast_points:
            temp_data = []
            for point in forecast_points:
                temp = point.get("temperature", 0)
                if temp < -20:
                    color = [0, 0, 139]
                elif temp < -10:
                    color = [0, 0, 255]
                elif temp < 0:
                    color = [100, 150, 255]
                elif temp < 10:
                    color = [200, 200, 100]
                elif temp < 20:
                    color = [255, 165, 0]
                elif temp < 30:
                    color = [255, 100, 50]
                else:
                    color = [200, 0, 0]
                
                temp_data.append({
                    "pos": [point["lon"], point["lat"]],
                    "temp": temp,
                    "color": color,
                    "name": f"{temp}°C"
                })
            
            layers.append(pdk.Layer(
                "ScatterplotLayer",
                data=temp_data,
                get_position="pos",
                get_color="color",
                get_radius=15000,
                radius_min_pixels=25,
                pickable=True,
                opacity=0.7,
                stroked=True,
                get_line_color=[255, 255, 255],
                line_width_min_pixels=2
            ))
    
    # Precipitation forecast heatmap - use selected hour
    if layer_settings.get("show_weather_forecast", False):
        forecast_data = st.session_state.get("weather_forecast", {})
        hourly_forecasts = forecast_data.get("hourly_forecasts", {})
        
        # Get forecast points for selected hour (cap at 6)
        selected_hour_capped = min(selected_hour, 6)
        forecast_points = hourly_forecasts.get(selected_hour_capped, [])
        
        if forecast_points:
            rain_data = []
            snow_data = []
            
            for point in forecast_points:
                precip = point.get("precipitation", 0)
                temp = point.get("temperature", 0)
                
                if precip > 0.1:
                    is_snow = temp < 2
                    weight = min(precip / 10.0, 1.0)
                    
                    point_data = {
                        "pos": [point["lon"], point["lat"]],
                        "weight": weight
                    }
                    
                    if is_snow:
                        snow_data.append(point_data)
                    else:
                        rain_data.append(point_data)
            
            if rain_data:
                layers.append(pdk.Layer(
                    "HeatmapLayer",
                    data=rain_data,
                    id="rain_heatmap",
                    get_position="pos",
                    get_weight="weight",
                    radiusPixels=60,
                    intensity=2.0,
                    threshold=0.02,
                    colorRange=[
                        [240, 240, 240, 0],
                        [150, 200, 255, 80],
                        [100, 150, 255, 120],
                        [50, 100, 255, 160],
                        [0, 50, 200, 200],
                    ]
                ))
            
            if snow_data:
                layers.append(pdk.Layer(
                    "HeatmapLayer",
                    data=snow_data,
                    id="snow_heatmap",
                    get_position="pos",
                    get_weight="weight",
                    radiusPixels=60,
                    intensity=2.0,
                    threshold=0.02,
                    colorRange=[
                        [240, 240, 240, 0],
                        [200, 220, 255, 100],
                        [150, 180, 230, 140],
                        [100, 130, 200, 180],
                        [50, 80, 150, 220],
                    ]
                ))
    
    # Car position
    if layer_settings.get("show_car", False) and car_position:
        car_lat = car_position[0]
        car_lon = car_position[1]
        
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=[{
                "pos": [car_lon, car_lat],
                "name": "Auto",
                "color": [0, 100, 255]
            }],
            get_position="pos",
            get_color="color",
            get_radius=1000,
            radius_min_pixels=10,
            pickable=True,
            stroked=True,
            get_line_color=[255, 255, 255],
            line_width_min_pixels=2
        ))
    
    # Calculate view state
    if route_coords:
        formatted_points = [[p[1], p[0]] for p in route_coords]
        from pydeck.data_utils import compute_view
        view_state = compute_view(formatted_points, view_proportion=0.75)
        view_state.pitch = 0
    else:
        view_state = pdk.ViewState(
            latitude=61.92,
            longitude=25.74,
            zoom=6
        )
    
    tooltip = {"text": "{id}"}
    
    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=map_style,
        api_keys={"mapbox": MAPBOX_TOKEN},
        tooltip=tooltip
    )


# ============================================================================
# CALENDAR FUNCTIONS
# ============================================================================

def _get_available_calendars() -> List[str]:
    """Get list of available calendar sources."""
    cals = []
    if "outlook_events_data" in st.session_state:
        cals.append("Outlook")
    if "ical_events_data" in st.session_state:
        cals.append("iCal")
    return cals


@st.cache_data
def _add_outlook_events():
    """Format Outlook events for calendar display."""
    events = []
    for event in st.session_state["outlook_events_data"]:
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
    return events


@st.cache_data
def _add_ical_events():
    """Format iCal events for calendar display."""
    events = []
    for event in st.session_state["ical_events_data"]:
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
    return events


# ============================================================================
# WEATHER MAP FUNCTIONS
# ============================================================================

def get_color_for_temperature(temp: float) -> List[int]:
    """Get RGB color for temperature with interpolation."""
    temps = sorted(TEMP_COLORS.keys())
    if temp <= temps[0]:
        return TEMP_COLORS[temps[0]]
    if temp >= temps[-1]:
        return TEMP_COLORS[temps[-1]]
    
    for i in range(len(temps) - 1):
        if temps[i] <= temp <= temps[i + 1]:
            lower_temp, upper_temp = temps[i], temps[i + 1]
            lower_color, upper_color = TEMP_COLORS[lower_temp], TEMP_COLORS[upper_temp]
            ratio = (temp - lower_temp) / (upper_temp - lower_temp)
            return [int(lower_color[j] + ratio * (upper_color[j] - lower_color[j])) for j in range(3)]
    return [255, 255, 255]


def fetch_map_temperature_data(start_time: datetime, hours: int = 6, bbox: Dict = None) -> Optional[Dict]:
    """Fetch temperature data for map visualization."""
    if bbox is None:
        bbox = TEMPERATURE_REGIONS["Etelä-Suomi"]["bbox"]
    
    try:
        params = {
            "min_lon": bbox["min_lon"],
            "min_lat": bbox["min_lat"],
            "max_lon": bbox["max_lon"],
            "max_lat": bbox["max_lat"],
            "start_time": start_time.isoformat(),
            "hours": hours
        }
        response = requests.get(f"{METEO_BACKEND_URL}/api/forecast/temperature", params=params, timeout=120)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch temperature: {e}")
        return None


def fetch_map_precipitation_data(start_time: datetime, hours: int = 6, bbox: Dict = None) -> Optional[Dict]:
    """Fetch precipitation data for map visualization."""
    if bbox is None:
        bbox = TEMPERATURE_REGIONS["Etelä-Suomi"]["bbox"]
    
    try:
        params = {
            "min_lon": bbox["min_lon"],
            "min_lat": bbox["min_lat"],
            "max_lon": bbox["max_lon"],
            "max_lat": bbox["max_lat"],
            "start_time": start_time.isoformat(),
            "hours": hours
        }
        response = requests.get(f"{METEO_BACKEND_URL}/api/forecast/weather", params=params, timeout=120)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch precipitation: {e}")
        return None


def create_temperature_layer(data: List[Dict], selected_time: str) -> Optional[pdk.Layer]:
    """Create temperature scatterplot layer."""
    if not data:
        return None
    
    filtered = [d for d in data if d.get('time', '').startswith(selected_time[:13])]
    if not filtered:
        return None
    
    df = pd.DataFrame(filtered)
    df['color'] = df['temperature'].apply(lambda t: get_color_for_temperature(t) + [220])
    df['latitude'] = df['lat']
    df['longitude'] = df['lon']
    df['formatted_time'] = df['time'].apply(
        lambda t: datetime.fromisoformat(t.replace('Z', '')).strftime('%Y-%m-%d %H:%M')
    )
    
    return pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=14000,
        pickable=True,
        opacity=0.85,
        filled=True,
    )


def create_precipitation_layer(data: List[Dict], selected_time: str) -> Optional[pdk.Layer]:
    """Create precipitation heatmap layer."""
    if not data:
        return None
    
    precip_data = []
    for d in data:
        if d.get('time', '').startswith(selected_time[:13]):
            precip = d.get('precipitation', 0)
            if precip and precip > 0.01:
                temp = d.get('temperature', 0)
                time_str = d.get('time', '')
                formatted_time = datetime.fromisoformat(time_str.replace('Z', '')).strftime('%Y-%m-%d %H:%M')
                
                precip_data.append({
                    'lat': d['lat'],
                    'lon': d['lon'],
                    'latitude': d['lat'],
                    'longitude': d['lon'],
                    'temperature': temp,
                    'precipitation': precip,
                    'weight': min(precip / 5.0, 1.0),
                    'formatted_time': formatted_time
                })
    
    if not precip_data:
        return None
    
    df = pd.DataFrame(precip_data)
    
    return pdk.Layer(
        "HeatmapLayer",
        data=df,
        get_position='[lon, lat]',
        get_weight='weight',
        radiusPixels=100,
        intensity=3,
        threshold=0.02,
        opacity=0.6,
        colorRange=[
            [200, 220, 255],
            [100, 150, 255],
            [50, 100, 255],
            [0, 50, 200],
            [0, 0, 150],
        ],
    )


def get_unique_times(data: List[Dict]) -> List[str]:
    """Extract unique timestamps from data."""
    if not data:
        return []
    return sorted(set(d.get('time', '') for d in data if d.get('time')))


# ============================================================================
# MAIN APP
# ============================================================================

st.set_page_config(page_title="Tienkäyttäjän Apuri", layout="wide")

st.title("Tienkäyttäjän Apuri")
st.caption("Yhdistetty matkasuunnittelutyökalu: Kalenteri, Reititys, Sää ja Liikenne")

# Käyttöohjeet
with st.expander("Käyttöohjeet", expanded=False):
    st.markdown("""
    Tervetuloa käyttämään työkalua, jonka avulla voit sujuvasti suunnitella esim. koulumatkasi omien aikataulujesi sekä sää- ja tieolosuhteiden mukaan.

    Voit aloittaa ohjelman käytön valitsemalla kalenteripalvelun jota haluat hyödyntää matkan suunnittelussa. Tämän jälkeen sinulle aukeaa reittisuunnittelu. Kun olet valinnut reitin niin sinulle aukeaa tieto matkastasi - voit itse valita mitä tietoja haluat tarkastella.

    Rainviewer näkymä kartalla antaa valitsemasi lähtöajan sadenäkymän. Jos sinua kiinnostaa ennustettu sää kartalla niin sitä voit tarkastella lämpötila- ja sade-ennustuksen kautta.

    Säätietoja voi myös tarkastella tehokkaasti omasta valikostaan. Voit myös simuloida säätä matkallesi 15min välein.

    Turvallista matkaa!
    """)

if "layer_settings" not in st.session_state:
    st.session_state["layer_settings"] = {
        "show_route": True,
        "show_weather_forecast": False,
        "show_rainviewer": True,
        "show_temperature": False,
        "show_incidents": True,
        "show_cameras": True,
        "show_road_weather": True,
        "show_vms": False,
        "show_maintenance": False,
        "show_lam": False,
        "show_car": True,
    }

layer_settings = st.session_state["layer_settings"]

with st.sidebar:
    # KALENTERIHAKU (ylimpänä)
    st.subheader("Kalenterit")
    
    with st.expander("iCal-kalenteri"):
        ical_url = st.text_input(
            "iCal URL",
            value="https://lukkarit.kamk.fi/ical.php?hash=E74AC94AE7A19AC99110C39EE535C0DBB0DF8AAE",
            key="ical_url"
        )
        if st.button("Hae iCal", key="fetch_ical"):
            try:
                response = requests.get(f"{API_BASE_URL}/ical/events", params={"url": ical_url})
                if response.status_code == 200:
                    st.session_state["ical_events_data"] = response.json()
                    st.success(f"{len(st.session_state['ical_events_data'])} tapahtumaa haettu")
                else:
                    st.error(f"Virhe: {response.status_code}")
            except Exception as e:
                st.error(f"Yhteysvirhe: {e}")
    
    with st.expander("Outlook-kalenteri"):
        if "access_token" in st.query_params:
            st.session_state["access_token"] = st.query_params["access_token"]
            st.query_params.clear()
            st.rerun()
        
        login_url = f"{API_BASE_URL}/graph/login"
        st.markdown(f"**[Kirjaudu sisään]({login_url})**")
        
        token = st.text_input(
            "Token",
            value=st.session_state.get("access_token", ""),
            type="password",
            key="outlook_token"
        )
        
        if st.button("Hae Outlook", key="fetch_outlook"):
            if token:
                try:
                    response = requests.get(f"{API_BASE_URL}/graph/events", params={"token": token})
                    if response.status_code == 200:
                        st.session_state["outlook_events_data"] = response.json()
                        st.success(f"{len(st.session_state['outlook_events_data'])} tapahtumaa haettu")
                    else:
                        st.error(f"Virhe: {response.status_code}")
                except Exception as e:
                    st.error(f"Yhteysvirhe: {e}")
            else:
                st.warning("Anna token ensin")
    
    st.divider()
    
    # ASETUKSET
    st.header("Asetukset")
    
    st.subheader("Karttatyyli")
    map_style = st.selectbox(
        "Tyyli",
        ["mapbox://styles/mapbox/dark-v11", "mapbox://styles/mapbox/streets-v12", "mapbox://styles/mapbox/satellite-streets-v12"],
        format_func=lambda x: {"mapbox://styles/mapbox/dark-v11": "Tumma", "mapbox://styles/mapbox/streets-v12": "Kadut", "mapbox://styles/mapbox/satellite-streets-v12": "Satelliitti"}[x],
        key="sidebar_map_style"
    )
    
    st.divider()
    
    st.subheader("Reititys")
    st.session_state["routing_mode"] = st.radio(
        "Optimointi",
        ["fast", "short"],
        format_func=lambda x: "Nopein" if x == "fast" else "Lyhin",
        index=0 if st.session_state.get("routing_mode", "fast") == "fast" else 1
    )
    
    st.session_state["avoid_options"] = []
    if st.checkbox("Vältä moottoriteitä", value="controlledAccessHighway" in st.session_state.get("avoid_options", [])):
        if "controlledAccessHighway" not in st.session_state["avoid_options"]:
            st.session_state["avoid_options"].append("controlledAccessHighway")
    else:
        if "controlledAccessHighway" in st.session_state.get("avoid_options", []):
            st.session_state["avoid_options"].remove("controlledAccessHighway")
            
    if st.checkbox("Vältä tietulleja", value="tollRoad" in st.session_state.get("avoid_options", [])):
        if "tollRoad" not in st.session_state["avoid_options"]:
            st.session_state["avoid_options"].append("tollRoad")
    else:
        if "tollRoad" in st.session_state.get("avoid_options", []):
            st.session_state["avoid_options"].remove("tollRoad")
    
    st.divider()
    
    # Camera selection (dropdown as workaround for PyDeck click issues)
    if "current_route" in st.session_state and st.session_state.get("cameras"):
        st.subheader("📷 Kelikamerat")
        cameras_list = st.session_state.get("cameras", [])
        st.caption(f"{len(cameras_list)} kameraa reitin varrella")
        
        # Create dropdown options
        camera_options = ["Valitse kamera..."] + [f"{cam.get('id', 'N/A')} - {cam.get('name', 'Tuntematon')}" for cam in cameras_list]
        
        selected_option = st.selectbox(
            "Valitse kelikamera",
            camera_options,
            key="camera_selector"
        )
        
        if selected_option != "Valitse kamera...":
            # Find selected camera
            selected_index = camera_options.index(selected_option) - 1
            st.session_state["selected_camera"] = cameras_list[selected_index]
        elif "selected_camera" in st.session_state:
            # Clear if "Valitse kamera..." is selected
            if selected_option == "Valitse kamera...":
                pass  # Keep current selection
    
    # Selected camera display
    if "selected_camera" in st.session_state and st.session_state["selected_camera"]:
        camera = st.session_state["selected_camera"]
        logger.info(f"Displaying camera in sidebar: {camera.get('name')}")
        
        st.markdown(f"**{camera.get('name', 'Tuntematon')}**")
        st.caption(f"ID: {camera.get('id', 'N/A')}, Lat: {camera.get('lat', 'N/A'):.4f}, Lon: {camera.get('lon', 'N/A'):.4f}")
        
        img_url = camera.get("imageUrl")
        logger.info(f"Camera image URL: {img_url}")
        
        if img_url:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(img_url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    st.image(resp.content, use_container_width=True)
                    logger.info("Camera image loaded successfully")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 Päivitä", key="refresh_camera"):
                            st.rerun()
                    with col2:
                        if st.button("❌ Sulje", key="close_camera"):
                            del st.session_state["selected_camera"]
                            st.rerun()
                else:
                    st.error(f"Kuvan lataus epäonnistui: {resp.status_code}")
                    logger.error(f"Camera image load failed: {resp.status_code}")
            except Exception as e:
                st.error(f"Yhteysvirhe: {e}")
                logger.error(f"Camera image exception: {e}")
        else:
            st.warning("Ei kuvaa saatavilla")
            logger.warning("Camera has no imageUrl")
        
        st.divider()
    else:
        logger.debug("No camera selected in session state")
    
    if "current_route" in st.session_state and st.session_state["current_route"].get("polyline"):
        st.subheader("Reitin korkeusprofiili")
        
        try:
            route = st.session_state["current_route"]
            route_coords = flexpolyline.decode(route["polyline"])
            
            has_elevation = len(route_coords[0]) > 2 if route_coords else False
            
            if has_elevation:
                elevations = [coord[2] if len(coord) > 2 else 0 for coord in route_coords]
                
                total_duration_hours = route.get("duration_hours", 0)
                total_minutes = int(total_duration_hours * 60) if total_duration_hours > 0 else 1
                current_time = st.session_state.get("car_time_minutes", 0)
                progress = current_time / total_minutes if total_minutes > 0 else 0
                current_idx = int(progress * len(elevations))
                current_idx = min(current_idx, len(elevations) - 1)
                
                import pandas as pd
                import numpy as np
                
                df = pd.DataFrame({
                    "Kuljettu": [elevations[i] if i <= current_idx else np.nan for i in range(len(elevations))],
                    "Jäljellä": [elevations[i] if i > current_idx else np.nan for i in range(len(elevations))]
                })
                
                st.area_chart(
                    df,
                    color=["#ffaa00", "#cccccc"],
                    use_container_width=True,
                    height=200
                )
                
                st.caption(f"Nykyinen korkeus: {elevations[current_idx]:.0f} m")
                
            else:
                st.info("Ei korkeusdataa")
                
                total_duration_hours = route.get("duration_hours", 0)
                total_minutes = int(total_duration_hours * 60) if total_duration_hours > 0 else 1
                current_time = st.session_state.get("car_time_minutes", 0)
                progress = current_time / total_minutes if total_minutes > 0 else 0
                
                st.progress(progress)
                st.caption(f"Edistyminen: {progress*100:.0f}%")
                
        except Exception as e:
            st.error(f"Profiilin virhe: {e}")

st.markdown("---")
st.header("Kalenteri")

available_calendars = _get_available_calendars()

if not available_calendars:
    st.info("Lisää kalenteri sivupalkista (Asetukset)")
else:
    selected_calendars = st.pills(
        "Näytä kalenterit:",
        available_calendars,
        selection_mode="multi",
        default=available_calendars
    )
    
    events = []
    if "iCal" in selected_calendars:
        events.extend(_add_ical_events())
    if "Outlook" in selected_calendars:
        events.extend(_add_outlook_events())
    
    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay",
        },
        "initialView": "timeGridWeek",
        "slotMinTime": "06:00:00",
        "slotMaxTime": "21:00:00",
        "contentHeight": "auto",
        "height": "auto",
        "expandRows": True
    }
    
    # CSS to remove empty space after last time slot
    st.markdown("""
        <style>
        /* Force calendar to fit content without extra space */
        .fc .fc-scrollgrid {
            height: auto !important;
        }
        .fc .fc-scrollgrid-section-body > * {
            height: auto !important;
        }
        .fc-timegrid-body {
            max-height: 750px !important;
            overflow: hidden !important;
        }
        .fc-scroller {
            overflow-y: hidden !important;
            height: auto !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    calendar_state = calendar(events=events, options=calendar_options, key="main_calendar")
    
    if calendar_state.get("eventClick"):
        event_click = calendar_state["eventClick"]["event"]
        title = event_click.get("title", "").split(" (@")[0]
        start = event_click.get("start", "")
        end = event_click.get("end", "")
        location = event_click.get("extendedProps", {}).get("location", "")
        
        @st.dialog(f"Tapahtuma: {title}")
        def show_event():
            st.write(f"**Alkaa:** {start}")
            st.write(f"**Päättyy:** {end}")
            if location:
                st.write(f"**Sijainti:** {location}")
                if st.button("Suunnittele matka tähän", type="primary"):
                    st.session_state["route_destination"] = location
                    st.rerun()
        
        show_event()

st.markdown("---")
st.header("Suunnittele matka")

col1, col2 = st.columns(2)

with col1:
    origin = st.text_input(
        "Lähtöpaikka",
        value=st.session_state.get("route_origin", "Helsinki"),
        key="route_origin_input"
    )

with col2:
    destination = st.text_input(
        "Määränpää",
        value=st.session_state.get("route_destination", "Tampere"),
        key="route_destination_input"
    )

# Time selection mode
time_mode = st.radio(
    "Määritä matka",
    ["Lähtöajan mukaan", "Saapumisajan mukaan"],
    horizontal=True,
    key="time_mode"
)

# Initialize times
if "estimated_duration_hours" not in st.session_state:
    st.session_state["estimated_duration_hours"] = 0

# Create time options (15-minute intervals)
time_options = []
for hour in range(24):
    for minute in [0, 15, 30, 45]:
        time_options.append(f"{hour:02d}:{minute:02d}")

# Find current time closest to 15-minute interval
now = datetime.now()
current_rounded = now.replace(minute=(now.minute // 15) * 15, second=0, microsecond=0)
default_time_str = current_rounded.strftime("%H:%M")

if time_mode == "Lähtöajan mukaan":
    selected_time_str = st.selectbox(
        "Toivottu lähtöaika",
        time_options,
        index=time_options.index(default_time_str) if default_time_str in time_options else 0,
        key="departure_time_select"
    )
    # Convert string to time object
    hour, minute = map(int, selected_time_str.split(":"))
    departure_time = datetime.strptime(selected_time_str, "%H:%M").time()
    st.session_state["departure_time"] = departure_time
    
    # Calculate arrival time if we have route
    if st.session_state.get("estimated_duration_hours", 0) > 0:
        arrival_dt = datetime.combine(datetime.now().date(), departure_time) + timedelta(hours=st.session_state["estimated_duration_hours"])
        arrival_time = arrival_dt.time()
    else:
        arrival_time = departure_time
else:
    # Show arrival time input
    selected_time_str = st.selectbox(
        "Toivottu saapumisaika",
        time_options,
        index=time_options.index(default_time_str) if default_time_str in time_options else 0,
        key="arrival_time_select"
    )
    # Convert string to time object
    hour, minute = map(int, selected_time_str.split(":"))
    arrival_time = datetime.strptime(selected_time_str, "%H:%M").time()
    st.session_state["arrival_time"] = arrival_time
    
    # Calculate departure time if we have route
    if st.session_state.get("estimated_duration_hours", 0) > 0:
        departure_dt = datetime.combine(datetime.now().date(), arrival_time) - timedelta(hours=st.session_state["estimated_duration_hours"])
        departure_time = departure_dt.time()
    else:
        departure_time = arrival_time
    st.session_state["departure_time"] = departure_time

# Show suggestion box
if st.session_state.get("estimated_duration_hours", 0) > 0:
    if time_mode == "Lähtöajan mukaan":
        st.info(f"💡 Lähde klo {departure_time.strftime('%H:%M')} jos haluat olla perillä klo {arrival_time.strftime('%H:%M')}")
    else:
        st.info(f"💡 Lähde klo {departure_time.strftime('%H:%M')} jos haluat olla perillä klo {arrival_time.strftime('%H:%M')}")

if st.button("Hae reitti", type="primary", key="search_route"):
    logger.info("========== ROUTE SEARCH BUTTON CLICKED ==========")
    with st.spinner("Haetaan reittiä..."):
        # Get departure time from session state
        departure_time = st.session_state.get("departure_time", datetime.now().time())
        
        logger.info("Step 1: Geocoding origin and destination")
        origin_coords = fetch_here_geocode(origin)
        dest_coords = fetch_here_geocode(destination)
        
        logger.info(f"Step 2: Origin coords: {origin_coords}, Dest coords: {dest_coords}")
        
        if not origin_coords:
            st.error(f"Lähtöpaikkaa '{origin}' ei löytynyt")
        elif not dest_coords:
            st.error(f"Määränpäätä '{destination}' ei löytynyt")
        else:
            logger.info("Step 3: Both coords found, fetching route")
            departure_dt = datetime.combine(datetime.now().date(), departure_time)
            departure_iso = departure_dt.isoformat()
            
            routing_mode = st.session_state.get("routing_mode", "fast")
            avoid_options = st.session_state.get("avoid_options", [])
            alternatives = 2
            
            logger.info(f"Step 4: Calling HERE API with mode={routing_mode}, avoid={avoid_options}")
            route_data = fetch_here_route(
                origin_coords[0], origin_coords[1],
                dest_coords[0], dest_coords[1],
                departure_iso,
                routing_mode=routing_mode,
                avoid_features=avoid_options,
                alternatives=alternatives
            )
            
            logger.info(f"Step 5: Route data received: success={route_data.get('success') if route_data else None}")
            
            if route_data and route_data.get("success"):
                logger.info("Step 6: Route successful, processing...")
                st.session_state["all_routes"] = []
                st.session_state["route_summaries"] = []
                
                if "routes" in route_data and isinstance(route_data["routes"], list):
                    for route_item in route_data["routes"]:
                        st.session_state["all_routes"].append(route_item)
                        st.session_state["route_summaries"].append({
                            "distance_km": route_item.get("distance_km"),
                            "duration_hours": route_item.get("duration_hours"),
                            "polyline": route_item.get("polyline")
                        })
                else:
                    st.session_state["all_routes"].append(route_data)
                    st.session_state["route_summaries"].append({
                        "distance_km": route_data.get("distance_km"),
                        "duration_hours": route_data.get("duration_hours"),
                        "polyline": route_data.get("polyline")
                    })
                
                logger.info(f"Step 7: Stored {len(st.session_state['all_routes'])} routes")
                
                st.session_state["selected_route_index"] = 0
                st.session_state["current_route"] = st.session_state["all_routes"][0]
                st.session_state["route_origin_coords"] = origin_coords
                st.session_state["route_dest_coords"] = dest_coords
                st.session_state["departure_time"] = departure_time
                
                # Store estimated duration for time calculations
                first_route = st.session_state["all_routes"][0]
                st.session_state["estimated_duration_hours"] = first_route.get("duration_hours", 0)
                
                logger.info(f"Step 8: Checking if polyline exists: {bool(first_route.get('polyline'))}")
                
                if first_route.get("polyline"):
                    logger.info("Step 9: Polyline exists, decoding...")
                    route_coords_list = flexpolyline.decode(first_route["polyline"])
                    logger.info(f"Step 10: Decoded {len(route_coords_list)} coordinates")
                    
                    # Fetch weather forecast FIRST (most important, external API)
                    logger.info("Step 11: Starting weather forecast fetch...")
                    with st.spinner("Haetaan sääennustetta..."):
                        departure_dt = datetime.combine(datetime.now().date(), departure_time)
                        logger.info(f"Step 12: Fetching weather forecast for {len(route_coords_list)} route points, duration: {first_route.get('duration_hours', 0)}h")
                        
                        weather_data = fetch_route_weather_forecast(
                            route_coords_list,
                            departure_dt,
                            first_route.get("duration_hours", 0)
                        )
                        
                        logger.info(f"Step 13: Weather forecast fetched: {len(weather_data.get('hourly_forecasts', {}))} hours")
                        st.session_state["weather_forecast"] = weather_data
                        logger.info("Step 14: Weather forecast stored in session state")
                    
                    # Fetch Rainviewer
                    with st.spinner("Haetaan Rainviewer dataa..."):
                        host, ts_dict = get_rainviewer_data()
                        st.session_state["rainviewer_host"] = host
                        st.session_state["rainviewer_timestamps"] = sorted(list(ts_dict.keys())) if ts_dict else []
                        st.session_state["rainviewer_paths"] = ts_dict
                    
                    # Fetch Digitraffic layers (may fail, not critical)
                    with st.spinner("Haetaan liikenne- ja infratietoja..."):
                        try:
                            st.session_state["cameras"] = fetch_digitraffic_cameras(route_coords_list)
                            time.sleep(0.3)  # Small delay to prevent API overload
                        except Exception as e:
                            logger.error(f"Camera fetch failed: {e}")
                            st.session_state["cameras"] = []
                        
                        try:
                            st.session_state["road_weather"] = fetch_digitraffic_road_weather(route_coords_list)
                            time.sleep(0.3)
                        except Exception as e:
                            logger.error(f"Road weather fetch failed: {e}")
                            st.session_state["road_weather"] = []
                        
                        try:
                            st.session_state["vms"] = fetch_digitraffic_vms(route_coords_list)
                            time.sleep(0.3)
                        except Exception as e:
                            logger.error(f"VMS fetch failed: {e}")
                            st.session_state["vms"] = []
                        
                        try:
                            st.session_state["maintenance"] = fetch_digitraffic_maintenance(route_coords_list)
                            time.sleep(0.3)
                        except Exception as e:
                            logger.error(f"Maintenance fetch failed: {e}")
                            st.session_state["maintenance"] = []
                        
                        try:
                            st.session_state["lam"] = fetch_digitraffic_lam(route_coords_list)
                            time.sleep(0.3)
                        except Exception as e:
                            logger.error(f"LAM fetch failed: {e}")
                            st.session_state["lam"] = []
                        
                        try:
                            st.session_state["messages"] = fetch_digitraffic_messages(route_coords_list)
                            logger.info(f"✓ Tiedotteet haettu: {len(st.session_state['messages'])} kpl")
                        except Exception as e:
                            logger.error(f"Messages fetch failed: {e}")
                            st.session_state["messages"] = []
                
                # Log all digitraffic data counts
                logger.info("========== DIGITRAFFIC DATA SUMMARY ==========")
                logger.info(f"Kelikamerat: {len(st.session_state.get('cameras', []))} kpl")
                logger.info(f"Tiesää-asemat: {len(st.session_state.get('road_weather', []))} kpl")
                logger.info(f"Opasteet (VMS): {len(st.session_state.get('vms', []))} kpl")
                logger.info(f"Kunnossapito: {len(st.session_state.get('maintenance', []))} kpl")
                logger.info(f"LAM-pisteet: {len(st.session_state.get('lam', []))} kpl")
                logger.info(f"Tiedotteet: {len(st.session_state.get('messages', []))} kpl")
                logger.info(f"Häiriöt (HERE): {len(first_route.get('incidents', []))} kpl")
                logger.info("=============================================")
                
                num_routes = len(st.session_state["all_routes"])
                st.success(f"Reitti laskettu: {first_route.get('distance_km', 0):.1f} km, {first_route.get('duration_hours', 0):.1f}h ({num_routes} vaihtoehtoa)")
                st.rerun()
            else:
                error_msg = route_data.get("error", "Tuntematon virhe") if route_data else "Ei yhteyttä"
                st.error(f"Reitin haku epäonnistui: {error_msg}")

if "current_route" in st.session_state and "all_routes" in st.session_state:
    route = st.session_state["current_route"]
    
    st.markdown("---")
    
    if len(st.session_state["all_routes"]) > 1:
        st.subheader("Valitse reitti")
        route_options = []
        for i, summary in enumerate(st.session_state["route_summaries"]):
            dist = summary.get("distance_km", 0)
            dur = summary.get("duration_hours", 0)
            route_options.append(f"Reitti {i+1}: {dist:.1f} km, {int(dur)}h {int((dur%1)*60)}min")
        
        selected_index = st.session_state.get("selected_route_index", 0)
        selected_option = st.radio(
            "Vaihtoehdot",
            route_options,
            index=selected_index,
            horizontal=True,
            label_visibility="collapsed"
        )
        
        new_index = route_options.index(selected_option)
        if new_index != selected_index:
            st.session_state["selected_route_index"] = new_index
            st.session_state["current_route"] = st.session_state["all_routes"][new_index]
            
            # Update estimated duration
            st.session_state["estimated_duration_hours"] = st.session_state["all_routes"][new_index].get("duration_hours", 0)
            
            selected_route = st.session_state["all_routes"][new_index]
            if selected_route.get("polyline"):
                route_coords_list = flexpolyline.decode(selected_route["polyline"])
                
                # Fetch weather forecast for new route
                with st.spinner("Päivitetään sääennustetta..."):
                    departure_dt = datetime.combine(datetime.now().date(), st.session_state.get("departure_time", datetime.now().time()))
                    weather_data = fetch_route_weather_forecast(
                        route_coords_list,
                        departure_dt,
                        selected_route.get("duration_hours", 0)
                    )
                    st.session_state["weather_forecast"] = weather_data
                
                # Update Digitraffic layers (may fail)
                with st.spinner("Päivitetään liikenne- ja infratietoja..."):
                    try:
                        st.session_state["cameras"] = fetch_digitraffic_cameras(route_coords_list)
                        time.sleep(0.3)
                    except Exception as e:
                        logger.error(f"Camera fetch failed: {e}")
                        st.session_state["cameras"] = []
                    
                    try:
                        st.session_state["road_weather"] = fetch_digitraffic_road_weather(route_coords_list)
                        time.sleep(0.3)
                    except Exception as e:
                        logger.error(f"Road weather fetch failed: {e}")
                        st.session_state["road_weather"] = []
                    
                    try:
                        st.session_state["vms"] = fetch_digitraffic_vms(route_coords_list)
                        time.sleep(0.3)
                    except Exception as e:
                        logger.error(f"VMS fetch failed: {e}")
                        st.session_state["vms"] = []
                    
                    try:
                        st.session_state["maintenance"] = fetch_digitraffic_maintenance(route_coords_list)
                        time.sleep(0.3)
                    except Exception as e:
                        logger.error(f"Maintenance fetch failed: {e}")
                        st.session_state["maintenance"] = []
                    
                    try:
                        st.session_state["lam"] = fetch_digitraffic_lam(route_coords_list)
                        time.sleep(0.3)
                    except Exception as e:
                        logger.error(f"LAM fetch failed: {e}")
                        st.session_state["lam"] = []
                    
                    try:
                        st.session_state["messages"] = fetch_digitraffic_messages(route_coords_list)
                    except Exception as e:
                        logger.error(f"Messages fetch failed: {e}")
                        st.session_state["messages"] = []
            
            st.rerun()
        
        route = st.session_state["current_route"]
    
    st.subheader("Reittisi")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Matka", f"{route['distance_km']:.1f} km")
    with col2:
        st.metric("Aika", f"{int(route['duration_hours'])}h {int((route['duration_hours']%1)*60)}min")
    with col3:
        dep_time = st.session_state.get("departure_time", datetime.now().time())
        arrival = datetime.combine(datetime.now().date(), dep_time) + timedelta(hours=route['duration_hours'])
        st.metric("Perillä", arrival.strftime("%H:%M"))
    
    st.markdown("### Reittikartta")
    
    # Calculate selected hour early for layer visibility logic
    car_time_minutes = st.session_state.get("car_time_minutes", 0)
    selected_hour = min(int(car_time_minutes / 60), 6)
    
    with st.expander("Karttatasot & Näkymä", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Data**")
            layer_settings["show_route"] = st.checkbox("Reittiviiva", value=layer_settings.get("show_route", True), key="layer_route")
            layer_settings["show_weather_forecast"] = st.checkbox("Sade-ennuste", value=layer_settings.get("show_weather_forecast", False), key="layer_forecast")
            layer_settings["show_rainviewer"] = st.checkbox("Sade (Rainviewer)", value=layer_settings.get("show_rainviewer", True), key="layer_rain")
            
            if layer_settings.get("show_rainviewer") and selected_hour >= 1:
                st.caption("ℹ️ Rainviewer piilotettu (näkyy vain 1. tunnilla)")
            
            weather_opacity = 0.6
            if layer_settings.get("show_rainviewer"):
                weather_opacity = st.slider("Rainviewer läpinäkyvyys", 0.0, 1.0, 0.6, step=0.1, key="rainviewer_opacity")
            
            layer_settings["show_temperature"] = st.checkbox("Lämpötila", value=layer_settings.get("show_temperature", False), key="layer_temp")
        
        with col2:
            st.markdown("**Infra**")
            layer_settings["show_cameras"] = st.checkbox("Kelikamerat", value=layer_settings.get("show_cameras", True), key="layer_cameras")
            layer_settings["show_road_weather"] = st.checkbox("Tiesää", value=layer_settings.get("show_road_weather", True), key="layer_roadweather")
            layer_settings["show_vms"] = st.checkbox("Opasteet", value=layer_settings.get("show_vms", False), key="layer_vms")
            layer_settings["show_maintenance"] = st.checkbox("Kunnossapito", value=layer_settings.get("show_maintenance", False), key="layer_maintenance")
        
        with col3:
            st.markdown("**Muut**")
            layer_settings["show_incidents"] = st.checkbox("Häiriöt", value=layer_settings.get("show_incidents", True), key="layer_incidents")
            layer_settings["show_lam"] = st.checkbox("LAM-pisteet", value=layer_settings.get("show_lam", False), key="layer_lam")
            layer_settings["show_car"] = st.checkbox("Auto", value=layer_settings.get("show_car", True), key="layer_car")
    
    # Häiriöt, Tiedotteet ja Kunnossapito info-laatikot karttatasojen alla
    incidents_data = route.get("incidents", [])
    logger.info(f"Rendering incidents expander: {len(incidents_data)} incidents")
    if incidents_data:
        with st.expander(f"⚠️ Häiriöt reitillä ({len(incidents_data)} kpl)", expanded=False):
            for inc in incidents_data:
                incident_type = inc.get('tyyppi') or inc.get('type', 'Häiriö')
                incident_level = inc.get('taso') or inc.get('criticality', '')
                incident_desc = inc.get('kuvaus') or inc.get('description', 'Ei kuvausta')
                incident_loc = inc.get('paikka') or inc.get('location', '')
                
                st.markdown(f"**{incident_type}** {f'- {incident_level}' if incident_level else ''}")
                st.write(incident_desc)
                if incident_loc:
                    st.caption(f"📍 {incident_loc}")
                st.divider()
    
    messages_data = st.session_state.get("messages", [])
    logger.info(f"Rendering messages expander: {len(messages_data)} messages")
    if messages_data:
        logger.info(f"First message data: {messages_data[0]}")
        with st.expander(f"📢 Tiedotteet reitillä ({len(messages_data)} kpl)", expanded=False):
            for msg in messages_data[:10]:  # Show max 10 messages
                message_text = msg.get('text') or msg.get('message', 'Ei viestiä')
                message_type = msg.get('type', 'Tiedote')
                
                st.markdown(f"**{message_type}**")
                st.write(message_text)
                if msg.get('location'):
                    st.caption(f"📍 {msg['location']}")
                if msg.get('valid_until'):
                    st.caption(f"⏰ Voimassa: {msg['valid_until']}")
                st.divider()
    
    maintenance_data = st.session_state.get("maintenance", [])
    logger.info(f"Rendering maintenance expander: {len(maintenance_data)} tasks")
    if maintenance_data:
        logger.info(f"First maintenance data: {maintenance_data[0]}")
        with st.expander(f"🚧 Kunnossapito reitillä ({len(maintenance_data)} tehtävää)", expanded=False):
            for task in maintenance_data[:10]:  # Show max 10 tasks
                task_type = task.get('type', 'Kunnossapito')
                st.markdown(f"**{task_type}**")
                if task.get('time'):
                    st.caption(f"🕐 {task['time']}")
                if task.get('location'):
                    st.caption(f"📍 {task['location']}")
                st.divider()
    
    if layer_settings.get("show_temperature", False):
        st.markdown("**Lämpötila-asteikko:**")
        temp_scale = {
            "-30°C": [0, 0, 139],
            "-20°C": [0, 0, 255],
            "-10°C": [100, 150, 255],
            "0°C": [200, 200, 100],
            "10°C": [255, 165, 0],
            "20°C": [255, 100, 50],
            "30°C": [200, 0, 0]
        }
        cols = st.columns(len(temp_scale))
        for i, (temp, color) in enumerate(temp_scale.items()):
            with cols[i]:
                st.markdown(
                    f"<div style='background-color: rgb({color[0]}, {color[1]}, {color[2]}); "
                    f"height: 20px; text-align: center; color: white; "
                    f"line-height: 20px; font-size: 10px; border: 1px solid #333;'>{temp}</div>",
                    unsafe_allow_html=True
                )
    
    if layer_settings.get("show_weather_forecast", False):
        st.markdown("**Vesisade:**")
        rain_scale = {
            "Ei sadetta": [240, 240, 240],
            "Kevyt": [150, 200, 255],
            "Kohtalainen": [100, 150, 255],
            "Voimakas": [50, 100, 255],
            "Erittäin voimakas": [0, 50, 200]
        }
        cols = st.columns(len(rain_scale))
        for i, (desc, color) in enumerate(rain_scale.items()):
            with cols[i]:
                st.markdown(
                    f"<div style='background-color: rgb({color[0]}, {color[1]}, {color[2]}); "
                    f"height: 20px; text-align: center; color: {'black' if i < 2 else 'white'}; "
                    f"line-height: 20px; font-size: 10px; border: 1px solid #333;'>{desc}</div>",
                    unsafe_allow_html=True
                )
        
        st.markdown("**Lumisade:**")
        snow_scale = {
            "Ei sadetta": [240, 240, 240],
            "Kevyt": [200, 220, 255],
            "Kohtalainen": [150, 180, 230],
            "Voimakas": [100, 130, 200],
            "Erittäin voimakas": [50, 80, 150]
        }
        cols = st.columns(len(snow_scale))
        for i, (desc, color) in enumerate(snow_scale.items()):
            with cols[i]:
                st.markdown(
                    f"<div style='background-color: rgb({color[0]}, {color[1]}, {color[2]}); "
                    f"height: 20px; text-align: center; color: {'black' if i < 3 else 'white'}; "
                    f"line-height: 20px; font-size: 10px; border: 1px solid #333;'>{desc}</div>",
                    unsafe_allow_html=True
                )
    
    weather_ts = None
    weather_path = None
    weather_host = st.session_state.get("rainviewer_host")
    
    if st.session_state.get("rainviewer_timestamps"):
        current_ts = int(datetime.now().timestamp())
        weather_ts = get_closest_timestamp(current_ts, st.session_state["rainviewer_timestamps"])
        if weather_ts and st.session_state.get("rainviewer_paths"):
            weather_path = st.session_state["rainviewer_paths"].get(weather_ts)
    
    
    map_placeholder = st.empty()
    
    st.markdown("---")
    
    # Weather forecast expander
    if "weather_forecast" in st.session_state and st.session_state["weather_forecast"].get("hourly_forecasts"):
        with st.expander("🌤️ Tässä säätietoja valitsemaltasi matkareitiltä", expanded=False):
            forecast = st.session_state["weather_forecast"]
            
            # Lähtöpaikka ja määränpää sää
            col1, col2, col3 = st.columns(3)
            
            if forecast.get("departure_weather"):
                dep_wx = forecast["departure_weather"]
                with col1:
                    st.markdown("**Lähtöpaikka**")
                    st.write(f"🌡️ {dep_wx.get('temperature', 'N/A')}°C")
                    st.write(dep_wx.get('weather_desc', 'Ei tietoa'))
            
            if forecast.get("midpoint_weather"):
                mid_wx = forecast["midpoint_weather"]
                with col2:
                    st.markdown("**Matkan puolivälissä**")
                    offset = mid_wx.get('time_offset_hours', 0)
                    st.write(f"🌡️ {mid_wx.get('temperature', 'N/A')}°C")
                    st.write(mid_wx.get('weather_desc', 'Ei tietoa'))
            
            if forecast.get("arrival_weather"):
                arr_wx = forecast["arrival_weather"]
                with col3:
                    st.markdown("**Määränpää**")
                    st.write(f"🌡️ {arr_wx.get('temperature', 'N/A')}°C")
                    st.write(arr_wx.get('weather_desc', 'Ei tietoa'))
            
            st.divider()
            st.markdown("**Tuntikohtainen ennuste**")
            
            hourly_forecasts = forecast.get("hourly_forecasts", {})
            route_duration = route.get("duration_hours", 0)
            
            if hourly_forecasts:
                # Create 5 boxes for hours: Now, +1h, +2h, +3h, +4h
                max_hours = min(5, int(route_duration) + 1)
                
                cols = st.columns(5)
                road_weather_stations = st.session_state.get("road_weather", [])
                
                for hour in range(5):
                    with cols[hour]:
                        if hour >= max_hours:
                            st.markdown("**-**")
                            st.write("Matka päättyy")
                            continue
                        
                        # Get forecast for this hour
                        hour_forecast = hourly_forecasts.get(hour, [])
                        # Get first route point (not grid point)
                        route_points = [p for p in hour_forecast if p.get("is_route_point", False)]
                        
                        if not route_points:
                            st.markdown(f"**+{hour}h**")
                            st.write("Ei dataa")
                            continue
                        
                        point = route_points[0]  # Use first route point for this hour
                        
                        temp = point.get('temperature', 'N/A')
                        precip = point.get('precipitation', 0)
                        is_snow = point.get('is_snow', False)
                        weather_desc = point.get('weather_desc', 'Ei tietoa')
                        
                        # Time label
                        if hour == 0:
                            time_label = "Nyt"
                        else:
                            time_label = f"+{hour}h"
                        
                        # Find nearest road weather station
                        road_temp = None
                        if road_weather_stations:
                            point_lat = point.get('lat')
                            point_lon = point.get('lon')
                            
                            min_dist = float('inf')
                            nearest_station = None
                            for station in road_weather_stations:
                                st_lat = station.get('lat')
                                st_lon = station.get('lon')
                                if st_lat and st_lon:
                                    lat_diff = (st_lat - point_lat) * 111
                                    lon_diff = (st_lon - point_lon) * 111 * math.cos(math.radians(point_lat))
                                    dist = math.sqrt(lat_diff**2 + lon_diff**2)
                                    if dist < min_dist:
                                        min_dist = dist
                                        nearest_station = station
                            
                            if nearest_station and min_dist < 50:
                                road_temp = nearest_station.get('road_temp')
                        
                        st.markdown(f"**{time_label}**")
                        st.write(f"🌡️ {temp}°C")
                        st.write(weather_desc)
                        
                        if road_temp is not None:
                            st.write(f"🛣️ Tie: {road_temp}°C")
    
    st.markdown("**Simuloi matkan etenemistä**")
    
    col_time_select, col_info = st.columns([2, 3])
    
    total_duration_hours = route.get("duration_hours", 0)
    total_minutes = int(total_duration_hours * 60)
    if total_minutes < 1:
        total_minutes = 1
    
    if "car_time_minutes" not in st.session_state:
        st.session_state["car_time_minutes"] = 0
    
    with col_time_select:
        # Create time options: 0min, 15min, 30min, 45min, 1h, 1h15min, etc.
        time_options = []
        time_values = []
        
        for minutes in range(0, total_minutes + 1, 15):  # 15 minute intervals
            hours = minutes // 60
            mins = minutes % 60
            if hours == 0:
                label = f"{mins}min"
            elif mins == 0:
                label = f"{hours}h"
            else:
                label = f"{hours}h {mins}min"
            time_options.append(label)
            time_values.append(minutes)
        
        # Find current index
        current_minutes = st.session_state.get("car_time_minutes", 0)
        try:
            current_index = time_values.index(current_minutes)
        except ValueError:
            # Find closest
            current_index = min(range(len(time_values)), key=lambda i: abs(time_values[i] - current_minutes))
        
        selected_option = st.selectbox(
            "Valitse aika matkalta",
            time_options,
            index=current_index,
            key="time_selector"
        )
        
        # Update car time
        selected_index = time_options.index(selected_option)
        st.session_state["car_time_minutes"] = time_values[selected_index]
    
    with col_info:
        # Show current time and weather at car position
        time_minutes = st.session_state["car_time_minutes"]
        dep_time = st.session_state.get("departure_time", datetime.now().time())
        current_time = datetime.combine(datetime.now().date(), dep_time) + timedelta(minutes=time_minutes)
        selected_hour_display = min(int(time_minutes / 60), 6)
        
        st.write(f"⏰ Kello: **{current_time.strftime('%H:%M')}**")
        st.write(f"📍 Matka-aika: **{time_minutes}/{total_minutes} min**")
        st.write(f"🌤️ Sää kartalla: **+{selected_hour_display}h**")
    
    # Calculate car position based on selected time
    if route.get("polyline"):
        try:
            route_coords = flexpolyline.decode(route["polyline"])
            
            if len(route_coords) > 0:
                progress = time_minutes / total_minutes
                car_index = int(progress * (len(route_coords) - 1))
                car_index = min(car_index, len(route_coords) - 1)
                
                st.session_state["car_position"] = route_coords[car_index]
                selected_hour_car = min(int(time_minutes / 60), 6)
        except Exception as e:
            logger.error(f"Virhe auton sijainnin laskennassa: {e}")
            selected_hour_car = 0
    else:
        selected_hour_car = 0
    
    # Render map ONCE with all data including car position
    final_deck = create_route_map(
        route_polyline=route.get("polyline", ""),
        origin_coords=st.session_state.get("route_origin_coords"),
        dest_coords=st.session_state.get("route_dest_coords"),
        cameras=st.session_state.get("cameras", []),
        road_weather=st.session_state.get("road_weather", []),
        vms=st.session_state.get("vms", []),
        maintenance=st.session_state.get("maintenance", []),
        lam=st.session_state.get("lam", []),
        incidents=route.get("incidents", []),
        messages=st.session_state.get("messages", []),
        layer_settings=layer_settings,
        car_position=st.session_state.get("car_position"),
        all_routes=[s.get("polyline") for s in st.session_state.get("route_summaries", []) if s.get("polyline")],
        selected_route_index=st.session_state.get("selected_route_index", 0),
        map_style=map_style,
        weather_ts=weather_ts,
        weather_path=weather_path,
        weather_host=weather_host,
        weather_opacity=weather_opacity,
        selected_hour=selected_hour_car
    )
    
    selection = map_placeholder.pydeck_chart(final_deck, use_container_width=True, height=500, on_select="rerun", selection_mode="single-object")
    
    if selection.selection and "objects" in selection.selection:
        objs = selection.selection["objects"]
        logger.info(f"Map selection detected: {list(objs.keys())}")
        
        if objs.get("ScatterplotLayer") and len(objs["ScatterplotLayer"]) > 0:
            clicked = objs["ScatterplotLayer"][0]
            logger.info(f"Clicked object keys: {list(clicked.keys())}")
            
            # Check if clicked object is a camera (has imageUrl)
            if "imageUrl" in clicked:
                logger.info(f"Camera clicked: {clicked.get('name')}")
                st.session_state["selected_camera"] = clicked
                st.rerun()
            else:
                logger.info("Clicked object is not a camera (no imageUrl)")

                