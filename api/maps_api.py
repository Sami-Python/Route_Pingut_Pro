"""
FastAPI Backend - Reitti- ja liikennetiedot
Tarjoaa REST API:n HERE, Digitraffic ja RainViewer -kutsuille.
Swagger docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
import requests
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel
import uvicorn
from flexpolyline import decode as decode_polyline

print("[DEBUG] LOADING MAPS_API.PY - VERSION WITH FIXED ROUTES")

# Tuodaan client-moduulit
from api.utils.here_client import geocode, route, parse_traffic_incidents
from api.utils.digitraffic_client import (
    get_weather_cameras, 
    traffic_messages_near_route,
    get_road_weather_stations,
    get_vms_stations,
    get_maintenance_data,
    get_lam_stations,
    get_road_weather_history,
    get_weather_cameras_by_point,
    get_road_weather_stations_by_point,
    traffic_messages_near_point,
    get_lam_stations_by_point
)
from api.utils.weather_client import get_rainviewer_data, get_closest_timestamp
from api.utils.meteo_client import MeteoClient
from api.utils.gemini_client import GeminiRouteAnalyzer
import requests
import datetime
from ics import Calendar
import arrow

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
    alternatives: int = 0

class RouteSummary(BaseModel):
    distance_km: float
    duration_hours: float
    polyline: str
    coordinates: List[Tuple[float, float]]
    incidents: Optional[List[Dict[str, Any]]] = None

class RouteResponse(BaseModel):
    success: bool
    distance_km: Optional[float] = None
    duration_hours: Optional[float] = None
    polyline: Optional[str] = None
    coordinates: Optional[List[Tuple[float, float]]] = None
    incidents: Optional[List[Dict[str, Any]]] = None
    alternatives: Optional[List[RouteSummary]] = None
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

class CalendarEvent(BaseModel):
    title: str
    start: str
    end: str
    location: Optional[str] = None

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="Reitti API",
    description="REST API HERE, Digitraffic ja RainViewer -datalle",
    version="1.4.0"
)

# CORS handled in main.py
# app.add_middleware(CORSMiddleware, ...)

# --- MOUNT ADDITIONAL APIs ---
import sys
import os

# Add 'api' folder to path so internal imports in api/*.py work (e.g. import utils)
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))

try:
    from gcal_api import app as gcal_app
    app.mount("/gcal", gcal_app)
    # Mount Graph API as well for completeness if needed
    from graph_api import app as graph_app
    app.mount("/graph", graph_app)
    print("[OK] Google Calendar & Graph APIs mounted successfully.")
except Exception as e:
    print(f"[ERROR] Failed to mount sub-APIs: {e}")

meteo_client = MeteoClient()
gemini_analyzer = GeminiRouteAnalyzer()
FINLAND_BBOX = (20.5, 59.5, 31.5, 70.1)

# ====================================================================
# ENDPOINTS - HERE API
# ====================================================================

@app.get("/geocode", response_model=GeocodeResponse, tags=["HERE API"])
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

@app.post("/route", response_model=RouteResponse, tags=["HERE API"])
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
        avoid_features=req.avoid_features or [],
        alternatives=req.alternatives
    )
    
    if not route_data or "error" in route_data:
        msg = route_data.get("message", "Unknown error") if route_data else "No data returned"
        code = route_data.get("status_code", 500) if route_data else 500
        raise HTTPException(status_code=code, detail=f"Route failed: {msg}")
    
    try:
        # Parse all routes
        parsed_routes = []
        routes_list = route_data.get("routes", [])
        
        for r in routes_list:
            if not r.get("sections"): continue
            
            section = r["sections"][0]
            summary = section["summary"]
            polyline = section["polyline"]
            
            decoded_coords = decode_polyline(polyline)
            coordinates = [(lat, lon) for lat, lon, *rest in decoded_coords]
            
            # Incidents specific to this route variant
            # Note: parse_traffic_incidents expects full route_data structure but only processes spans.
            # We need to be careful if we want incidents for EACH route.
            # The current here_client.parse_traffic_incidents iterates ALL routes in route_data.
            # So if we pass the whole object, we get all incidents combined?
            # Let's check here_client.parse_traffic_incidents implementation.
            # It iterates 'for route_obj in route_data["routes"]'. 
            # So it aggregates incidents from ALL routes into one list.
            # For per-route incidents, we might need to construct a mini-response object.
            
            mini_route_data = {"routes": [r]}
            incidents = parse_traffic_incidents(mini_route_data)
            
            parsed_routes.append(RouteSummary(
                distance_km=summary["length"] / 1000.0,
                duration_hours=summary["duration"] / 3600.0,
                polyline=polyline,
                coordinates=coordinates,
                incidents=incidents
            ))
            
        if not parsed_routes:
             raise HTTPException(status_code=404, detail="No routes found in response")

        # Primary route (first one)
        primary = parsed_routes[0]
        
        return RouteResponse(
            success=True,
            distance_km=primary.distance_km,
            duration_hours=primary.duration_hours,
            polyline=primary.polyline,
            coordinates=primary.coordinates,
            incidents=primary.incidents,
            alternatives=parsed_routes # Returns all routes including primary in the list
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Virhe datan parsinnassa: {e}")

@app.get("/tiles/here_traffic/{z}/{x}/{y}", tags=["HERE API"])
def proxy_here_traffic_tiles(z: int, x: int, y: int):
    """
    Proxy HERE Traffic tiles to avoid exposing API KEY to client.
    """
    import os
    import base64
    from fastapi.responses import Response
    
    api_key = os.getenv("HERE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="HERE_API_KEY no configured in backend")
    
    print(f"DEBUG: Proxying tile {z}/{x}/{y} with Key len={len(api_key)}")


    # URL Format for HERE Traffic Flow Tiles (Raster)
    url = f"https://traffic.ls.hereapi.com/traffic/1.0/flowtile/png/{z}/{x}/{y}/256/png8"
    
    try:
        # TIMEOUT INCREASED: 10s -> 20s
        # Not streaming anymore to avoid protocol errors with h11/uvicorn
        req = requests.get(url, params={"apiKey": api_key}, stream=False, timeout=20)
        
        if req.status_code == 200:
            return Response(
                content=req.content, 
                media_type=req.headers.get("Content-Type", "image/png"),
                status_code=200
            ) 
        elif req.status_code == 404:
            # HERE returns 404 for empty tiles (no traffic data).
            # Return a 1x1 transparent PNG to shut up the client errors.
            # 1x1 Transparent PNG Base64 decoded
            transparent_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
            return Response(content=base64.b64decode(transparent_png_b64), media_type="image/png")
        else:
            print(f"HERE API Error: {req.status_code} - {req.text}")
            return Response(content=req.content, status_code=req.status_code)
            
    except Exception as e:
        print(f"Tile proxy exception: {e}")
        # Return transparent PNG on exception too? Maybe better to error.
        raise HTTPException(status_code=502, detail=f"Upstream connection failed: {str(e)}")

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

@app.get("/digitraffic/cameras", response_model=WeatherCameraResponse, tags=["Digitraffic"])
def api_weather_cameras(
    route_coords: Optional[str] = Query(None, description="Reitin koordinaatit CSV-muodossa"),
    polyline: Optional[str] = Query(None, description="Reitin flexpolyline-merkkijono"),
    lat: Optional[float] = Query(None, description="Leveysaste (jos ei reittiä)"),
    lon: Optional[float] = Query(None, description="Pituusaste (jos ei reittiä)"),
    radius: float = Query(50.0, description="Hakusäde km")
):
    """
    Hakee kelikamerat reitin varrelta TAI tietystä pisteestä.
    """
    if polyline:
        decoded = decode_polyline(polyline)
        coords = [(p[0], p[1]) for p in decoded]
        cameras = get_weather_cameras(coords)
    elif route_coords:
        coords = parse_route_coords(route_coords)
        cameras = get_weather_cameras(coords)
    elif lat is not None and lon is not None:
        cameras = get_weather_cameras_by_point(lat, lon, radius)
    else:
        raise HTTPException(status_code=400, detail="Anna joko polyline, route_coords tai lat/lon")
        
    return WeatherCameraResponse(cameras=cameras, count=len(cameras))

@app.get("/digitraffic/messages", response_model=TrafficMessageResponse, tags=["Digitraffic"])
def api_traffic_messages(
    route_coords: Optional[str] = Query(None, description="Reitin koordinaatit CSV-muodossa"),
    polyline: Optional[str] = Query(None, description="Reitin flexpolyline-merkkijono"),
    lat: Optional[float] = Query(None, description="Leveysaste (jos ei reittiä)"),
    lon: Optional[float] = Query(None, description="Pituusaste (jos ei reittiä)"),
    radius: float = Query(50.0, description="Hakusäde km")
):
    """
    Hakee liikennetiedotteet reitin varrelta TAI tietystä pisteestä.
    """
    if polyline:
        decoded = decode_polyline(polyline)
        coords = [(p[0], p[1]) for p in decoded]
        messages = traffic_messages_near_route(coords)
    elif route_coords:
        coords = parse_route_coords(route_coords)
        messages = traffic_messages_near_route(coords)
    elif lat is not None and lon is not None:
        messages = traffic_messages_near_point(lat, lon, radius)
    else:
        raise HTTPException(status_code=400, detail="Anna joko polyline, route_coords tai lat/lon")
        
    return TrafficMessageResponse(messages=messages, count=len(messages))

@app.get("/digitraffic/road-weather", response_model=RoadWeatherResponse, tags=["Digitraffic"])
def api_road_weather(
    route_coords: Optional[str] = Query(None, description="Reitin koordinaatit CSV-muodossa"),
    polyline: Optional[str] = Query(None, description="Reitin flexpolyline-merkkijono"),
    lat: Optional[float] = Query(None, description="Leveysaste"),
    lon: Optional[float] = Query(None, description="Pituusaste"),
    radius: float = Query(50.0, description="Hakusäde km")
):
    """
    Hakee tiesääasemat reitin varrelta TAI tietystä pisteestä.
    """
    if polyline:
        decoded = decode_polyline(polyline)
        coords = [(p[0], p[1]) for p in decoded]
        stations = get_road_weather_stations(coords)
    elif route_coords:
        coords = parse_route_coords(route_coords)
        stations = get_road_weather_stations(coords)
    elif lat is not None and lon is not None:
        stations = get_road_weather_stations_by_point(lat, lon, radius)
    else:
        raise HTTPException(status_code=400, detail="Anna joko polyline, route_coords tai lat/lon")
        
    return RoadWeatherResponse(stations=stations, count=len(stations))

@app.get("/digitraffic/vms", response_model=VMSResponse, tags=["Digitraffic"])
def api_vms(
    route_coords: str = Query(..., description="Reitin koordinaatit CSV-muodossa")
):
    """
    Hakee muuttuvat opasteet (VMS) reitin varrelta.
    """
    coords = parse_route_coords(route_coords)
    signs = get_vms_stations(coords)
    return VMSResponse(signs=signs, count=len(signs))

@app.get("/digitraffic/maintenance", response_model=MaintenanceResponse, tags=["Digitraffic"])
def api_maintenance(
    route_coords: str = Query(..., description="Reitin koordinaatit CSV-muodossa")
):
    """
    Hakee kunnossapitotehtävät (esim. auraus) reitin varrelta.
    """
    coords = parse_route_coords(route_coords)
    tasks = get_maintenance_data(coords)
    return MaintenanceResponse(tasks=tasks, count=len(tasks))

@app.get("/digitraffic/lam", response_model=LAMResponse, tags=["Digitraffic"])
def api_lam(
    route_coords: Optional[str] = Query(None, description="Reitin koordinaatit CSV-muodossa"),
    polyline: Optional[str] = Query(None, description="Reitin flexpolyline-merkkijono"),
    lat: Optional[float] = Query(None, description="Leveysaste"),
    lon: Optional[float] = Query(None, description="Pituusaste"),
    radius: float = Query(50.0, description="Hakusäde km")
):
    """
    Hakee LAM-mittauspisteet reitin varrelta TAI säteellä.
    """
    if polyline:
        decoded = decode_polyline(polyline)
        coords = [(p[0], p[1]) for p in decoded]
        stations = get_lam_stations(coords)
    elif route_coords:
        coords = parse_route_coords(route_coords)
        stations = get_lam_stations(coords)
    elif lat is not None and lon is not None:
        stations = get_lam_stations_by_point(lat, lon, radius)
    else:
        raise HTTPException(status_code=400, detail="Anna joko polyline, route_coords tai lat/lon")

    return LAMResponse(stations=stations, count=len(stations))

@app.get("/digitraffic/road-weather/{station_id}/history", response_model=HistoryResponse, tags=["Digitraffic"])
def api_road_weather_history(station_id: int):
    """
    Hakee tiesääaseman historiatiedot (demo/mock).
    """
    history = get_road_weather_history(station_id)
    return HistoryResponse(history=history, count=len(history))

# ====================================================================
# ENDPOINTS - AI ANALYSIS
# ====================================================================

@app.post("/analyze/route", tags=["AI"])
async def analyze_route(route_data: Dict[str, Any]):
    """
    Analysoi reitin tiedot (Gemini AI).
    Vastaanottaa: { "duration_hours": float, "distance_km": float, ... }
    """
    try:
        from api.utils.gemini_client import GeminiRouteAnalyzer
        analyzer = GeminiRouteAnalyzer()
        
        # Convert frontend format (hours/km) to Gemini client expectation (sec/m)
        # to match generic handler, OR update Gemini client. 
        # Easier to adapt here using a specific adapter dict.
        
        # Frontend sends: distance_km, duration_hours
        # Gemini Client expects: length (m), duration (s)
        
        d_km = route_data.get("distance_km", 0)
        t_h = route_data.get("duration_hours", 0)
        
        adapter_summary = {
            "length": d_km * 1000,
            "duration": t_h * 3600
        }
        
        # We can also pass raw incidents if available
        incidents = route_data.get("incidents", [])
        
        analysis = analyzer.analyze_route(adapter_summary, incidents, [])
        return {"analysis": analysis}
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return {"analysis": "Analyysi epäonnistui palvelinvirheen vuoksi."}

@app.get("/weather/rainviewer", response_model=RainViewerResponse, tags=["RainViewer"])
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

@app.get("/weather/closest-timestamp", tags=["RainViewer"])
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
# ENDPOINTS - OPEN-METEO
# ====================================================================

@app.get("/forecast/temperature", tags=["Open-Meteo"])
async def get_temperature_forecast(
    min_lon: float = Query(FINLAND_BBOX[0]),
    min_lat: float = Query(FINLAND_BBOX[1]),
    max_lon: float = Query(FINLAND_BBOX[2]),
    max_lat: float = Query(FINLAND_BBOX[3]),
    start_time: Optional[str] = Query(None),
    hours: int = Query(6)
):
    """Hakee lämpötilaennusteen alueelle (Grid)."""
    try:
        hours = min(hours, 6)
        if start_time:
            start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = datetime.datetime.utcnow()
        end_dt = start_dt + datetime.timedelta(hours=hours)
        
        bbox = (min_lon, min_lat, max_lon, max_lat)
        data = meteo_client.get_temperature_forecast(bbox, start_dt, end_dt)
        return {"bbox": bbox, "start_time": start_dt.isoformat(), "end_time": end_dt.isoformat(), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forecast/weather", tags=["Open-Meteo"])
async def get_weather_forecast(
    min_lon: float = Query(FINLAND_BBOX[0]),
    min_lat: float = Query(FINLAND_BBOX[1]),
    max_lon: float = Query(FINLAND_BBOX[2]),
    max_lat: float = Query(FINLAND_BBOX[3]),
    start_time: Optional[str] = Query(None),
    hours: int = Query(6)
):
    """Hakee sääennusteen (sade) alueelle (Grid)."""
    try:
        hours = min(hours, 6)
        if start_time:
            start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = datetime.datetime.utcnow()
        end_dt = start_dt + datetime.timedelta(hours=hours)
        
        bbox = (min_lon, min_lat, max_lon, max_lat)
        data = meteo_client.get_weather_symbols(bbox, start_dt, end_dt)
        return {"bbox": bbox, "start_time": start_dt.isoformat(), "end_time": end_dt.isoformat(), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====================================================================
# ENDPOINTS - CALENDAR
# ====================================================================

@app.get("/ical/events", response_model=List[CalendarEvent], tags=["Calendar"])
def get_ical_events(url: str = Query(..., description="iCal-tiedoston URL")):
    """
    Hakee ja parsii tapahtumat iCal-URL:sta (sisältää toistuvat).
    """
    try:
        from icalevents.icalevents import events as fetch_events
        import datetime
        
        # Haetaan tapahtumat: mennyt viikko -> +2kk
        start = datetime.datetime.now() - datetime.timedelta(days=7)
        end = datetime.datetime.now() + datetime.timedelta(days=60)
        
        # icalevents hoitaa latauksen ja parsinnan
        ical_evts = fetch_events(url=url, start=start, end=end)
        
        events = []
        for e in ical_evts:
            # e.start on datetime (voi olla timezonella)
            events.append(CalendarEvent(
                title=e.summary or "No Title",
                start=str(e.start),
                end=str(e.end),
                location=e.location
            ))
            
        # Järjestetään ajan mukaan
        events.sort(key=lambda x: x.start)
            
        return events
    except Exception as e:
        print(f"Calendar error: {e}")
        raise HTTPException(status_code=500, detail=f"Virhe kalenterin haussa: {str(e)}")

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
        port=8001,
        reload=True,
        log_level="info"
    )

