"""
FastAPI Backend - Reitti- ja liikennetiedot
Tarjoaa REST API:n HERE, Digitraffic ja RainViewer -kutsuille.
Swagger docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel
import uvicorn

# Tuodaan client-moduulit
from here_client import geocode, route, parse_traffic_incidents
from digitraffic_client import (
    get_weather_cameras, 
    traffic_messages_near_route,
    get_road_weather_stations,
    get_vms_stations,
    get_maintenance_data,
    get_lam_stations,
    get_road_weather_history
)
from weather_client import get_rainviewer_data, get_closest_timestamp

# ====================================================================
# PYDANTIC MODELS (Request/Response)
# ====================================================================

class GeocodeResponse(BaseModel):
    address: str
    latitude: Optional[float]
    longitude: Optional[float]
    success: bool

class RouteRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    departure_time: Optional[str] = None
    routing_mode: str = "fast"
    avoid_features: Optional[List[str]] = None

class RouteResponse(BaseModel):
    success: bool
    distance_km: Optional[float] = None
    duration_hours: Optional[float] = None
    polyline: Optional[str] = None
    incidents: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class WeatherCameraResponse(BaseModel):
    cameras: List[Dict[str, Any]]
    count: int

class TrafficMessageResponse(BaseModel):
    messages: List[Dict[str, Any]]
    count: int

class RoadWeatherResponse(BaseModel):
    stations: List[Dict[str, Any]]
    count: int

class VMSResponse(BaseModel):
    signs: List[Dict[str, Any]]
    count: int

class MaintenanceResponse(BaseModel):
    tasks: List[Dict[str, Any]]
    count: int

class LAMResponse(BaseModel):
    stations: List[Dict[str, Any]]
    count: int

class HistoryResponse(BaseModel):
    history: List[Dict[str, Any]]
    count: int

class RainViewerResponse(BaseModel):
    host: str
    timestamps: List[int]
    count: int

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="Reitti API",
    description="REST API HERE, Digitraffic ja RainViewer -datalle",
    version="1.4.0"
)

# CORS (jos frontend on eri portissa)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================================================================
# ENDPOINTS - HERE API
# ====================================================================

@app.get("/api/geocode", response_model=GeocodeResponse, tags=["HERE API"])
def api_geocode(address: str = Query(..., description="Osoite geokoodaukseen")):
    """
    Muuttaa osoitteen koordinaateiksi HERE Geocode API:lla.
    """
    coords = geocode(address)
    if coords:
        return GeocodeResponse(
            address=address,
            latitude=coords[0],
            longitude=coords[1],
            success=True
        )
    return GeocodeResponse(address=address, latitude=None, longitude=None, success=False)

@app.post("/api/route", response_model=RouteResponse, tags=["HERE API"])
def api_route(req: RouteRequest):
    """
    Hakee reitin HERE Routing API:lla.
    """
    origin = (req.origin_lat, req.origin_lon)
    dest = (req.dest_lat, req.dest_lon)
    
    route_data = route(
        origin, 
        dest, 
        departure_time=req.departure_time,
        routing_mode=req.routing_mode,
        avoid_features=req.avoid_features or []
    )
    
    if not route_data or "error" in route_data:
        raise HTTPException(status_code=500, detail="Reitin haku epäonnistui")
    
    try:
        section = route_data["routes"][0]["sections"][0]
        summary = section["summary"]
        polyline = section["polyline"]
        
        incidents = parse_traffic_incidents(route_data)
        
        return RouteResponse(
            success=True,
            distance_km=summary["length"] / 1000.0,
            duration_hours=summary["duration"] / 3600.0,
            polyline=polyline,
            incidents=incidents
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Virhe datan parsinnassa: {e}")

# ====================================================================
# ENDPOINTS - DIGITRAFFIC
# ====================================================================

def parse_route_coords(route_coords: str) -> List[Tuple[float, float]]:
    try:
        coords = []
        for pair in route_coords.split(";"):
            lat, lon = map(float, pair.split(","))
            coords.append((lat, lon))
        return coords
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Virheellinen koordinaattimuoto: {e}")

@app.get("/api/digitraffic/cameras", response_model=WeatherCameraResponse, tags=["Digitraffic"])
def api_weather_cameras(
    route_coords: str = Query(..., description="Reitin koordinaatit CSV-muodossa: lat1,lon1;lat2,lon2;...")
):
    """
    Hakee kelikamerat reitin varrelta.
    """
    coords = parse_route_coords(route_coords)
    cameras = get_weather_cameras(coords)
    return WeatherCameraResponse(cameras=cameras, count=len(cameras))

@app.get("/api/digitraffic/messages", response_model=TrafficMessageResponse, tags=["Digitraffic"])
def api_traffic_messages(
    route_coords: str = Query(..., description="Reitin koordinaatit CSV-muodossa")
):
    """
    Hakee liikennetiedotteet reitin varrelta.
    """
    coords = parse_route_coords(route_coords)
    messages = traffic_messages_near_route(coords)
    return TrafficMessageResponse(messages=messages, count=len(messages))

@app.get("/api/digitraffic/road-weather", response_model=RoadWeatherResponse, tags=["Digitraffic"])
def api_road_weather(
    route_coords: str = Query(..., description="Reitin koordinaatit CSV-muodossa")
):
    """
    Hakee tiesääasemat ja niiden mittaustiedot reitin varrelta.
    """
    coords = parse_route_coords(route_coords)
    stations = get_road_weather_stations(coords)
    return RoadWeatherResponse(stations=stations, count=len(stations))

@app.get("/api/digitraffic/vms", response_model=VMSResponse, tags=["Digitraffic"])
def api_vms(
    route_coords: str = Query(..., description="Reitin koordinaatit CSV-muodossa")
):
    """
    Hakee muuttuvat opasteet (VMS) reitin varrelta.
    """
    coords = parse_route_coords(route_coords)
    signs = get_vms_stations(coords)
    return VMSResponse(signs=signs, count=len(signs))

@app.get("/api/digitraffic/maintenance", response_model=MaintenanceResponse, tags=["Digitraffic"])
def api_maintenance(
    route_coords: str = Query(..., description="Reitin koordinaatit CSV-muodossa")
):
    """
    Hakee kunnossapitotehtävät (esim. auraus) reitin varrelta.
    """
    coords = parse_route_coords(route_coords)
    tasks = get_maintenance_data(coords)
    return MaintenanceResponse(tasks=tasks, count=len(tasks))

@app.get("/api/digitraffic/lam", response_model=LAMResponse, tags=["Digitraffic"])
def api_lam(
    route_coords: str = Query(..., description="Reitin koordinaatit CSV-muodossa")
):
    """
    Hakee LAM-mittauspisteet reitin varrelta.
    """
    coords = parse_route_coords(route_coords)
    stations = get_lam_stations(coords)
    return LAMResponse(stations=stations, count=len(stations))

@app.get("/api/digitraffic/road-weather/{station_id}/history", response_model=HistoryResponse, tags=["Digitraffic"])
def api_road_weather_history(station_id: int):
    """
    Hakee tiesääaseman historiatiedot (demo/mock).
    """
    history = get_road_weather_history(station_id)
    return HistoryResponse(history=history, count=len(history))

# ====================================================================
# ENDPOINTS - RAINVIEWER (SÄÄ)
# ====================================================================

@app.get("/api/weather/rainviewer", response_model=RainViewerResponse, tags=["RainViewer"])
def api_rainviewer():
    """
    Hakee RainViewerin säätiilien palvelimen (host) ja aikaleimat.
    """
    host, ts_dict = get_rainviewer_data()
    timestamps = sorted(list(ts_dict.keys()))
    
    return RainViewerResponse(
        host=host,
        timestamps=timestamps,
        count=len(timestamps)
    )

@app.get("/api/weather/closest-timestamp", tags=["RainViewer"])
def api_closest_timestamp(
    target: int = Query(..., description="Tavoitteellinen Unix-aikaleima"),
    timestamps: str = Query(..., description="CSV-lista aikaleimoja: 1234567890,1234567900,...")
):
    """
    Löytää lähimmän aikaleiman annetusta listasta.
    """
    try:
        ts_list = [int(t) for t in timestamps.split(",")]
        closest = get_closest_timestamp(target, ts_list)
        return {"target": target, "closest": closest}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Virhe aikaleiman parsinnassa: {e}")

# ====================================================================
# ROOT
# ====================================================================

@app.get("/", tags=["Info"])
def root():
    """
    API:n pääsivu. Ohjaa Swagger-dokumentaatioon.
    """
    return {
        "message": "Reitti API - HERE, Digitraffic, RainViewer",
        "docs": "/docs",
        "redoc": "/redoc",
        "version": "1.4.0"
    }

# ====================================================================
# KÄYNNISTYS
# ====================================================================

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
