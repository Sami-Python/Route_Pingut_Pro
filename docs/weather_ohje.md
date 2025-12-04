# RainViewer API -dokumentaatio

Tämä dokumentaatio kuvaa, miten RainViewer API:ta käytetään sade-ennusteen näyttämiseen.

## Yleistä

RainViewer on ilmainen sääkarttapalvelu, joka tarjoaa:
- **Sadetutkakartat** (radar)
- **Satelliittikuvat** (satellite)
- **Ennusteet** (nowcast)

Tässä projektissa käytetään sadetutkakarttoja koko Suomen alueelle.

## API-avain

RainViewer API on **ilmainen** eikä vaadi API-avainta.

## Käytetyt rajapinnat

### 1. Weather Maps Metadata

Hakee saatavilla olevat aikaleimat ja tile-palvelimen osoitteen.

**Endpoint:** `https://api.rainviewer.com/public/weather-maps.json`

**Metodi:** GET

**Parametrit:** Ei parametreja

**Esimerkki:**
```
GET https://api.rainviewer.com/public/weather-maps.json
```

**Vastaus:**
```json
{
  "version": "1.4",
  "generated": 1701456000,
  "host": "https://tilecache.rainviewer.com",
  "radar": {
    "past": [
      {
        "time": 1701455400,
        "path": "/v2/radar/1701455400"
      }
    ],
    "nowcast": [
      {
        "time": 1701456600,
        "path": "/v2/radar/1701456600"
      }
    ]
  }
}
```

**Käyttö koodissa:**
```python
from weather_client import get_rainviewer_data

host, timestamps_dict = get_rainviewer_data()
# host: "https://tilecache.rainviewer.com"
# timestamps_dict: {1701455400: "/v2/radar/1701455400", ...}
```

### 2. Tile URL -rakenne

Yksittäinen säätiili haetaan seuraavalla URL-rakenteella:

```
{host}{path}/256/{z}/{x}/{y}/6/1_1.png
```

**Parametrit:**
- `host`: Palvelimen osoite (metadata-API:sta)
- `path`: Aikaleiman polku (metadata-API:sta)
- `z`: Zoom-taso (6 = koko Suomi)
- `x`: Tiilen X-koordinaatti
- `y`: Tiilen Y-koordinaatti
- `6`: Väripaletti (6 = Universal Blue)
- `1_1`: Smooth/Snow (1 = smooth, 1 = no snow)

**Esimerkki:**
```
https://tilecache.rainviewer.com/v2/radar/1701455400/256/6/36/19/6/1_1.png
```

## Tiilien laskenta (Web Mercator)

Projekti käyttää **manuaalista tiilauslaskentaa**, koska Pydeckin TileLayer ei toimi kunnolla.

### Koordinaatit → Tiili

```python
import math

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)
```

### Tiili → Koordinaatit

```python
def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)
```

### Suomen bounding box

```python
# Koko Suomi
min_lat, max_lat = 59.0, 71.0
min_lon, max_lon = 19.0, 33.0

zoom = 6

# Laske tiilialue
x_min, y_max = deg2num(min_lat, min_lon, zoom)
x_max, y_min = deg2num(max_lat, max_lon, zoom)
```

## Pydeck-integraatio

Koska TileLayer ei toimi, käytetään **BitmapLayeriä** jokaiselle tiilelle:

```python
import pydeck as pdk

layers = []

for x in range(x_start, x_end + 1):
    for y in range(y_start, y_end + 1):
        # Laske tiilen bbox
        nw_lat, nw_lon = num2deg(x, y, zoom)
        se_lat, se_lon = num2deg(x + 1, y + 1, zoom)
        
        bounds = [nw_lon, se_lat, se_lon, nw_lat]
        
        tile_url = f"{host}{path}/256/{zoom}/{x}/{y}/6/1_1.png"
        
        layers.append(pdk.Layer(
            "BitmapLayer",
            id=f"weather-tile-{x}-{y}",
            image=tile_url,
            bounds=bounds,
            opacity=0.6
        ))
```

## Aikaleiman valinta

Valitaan lähin aikaleima simuloidulle ajalle:

```python
from weather_client import get_closest_timestamp

# Simuloitu aika (Unix timestamp)
sim_ts = int(datetime.now().timestamp())

# Lähin saatavilla oleva aikaleima
closest_ts = get_closest_timestamp(sim_ts, available_timestamps)
```

## Väripaletit

RainViewer tukee useita väripaletteja (viimeinen numero URL:ssa):

- `0` - Original
- `1` - Universal Blue
- `2` - TITAN
- `3` - The Weather Channel (TWC)
- `4` - Meteored
- `5` - NEXRAD Level III
- `6` - Rainbow @ SELEX-SI (suositeltu)

Tässä projektissa käytetään **6** (Rainbow).

## Rajoitukset

### Tiilimäärä
- Rajoitettu 50 tiiliin suorituskyvyn vuoksi
- Koko Suomi zoom-tasolla 6 = ~20-30 tiiliä

### Zoom-taso
- Kiinteä zoom 6 (ei dynaamista zoomausta)
- Pienempi zoom = vähemmän yksityiskohtia
- Suurempi zoom = enemmän tiiliä

### TileLayer-ongelma
- Pydeckin TileLayer ei toimi RainViewerin kanssa
- Käytetään BitmapLayeriä workaroundina

## Caching

```python
@st.cache_data(ttl=300)  # 5 minuuttia
def get_cached_weather_data():
    return get_rainviewer_data()
```

## Virheenkäsittely

```python
try:
    resp = requests.get(url, timeout=10)
    data = resp.json()
    
    host = data.get("host", "https://tilecache.rainviewer.com")
    
    # Poista mahdollinen lopun kauttaviiva
    if host.endswith("/"):
        host = host[:-1]
        
except Exception as e:
    print(f"RainViewer API error: {e}")
    # Fallback
    host = "https://tilecache.rainviewer.com"
    timestamps = {int(time.time()): "/v2/radar/..."}
```

## Optimointi

### 1. Rajoita tiilimäärää
```python
max_tiles = 50
count = 0

for x in range(x_start, x_end + 1):
    for y in range(y_start, y_end + 1):
        if count >= max_tiles:
            break
        # ...
        count += 1
```

### 2. Käytä oikeaa zoom-tasoa
- Zoom 6 = Koko Suomi (~20 tiiliä)
- Zoom 7 = Etelä-Suomi (~50 tiiliä)
- Zoom 8 = Pääkaupunkiseutu (~100 tiiliä)

### 3. Cacheta metadata
```python
@st.cache_data(ttl=300)
def get_cached_weather_data():
    return get_rainviewer_data()
```

## Lisätietoja

- Virallinen dokumentaatio: https://www.rainviewer.com/api.html
- Tile-palvelin: https://tilecache.rainviewer.com
- Web Mercator: https://en.wikipedia.org/wiki/Web_Mercator_projection

---

Katso myös:
- [app.md](app.md) - Sovelluksen kehityshistoria
- [here_api.md](here_api.md) - HERE API -dokumentaatio
