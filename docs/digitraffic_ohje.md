# Digitraffic API -dokumentaatio

Tämä dokumentaatio kuvaa, miten Digitraffic API:ta käytetään tässä projektissa.

## Yleistä

Digitraffic on Suomen liikenneviraston avoin data -palvelu, joka tarjoaa reaaliaikaista tietoa:
- **Kelikamerat** (weathercam)
- **Liikennetiedotteet** (traffic messages)
- **Tiesääasemat** (weather stations)
- **LAM-pisteet** (liikenteen automaattinen mittaus)

Tässä projektissa käytetään kelikameroita ja liikennetiedotteita.

## API-avain

Digitraffic API on **ilmainen** eikä vaadi API-avainta. Suositellaan kuitenkin käyttämään User-Agent -headeria:

```python
headers = {"User-Agent": "StreamlitApp/1.0 (gzip)"}
```

## Käytetyt rajapinnat

### 1. Kelikamerat

Hakee kelikamerat reitin varrelta.

**Endpoint:** `https://tie.digitraffic.fi/api/weathercam/v1/stations`

**Metodi:** GET

**Parametrit:** Ei pakollisia (haetaan kaikki kamerat)

**Esimerkki:**
```
GET https://tie.digitraffic.fi/api/weathercam/v1/stations
```

**Vastaus:**
```json
{
  "features": [
    {
      "geometry": {
        "coordinates": [24.9384, 60.1699]
      },
      "properties": {
        "id": "C0450701",
        "names": {
          "fi": "Kehä I Tapiola"
        },
        "presets": [
          {
            "id": "C045070101",
            "imageUrl": "https://weathercam.digitraffic.fi/C045070101.jpg"
          }
        ]
      }
    }
  ]
}
```

**Käyttö koodissa:**
```python
from digitraffic_client import get_weather_cameras

cameras = get_weather_cameras(route_coords, buffer_meters=1000)
# Palauttaa listan:
# [
#   {
#     "id": "C0450701",
#     "name": "Kehä I Tapiola",
#     "lat": 60.1699,
#     "lon": 24.9384,
#     "imageUrl": "https://weathercam.digitraffic.fi/C045070101.jpg"
#   }
# ]
```

**Suodatus:**
- Käytetään **Shapely**-kirjastoa geometriseen suodatukseen
- Buffer: 1000 metriä reitistä
- Bbox-optimointi nopeuttaa hakua

### 2. Liikennetiedotteet

Hakee liikennetiedotteet reitin varrelta.

**Endpoint:** `https://tie.digitraffic.fi/api/traffic-message/v1/messages`

**Metodi:** GET

**Parametrit:**
- `inactiveHours`: Kuinka vanhoja tiedotteita haetaan (0 = vain aktiiviset)
- `situationType`: Tiedotteen tyyppi (esim. `TRAFFIC_ANNOUNCEMENT`)
- `includeAreaGeometry`: Sisällytetäänkö geometria (`false`)
- `bbox`: Bounding box (min_lon,min_lat,max_lon,max_lat)

**Esimerkki:**
```
GET https://tie.digitraffic.fi/api/traffic-message/v1/messages?
  inactiveHours=0&
  situationType=TRAFFIC_ANNOUNCEMENT&
  includeAreaGeometry=false&
  bbox=24.5,60.0,25.5,61.0
```

**Vastaus:**
```json
{
  "features": [
    {
      "geometry": {
        "type": "LineString",
        "coordinates": [[24.9384, 60.1699], [24.9500, 60.1800]]
      },
      "properties": {
        "announcementUpdateTime": "2024-12-03T10:00:00Z",
        "announcements": [
          {
            "title": "Tietyö",
            "comment": "Tietyö Kehä I:llä",
            "description": "Kaista suljettu",
            "location": {
              "description": "Kehä I, Tapiola"
            }
          }
        ]
      }
    }
  ]
}
```

**Käyttö koodissa:**
```python
from digitraffic_client import traffic_messages_near_route

messages = traffic_messages_near_route(route_coords, buffer_meters=500)
# Palauttaa listan:
# [
#   {
#     "otsikko": "Tietyö",
#     "kuvaus": "Tietyö Kehä I:llä",
#     "sijainti": "Kehä I, Tapiola",
#     "aika": "2024-12-03T10:00:00Z",
#     "lat": 60.1699,
#     "lon": 24.9384
#   }
# ]
```

**Suodatus:**
- Shapely-pohjainen geometrinen suodatus
- Buffer: 500 metriä reitistä
- Bbox-rajoitus API-kutsussa
- Fallback ilman bboxia jos API palauttaa 400/413

## Geometrinen suodatus (Shapely)

Projekti käyttää **Shapely**-kirjastoa tarkempaan suodatukseen:

```python
from shapely.geometry import LineString, Point, shape

# 1. Luodaan reittiviiva
route_line = LineString([(lon, lat) for lat, lon in route_coords])

# 2. Lasketaan bounding box
min_x, min_y, max_x, max_y = route_line.bounds

# 3. Tarkistetaan etäisyys
buffer_degrees = buffer_meters / 111000.0  # metrit → asteet
if route_line.distance(point) < buffer_degrees:
    # Piste on tarpeeksi lähellä
```

## CORS-ongelma kelikameroissa

Selaimet estävät kuvien lataamisen suoraan Digitrafficista. Ratkaisu:

```python
import requests

# Server-side fetch
img_url = "https://weathercam.digitraffic.fi/C045070101.jpg"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(img_url, headers=headers, timeout=5)

if resp.status_code == 200:
    st.image(resp.content)
```

## Virheenkäsittely

### Bbox-virheet
```python
try:
    resp = requests.get(url, params=params, timeout=5)
    
    # Jos bbox liian iso, yritä ilman
    if resp.status_code in [400, 413, 414]:
        del params["bbox"]
        resp = requests.get(url, params=params, timeout=10)
    
    resp.raise_for_status()
except Exception as e:
    print(f"Digitraffic API error: {e}")
    return []
```

### Timeout
```python
resp = requests.get(url, timeout=10)  # 10 sekuntia
```

## Rajoitukset

- **Bbox-koko:** Liian iso bbox voi aiheuttaa 400/413-virheen
- **Kuvien lataus:** Voi olla hidasta, timeout 5s
- **User-Agent:** Pakollinen kelikamerakuville
- **Geometria:** Tiedotteissa voi olla pisteitä tai viivoja

## Vinkkejä

1. **Cachetus:** Käytä `@st.cache_data(ttl=300)` (5 min)
2. **Bbox-optimointi:** Rajaa alue ennen Shapely-suodatusta
3. **Fallback:** Varaudu bbox-virheisiin
4. **User-Agent:** Käytä aina headereissa

## Lisätietoja

- Virallinen dokumentaatio: https://www.digitraffic.fi/
- Kelikamerat: https://www.digitraffic.fi/tieliikenne/#kelikamerat
- Liikennetiedotteet: https://www.digitraffic.fi/tieliikenne/#liikennetiedotteet

---

Katso myös:
- [here_api.md](here_api.md) - HERE API -dokumentaatio
- [weather_ohje.md](weather_ohje.md) - RainViewer-dokumentaatio
