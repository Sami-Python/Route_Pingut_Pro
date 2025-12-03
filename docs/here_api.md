# HERE API -dokumentaatio

Tämä dokumentaatio kuvaa, miten HERE API:ta käytetään tässä projektissa.

## Yleistä

HERE API tarjoaa kartta-, reitti- ja liikennetietopalvelut REST-rajapinnan kautta. Tässä projektissa käytetään seuraavia HERE API -palveluita:
- **Geokoodaus** (osoite → koordinaatit)
- **Reititys** (reitin haku ja optimointi)
- **Liikennetiedot** (häiriöt ja viivästykset)

## API-avain

API-avain tallennetaan `.env`-tiedostoon:
```env
HERE_API_KEY=your_api_key_here
```

Avain haetaan HERE Developer Portalista: https://developer.here.com/

## Käytetyt rajapinnat

### 1. Geokoodaus

Muuttaa osoitteen koordinaateiksi.

**Endpoint:** `https://geocode.search.hereapi.com/v1/geocode`

**Metodi:** GET

**Parametrit:**
- `q`: Osoite (esim. "Helsinki")
- `limit`: Tulosten määrä (yleensä 1)
- `apiKey`: HERE API -avain

**Esimerkki:**
```
GET https://geocode.search.hereapi.com/v1/geocode?q=Helsinki&limit=1&apiKey=YOUR_API_KEY
```

**Vastaus:**
```json
{
  "items": [
    {
      "position": {
        "lat": 60.1699,
        "lng": 24.9384
      },
      "address": {
        "label": "Helsinki, Suomi"
      }
    }
  ]
}
```

**Käyttö koodissa:**
```python
from here_client import geocode

coords = geocode("Helsinki")  # Palauttaa (lat, lon)
```

### 2. Reititys

Hakee reitin kahden pisteen välille.

**Endpoint:** `https://router.hereapi.com/v8/routes`

**Metodi:** GET

**Parametrit:**
- `transportMode`: Kulkutapa (esim. `car`)
- `origin`: Lähtöpiste (lat,lon)
- `destination`: Määränpää (lat,lon)
- `return`: Palautettavat tiedot (esim. `polyline,summary,incidents,elevation`)
- `spans`: Lisätiedot (esim. `incidents`)
- `departureTime`: Lähtöaika (ISO 8601)
- `routingMode`: Optimointi (`fast` tai `short`)
- `avoid[features]`: Vältettävät (esim. `tollRoad,controlledAccessHighway`)
- `apiKey`: HERE API -avain

**Esimerkki:**
```
GET https://router.hereapi.com/v8/routes?
  transportMode=car&
  origin=60.1699,24.9384&
  destination=61.4985,23.7717&
  return=polyline,summary,incidents,elevation&
  spans=incidents&
  routingMode=fast&
  apiKey=YOUR_API_KEY
```

**Vastaus:**
```json
{
  "routes": [
    {
      "sections": [
        {
          "polyline": "BFoz5xJ67...",
          "summary": {
            "length": 178000,
            "duration": 7200,
            "baseDuration": 7000
          },
          "incidents": [
            {
              "type": "ACCIDENT",
              "description": "Onnettomuus",
              "criticality": "major"
            }
          ],
          "spans": [
            {
              "offset": 0,
              "incidents": [0]
            }
          ]
        }
      ]
    }
  ]
}
```

**Käyttö koodissa:**
```python
from here_client import route

route_data = route(
    origin=(60.1699, 24.9384),
    destination=(61.4985, 23.7717),
    departure_time="2024-12-03T10:00:00+02:00",
    routing_mode="fast",
    avoid_features=["tollRoad"]
)
```

### 3. Polyline-dekoodaus

HERE käyttää "Flexible Polyline" -muotoa reittiviivan tallentamiseen.

**Kirjasto:** `flexpolyline`

**Käyttö:**
```python
import flexpolyline

polyline_str = "BFoz5xJ67..."
coords = flexpolyline.decode(polyline_str)
# Palauttaa listan: [(lat, lon, elevation), ...]
```

### 4. Häiriötietojen parsinta

Häiriöt palautetaan kahdessa osassa:
1. `incidents` - Häiriöiden määritelmät
2. `spans` - Häiriöiden sijainnit reitillä

**Käyttö koodissa:**
```python
from here_client import parse_traffic_incidents

incidents = parse_traffic_incidents(route_data)
# Palauttaa listan:
# [
#   {
#     "tyyppi": "ACCIDENT",
#     "kuvaus": "Onnettomuus tiellä",
#     "taso": "major",
#     "lat": 60.5,
#     "lon": 24.8,
#     "paikka": "Indeksi: 42"
#   }
# ]
```

## Matkan tiedot

### Matka ja aika
```python
section = route_data["routes"][0]["sections"][0]
summary = section["summary"]

matka_km = summary["length"] / 1000.0
aika_h = summary["duration"] / 3600.0
```

### Keskinopeus
```python
nopeus_kmh = (summary["length"] / 1000) / (summary["duration"] / 3600)
```

### Viivästys
```python
viivastys_s = summary["duration"] - summary["baseDuration"]
```

## Virheenkäsittely

```python
route_data = route(origin, destination)

if route_data and "error" not in route_data:
    # Onnistui
    polyline = route_data["routes"][0]["sections"][0]["polyline"]
else:
    # Epäonnistui
    print("Reitin haku epäonnistui")
```

## Rajoitukset

- **Maksuttomat kyselyt:** Rajoitettu määrä kuukaudessa
- **Rate limiting:** Liian nopeat kyselyt estetään
- **Geokoodaus:** Ei aina löydä pieniä paikkoja
- **Reititys:** Vaatii koordinaatit, ei osoitteita

## Vinkkejä

1. **Cachetus:** Käytä `@st.cache_data` välttääksesi turhia API-kutsuja
2. **Virheenkäsittely:** Tarkista aina vastauksen olemassaolo
3. **Timeout:** Aseta `requests.get(..., timeout=10)`
4. **API-avain:** Älä koskaan commitoi `.env`-tiedostoa

## Lisätietoja

- Virallinen dokumentaatio: https://developer.here.com/documentation
- Routing API v8: https://developer.here.com/documentation/routing-api/8/dev_guide/index.html
- Geocoding API: https://developer.here.com/documentation/geocoding-search-api/dev_guide/index.html

---

Katso myös:
- [app.md](app.md) - Sovelluksen kehityshistoria
- [fastapi_ohje.md](fastapi_ohje.md) - REST API -dokumentaatio
