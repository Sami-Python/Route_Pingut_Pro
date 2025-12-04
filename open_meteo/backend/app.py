"""FastAPI backend for Open-Meteo weather data service."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime, timedelta
import logging
from clients.meteo_client import MeteoClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Open-Meteo Weather API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

meteo_client = MeteoClient()

# Finland bounding box coordinates
FINLAND_BBOX = (20.5, 59.5, 31.5, 70.1)

@app.get("/")
async def root():
    """Health check endpoint.
    
    Returns
    -------
    dict
        Status message.
    """
    return {"status": "ok", "service": "Open-Meteo Weather API"}


@app.get("/api/forecast/temperature")
async def get_temperature_forecast(
    min_lon: float = Query(FINLAND_BBOX[0], description="Minimum longitude"),
    min_lat: float = Query(FINLAND_BBOX[1], description="Minimum latitude"),
    max_lon: float = Query(FINLAND_BBOX[2], description="Maximum longitude"),
    max_lat: float = Query(FINLAND_BBOX[3], description="Maximum latitude"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    hours: int = Query(6, description="Forecast hours from start time")
):
    """Get temperature forecast for a bounding box.
    
    Fetches temperature data from Open-Meteo for a grid of points
    within the specified bounding box.
    
    Parameters
    ----------
    min_lon : float
        Minimum longitude of bounding box.
    min_lat : float
        Minimum latitude of bounding box.
    max_lon : float
        Maximum longitude of bounding box.
    max_lat : float
        Maximum latitude of bounding box.
    start_time : Optional[str]
        Start time in ISO format. Defaults to current time.
    hours : int
        Number of hours to forecast. Max 6.
    
    Returns
    -------
    dict
        Temperature forecast data with 100 grid points.
    """
    try:
        # Limit forecast to maximum 6 hours
        hours = min(hours, 6)
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = datetime.utcnow()
        
        end_dt = start_dt + timedelta(hours=hours)
        
        bbox = (min_lon, min_lat, max_lon, max_lat)
        data = meteo_client.get_temperature_forecast(bbox, start_dt, end_dt)
        
        logger.info(f"Temperature forecast: {len(data)} data points returned")
        
        return {
            "bbox": bbox,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching temperature forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast/weather")
async def get_weather_forecast(
    min_lon: float = Query(FINLAND_BBOX[0], description="Minimum longitude"),
    min_lat: float = Query(FINLAND_BBOX[1], description="Minimum latitude"),
    max_lon: float = Query(FINLAND_BBOX[2], description="Maximum longitude"),
    max_lat: float = Query(FINLAND_BBOX[3], description="Maximum latitude"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    hours: int = Query(6, description="Forecast hours from start time")
):
    """Get weather forecast with precipitation for a bounding box.
    
    Returns precipitation data and weather symbols (rain/snow/sleet)
    determined by temperature and precipitation intensity.
    
    Parameters
    ----------
    min_lon : float
        Minimum longitude of bounding box.
    min_lat : float
        Minimum latitude of bounding box.
    max_lon : float
        Maximum longitude of bounding box.
    max_lat : float
        Maximum latitude of bounding box.
    start_time : Optional[str]
        Start time in ISO format. Defaults to current time.
    hours : int
        Number of hours to forecast. Max 6.
    
    Returns
    -------
    dict
        Weather forecast data with precipitation and weather symbols.
    """
    try:
        hours = min(hours, 6)
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = datetime.utcnow()
        
        end_dt = start_dt + timedelta(hours=hours)
        
        bbox = (min_lon, min_lat, max_lon, max_lat)
        data = meteo_client.get_weather_symbols(bbox, start_dt, end_dt)
        
        # Count precipitation points for logging
        with_precip = sum(1 for d in data if d.get('precipitation', 0) > 0.1)
        logger.info(f"Weather forecast: {len(data)} total points, {with_precip} with precipitation")
        
        return {
            "bbox": bbox,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching weather forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast/point")
async def get_point_forecast(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    hours: int = Query(6, description="Forecast hours from start time")
):
    """Get detailed forecast for a specific point.
    
    Returns hourly temperature and precipitation forecast for
    a single coordinate location.
    
    Parameters
    ----------
    lat : float
        Latitude coordinate.
    lon : float
        Longitude coordinate.
    start_time : Optional[str]
        Start time in ISO format. Defaults to current time.
    hours : int
        Number of hours to forecast. Max 6.
    
    Returns
    -------
    dict
        Detailed forecast for the point location.
    """
    try:
        hours = min(hours, 6)
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = datetime.utcnow()
        
        end_dt = start_dt + timedelta(hours=hours)
        
        data = meteo_client.get_point_forecast(lat, lon, start_dt, end_dt)
        
        return {
            "location": {"lat": lat, "lon": lon},
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "forecast": data
        }
    except Exception as e:
        logger.error(f"Error fetching point forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast/precipitation")
async def get_precipitation_forecast(
    min_lon: float = Query(FINLAND_BBOX[0], description="Minimum longitude"),
    min_lat: float = Query(FINLAND_BBOX[1], description="Minimum latitude"),
    max_lon: float = Query(FINLAND_BBOX[2], description="Maximum longitude"),
    max_lat: float = Query(FINLAND_BBOX[3], description="Maximum latitude"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    hours: int = Query(6, description="Forecast hours from start time")
):
    """Get precipitation forecast for a bounding box.
    
    Returns precipitation intensity and weather symbols for
    visualization on map overlay.
    
    Parameters
    ----------
    min_lon : float
        Minimum longitude of bounding box.
    min_lat : float
        Minimum latitude of bounding box.
    max_lon : float
        Maximum longitude of bounding box.
    max_lat : float
        Maximum latitude of bounding box.
    start_time : Optional[str]
        Start time in ISO format. Defaults to current time.
    hours : int
        Number of hours to forecast. Max 6.
    
    Returns
    -------
    dict
        Precipitation forecast data with 64 grid points.
    """
    try:
        hours = min(hours, 6)
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = datetime.utcnow()
        
        end_dt = start_dt + timedelta(hours=hours)
        
        bbox = (min_lon, min_lat, max_lon, max_lat)
        data = meteo_client.get_precipitation_forecast(bbox, start_dt, end_dt)
        
        return {
            "bbox": bbox,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching precipitation forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
