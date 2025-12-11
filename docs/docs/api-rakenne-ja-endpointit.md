# API Rakenne ja Endpointit

Tämä dokumentti kuvaa projektin API-rakenteen ja tarjolla olevat endpointit. API toimii yhdyskäytävänä (Gateway), joka yhdistää useita eri palveluita (Google Calendar, Outlook, HERE Maps, Digitraffic, Sääpalvelut) yhden rajapinnan alle.

## 1. Päärajapinta (API Gateway)

Tiedosto: `api/main.py`

Päärajapinta kokoaa kaikki alimoduulit ja tarjoaa keskitetyn pääsypisteen.

| Metodi | Polku | Kuvaus |
| :--- | :--- | :--- |
| `GET` | `/` | Palauttaa listauksen saatavilla olevista reiteistä ja niiden kuvauksista. |
| `GET` | `/logs` | Palauttaa `api.log` -logitiedoston sisällön (jos olemassa). |

**Alimoduulien kiinnityspisteet:**

| Polku | Kuvaus |
| :--- | :--- |
| `/graph` | Microsoft Graph API |
| `/ical` | iCal API |
| `/weather` | Weather API |
| `/gcal` | Google Calendar API |
| `/maps` | Maps API |

---

## 2. Google Calendar API

Tiedosto: `api/gcal_api.py`
Polku: `/gcal`

Tämä moduuli hoitaa Google-kalenterin OAuth2-tunnistautumisen ja tapahtumien haun.

| Metodi | Polku | Parametrit | Kuvaus |
| :--- | :--- | :--- | :--- |
| `GET` | `/gcal/` | - | Tervetuloviesti. |
| `GET` | `/gcal/login` | `redirect_url` (opt) | Aloittaa OAuth2-kirjautumisprosessin ja ohjaa Googlen kirjautumissivulle. `redirect_url` määrittää paluuosoitteen kirjautumisen jälkeen. |
| `GET` | `/gcal/callback` | `code`, `state` | OAuth2-callback. Vaihtaa koodin access tokeniin. Palauttaa tokenin redirect URL:n parametrina (`gcal_access_token`). |
| `GET` | `/gcal/calendars` | `token` | Listaa käyttäjän kalenterit. Vaatii access tokenin. |
| `GET` | `/gcal/events` | `token`, `calendar_id` (opt) | Listaa tulevat 10 tapahtumaa valitusta kalenterista. |

---

## 3. Microsoft Graph API (Outlook)

Tiedosto: `api/graph_api.py`
Polku: `/graph`

Tämä moduuli hoitaa Microsoft Outlook -kalenterin integraation.

| Metodi | Polku | Parametrit | Kuvaus |
| :--- | :--- | :--- | :--- |
| `GET` | `/graph/` | - | Tervetuloviesti. |
| `GET` | `/graph/login` | - | Aloittaa OAuth2-kirjautumisprosessin. |
| `GET` | `/graph/callback` | `code` | OAuth2-callback. Hakee access tokenin ja ohjaa takaisin frontendiin tokenin kera. |
| `GET` | `/graph/calendars` | `token` | Hakee käyttäjän kalenterit Outlookista. |
| `GET` | `/graph/events` | `token`, `calendar_id` (opt) | Hakee käyttäjän kalenteritapahtumat Outlookista. |

---

## 4. iCal API

Tiedosto: `api/ical_api.py`
Polku: `/ical`

Tämä moduuli lukee julkisia iCal (.ics) kalenteritiedostoja URL-osoitteesta.

| Metodi | Polku | Parametrit | Kuvaus |
| :--- | :--- | :--- | :--- |
| `GET` | `/ical/` | - | Tervetuloviesti. |
| `GET` | `/ical/events` | `url` | Lataa ja parsii tapahtumat annetusta iCal-URL:sta. Palauttaa tapahtumat listana. |

---

## 5. Maps & Liikenne API

Tiedosto: `api/maps_api.py`
Polku: `/maps`

Tämä on laaja moduuli, joka yhdistää HERE Mapsin, Digitrafficin, RainViewerin ja Open-Meteon palvelut.

### HERE Maps -toiminnot
| Metodi | Polku | Parametrit | Kuvaus |
| :--- | :--- | :--- | :--- |
| `GET` | `/maps/api/geocode` | `address` | Muuttaa osoitteen koordinaateiksi (geokoodaus). |
| `POST` | `/maps/api/route` | Body: `origin_lat`, `origin_lon`, `dest_lat`, `dest_lon`, ... | Hakee reitin kahden pisteen välillä, sisältäen etäisyyden, keston ja reittiviivan (polyline). |

### Digitraffic (Liikennevirasto)
| Metodi | Polku | Parametrit | Kuvaus |
| :--- | :--- | :--- | :--- |
| `GET` | `/maps/api/digitraffic/cameras` | `route_coords` | Hakee kelikamerat reitin varrelta. |
| `GET` | `/maps/api/digitraffic/messages` | `route_coords` | Hakee liikennehäiriötiedotteet reitin varrelta. |
| `GET` | `/maps/api/digitraffic/road-weather` | `route_coords` | Hakee tiesääasemat reitin varrelta. |
| `GET` | `/maps/api/digitraffic/vms` | `route_coords` | Hakee sähköiset opasteet (VMS) reitin varrelta. |
| `GET` | `/maps/api/digitraffic/maintenance` | `route_coords` | Hakee kunnossapitotehtävät (esim. auraus). |
| `GET` | `/maps/api/digitraffic/lam` | `route_coords` | Hakee liikenteen mittauspisteet (LAM). |
| `GET` | `/maps/api/digitraffic/road-weather/{id}/history` | `station_id` | Hakee tiesääaseman historiatiedot (demo). |

### Sääpalvelut (RainViewer & Open-Meteo)
| Metodi | Polku | Parametrit | Kuvaus |
| :--- | :--- | :--- | :--- |
| `GET` | `/maps/api/weather/rainviewer` | - | Hakee RainViewerin tutkakuva-aikaleimat ja palvelimen tiedot. |
| `GET` | `/maps/api/weather/closest-timestamp` | `target`, `timestamps` | Etsii lähimmän saatavilla olevan sääkuvan aikaleiman. |
| `GET` | `/maps/api/forecast/temperature` | `bbox`, `start_time`... | Hakee lämpötilaennusteen (grid) alueelle. |
| `GET` | `/maps/api/forecast/weather` | `bbox`, `start_time`... | Hakee sääsymbolien ennusteen (grid) alueelle. |

### Kalenteri (iCal integraatio Maps-moduulin sisällä)
| Metodi | Polku | Parametrit | Kuvaus |
| :--- | :--- | :--- | :--- |
| `GET` | `/maps/ical/events` | `url` | Hakee iCal-tapahtumat (vaihtoehtoinen reitti ical_api:lle). |

---

## 6. Weather API (Sääennusteet)

Tiedosto: `api/weather_api.py`
Polku: `/weather`

Tämä moduuli tarjoaa yksinkertaistetun sääennusteen kaupungeille ja reiteille.

| Metodi | Polku | Parametrit | Kuvaus |
| :--- | :--- | :--- | :--- |
| `GET` | `/weather/` | - | API info ja endpointit. |
| `GET` | `/weather/city` | `name`, `hours` | Sääennuste nimetylle kaupungille (tukee vain määriteltyjä kaupunkeja). |
| `GET` | `/weather/route` | `from`, `to`, `hours` | Sääennuste lähtö- ja määränpääkaupungeille. |
| `GET` | `/weather/point` | `lat`, `lon`, `hours` | Sääennuste mille tahansa koordinaattipisteelle. |
| `GET` | `/weather/route-coords` | `from_lat`, `from_lon`, `to_lat`, `to_lon`... | Sääennuste reitin alku- ja loppupisteelle koordinaattien perusteella. |
| `GET` | `/weather/cities` | - | Listaa tuetut kaupungit koordinaatteineen demo-käyttöä varten. |
