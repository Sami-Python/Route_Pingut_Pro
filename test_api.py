from fastapi.testclient import TestClient

from api_server import app


client = TestClient(app)


def test_root_ok():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    # Viestin pitäisi olla tyyliä "Reitti API - HERE, Digitraffic, RainViewer"
    assert "Reitti API" in data["message"]


def test_geocode_missing_param():
    response = client.get("/api/geocode")
    # FastAPI palauttaa 422, kun pakollinen query-parametri puuttuu
    assert response.status_code == 422


def test_geocode_with_address():
    # Käytetään melko turvallista osoitetta; testi tarkistaa vain rakenteen
    response = client.get("/api/geocode", params={"address": "Helsinki"})
    assert response.status_code == 200
    data = response.json()
    # Riittää, että rakenteessa on nämä avaimet
    for key in ("address", "latitude", "longitude", "success"):
        assert key in data
    assert data["success"] is True


def test_rainviewer_metadata():
    response = client.get("/api/weather/rainviewer")
    assert response.status_code == 200
    data = response.json()
    # Rakennetesti: host ja timestamps-lista olemassa
    assert "host" in data
    assert "timestamps" in data
    assert isinstance(data["timestamps"], list)
