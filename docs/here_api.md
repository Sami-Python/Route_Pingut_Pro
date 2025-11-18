# HERE API -dokumentaatio

Tämä dokumentaatio kuvaa, miten HERE API:ta käytetään tässä projektissa.

## Yleistä
HERE API tarjoaa kartta-, reitti- ja liikennetietopalvelut REST-rajapinnan kautta. Tässä projektissa käytetään seuraavia HERE API -palveluita:
- Geokoodaus (osoite → koordinaatit)
- Reitin haku (koordinaatit → reitti)
- Reitin polyline (reittiviiva kartalle)
- (Liikennetiedot, jos käytössä)

## Käytetyt päärajapinnat

### 1. Geokoodaus
- **Endpoint:** `https://geocode.search.hereapi.com/v1/geocode`
- **Metodi:** GET
- **Parametrit:**
    - `q`: Osoite (esim. "Helsinki")
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
    {
      "position": { "lat": 60.1699, "lng": 24.9384 }, ...
    }
  ]
}
```

### 2. Reitin haku
- **Endpoint:** `https://router.hereapi.com/v8/routes`
- **Metodi:** GET
- **Parametrit:**
    - `transportMode`: esim. `car`
    - `origin`: Lähtöpaikan koordinaatit (lat,lon)
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
        {
          "polyline": "BFoz5xJ67...", // Flexible polyline
          ...
        }
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
