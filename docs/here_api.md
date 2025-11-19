# HERE API -dokumentaatio

Tämä dokumentaatio kuvaa, miten HERE API:ta käytetään tässä projektissa.

## Yleistä
HERE API tarjoaa kartta-, reitti- ja liikennetietopalvelut REST-rajapinnan kautta. Tässä projektissa käytetään seuraavia HERE API -palveluita:
- Geokoodaus (osoite → koordinaatit)

## Käytetyt päärajapinnat

- **Endpoint:** `https://geocode.search.hereapi.com/v1/geocode`
- **Metodi:** GET
- **Parametrit:**
    - `limit`: Tulosten määrä (yleensä 1)
    - `apiKey`: HERE API -avain
- **Esimerkki:**
```
GET https://geocode.search.hereapi.com/v1/geocode?q=Helsinki&limit=1&apiKey=YOUR_API_KEY
```
- **Vastaus:**
```json
{
  "items": [
  ]
}
```

### 2. Reitin haku
- **Metodi:** GET
- **Parametrit:**
    - `transportMode`: esim. `car`
    - `destination`: Määränpään koordinaatit (lat,lon)
    - `return`: Mitä tietoja palautetaan (esim. `polyline,summary`)
    - `apiKey`: HERE API -avain
- **Esimerkki:**
```
GET https://router.hereapi.com/v8/routes?transportMode=car&origin=60.1699,24.9384&destination=61.4985,23.7717&return=polyline,summary&apiKey=YOUR_API_KEY
```
- **Vastaus:**
```json
{
  "routes": [
    {
      "sections": [
### 2. Reitin haku ja liikennetiedot
- **Endpoint:** `https://router.hereapi.com/v8/routes`
- **Metodi:** GET
- **Parametrit:**
    - `transportMode`: esim. `car`
    - `origin`: Lähtöpaikan koordinaatit (lat,lon)
    - `destination`: Määränpään koordinaatit (lat,lon)
    - `return`: Mitä tietoja palautetaan (esim. `polyline,summary,incidents`)
    - `apiKey`: HERE API -avain
- **Esimerkki:**
```
GET https://router.hereapi.com/v8/routes?transportMode=car&origin=60.1699,24.9384&destination=61.4985,23.7717&return=polyline,summary,incidents&apiKey=YOUR_API_KEY
```
- **Vastaus:**
```json
{
  "routes": [
    {
      "sections": [
        {
          "polyline": "BFoz5xJ67...", // Flexible polyline
          "summary": {
            "length": 178000, // matka metreinä
            "duration": 7200, // aika sekunteina
            "baseDuration": 7000, // aika ilman liikennettä
            // ...
          },
          "incidents": [
            {
              "type": "accident",
              "location": {"lat": 60.2, "lng": 24.9},
              "description": "Onnettomuus tiellä X"
            }
          ]
        }
      ]
    }
  ]
}
```

#### Matka, aika ja nopeus
- Matka: `summary['length']` (metreinä)
- Aika: `summary['duration']` (sekunteina)
- Nopeus: `(length / 1000) / (duration / 3600)` (km/h)

#### Liikennemarkerit kartalle
- Jokainen `incidents`-listan kohde lisätään Folium-kartalle:
```python
for incident in incidents:
    folium.Marker(
        location=[incident['location']['lat'], incident['location']['lng']],
        popup=incident['description'],
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(kartta)
```
        {
          "polyline": "BFoz5xJ67...", // Flexible polyline
      ]
    }
  ]
}
```

### 3. Polyline-dekoodaus
- Polyline on HERE:n "flexible polyline" -muodossa.
- Pythonissa käytetään `flexpolyline`-kirjastoa:
```python
from flexpolyline import decode
coords = decode(polyline_str)  # Palauttaa listan (lat, lon) tupleja
```

## Käyttö Pythonissa
- Kaikki API-kutsut tehdään `requests`-kirjastolla:
```python
import requests
resp = requests.get(url)
data = resp.json()
```
- API-avaimen saat HERE Developer Portalista.

## Vinkkejä
- API-kutsut ovat REST-muotoisia (HTTP GET).
- Muista suojata API-avaimesi.
- Katso HERE:n virallinen dokumentaatio: https://developer.here.com/documentation

---
Lisätietoja ja esimerkkejä löytyy projektin koodista (`here_client.py`).
