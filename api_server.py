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
from digitraffic_client import get_weather_cameras, traffic_messages_near_route
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
    version="1.0.0"
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
    
    **Esimerkki:**
    ```
    GET /api/geocode?address=Helsinki
    ```
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
    
    **Parametrit:**
    - origin_lat, origin_lon: Lähtöpiste
    - dest_lat, dest_lon: Määränpää
    - departure_time: ISO-muotoinen aika (valinnainen)
    - routing_mode: "fast" tai "short"
    - avoid_features: Lista välttämisiä (esim. ["tollRoad", "ferry"])
    
    **Palauttaa:**
    - Matka (km), kesto (h), polyline, häiriöt
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

@app.get("/api/digitraffic/cameras", response_model=WeatherCameraResponse, tags=["Digitraffic"])
def api_weather_cameras(
    route_coords: str = Query(..., description="Reitin koordinaatit CSV-muodossa: lat1,lon1;lat2,lon2;...")
):
    """
    Hakee kelikamerat reitin varrelta Digitraffic API:sta.
    
    **Esimerkki:**
    ```
    GET /api/digitraffic/cameras?route_coords=60.17,24.94;61.49,23.77
    ```
    """
    try:
        # Parsitaan koordinaatit
        coords = []
        for pair in route_coords.split(";"):
            lat, lon = map(float, pair.split(","))
            coords.append((lat, lon))
        
        cameras = get_weather_cameras(coords)
        return WeatherCameraResponse(cameras=cameras, count=len(cameras))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Virheellinen koordinaattimuoto: {e}")

@app.get("/api/digitraffic/messages", response_model=TrafficMessageResponse, tags=["Digitraffic"])
def api_traffic_messages(
    route_coords: str = Query(..., description="Reitin koordinaatit CSV-muodossa")
):
    """
    Hakee liikennetiedotteet reitin varrelta Digitraffic API:sta.
    
    **Esimerkki:**
    ```
    GET /api/digitraffic/messages?route_coords=60.17,24.94;61.49,23.77
    ```
    """
    try:
        coords = []
        for pair in route_coords.split(";"):
            lat, lon = map(float, pair.split(","))
            coords.append((lat, lon))
        
        messages = traffic_messages_near_route(coords)
        return TrafficMessageResponse(messages=messages, count=len(messages))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Virheellinen koordinaattimuoto: {e}")

# ====================================================================
# ENDPOINTS - RAINVIEWER (SÄÄ)
# ====================================================================

@app.get("/api/weather/rainviewer", response_model=RainViewerResponse, tags=["RainViewer"])
def api_rainviewer():
    """
    Hakee RainViewerin säätiilien palvelimen (host) ja aikaleimat.
    
    **Palauttaa:**
    - host: Tile-palvelimen URL
    - timestamps: Lista Unix-aikaleimoja (sekunteina)
    - count: Aikaleiman määrä
    
    **Käyttö:**
    Rakenna tile URL: `{host}/v2/radar/{timestamp}/256/{z}/{x}/{y}/6/1_1.png`
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
    
    **Esimerkki:**
    ```
    GET /api/weather/closest-timestamp?target=1701456000&timestamps=1701455400,1701456000,1701456600
    ```
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
        "version": "1.0.0"
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
