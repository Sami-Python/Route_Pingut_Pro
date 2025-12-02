# FastAPI Backend - Käyttöohje

## Asennus

Asenna FastAPI-riippuvuudet:
```bash
pip install fastapi uvicorn[standard] pydantic
```

## Käynnistys

### Vaihtoehto 1: Suoraan Pythonilla
```bash
python api_server.py
```

### Vaihtoehto 2: Uvicorn-komennolla
```bash
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

## Dokumentaatio

Kun palvelin on käynnissä, avaa selaimessa:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpointit

### HERE API

#### Geokoodaus
```http
GET /api/geocode?address=Helsinki
```

Vastaus:
```json
{
  "address": "Helsinki",
  "latitude": 60.1699,
  "longitude": 24.9384,
  "success": true
}
```

#### Reititys
```http
POST /api/route
Content-Type: application/json

{
  "origin_lat": 60.1699,
  "origin_lon": 24.9384,
  "dest_lat": 61.4978,
  "dest_lon": 23.7610,
  "routing_mode": "fast",
  "avoid_features": ["tollRoad"]
}
```

Vastaus:
```json
{
  "success": true,
  "distance_km": 178.5,
  "duration_hours": 2.1,
  "polyline": "BFoz5xJ67...",
  "incidents": [...]
}
```

### Digitraffic

#### Kelikamerat
```http
GET /api/digitraffic/cameras?route_coords=60.17,24.94;61.49,23.77
```

#### Liikennetiedotteet
```http
GET /api/digitraffic/messages?route_coords=60.17,24.94;61.49,23.77
```

### RainViewer (Sää)

#### Hae säätiilien data
```http
GET /api/weather/rainviewer
```

Vastaus:
```json
{
  "host": "https://tilecache.rainviewer.com",
  "timestamps": [1701455400, 1701456000, ...],
  "count": 20
}
```

#### Lähin aikaleima
```http
GET /api/weather/closest-timestamp?target=1701456000&timestamps=1701455400,1701456000,1701456600
```

## Docker

Voit ajaa FastAPI:n myös Dockerissa. Lisää `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Käynnistä:
```bash
docker build -t reitti-api .
docker run -p 8000:8000 reitti-api
```

## Yhteenveto

FastAPI tarjoaa:
- ✅ Automaattinen Swagger-dokumentaatio (`/docs`)
- ✅ ReDoc-dokumentaatio (`/redoc`)
- ✅ Pydantic-validointi
- ✅ Nopea ja kevyt
- ✅ CORS-tuki frontendille

Kaikki HERE, Digitraffic ja RainViewer -kutsut ovat nyt REST API:na käytettävissä!
