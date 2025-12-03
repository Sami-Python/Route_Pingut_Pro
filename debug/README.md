# Debug-työkalut

Tämä kansio sisältää debug- ja testaustyökaluja projektin kehitykseen.

## Tiedostot

### API-testit
- **API_test.py** - Testaa HERE API:n toimintaa (geokoodaus, reititys)
- **API_digi_test.py** - Testaa Digitraffic API:n toimintaa (kamerat, tiedotteet)

### Säätiilien testaus
- **scan_rain.py** - Skannaa RainViewer-tiiliä ja tarkistaa onko niissä sadetta
- **repro_rain.py** - Toinen säätiilien testaustyökalu
- **debug_headers.py** - Testaa HTTP-headereita API-kutsuissa

## Käyttö

Kaikki skriptit ajetaan projektin juuresta:

```bash
# Testaa HERE API
python debug/API_test.py

# Testaa Digitraffic API
python debug/API_digi_test.py

# Skannaa säätiiliä
python debug/scan_rain.py
```

## Huomiot

- Nämä työkalut eivät ole osa tuotantokoodia
- Vaativat `.env`-tiedoston API-avaimilla
- Käytä debuggaukseen ja kehitykseen
