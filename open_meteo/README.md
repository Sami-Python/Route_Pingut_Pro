# Open-Meteo Sääkartta -testisovellus

Testisovellus sääennustetietojen visualisointiin interaktiivisella Suomen kartalla käyttäen Open-Meteo API:a, joka hyödyntää FMI:n HARMONIE-mallia.

## Ominaisuudet

- Lämpötilan visualisointi värikoodatulla kartalla (100 datapistettä)
- Sadetiedot ja säasymbolit (sade, lumi, räntä) (64 datapistettä)
- 6 tunnin ennuste valitusta ajanhetkestä
- Interaktiivinen aikaliukusäädin ennusteen animointiin
- Play/Pause -toiminto animaatiolle
- Min/Max/Keskiarvo -tilastot molemmille kartoille
- Zoomattava Suomen kartta
- Reaaliaikainen data Open-Meteo API:sta (ei vaadi API-avainta!)

## Miksi Open-Meteo FMI:n sijaan?

Open-Meteo tarjoaa merkittäviä etuja suoraan FMI:n API:in verrattuna:

1. **Ei autentikaatiota**: Toimii ilman API-avaimia
2. **JSON-muoto**: Helppo käsitellä verrattuna FMI:n XML/WFS-formaattiin
3. **Bulk-haku**: 100 pistettä yhdellä API-kutsulla vs. 100 erillistä kutsua
4. **Nopeus**: Merkittävästi nopeampi kuin FMI:n XML-parsinta
5. **Interpolointi**: Open-Meteo interpoloi datan valmiiksi tarkkoihin koordinaatteihin
6. **Luotettavuus**: Käyttää FMI:n HARMONIE-mallia taustalla, mutta palauttaa datan luotettavammin

## Teknologiat

### Backend
- **FastAPI**: REST API -kehys
- **Python 3.11**: Ohjelmointikieli
- **Open-Meteo API**: Säädatan lähde (käyttää FMI:n HARMONIE-mallia)
- **Numpy**: Gridilaskenta

### Frontend
- **Streamlit**: Käyttöliittymäkehys
- **PyDeck**: Karttojen visualisointi
- **Pandas**: Datan käsittely

### Infrastruktuuri
- **Docker**: Kontituksen hallinta
- **Docker Compose**: Monikonttiorkestraatio

## Projektin rakenne
```
testi_meteo/
├── backend/
│   ├── app.py                 # FastAPI-sovellus
│   ├── clients/
│   │   └── meteo_client.py    # Open-Meteo API -asiakas
│   ├── requirements.txt       # Python-riippuvuudet
│   └── Dockerfile             # Backend-kontin konfiguraatio
├── frontend/
│   ├── app.py                 # Streamlit-sovellus
│   ├── requirements.txt       # Python-riippuvuudet
│   └── Dockerfile             # Frontend-kontin konfiguraatio
├── scripts/
│   ├── setup_backend.sh       # Backend-asennusskripti
│   ├── setup_frontend.sh      # Frontend-asennusskripti
│   └── setup_all.sh           # Täydellinen asennusskripti
├── docker-compose.yml         # Konttiorkestraatio
└── README.md                  # Tämä tiedosto
```

## Edellytykset

- Docker ja Docker Compose asennettuna
- Python 3.11 (paikallista kehitystä varten)
- Internet-yhteys Open-Meteo API:n käyttöön
- Bash-komentotulkki (Git Bash Windowsissa, natiivi Linuxissa/Macissa)

## Asennus ja käynnistys

### Docker Composen käyttö (suositeltu)

1. Siirry projektin hakemistoon:
```bash
cd ~/code/projekti4/testi_meteo
```

2. Rakenna ja käynnistä kontit:
```bash
docker-compose up --build
```

3. Käytä sovellusta:
   - **Frontend-käyttöliittymä**: http://localhost:8001
   - **Backend API**: http://localhost:8081
   - **API-dokumentaatio**: http://localhost:8081/docs

4. Pysäytä kontit:
```bash
docker-compose down
```

### Paikallinen kehitys (ilman Dockeria)

#### Nopea asennus kaikelle

```bash
# Siirry projektin juureen
cd ~/code/projekti4/testi_meteo

# Tee skripteistä suoritettavia (Linux/Mac/Git Bash)
chmod +x scripts/*.sh

# Suorita täydellinen asennus
bash scripts/setup_all.sh
```

#### Backend

1. Luo virtuaaliympäristö ja asenna riippuvuudet:
```bash
cd backend
python3.11 -m venv .venv

# Linux/Mac:
source .venv/bin/activate

# Windows (Git Bash):
source .venv/Scripts/activate

pip install -r requirements.txt
```

2. Käynnistä backend:
```bash
python app.py
```

#### Frontend

1. Luo virtuaaliympäristö ja asenna riippuvuudet:
```bash
cd frontend
python3.11 -m venv .venv

# Linux/Mac:
source .venv/bin/activate

# Windows (Git Bash):
source .venv/Scripts/activate

pip install -r requirements.txt
```

2. Päivitä backend-URL tiedostossa `app.py`:
```python
BACKEND_URL = "http://localhost:8081"  # Muuta: "http://backend:8081" -> "http://localhost:8081"
```

3. Käynnistä frontend:
```bash
streamlit run app.py --server.port=8001
```

## API-päätepisteet

### Backend API

- `GET /` - Terveystarkistus
- `GET /api/forecast/temperature` - Hae lämpötilaennuste (100 pistettä, 10×10 grid)
- `GET /api/forecast/weather` - Hae säasymbolit ja sadetiedot (64 pistettä, 8×8 grid)
- `GET /api/forecast/precipitation` - Hae sadeennuste rajauslaatikolta
- `GET /api/forecast/point` - Hae yksityiskohtainen ennuste tietyille koordinaateille

Katso täydellinen API-dokumentaatio osoitteesta http://localhost:8081/docs kun backend on käynnissä.

## Datalähde

Tämä sovellus käyttää **Open-Meteo API:a**, joka hyödyntää Ilmatieteen laitoksen HARMONIE-mallia:
- API: https://open-meteo.com
- Lähdedata: FMI HARMONIE-malli
- Lisenssi: Open-Meteo on ilmainen ei-kaupalliseen käyttöön
- Alkuperäinen data: Creative Commons Nimeä 4.0 Kansainvälinen (CC BY 4.0)
- Vaadittu viittaus: "Open-Meteo (FMI HARMONIE-malli)"

### Open-Meteo edut

1. **Ei API-avainta**: Toimii suoraan ilman rekisteröitymistä
2. **Bulk-kyselyt**: Hae 100 pistettä yhdellä API-kutsulla
3. **JSON-formaatti**: Kevyt ja nopea verrattuna XML:ään
4. **Interpoloitu data**: Tarkat arvot tietyille koordinaateille
5. **Luotettava**: Käyttää samaa FMI:n HARMONIE-mallia kuin virallinen FMI API

## Konfiguraatio

### Lämpötilan väriasteikko

Lämpötilan värit määritellään tiedostossa `frontend/app.py`:
```python
TEMP_COLORS = {
    -30: [139, 0, 139],    # Violetti - erittäin kylmä
    -20: [0, 0, 255],      # Sininen - kylmä
    -10: [0, 191, 255],    # Vaaleansininen - pakkanen
    0: [173, 216, 230],    # Hyvin vaalea sininen - nollan tienoilla
    5: [255, 255, 255],    # Valkoinen - viileä
    10: [255, 255, 200],   # Vaaleankeltainen - lämmin
    15: [255, 255, 0],     # Keltainen - lämmin
    20: [255, 200, 0],     # Oranssinkeltainen - kuuma
    25: [255, 165, 0],     # Oranssi - erittäin kuuma
    30: [255, 100, 0],     # Tumma oranssi - äärimmäisen kuuma
    35: [255, 0, 0]        # Punainen - helleaalto
}
```

### Suomen rajauslaatikko

Oletuskattoalue (voidaan muuttaa sekä backendissa että frontendissa):
```python
FINLAND_BBOX = {
    "min_lon": 20.5,
    "min_lat": 59.5,
    "max_lon": 31.5,
    "max_lat": 70.1
}
```

### Grid-tiheykset

Määritelty tiedostossa `backend/clients/meteo_client.py`:
- **Lämpötila**: 10×10 = 100 pistettä
- **Sade**: 8×8 = 64 pistettä

### Ennusteen kesto

Maksimi ennuste on rajoitettu 6 tuntiin valitusta ajanhetkestä (määritettävissä tiedostossa `backend/app.py`).

## Ominaisuudet vs. FMI-versio

| Ominaisuus | FMI API | Open-Meteo |
|------------|---------|------------|
| API-avain | Ei vaadita | Ei vaadita |
| Dataformaatti | XML/WFS | JSON |
| Lämpötilapisteet | 22×22 = 484 | 10×10 = 100 |
| Sadepisteet | 15×15 = 225 | 8×8 = 64 |
| Bulk-haku | Ei (yksi piste/kutsu) | Kyllä (kaikki pisteet/kutsu) |
| Nopeus | Hidas (XML-parsinta) | Nopea (JSON) |
| Ennusteet tulevaisuuteen | Rajoitettu | Toimii hyvin |
| Animaatio | Ei toimi | Toimii |

## Tunnetut rajoitukset

1. **Grid-tarkkuus**: Käyttää harvempaa gridia (10×10 ja 8×8) tehokkuuden vuoksi
2. **Play-nappi**: Animaatio voi olla hidas hitailla yhteyksillä
3. **Datan välimuisti**: Välimuistia ei ole toteutettu
4. **Säätyypit**: Määritetään lämpötilan ja sateen perusteella (ei suoraa sääsymbolia API:sta)

## Vianmääritys

### Backend-yhteysvirhe
- Tarkista että backend-kontti on käynnissä: `docker ps`
- Varmista että backend on tavoitettavissa: `curl http://localhost:8081/`
- Tarkista lokit: `docker logs meteo-backend`

### Dataa ei näytetä
- Open-Meteo API saattaa olla tilapäisesti poissa käytöstä
- Tarkista backend-lokeista API-virheet
- Varmista internet-yhteys
- Kokeile valita eri ajanhetki

### Kartta ei lataudu
- Tarkista selaimen konsolista JavaScript-virheet
- Varmista että PyDeck on asennettu oikein
- Kokeila päivittää sivu

### Animaatio ei toimi
- Tarkista että dataa on saatavilla (katso Debug-paneeli)
- Varmista että aikapisteitä on enemmän kuin yksi
- Kokeila ladata data uudelleen "Hae säädataa" -napilla

## Asennusskriptit (paikallinen kehitys)

Projekti sisältää asennusskriptejä paikallisen kehitysympäristön asennuksen automatisointiin. Skriptit tukevat sekä Linuxia/Macia että Windowsia (Git Bash).

### Skriptien edellytykset

- Python 3.11 asennettuna ja PATH-muuttujassa
- Bash-komentotulkki (Git Bash Windowsissa, natiivi terminaali Linuxissa/Macissa)

### Asennusskriptien käyttö

#### Vaihtoehto 1: Asenna kaikki kerralla
```bash
# Siirry projektin juureen
cd ~/code/projekti4/pingut-projekti-4/open_meteo

# Tee skripteistä suoritettavia (Linux/Mac/Git Bash)
chmod +x scripts/*.sh

# Suorita täydellinen asennus
bash scripts/setup_all.sh
```

Tämä:
1. Luo `.venv`-hakemistot sekä backendiin että frontendiin
2. Asentaa kaikki Python-riippuvuudet
3. Valmistelee molemmat palvelut paikallista kehitystä varten
4. Tunnistaa käyttöjärjestelmän automaattisesti (Windows/Linux/Mac)

#### Vaihtoehto 2: Asenna vain backend
```bash
bash scripts/setup_backend.sh
```

Asennuksen jälkeen, aktivoi ja käynnistä:
```bash
cd backend

# Linux/Mac:
source .venv/bin/activate

# Windows (Git Bash):
source .venv/Scripts/activate

python app.py
```

#### Vaihtoehto 3: Asenna vain frontend
```bash
bash scripts/setup_frontend.sh
```

Asennuksen jälkeen, aktivoi ja käynnistä:
```bash
cd frontend

# Linux/Mac:
source .venv/bin/activate

# Windows (Git Bash):
source .venv/Scripts/activate

streamlit run app.py --server.port=8001
```

### Windows-tuki

Kaikki asennusskriptit tunnistavat automaattisesti käyttöjärjestelmän ja käyttävät oikeaa aktivointikomentoa:
- **Windows**: `.venv/Scripts/activate`
- **Linux/Mac**: `.venv/bin/activate`

## Kehitystyönkulku

### Dockerin kanssa (suositeltu)
1. Tee koodimuutoksia
2. Rakenna ja käynnistä uudelleen: `docker-compose up --build`
3. Testaa osoitteessa http://localhost:8001

### Ilman Dockeria (paikallinen)
1. Suorita asennusskriptit kerran: `bash scripts/setup_all.sh`
2. Käynnistä molemmat palvelut eri terminaaleissa
3. Tee koodimuutoksia
4. Palvelut lataavat automaattisesti uudelleen (Streamlit ja Uvicorn valvovat muutoksia)
5. Testaa osoitteessa http://localhost:8001

## Vertailu FMI-versioon

Tämä Open-Meteo-versio toimii rinnakkain alkuperäisen FMI-version kanssa:

| Palvelu | Frontend | Backend |
|---------|----------|---------|
| FMI | http://localhost:8000 | http://localhost:8080 |
| Open-Meteo | http://localhost:8001 | http://localhost:8081 |

Molemmat voidaan käynnistää samaan aikaan eri porteissa vertailua varten!

## Lisenssit

- **Sovellus**: Projektikoodi on vapaasti käytettävissä
- **Data**: Open-Meteo (FMI HARMONIE-malli) - CC BY 4.0
- **Riippuvuudet**: Katso kunkin kirjaston omat lisenssit

## Tekijätiedot

Testisovellus Open-Meteo API:n ja FMI:n HARMONIE-mallin käyttöön Suomen sääennusteiden visualisoinnissa.
