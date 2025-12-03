# Reitti Pro 🚗

Suomalainen reititys- ja liikennetietosovellus, joka yhdistää HERE API:n, Digitrafficin ja RainViewerin reaaliaikaiset tiedot.

## Ominaisuudet

### 🗺️ Streamlit-sovellus (app.py)
- **Dynaaminen reititys** HERE API:lla
- **3D-karttanäkymä** Pydeck-kirjastolla
- **Reaaliaikaiset häiriötiedot** (HERE + Digitraffic)
- **Sade-ennuste** koko Suomen alueelle (RainViewer)
- **Kelikamerat** reitin varrelta (Digitraffic)
- **Autoanimaatio** reitin varrella
- **GPS-sijainti** selaimesta
- **Korkeuprofiili** reitille

### 🚀 FastAPI Backend (api_server.py)
REST API reitti- ja liikennetiedoille:
- Geokoodaus (osoite → koordinaatit)
- Reitin haku ja optimointi
- Kelikamerat
- Liikennetiedotteet
- Tiesääasemat
- Muuttuvat opasteet (VMS)
- Kunnossapitotehtävät
- LAM-mittauspisteet
- Säätiilien metatiedot

## Asennus

### 1. Kloonaa repositorio
```bash
git clone https://gitlab.dclabra.fi/Sami/here_api.git
cd here_api
```

### 2. Luo virtuaaliympäristö
```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows
# tai
source .venv/bin/activate      # Linux/Mac
```

### 3. Asenna riippuvuudet
```bash
pip install -r requirements.txt
```

### 4. Konfiguroi API-avaimet
Luo `.env`-tiedosto projektin juureen:
```env
HERE_API_KEY=your_here_api_key
MAPBOX_TOKEN=your_mapbox_token
```

**API-avainten hankkiminen:**
- HERE API: https://developer.here.com/
- Mapbox: https://www.mapbox.com/

## Käyttö

### Streamlit-sovellus
```bash
streamlit run app.py --server.port 8502
```
Avaa selaimessa: http://localhost:8502

### FastAPI-palvelin
```bash
python api_server.py
```
- API: http://localhost:8000
- Swagger-dokumentaatio: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker
```bash
docker build -t reitti-pro .
docker run -p 8502:8502 --env-file .env reitti-pro
```

## Projektin rakenne

```
here_api/
├── app.py                    # Streamlit-sovellus
├── api_server.py             # FastAPI REST API
├── here_client.py            # HERE API -integraatio
├── digitraffic_client.py     # Digitraffic API -integraatio
├── weather_client.py         # RainViewer API -integraatio
├── requirements.txt          # Python-riippuvuudet
├── Dockerfile               # Docker-konfiguraatio
├── .env                     # API-avaimet (ei versionhallinnassa)
└── docs/                    # Dokumentaatio
    ├── app.md               # Sovelluksen kehityshistoria
    ├── here_api.md          # HERE API -ohje
    ├── fastapi_ohje.md      # FastAPI-ohje
    └── docker_ohje.md       # Docker-ohje
```

## Teknologiat

### Backend
- **Python 3.11+**
- **FastAPI** - REST API
- **Uvicorn** - ASGI-palvelin
- **Requests** - HTTP-pyynnöt
- **Shapely** - Geometrinen laskenta

### Frontend
- **Streamlit** - Web-sovelluskehys
- **Pydeck** - 3D-karttavisualisointi
- **Flexpolyline** - Reittiviivan dekoodaus

### API-integraatiot
- **HERE API** - Reititys ja geokoodaus
- **Digitraffic** - Kelikamerat ja liikennetiedotteet
- **RainViewer** - Sadekartat

## Dokumentaatio

Lisää dokumentaatiota löytyy `docs/`-kansiosta:
- [Sovelluksen kehitys](docs/app.md)
- [HERE API -ohje](docs/here_api.md)
- [FastAPI-ohje](docs/fastapi_ohje.md)
- [Docker-ohje](docs/docker_ohje.md)

## Kehitys

### Testaus
```bash
# API-testit
python debug/API_test.py
python debug/API_digi_test.py
```

### CI/CD
Projekti käyttää GitLab CI/CD:tä (`.gitlab-ci.yml`)

## Lisenssi

Projekti on kehitetty opetus- ja demonstraatiotarkoituksiin.

## Tekijät

- Sami - Pääkehittäjä

## Versiohistoria

- **v1.0** - Perusreititys ja kartta
- **v1.1** - Kelikamerat ja häiriötiedot
- **v1.2** - Sade-ennuste koko Suomelle
- **v1.3** - FastAPI REST API
- **v1.4** - Laajennettu Digitraffic-tuki (Tiesää, VMS, Kunnossapito, LAM) ja sääreititys
