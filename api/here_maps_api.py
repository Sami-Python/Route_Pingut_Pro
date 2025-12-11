"""HERE Maps and Digitraffic API.

This module provides FastAPI endpoints for:
- HERE Maps routing and geocoding
- Digitraffic traffic information (cameras, messages, road weather, etc.)
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import client modules from clients subdirectory
from clients.here_client import geocode, route, parse_traffic_incidents
from clients.digitraffic_client import (
    get_weather_cameras,
    traffic_messages_near_route,
    get_road_weather_stations,
    get_vms_stations,
    get_maintenance_data,
    get_lam_stations,
    get_road_weather_history
)

app = FastAPI(
    title="HERE Maps & Digitraffic API",
    description="Routing, traffic, and road condition information",
    version="1.0.0"
)

# ============================================================================
# PYDANTIC MODELS - HERE MAPS
# ============================================================================

class GeocodeResponse(BaseModel):
    """Response model for geocoded address.
    
    Attributes
    ----------
    address : str
        Original address string.
    latitude : Optional[float]
        Latitude coordinate if found.
    longitude : Optional[float]
        Longitude coordinate if found.
    success : bool
        Whether geocoding was successful.
    """
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    success: bool


class RouteRequest(BaseModel):
    """Request model for route calculation.
    
    Attributes
    ----------
    origin_lat : float
        Origin latitude (-90 to 90).
    origin_lon : float
        Origin longitude (-180 to 180).
    dest_lat : float
        Destination latitude (-90 to 90).
    dest_lon : float
        Destination longitude (-180 to 180).
    departure_time : Optional[str]
        ISO format departure time (e.g., "2025-12-07T14:00:00").
    routing_mode : str
        Routing mode: "fast" (default) or "short".
    avoid_features : Optional[List[str]]
        Features to avoid (e.g., ["tollRoad", "ferry"]).
    alternatives : int
        Number of alternative routes (0-3).
    """
    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lon: float = Field(..., ge=-180, le=180)
    dest_lat: float = Field(..., ge=-90, le=90)
    dest_lon: float = Field(..., ge=-180, le=180)
    departure_time: Optional[str] = None
    routing_mode: str = Field(default="fast", pattern="^(fast|short)$")
    avoid_features: Optional[List[str]] = None
    alternatives: int = Field(default=0, ge=0, le=3)


class RouteResponse(BaseModel):
    """Response model for calculated route.
    
    Attributes
    ----------
    success : bool
        Whether route calculation succeeded.
    distance_km : Optional[float]
        Route distance in kilometers.
    duration_hours : Optional[float]
        Route duration in hours (with traffic).
    base_duration_hours : Optional[float]
        Route duration without traffic.
    polyline : Optional[str]
        Encoded route polyline (flexpolyline format).
    incidents : Optional[List[Dict[str, Any]]]
        Traffic incidents along route.
    error : Optional[str]
        Error message if failed.
    """
    success: bool
    distance_km: Optional[float] = None
    duration_hours: Optional[float] = None
    base_duration_hours: Optional[float] = None
    polyline: Optional[str] = None
    incidents: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS - DIGITRAFFIC
# ============================================================================

class WeatherCameraResponse(BaseModel):
    """Response model for weather cameras.
    
    Attributes
    ----------
    cameras : List[Dict[str, Any]]
        List of camera data.
    count : int
        Number of cameras found.
    """
    cameras: List[Dict[str, Any]]
    count: int


class TrafficMessageResponse(BaseModel):
    """Response model for traffic messages.
    
    Attributes
    ----------
    messages : List[Dict[str, Any]]
        List of traffic messages.
    count : int
        Number of messages found.
    """
    messages: List[Dict[str, Any]]
    count: int


class RoadWeatherResponse(BaseModel):
    """Response model for road weather stations.
    
    Attributes
    ----------
    stations : List[Dict[str, Any]]
        List of road weather stations with measurements.
    count : int
        Number of stations found.
    """
    stations: List[Dict[str, Any]]
    count: int


class VMSResponse(BaseModel):
    """Response model for variable message signs.
    
    Attributes
    ----------
    signs : List[Dict[str, Any]]
        List of VMS signs.
    count : int
        Number of signs found.
    """
    signs: List[Dict[str, Any]]
    count: int


class MaintenanceResponse(BaseModel):
    """Response model for maintenance tasks.
    
    Attributes
    ----------
    tasks : List[Dict[str, Any]]
        List of maintenance tasks.
    count : int
        Number of tasks found.
    """
    tasks: List[Dict[str, Any]]
    count: int


class LAMResponse(BaseModel):
    """Response model for LAM stations.
    
    Attributes
    ----------
    stations : List[Dict[str, Any]]
        List of LAM measurement stations.
    count : int
        Number of stations found.
    """
    stations: List[Dict[str, Any]]
    count: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _parse_route_coords(route_coords: str) -> List[Tuple[float, float]]:
    """Parse route coordinates from semicolon-separated string.
    
    Parameters
    ----------
    route_coords : str
        Route coordinates in format "lat1,lon1;lat2,lon2;...".
    
    Returns
    -------
    List[Tuple[float, float]]
        List of (lat, lon) tuples.
    
    Raises
    ------
    HTTPException
        If coordinate format is invalid.
    """
    try:
        coords = []
        for pair in route_coords.split(";"):
            lat, lon = map(float, pair.split(","))
            coords.append((lat, lon))
        return coords
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid coordinate format: {e}"
        )


# ============================================================================
# ENDPOINTS - ROOT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint providing API information.
    
    Returns
    -------
    dict
        API metadata and available endpoints.
    """
    return {
        "api": "HERE Maps & Digitraffic API",
        "version": "1.0.0",
        "endpoints": {
            "here_maps": {
                "/geocode": "Convert address to coordinates",
                "/route": "Calculate route between points"
            },
            "digitraffic": {
                "/cameras": "Weather cameras along route",
                "/messages": "Traffic messages along route",
                "/road-weather": "Road weather stations",
                "/vms": "Variable message signs",
                "/maintenance": "Road maintenance tasks",
                "/lam": "Traffic measurement stations"
            },
            "/health": "Health check",
            "/docs": "API documentation"
        }
    }


# ============================================================================
# ENDPOINTS - HERE MAPS
# ============================================================================

@app.get("/geocode", response_model=GeocodeResponse, tags=["HERE Maps"])
async def geocode_address(
    address: str = Query(..., description="Address to geocode")
):
    """Convert address to geographic coordinates using HERE Geocoding API.
    
    Parameters
    ----------
    address : str
        Address string (e.g., "Helsinki, Finland").
    
    Returns
    -------
    GeocodeResponse
        Geocoded coordinates or error.
    
    Raises
    ------
    HTTPException
        If HERE API key is missing or geocoding fails.
    """
    if not os.getenv("HERE_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="HERE_API_KEY not configured"
        )
    
    try:
        coords = geocode(address)
        
        if coords:
            return GeocodeResponse(
                address=address,
                latitude=coords[0],
                longitude=coords[1],
                success=True
            )
        else:
            return GeocodeResponse(
                address=address,
                success=False
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Geocoding failed: {str(e)}"
        )


@app.post("/route", tags=["HERE Maps"])
async def calculate_route(req: RouteRequest):
    """Calculate route between two coordinates using HERE Routing API.
    
    Parameters
    ----------
    req : RouteRequest
        Route request with origin, destination, and routing options.
    
    Returns
    -------
    RouteResponse
        Route with distance, duration, polyline, and traffic incidents.
        If alternatives > 0, returns array of routes in "routes" field.
    
    Raises
    ------
    HTTPException
        If HERE API key is missing or route calculation fails.
    """
    if not os.getenv("HERE_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="HERE_API_KEY not configured"
        )
    
    try:
        origin = (req.origin_lat, req.origin_lon)
        destination = (req.dest_lat, req.dest_lon)
        
        route_data = route(
            origin=origin,
            destination=destination,
            departure_time=req.departure_time,
            routing_mode=req.routing_mode,
            avoid_features=req.avoid_features or [],
            alternatives=req.alternatives
        )
        
        if not route_data or "error" in route_data:
            error_msg = route_data.get("message", "Unknown error") if route_data else "No response"
            return RouteResponse(
                success=False,
                error=f"Route calculation failed: {error_msg}"
            )
        
        if "routes" not in route_data or not route_data["routes"]:
            return RouteResponse(
                success=False,
                error="No routes found"
            )
        
        # DEBUG: Log how many routes HERE API returned
        print(f"DEBUG: HERE API returned {len(route_data['routes'])} routes (requested alternatives={req.alternatives})")
        for i, r in enumerate(route_data["routes"]):
            print(f"  Route {i+1}: {r['sections'][0]['summary']['length']/1000:.1f} km")
        
        # KORJAUS: Kun alternatives > 0, palauta kaikki reitit
        if req.alternatives > 0 and len(route_data["routes"]) > 1:
            # Return multiple routes
            all_routes = []
            for route_obj in route_data["routes"]:
                section = route_obj["sections"][0]
                summary = section["summary"]
                
                all_routes.append({
                    "distance_km": summary["length"] / 1000.0,
                    "duration_hours": summary["duration"] / 3600.0,
                    "base_duration_hours": summary.get("baseDuration", summary["duration"]) / 3600.0,
                    "polyline": section["polyline"],
                    "incidents": []  # Incidents per route if needed
                })
            
            # Parse incidents from all routes
            all_incidents = parse_traffic_incidents(route_data)
            
            # Return with routes array - MUST be a proper dict for FastAPI
            return {
                "success": True,
                "routes": all_routes,
                "incidents": all_incidents,
                "error": None,
                # For compatibility, also return first route data at top level
                "distance_km": all_routes[0]["distance_km"],
                "duration_hours": all_routes[0]["duration_hours"],
                "base_duration_hours": all_routes[0]["base_duration_hours"],
                "polyline": all_routes[0]["polyline"]
            }
        else:
            # Single route response
            first_route = route_data["routes"][0]
            section = first_route["sections"][0]
            summary = section["summary"]
            
            incidents = parse_traffic_incidents(route_data)
            
            return {
                "success": True,
                "distance_km": summary["length"] / 1000.0,
                "duration_hours": summary["duration"] / 3600.0,
                "base_duration_hours": summary.get("baseDuration", summary["duration"]) / 3600.0,
                "polyline": section["polyline"],
                "incidents": incidents,
                "error": None
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Route calculation failed: {str(e)}"
        )


# ============================================================================
# ENDPOINTS - DIGITRAFFIC
# ============================================================================

@app.get("/cameras", response_model=WeatherCameraResponse, tags=["Digitraffic"])
async def get_cameras(
    route_coords: str = Query(
        ...,
        description="Route coordinates: lat1,lon1;lat2,lon2;..."
    )
):
    """Get weather cameras along route from Digitraffic.
    
    Parameters
    ----------
    route_coords : str
        Route coordinates in CSV format.
    
    Returns
    -------
    WeatherCameraResponse
        Weather cameras near the route.
    """
    coords = _parse_route_coords(route_coords)
    cameras = get_weather_cameras(coords)
    return WeatherCameraResponse(cameras=cameras, count=len(cameras))


@app.get("/messages", response_model=TrafficMessageResponse, tags=["Digitraffic"])
async def get_messages(
    route_coords: str = Query(
        ...,
        description="Route coordinates: lat1,lon1;lat2,lon2;..."
    )
):
    """Get traffic messages along route from Digitraffic.
    
    Parameters
    ----------
    route_coords : str
        Route coordinates in CSV format.
    
    Returns
    -------
    TrafficMessageResponse
        Traffic messages near the route.
    """
    coords = _parse_route_coords(route_coords)
    messages = traffic_messages_near_route(coords)
    return TrafficMessageResponse(messages=messages, count=len(messages))


@app.get("/road-weather", response_model=RoadWeatherResponse, tags=["Digitraffic"])
async def get_road_weather(
    route_coords: str = Query(
        ...,
        description="Route coordinates: lat1,lon1;lat2,lon2;..."
    )
):
    """Get road weather stations along route from Digitraffic.
    
    Parameters
    ----------
    route_coords : str
        Route coordinates in CSV format.
    
    Returns
    -------
    RoadWeatherResponse
        Road weather stations with current measurements.
    """
    coords = _parse_route_coords(route_coords)
    stations = get_road_weather_stations(coords)
    return RoadWeatherResponse(stations=stations, count=len(stations))


@app.get("/vms", response_model=VMSResponse, tags=["Digitraffic"])
async def get_vms_signs(
    route_coords: str = Query(
        ...,
        description="Route coordinates: lat1,lon1;lat2,lon2;..."
    )
):
    """Get variable message signs along route from Digitraffic.
    
    Parameters
    ----------
    route_coords : str
        Route coordinates in CSV format.
    
    Returns
    -------
    VMSResponse
        Variable message signs near the route.
    """
    coords = _parse_route_coords(route_coords)
    signs = get_vms_stations(coords)
    return VMSResponse(signs=signs, count=len(signs))


@app.get("/maintenance", response_model=MaintenanceResponse, tags=["Digitraffic"])
async def get_maintenance_tasks(
    route_coords: str = Query(
        ...,
        description="Route coordinates: lat1,lon1;lat2,lon2;..."
    )
):
    """Get road maintenance tasks along route from Digitraffic.
    
    Parameters
    ----------
    route_coords : str
        Route coordinates in CSV format.
    
    Returns
    -------
    MaintenanceResponse
        Maintenance tasks (plowing, salting, etc.) near the route.
    """
    coords = _parse_route_coords(route_coords)
    tasks = get_maintenance_data(coords)
    return MaintenanceResponse(tasks=tasks, count=len(tasks))


@app.get("/lam", response_model=LAMResponse, tags=["Digitraffic"])
async def get_lam_data(
    route_coords: str = Query(
        ...,
        description="Route coordinates: lat1,lon1;lat2,lon2;..."
    )
):
    """Get LAM (traffic measurement) stations along route from Digitraffic.
    
    Parameters
    ----------
    route_coords : str
        Route coordinates in CSV format.
    
    Returns
    -------
    LAMResponse
        LAM stations with traffic flow and speed data.
    """
    coords = _parse_route_coords(route_coords)
    stations = get_lam_stations(coords)
    return LAMResponse(stations=stations, count=len(stations))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Check API health and configuration status.
    
    Returns
    -------
    dict
        Health status and HERE API key configuration status.
    """
    has_key = bool(os.getenv("HERE_API_KEY"))
    
    return {
        "status": "healthy" if has_key else "degraded",
        "here_api_key_configured": has_key,
        "digitraffic_available": True,  # Public API, no key needed
        "message": "OK" if has_key else "HERE_API_KEY not configured (some features unavailable)"
    }

