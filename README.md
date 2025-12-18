# Tienkäyttäjän Apuri

Matkasuunnittelutyökalu joka yhdistää kalenterit, reitityksen ja sääennusteet yhdeksi käyttöliittymäksi. Opiskelijoille ja autoilijoille suunniteltu sovellus, joka auttaa optimoimaan matkan ajankohdan sää- ja liikennetietojen perusteella.

## Arkkitehtuuri lyhyesti

Projekti koostuu kolmesta Docker-kontista:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Streamlit  │────▶│   FastAPI    │────▶│  Ext. APIs  │
│ (Localhost) │     │ (Localhost)  │     │   (Integr.) │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  MkDocs      │
                    │  (Localhost) │
                    └──────────────┘
```

### Servicet

- streamlit - Käyttöliittymä
- api - Backend API (FastAPI)
- docs - Dokumentaatio (MkDocs + Nginx)

**Ulkoiset integraatiot**

- HERE Maps API - Reititys ja geokoodaus
- Open-Meteo - Sääennusteet
- Digitraffic - Kelikamerat, tiesää, LAM, häiriöt
- Microsoft Graph - Outlook-kalenteri
- iCal - Kalenteri-integraatio


## Tech Stack

Backend:
- Python 3.11
- FastAPI + Uvicorn
- Requests (HTTP-kutsut)

Frontend:
- Streamlit
- PyDeck (kartta)

Infra:
- Docker + Docker Compose
- Nginx (dokumentaatio)

## Pika-aloitus

- Docker & Docker Compose
- API-avaimet (katso .env osio)

**Käynnistys**

```bash
# Kloonaa repo
git clone <repo-url>
cd pingut-projekti-4

# Luo .env tiedosto (katso alla)
cp .env.example .env
# Muokkaa .env - lisää API-avaimet

# Käynnistä servicet
docker compose up --build -d

# Tarkista lokeja
docker compose logs -f
```

### Servicet käynnissä

- Streamlit UI: http://localhost:8501
- FastAPI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dokumentaatio: http://localhost:80

## Ympäristömuuttujat

Luo .env tiedosto projektin juureen:

```bash
# HERE Maps
HERE_API_KEY=your_here_api_key

# Mapbox (karttatiilet)
MAPBOX_TOKEN=your_mapbox_token

# Microsoft Graph (Outlook-kalenteri)
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret

# Google (kalenteri, valinnainen)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Aikavyöhyke
TZ=Europe/Helsinki
```

**Huom:** .env on .gitignore:ssa - älä commitoi API-avaimia.

## Testit

Yksikkötestit sijaitsevat debug/ kansiossa.

## API-dokumentaatio

FastAPI:n automaattinen dokumentaatio:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Työskentely

```bash
# Pysäytä servicet
docker compose down

# Rebuild yksittäinen service
docker compose build api
docker compose up -d api

# Katso lokit
docker compose logs -f streamlit

# Puhdista kaikki
docker compose down --volumes --remove-orphans
```


