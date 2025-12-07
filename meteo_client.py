"""Open-Meteo API client for fetching weather forecast data.

Open-Meteo provides free weather forecast API with no authentication required.
Uses FMI's HARMONIE model data for Finland but with easier JSON interface.
Uses bounding box API for efficient grid data fetching.
"""

import requests
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeteoClient:
    """Client for interacting with Open-Meteo API using bounding box queries.
    
    Attributes
    ----------
    base_url : str
        The base URL for Open-Meteo API.
    """
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_temperature_forecast(
        self, 
        bbox: Tuple[float, float, float, float],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Fetch temperature forecast using GET with optimal grid size.
        """
        if start_time is None:
            start_time = datetime.utcnow()
        if end_time is None:
            end_time = start_time + timedelta(hours=6)
        
        min_lon, min_lat, max_lon, max_lat = bbox
        
        logger.info(f"Fetching temperature for bbox: {bbox}")
        
        # Reduced grid - 12x12 = 144 points (stays under URL length limit)
        # For Southern Finland bbox, this gives ~12km spacing
        lat_points = np.linspace(min_lat, max_lat, 12)
        lon_points = np.linspace(min_lon, max_lon, 12)
        
        coordinates = [(lat, lon) for lat in lat_points for lon in lon_points]
        
        logger.info(f"Querying {len(coordinates)} coordinate points")
        
        # Format dates
        start_date = start_time.strftime('%Y-%m-%d')
        end_date = end_time.strftime('%Y-%m-%d')
        
        # Build GET request with comma-separated coordinates
        latitudes = ','.join(str(lat) for lat, _ in coordinates)
        longitudes = ','.join(str(lon) for _, lon in coordinates)
        
        params = {
            'latitude': latitudes,
            'longitude': longitudes,
            'hourly': 'temperature_2m',
            'start_date': start_date,
            'end_date': end_date,
            'timezone': 'UTC'
        }
        
        try:
            logger.info(f"GET request to: {self.base_url}")
            
            response = requests.get(self.base_url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            all_data = []
            
            # Parse response
            if isinstance(data, list):
                logger.info(f"Received {len(data)} grid points from API")
                
                for i, location_data in enumerate(data):
                    if i >= len(coordinates):
                        break
                    
                    lat, lon = coordinates[i]
                    hourly = location_data.get('hourly', {})
                    
                    times = hourly.get('time', [])
                    temps = hourly.get('temperature_2m', [])
                    
                    for time_str, temp in zip(times, temps):
                        if temp is not None:
                            try:
                                time_dt = datetime.fromisoformat(time_str.replace('Z', ''))
                                if start_time <= time_dt <= end_time:
                                    all_data.append({
                                        'lat': lat,
                                        'lon': lon,
                                        'temperature': temp,
                                        'time': time_str
                                    })
                            except ValueError:
                                continue
            else:
                logger.warning(f"Unexpected data format: {type(data)}")
                return []
            
            logger.info(f"Successfully fetched {len(all_data)} temperature data points")
            return all_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch temperature data: {e}")
            return []
    
    def get_precipitation_forecast(
        self,
        bbox: Tuple[float, float, float, float],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Fetch precipitation forecast using GET with optimal grid.
        """
        if start_time is None:
            start_time = datetime.utcnow()
        if end_time is None:
            end_time = start_time + timedelta(hours=6)
        
        min_lon, min_lat, max_lon, max_lat = bbox
        
        logger.info(f"Fetching precipitation for bbox: {bbox}")
        
        # Grid - 20x20 = 400 points (Result: ~35km spacing)
        # We round coordinates to 2 decimals to keep URL length within limits (Avoid 414 Error)
        lat_points = np.linspace(min_lat, max_lat, 20)
        lon_points = np.linspace(min_lon, max_lon, 20)
        
        coordinates = [(lat, lon) for lat in lat_points for lon in lon_points]
        
        logger.info(f"Querying {len(coordinates)} coordinate points")
        
        # Format dates
        start_date = start_time.strftime('%Y-%m-%d')
        end_date = end_time.strftime('%Y-%m-%d')
        
        # KEY OPTIMIZATION: Round to 2 decimals to save char space in URL!
        latitudes = ','.join(f"{lat:.2f}" for lat, _ in coordinates)
        longitudes = ','.join(f"{lon:.2f}" for _, lon in coordinates)
        
        params = {
            'latitude': latitudes,
            'longitude': longitudes,
            'hourly': 'precipitation,temperature_2m',
            'start_date': start_date,
            'end_date': end_date,
            'timezone': 'UTC'
        }
        
        try:
            logger.info(f"GET request to: {self.base_url}")
            
            response = requests.get(self.base_url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            all_data = []
            
            if isinstance(data, list):
                logger.info(f"Received {len(data)} grid points from API")
                
                for i, location_data in enumerate(data):
                    if i >= len(coordinates):
                        break
                    
                    lat, lon = coordinates[i]
                    hourly = location_data.get('hourly', {})
                    
                    times = hourly.get('time', [])
                    precips = hourly.get('precipitation', [])
                    temps = hourly.get('temperature_2m', [])
                    
                    for time_str, precip, temp in zip(times, precips, temps):
                        if precip is not None and temp is not None:
                            try:
                                time_dt = datetime.fromisoformat(time_str.replace('Z', ''))
                                if start_time <= time_dt <= end_time:
                                    # Determine weather symbol
                                    if precip > 0:
                                        if temp < -1:
                                            weather_symbol = 51  # Snow
                                        elif temp < 2:
                                            weather_symbol = 81  # Sleet
                                        else:
                                            weather_symbol = 31  # Rain
                                    else:
                                        weather_symbol = 1  # Clear
                                    
                                    all_data.append({
                                        'lat': lat,
                                        'lon': lon,
                                        'precipitation': precip,
                                        'temperature': temp,
                                        'weather_symbol': weather_symbol,
                                        'time': time_str
                                    })
                            except ValueError:
                                continue
            else:
                logger.warning(f"Unexpected data format: {type(data)}")
                return []
            
            # Log statistics
            with_precip = sum(1 for d in all_data if d['precipitation'] > 0.1)
            logger.info(f"Successfully fetched {len(all_data)} precipitation points")
            logger.info(f"Points with precipitation > 0.1 mm/h: {with_precip}")
            
            return all_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch precipitation data: {e}")
            return []
    
    def get_weather_symbols(
        self,
        bbox: Tuple[float, float, float, float],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Get weather symbols (alias for precipitation forecast).
        """
        return self.get_precipitation_forecast(bbox, start_time, end_time)
