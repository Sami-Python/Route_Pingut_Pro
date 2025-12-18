# Reitti Pro Mobile - Dokumentaatio

## Yleiskatsaus
Reitti Pro Mobile on Flutterilla toteutettu mobiilisovellus, joka tarjoaa käyttäjille reittisuunnittelua ja reaaliaikaista liikennetietoa. Sovellus hyödyntää Pingut-projektin backend-rajapintaa datan hakemiseen.

**Tärkeimmät ominaisuudet:**
- Reittihaku ja vaihtoehtoiset reitit
- Liikennetilanteen visualisointi (HERE Traffic)
- Kelikamerat ja tiesääasemat reitin varrella
- Sadekartta (RainViewer)
- **Matkan sää:** Sääikonit reitin varrella (aika-arvioon perustuva ennuste)
- **Älykkäät varoitukset:** Varoittaa rankkasateesta, liukkaudesta ja myrskystä reitillä ⚠️
- **Asetukset:** Koti-osoitteen tallennus ja pikavalinta
- **Brändätty lataus:** Pyörivä pingviini-animaatio 🐧

## Arkkitehtuuri

Sovellus noudattaa kerrosarkkitehtuuria (Layered Architecture) ja käyttää **Riverpod**-kirjastoa tilanhallintaan.

### Hakemistorakenne (`lib/`)
- **`core/`**: Sovelluksen ytimen yleiset osat.
    - `router/`: Navigaatio (GoRouter).
    - `theme/`: Sovelluksen ulkoasu ja teemat.
- **`data/`**: Tiedonhaku ja ulkoiset palvelut.
    - `services/`: API-clientit (Dio) backend-kommunikaatioon.
- **`presentation/`**: Käyttöliittymä.
    - `screens/`: Sovelluksen näkymät (esim. Kartta, Haku).
    - `widgets/`: Uudelleenkäytettävät UI-komponentit.
- **`main.dart`**: Sovelluksen käynnistyspiste ja alustukset.

### Teknologiat
- **Flutter & Dart**: Kehitysalusta ja kieli.
- **Riverpod**: Tilanhallinta ja riippuvuuksien injektointi.
- **Dio**: HTTP-pyynnöt backendiin.
- **Flutter Map**: Karttakomponentti (OpenStreetMap/HERE tiilet).

## Käynnistysohjeet

### 1. Esivaatimukset
- Flutter SDK asennettuna (`flutter doctor` tarkistus).
- Backend-palvelin käynnissä (oletus: `http://localhost:8000` tai verkko-IP).

### 2. Konfiguraatio (.env)
Varmista, että hakemistossa `reitti_pro_mobile/assets/` on tiedosto `.env`.
Sen sisällön tulee vastata backendin osoitetta:
```ini
API_URL=http://<TIETOKONEESI_IP>:8000
```
*Huom: Emulaattorissa `localhost` viittaa emulaattoriin itseensä, joten käytä tietokoneen lähiverkon IP-osoitetta (esim. 192.168.x.x).*

### 3. Käynnistys
Aja sovellus komentoriviltä projektin juuressa (`reitti_pro_mobile/`):

**Debug-tila (kehitys):**
```bash
flutter run
```

**Release-tila (optimisoitu):**
```bash
flutter run --release
```

**Huomiot:**
- Jos saat `WARNING: Invalid HTTP request` backendissä, varmista että sovellus käyttää `http://` eikä `https://`, ellei backendissä ole SSL käytössä.

### 4. Vianmääritys

**Backend ei vastaa puhelimelle (Connection Timeout):**
- Varmista, että backend on käynnistetty kuuntelemaan `0.0.0.0`. Oletus `uvicorn` kuuntelee vain `localhost`.
- Käytä komentoa:
  ```powershell
  .venv\Scripts\python -m uvicorn api.main:app --reload --host 0.0.0.0
  ```
- Varmista, että `.venv` on aktiivinen tai käytä koko polkua pythoniin, jotta `msal` ym. kirjastot löytyvät.

**Android-sovellus kaatuu käynnistyksessä:**
- Tarkista `AndroidManifest.xml`. Android 10+ vaatii `ACCESS_BACKGROUND_LOCATION` ja `FOREGROUND_SERVICE` luvat `geolocator`-pluginille, vaikka sovellus olisi "vain" foregroundissa.
