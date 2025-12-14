"""Unit tests for weather_api.py

Tests API endpoints and helper functions.
Mocks external HTTP calls to Open-Meteo backend.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from weather_api import (
    app,
    _get_weather_description,
    _simplify_forecast,
    CITIES
)

client = TestClient(app)


class TestWeatherDescription:
    
    def test_lumisadetta(self):
        result = _get_weather_description(temperature=-5, precipitation=1.0)
        assert result == "lumisadetta"
    
    def test_rantaa(self):
        result = _get_weather_description(temperature=1, precipitation=1.0)
        assert result == "räntää"
    
    def test_sadetta(self):
        result = _get_weather_description(temperature=10, precipitation=1.0)
        assert result == "sadetta"
    
    def test_tihkusadetta(self):
        result = _get_weather_description(temperature=10, precipitation=0.2)
        assert result == "tihkusadetta"
    
    def test_aurinkoinen(self):
        result = _get_weather_description(temperature=20, precipitation=0)
        assert result == "aurinkoinen"
    
    def test_pilvista(self):
        result = _get_weather_description(temperature=10, precipitation=0)
        assert result == "pilvistä"
    
    def test_selkeaa(self):
        result = _get_weather_description(temperature=2, precipitation=0)
        assert result == "selkeää"


class TestSimplifyForecast:
    
    def test_valid_data(self):
        raw_data = {
            "forecast": {
                "forecast": [
                    {
                        "time": "2024-01-01T12:00:00Z",
                        "temperature": 5.7,
                        "precipitation": 0.3
                    },
                    {
                        "time": "2024-01-01T13:00:00Z",
                        "temperature": -2.1,
                        "precipitation": 1.5
                    }
                ]
            }
        }
        
        result = _simplify_forecast(raw_data)
        
        assert len(result) == 2
        assert result[0]["time"] == "12:00"
        assert result[0]["temperature"] == 6
        assert result[0]["precipitation"] == 0.3
        assert result[0]["weather"] == "tihkusadetta"
        assert result[1]["temperature"] == -2
        assert result[1]["weather"] == "lumisadetta"
    
    def test_empty_forecast(self):
        raw_data = {"forecast": {"forecast": []}}
        result = _simplify_forecast(raw_data)
        assert result == []


class TestRootEndpoint:
    
    def test_root(self):
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Weather API"
        assert "endpoints" in data


class TestCitiesEndpoint:
    
    def test_list_cities(self):
        response = client.get("/cities")
        
        assert response.status_code == 200
        data = response.json()
        assert "cities" in data
        assert len(data["cities"]) == len(CITIES)
        
        first = data["cities"][0]
        assert "name" in first
        assert "coordinates" in first
        assert "lat" in first["coordinates"]
        assert "lon" in first["coordinates"]


class TestCityEndpoint:
    
    @patch('weather_api._fetch_point_weather')
    def test_valid_city(self, mock_fetch):
        mock_fetch.return_value = {
            "forecast": {
                "forecast": [
                    {
                        "time": "2024-01-01T12:00:00Z",
                        "temperature": 5.0,
                        "precipitation": 0.0
                    }
                ]
            }
        }
        
        response = client.get("/city?name=Helsinki&hours=6")
        
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Helsinki"
        assert "coordinates" in data
        assert "current" in data
        assert "forecast" in data
        assert len(data["forecast"]) == 1
    
    def test_invalid_city(self):
        response = client.get("/city?name=InvalidCity&hours=6")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch('weather_api._fetch_point_weather')
    def test_backend_failure(self, mock_fetch):
        mock_fetch.return_value = None
        
        response = client.get("/city?name=Helsinki&hours=6")
        
        assert response.status_code == 503
        assert "failed" in response.json()["detail"].lower()


class TestPointEndpoint:
    
    @patch('weather_api._fetch_point_weather')
    def test_valid_coordinates(self, mock_fetch):
        mock_fetch.return_value = {
            "forecast": {
                "forecast": [
                    {
                        "time": "2024-01-01T12:00:00Z",
                        "temperature": 10.0,
                        "precipitation": 0.5
                    }
                ]
            }
        }
        
        response = client.get("/point?lat=60.17&lon=24.94&hours=3")
        
        assert response.status_code == 200
        data = response.json()
        assert data["coordinates"]["lat"] == 60.17
        assert data["coordinates"]["lon"] == 24.94
        assert "current" in data
        assert "forecast" in data
    
    def test_invalid_latitude(self):
        response = client.get("/point?lat=100&lon=24.94&hours=3")
        assert response.status_code == 422
    
    def test_invalid_longitude(self):
        response = client.get("/point?lat=60.17&lon=200&hours=3")
        assert response.status_code == 422


class TestRouteEndpoint:
    
    @patch('weather_api._fetch_point_weather')
    def test_valid_route(self, mock_fetch):
        mock_fetch.return_value = {
            "forecast": {
                "forecast": [
                    {
                        "time": "2024-01-01T12:00:00Z",
                        "temperature": 5.0,
                        "precipitation": 0.0
                    }
                ]
            }
        }
        
        response = client.get("/route?from=Helsinki&to=Tampere&hours=6")
        
        assert response.status_code == 200
        data = response.json()
        assert data["route"]["from"] == "Helsinki"
        assert data["route"]["to"] == "Tampere"
        assert "departure" in data
        assert "arrival" in data
        assert mock_fetch.call_count == 2
    
    def test_invalid_from_city(self):
        response = client.get("/route?from=InvalidCity&to=Tampere&hours=6")
        assert response.status_code == 404
    
    def test_invalid_to_city(self):
        response = client.get("/route?from=Helsinki&to=InvalidCity&hours=6")
        assert response.status_code == 404


class TestRouteCoordsEndpoint:
    
    @patch('weather_api._fetch_point_weather')
    def test_valid_coordinates(self, mock_fetch):
        mock_fetch.return_value = {
            "forecast": {
                "forecast": [
                    {
                        "time": "2024-01-01T12:00:00Z",
                        "temperature": 8.0,
                        "precipitation": 0.2
                    }
                ]
            }
        }
        
        response = client.get(
            "/route-coords?from_lat=60.17&from_lon=24.94"
            "&to_lat=61.50&to_lon=23.76&hours=6"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["route"]["from"]["lat"] == 60.17
        assert data["route"]["to"]["lat"] == 61.50
        assert "departure" in data
        assert "arrival" in data
        assert mock_fetch.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
