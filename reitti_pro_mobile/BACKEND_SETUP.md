# Backend API - Käynnistysohjeet

## Nopea käynnistys

### Vaihtoehto 1: Docker (SUOSITELTU)

```bash
cd c:\Users\samih\code\pingut-projekti-4
docker compose up -d api
```

Backend käynnistyy portissa **8000**.

### Vaihtoehto 2: Lokaalisti (Python)

```bash
cd c:\Users\samih\code\pingut-projekti-4

# Asenna riippuvuudet (jos ei ole vielä)
pip install uvicorn fastapi

# Käynnistä backend
cd api
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Tarkista että backend toimii

Avaa selaimessa: http://localhost:8000

Pitäisi näkyä:
```json
{
  "message": "Main API Gateway",
  "routes": { ... }
}
```

## Flutter-sovelluksen yhteys

Flutter-sovellus yhdistää automaattisesti backendiin kun se on käynnissä:
- **URL:** `http://localhost:8000`
- **Endpoint:** `/maps/route`

## Testaa yhteyttä

Kun backend on käynnissä, testaa Flutter-sovelluksessa:
1. Avaa http://localhost:8502
2. Syötä lähtö ja määränpää
3. Klikkaa "Hae reitti"
4. Reitin pitäisi latautua!

## Ongelmanratkaisu

### "Connection refused"
- Backend ei ole käynnissä
- Tarkista: `curl http://localhost:8000`

### "404 Not Found"
- Backend on käynnissä mutta endpoint puuttuu
- Tarkista API dokumentaatio: http://localhost:8000/docs

### CORS-virhe
- Backend tarvitsee CORS-asetukset
- Lisää `fastapi.middleware.cors` jos tarvitaan
