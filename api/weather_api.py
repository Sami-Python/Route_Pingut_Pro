"""Weather API for route-based weather forecasts.

This module provides simple weather data endpoints for cities and routes.
Designed to be called by Streamlit frontend and HERE Maps integration.
Returns simplified weather data (temperature, precipitation, description).
"""

from fastapi import FastAPI, Query, HTTPException
from typing import Dict, List, Optional, Tuple
import requests
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Weather API", version="1.0.0")

# Determine backend URL dynamically
import socket
import os

try:
    socket.gethostbyname("meteo-backend")
    default_backend = "http://meteo-backend:8081"
except socket.gaierror:
    default_backend = "http://localhost:8081"

OPEN_METEO_BACKEND = os.getenv("OPEN_METEO_BACKEND", default_backend)

CITIES = {
    "Helsinki": (60.1699, 24.9384),
    "Tampere": (61.4978, 23.7610),
    "Turku": (60.4518, 22.2666),
    "Oulu": (65.0121, 25.4651),
    "Rovaniemi": (66.5039, 25.7294),
    "Jyväskylä": (62.2426, 25.7473),
    "Kuopio": (62.8924, 27.6782),
    "Lahti": (60.9827, 25.6612),
    "Vaasa": (63.0959, 21.6164),
    "Joensuu": (62.6010, 29.7636)
}


def _get_weather_description(temperature: float, precipitation: float) -> str:
    """Determine weather description based on temperature and precipitation.
    
    Parameters
    ----------
    temperature : float
        Temperature in Celsius.
    precipitation : float
        Precipitation in mm/h.
    
    Returns
    -------
    str
        Finnish weather description.
    """
    if precipitation > 0.5:
        if temperature < 0:
            return "lumisadetta"
        elif temperature < 2:
            return "räntää"
        else:
            return "sadetta"
    elif precipitation > 0.1:
        return "tihkusadetta"
    elif temperature > 15:
        return "aurinkoinen"
    elif temperature > 5:
        return "pilvistä"
    else:
        return "selkeää"


def _fetch_point_weather(lat: float, lon: float, hours: int = 6, start_time: Optional[str] = None) -> Optional[Dict]:
    """Fetch weather data for a specific point from Open-Meteo backend.
    
    Parameters
    ----------
    lat : float
        Latitude coordinate.
    lon : float
        Longitude coordinate.
    hours : int
        Number of forecast hours.
    start_time : Optional[str]
        Start time in ISO format (e.g. 2023-10-27T10:00:00).
        If None, uses current UTC time.
    
    Returns
    -------
    Optional[Dict]
        Weather data or None if failed.
    """
    try:
        # Use provided start_time or fallback to current UTC time
        query_start_time = start_time if start_time else datetime.utcnow().isoformat()
        
        response = requests.get(
            f"{OPEN_METEO_BACKEND}/api/forecast/point",
            params={
                "lat": lat,
                "lon": lon,
                "start_time": query_start_time,
                "hours": hours
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch weather for ({lat}, {lon}): {e}")
        return None


def _simplify_forecast(raw_data: Dict) -> List[Dict]:
    """Convert raw Open-Meteo data to simplified forecast format.
    
    Parameters
    ----------
    raw_data : Dict
        Raw response from Open-Meteo backend.
    
    Returns
    -------
    List[Dict]
        Simplified forecast with time, temperature, precipitation, weather.
    """
    forecast = []
    
    # Extract forecast array from nested structure
    forecast_data = raw_data.get("forecast", {})
    if isinstance(forecast_data, dict):
        forecast_data = forecast_data.get("forecast", [])
    
    for point in forecast_data:
        temp = point.get("temperature", 0)
        precip = point.get("precipitation", 0)
        time_str = point.get("time", "")
        
        # Parse time to show only hour
        try:
            # Remove timezone indicator if present
            time_str_clean = time_str.replace('Z', '')
            dt = datetime.fromisoformat(time_str_clean)
            time_display = dt.strftime("%H:%M")
        except Exception:
            time_display = time_str
        
        forecast.append({
            "time": time_display,
            "temperature": round(temp),
            "precipitation": round(precip, 1),
            "wind_speed": round(point.get("windspeed_10m", 0), 1),
            "weather": _get_weather_description(temp, precip)
        })
    
    return forecast


@app.get("/")
async def root():
    """Root endpoint.
    
    Returns
    -------
    dict
        API information and available endpoints.
    """
    return {
        "service": "Weather API",
        "version": "1.0.0",
        "description": "Simple weather forecast API for city and route-based queries",
        "endpoints": {
            "coordinate_based": {
                "/point": "GET /point?lat=60.17&lon=24.94&hours=6 - Weather for any coordinate",
                "/route-coords": "GET /route-coords?from_lat=60.17&from_lon=24.94&to_lat=61.50&to_lon=23.76&hours=6 - Route weather by coordinates"
            },
            "city_based": {
                "/city": "GET /city?name=Helsinki&hours=6 - Weather for predefined city",
                "/route": "GET /route?from=Helsinki&to=Tampere&hours=6 - Route weather by city names",
                "/cities": "GET /cities - List available cities"
            }
        },
        "integration_notes": {
            "for_here_maps": "Use /point or /route-coords with latitude/longitude",
            "for_testing": "Use /city or /route with city names from /cities list",
            "backend": "Connects to Open-Meteo microservice at backend:8081"
        }
    }


@app.get("/city")
async def get_city_weather(
    name: str = Query(..., description="City name (e.g., Helsinki, Tampere)"),
    hours: int = Query(6, ge=1, le=6, description="Forecast hours (1-6)")
):
    """Get weather forecast for a specific city.
    
    Parameters
    ----------
    name : str
        City name (must be in CITIES dictionary).
    hours : int
        Number of forecast hours (1-6).
    
    Returns
    -------
    dict
        Weather forecast with current conditions and hourly data.
    
    Raises
    ------
    HTTPException
        If city not found or backend fails.
    """
    city_name = name.capitalize()
    
    if city_name not in CITIES:
        raise HTTPException(
            status_code=404,
            detail=f"City '{name}' not found. Available: {', '.join(CITIES.keys())}"
        )
    
    lat, lon = CITIES[city_name]
    
    raw_data = _fetch_point_weather(lat, lon, hours)
    if not raw_data:
        raise HTTPException(
            status_code=503,
            detail="Failed to fetch weather data from backend"
        )
    
    forecast = _simplify_forecast(raw_data)
    
    # Current conditions = first forecast point
    current = forecast[0] if forecast else {
        "temperature": 0,
        "precipitation": 0,
        "weather": "ei tietoa"
    }
    
    return {
        "city": city_name,
        "coordinates": {"lat": lat, "lon": lon},
        "current_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "current": current,
        "forecast": forecast
    }


@app.get("/route")
async def get_route_weather(
    from_city: str = Query(..., alias="from", description="Departure city"),
    to_city: str = Query(..., alias="to", description="Arrival city"),
    hours: int = Query(6, ge=1, le=6, description="Forecast hours (1-6)")
):
    """Get weather forecast for route departure and arrival cities.
    
    Parameters
    ----------
    from_city : str
        Departure city name.
    to_city : str
        Arrival city name.
    hours : int
        Number of forecast hours (1-6).
    
    Returns
    -------
    dict
        Weather data for both departure and arrival cities.
    
    Raises
    ------
    HTTPException
        If either city not found or backend fails.
    """
    from_name = from_city.capitalize()
    to_name = to_city.capitalize()
    
    # Validate both cities
    missing_cities = []
    if from_name not in CITIES:
        missing_cities.append(from_name)
    if to_name not in CITIES:
        missing_cities.append(to_name)
    
    if missing_cities:
        raise HTTPException(
            status_code=404,
            detail=f"Cities not found: {', '.join(missing_cities)}. Available: {', '.join(CITIES.keys())}"
        )
    
    # Fetch weather for both cities
    from_lat, from_lon = CITIES[from_name]
    to_lat, to_lon = CITIES[to_name]
    
    from_data = _fetch_point_weather(from_lat, from_lon, hours)
    to_data = _fetch_point_weather(to_lat, to_lon, hours)
    
    if not from_data or not to_data:
        raise HTTPException(
            status_code=503,
            detail="Failed to fetch weather data from backend"
        )
    
    from_forecast = _simplify_forecast(from_data)
    to_forecast = _simplify_forecast(to_data)
    
    # Current conditions for both
    from_current = from_forecast[0] if from_forecast else {"temperature": 0, "precipitation": 0, "weather": "ei tietoa"}
    to_current = to_forecast[0] if to_forecast else {"temperature": 0, "precipitation": 0, "weather": "ei tietoa"}
    
    return {
        "route": {
            "from": from_name,
            "to": to_name
        },
        "departure": {
            "city": from_name,
            "coordinates": {"lat": from_lat, "lon": from_lon},
            "current": from_current,
            "forecast": from_forecast
        },
        "arrival": {
            "city": to_name,
            "coordinates": {"lat": to_lat, "lon": to_lon},
            "current": to_current,
            "forecast": to_forecast
        },
        "current_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    }


@app.get("/point")
async def get_point_weather(
    lat: float = Query(..., ge=-90, le=90, description="Latitude (-90 to 90)"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude (-180 to 180)"),
    hours: int = Query(6, ge=1, le=6, description="Forecast hours (1-6)")
):
    """Get weather forecast for any coordinate point.
    
    This endpoint is designed for integration with HERE Maps or other
    external services that provide coordinates rather than city names.
    
    Parameters
    ----------
    lat : float
        Latitude coordinate.
    lon : float
        Longitude coordinate.
    hours : int
        Number of forecast hours (1-6).
    
    Returns
    -------
    dict
        Weather forecast for the specified point.
    
    Raises
    ------
    HTTPException
        If backend fails to fetch data.
    """
    raw_data = _fetch_point_weather(lat, lon, hours)
    if not raw_data:
        raise HTTPException(
            status_code=503,
            detail="Failed to fetch weather data from backend"
        )
    
    forecast = _simplify_forecast(raw_data)
    
    current = forecast[0] if forecast else {
        "temperature": 0,
        "precipitation": 0,
        "weather": "ei tietoa"
    }
    
    return {
        "coordinates": {"lat": lat, "lon": lon},
        "current_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "current": current,
        "forecast": forecast
    }


@app.get("/route-coords")
async def get_route_weather_coords(
    from_lat: float = Query(..., ge=-90, le=90, description="Departure latitude"),
    from_lon: float = Query(..., ge=-180, le=180, description="Departure longitude"),
    to_lat: float = Query(..., ge=-90, le=90, description="Arrival latitude"),
    to_lon: float = Query(..., ge=-180, le=180, description="Arrival longitude"),
    hours: int = Query(6, ge=1, le=6, description="Forecast hours (1-6)"),
    start_time: Optional[str] = Query(None, description="Departure time in ISO format (e.g. 2023-10-27T10:00:00). If missing, uses 'now'.")
):
    """Get weather forecast for route using coordinates.
    
    This endpoint is designed for integration with HERE Maps or other
    routing services. It accepts departure and arrival coordinates directly
    without requiring city names.
    
    Use case: HERE Maps provides route → pass start/end coordinates here.
    
    Parameters
    ----------
    from_lat : float
        Departure latitude.
    from_lon : float
        Departure longitude.
    to_lat : float
        Arrival latitude.
    to_lon : float
        Arrival longitude.
    hours : int
        Number of forecast hours (1-6).
    start_time : str, optional
        Departure time in ISO format.
    
    Returns
    -------
    dict
        Weather data for both departure and arrival points.
    
    Raises
    ------
    HTTPException
        If backend fails to fetch data.
    """
    # Fetch weather for both points
    # For departure: use start_time directly
    from_data = _fetch_point_weather(from_lat, from_lon, hours, start_time)
    
    # For arrival: ideally we'd add travel_duration to start_time, 
    # but for now we fetch the same time window and let frontend pick the right slot,
    # OR we could just pass the same start_time if the API returns enough hourly context.
    # Since we set hours=6, we have a 6h window from start_time.
    # If the trip is longer than 6 hours, we might miss the arrival weather with this simple logic.
    # But for this iteration, let's stick to fetching the window starting at start_time.
    to_data = _fetch_point_weather(to_lat, to_lon, hours, start_time)
    
    if not from_data or not to_data:
        raise HTTPException(
            status_code=503,
            detail="Failed to fetch weather data from backend"
        )
    
    from_forecast = _simplify_forecast(from_data)
    to_forecast = _simplify_forecast(to_data)
    
    from_current = from_forecast[0] if from_forecast else {"temperature": 0, "precipitation": 0, "weather": "ei tietoa"}
    to_current = to_forecast[0] if to_forecast else {"temperature": 0, "precipitation": 0, "weather": "ei tietoa"}
    
    return {
        "route": {
            "from": {"lat": from_lat, "lon": from_lon},
            "to": {"lat": to_lat, "lon": to_lon}
        },
        "departure": {
            "coordinates": {"lat": from_lat, "lon": from_lon},
            "current": from_current,
            "forecast": from_forecast
        },
        "arrival": {
            "coordinates": {"lat": to_lat, "lon": to_lon},
            "current": to_current,
            "forecast": to_forecast
        },
        "current_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    }


@app.get("/cities")
async def list_cities():
    """List all available cities for demo/testing purposes.
    
    Note: This endpoint is for convenience only. External integrations
    should use /point or /route-coords with coordinates directly.
    
    Returns
    -------
    dict
    
        Dictionary of city names and their coordinates.
    """
    return {
        "cities": [
            {
                "name": city,
                "coordinates": {"lat": coords[0], "lon": coords[1]}
            }
            for city, coords in CITIES.items()
        ]
    }


@app.get("/radar/config")
async def get_radar_config():
    """Get RainViewer radar configuration (timestamps).
    
    Returns
    -------
    dict
        Latest radar timestamps and configuration.
    """
    try:
        # Fetch configuration from RainViewer
        response = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch radar config: {e}")
        raise HTTPException(
            status_code=503, 
            detail="Failed to fetch radar configuration"
        )


from pydantic import BaseModel

class WeatherPointRequest(BaseModel):
    lat: float
    lon: float
    time: str  # ISO format

@app.post("/batch")
async def get_batch_weather(points: List[WeatherPointRequest]):
    """Get weather forecast for a batch of points at specific times.
    
    Parameters
    ----------
    points : List[WeatherPointRequest]
        List of objects containing lat, lon, and time.
    
    Returns
    -------
    List[dict]
        List of weather data for each point.
    """
    results = []
    
    for point in points:
        try:
            # We want the weather AT that specific time.
            # _fetch_point_weather fetches a window starting at start_time.
            # We will fetch 1 hour of data at that specific time.
            raw_data = _fetch_point_weather(point.lat, point.lon, hours=1, start_time=point.time)
            
            if raw_data:
                forecast = _simplify_forecast(raw_data)
                weather_data = forecast[0] if forecast else {"temperature": 0, "precipitation": 0, "weather": "ei tietoa"}
            else:
                weather_data = {"temperature": 0, "precipitation": 0, "weather": "virhe"}
                
            results.append({
                "coordinates": {"lat": point.lat, "lon": point.lon},
                "time": point.time,
                "data": weather_data
            })
        except Exception as e:
            logger.error(f"Batch fetch error for {point}: {e}")
            results.append({
                "coordinates": {"lat": point.lat, "lon": point.lon},
                "time": point.time,
                "data": {"temperature": 0, "precipitation": 0, "weather": "virhe"}
            })
            
    return results
