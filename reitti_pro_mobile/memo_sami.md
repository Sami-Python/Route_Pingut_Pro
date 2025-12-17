# Sami - Oppimispäiväkirja

## 2025-12-10 - Flutter Mobile App Kehitys

### Työaika
- **Aloitus:** 20:00
- **Lopetus:** 23:07
- **Yhteensä:** ~3 tuntia

source .venv/Scripts/activate
streamlit: uvicorn api.main:app --reload
PowerShell Android: flutter run
*Bash Android: uvicorn api.main:app --reload --host 0.0.0.0*

uuden version työntö puhelimeen PowerShell-> 
\reitti_pro_mobile> 
flutter run --release


Gitlab <-> GitHub
Siirretään GitLab sivuun nimelle "gitlab":
```git remote rename origin gitlab```
Nimetään sinun GitHub-yhteytesi "originiksi" (eli oletukseksi):
```git remote rename mygithub origin```
Pushataan nykyinen flutter-haara GitHubiin ja tallennetaan asetus:
```git push -u origin flutter```

GitHub on nyt origin. Kun jatkossa kirjoitat git push, koodi menee sinne.

GitLab on nyt nimellä gitlab. Se on tallessa, mutta sinne ei mene mitään, ellet erikseen komenna 
```git push gitlab flutter```



### Tehdyt tehtävät

#### 1. Flutter SDK Asennus
- Ladattu ja asennettu Flutter SDK (1.2 GB)
- Lisätty PATH-ympäristömuuttujaan
- Tarkistettu asennus: `flutter doctor`
- **Versio:** Flutter 3.16.0, Dart 3.2.0

#### 2. Flutter-projektin luonti
- Luotu `reitti_pro_mobile` projekti
- Määritetty riippuvuudet (`pubspec.yaml`):
  - `flutter_map` - Karttanäkymä
  - `dio` - HTTP-pyynnöt
  - `flutter_riverpod` - State management
  - `go_router` - Navigointi
  - `geolocator` - GPS-sijainti

#### 3. Projektin rakenne
Toteutettu Clean Architecture -rakenne:
```
lib/
├── main.dart
├── core/
│   ├── theme/app_theme.dart
│   └── router/app_router.dart
├── data/
│   └── services/api_client.dart
└── presentation/
    └── screens/
        ├── home_screen.dart
        ├── map_screen.dart
        └── route_details_screen.dart
```

#### 4. UI-toteutus
- **HomeScreen:** Reittihaku-lomake
  - Lähtö/määränpää-kentät
  - GPS-sijainnin haku
  - Päivämäärä/aika-valitsimet
  - Saapumis/lähtöaika-toggle
- **MapScreen:** Karttanäkymä
  - flutter_map integraatio
  - Lähtö/määränpää-markerit
  - Reitin polyline
  - Zoom-kontrollit
- **Material 3 Design** teema

#### 5. Backend-integraatio (osittain)
- Yhdistetty olemassa olevaan FastAPI-backendiin
- Luotu API-client (Dio)
- **Ongelma:** Web-versio ei tue API-kutsuja (CORS)
- **Ratkaisu:** Demo-tila ilman API:a

#### 6. Ongelmanratkaisu
- **Flutter PATH-ongelma:** Vaihdettu Bash → PowerShell
- **Android SDK puuttuu:** Käytetty Chrome (web-versio)
- **Puuttuvat asset-kansiot:** Luotu tarvittavat kansiot
- **API-yhteensopivuus:** Toteutettu demo-tila
- **Hot reload -ongelmat:** Käytetty hot restart (R)

### Oppimiskokemukset

#### Uudet teknologiat
1. **Flutter & Dart**
   - Ensimmäinen Flutter-projekti
   - Widget-pohjainen arkkitehtuuri
   - State management (Riverpod)
   - Hot reload -kehitys

2. **flutter_map**
   - Karttatiilien lataus
   - Markerit ja polyline
   - Kameran hallinta

3. **Cross-platform kehitys**
   - Yksi codebase → Web, Android, iOS
   - Platform-specific haasteet

#### Haasteet ja ratkaisut

**Haaste 1: Flutter-asennus**
- PATH-muuttuja ei päivittynyt Bash-terminaalissa
- Ratkaisu: PowerShell-terminaalin käyttö

**Haaste 2: Web vs. Native**
- API-kutsut eivät toimineet web-versiossa
- Ratkaisu: Demo-tila kovakoodatuilla arvoilla

**Haaste 3: Hot reload**
- Muutokset eivät päivittyneet aina
- Ratkaisu: Hot restart (R) tai täysi uudelleenkäynnistys

#### Oivallukset

1. **Flutter on nopea kehittää**
   - Hot reload nopeuttaa kehitystä merkittävästi
   - Widget-rakenne on looginen
   - Dokumentaatio on hyvä

2. **Web-versio on hyvä kehitykseen**
   - Ei tarvitse emulaattoria/laitetta
   - Nopea testaus selaimessa
   - Debuggaus helpompaa

3. **Clean Architecture toimii**
   - Selkeä rakenne helpottaa kehitystä
   - Koodin uudelleenkäyttö
   - Testattavuus paranee

### Tulokset

✅ **Toimii:**
- Reittihaku-lomake
- GPS-sijainnin haku
- Demo-reitin lataus
- Karttanäkymä lähtö/määränpää-pisteillä
- Navigointi näkymien välillä

❌ **Ei vielä toiminnassa:**
- Oikea reitti-API (HERE Maps)
- Digitraffic-data
- AI-analyysi
- Android/iOS-versiot

### Seuraavat askeleet

1. **API-integraation korjaus**
   - CORS-asetusten lisäys backendiin
   - Oikean reitin haku HERE Maps API:sta

2. **Reitin näyttö**
   - Oikeat reittipisteet (ei suora viiva)
   - Tien mukainen reitti

3. **Digitraffic-integraatio**
   - Kelikamerat kartalla
   - Tiesää-tiedot
   - Liikennetiedotteet

4. **Android APK**
   - Rakentaminen ja testaus
   - Asennus puhelimeen

### Ajankäyttö

| Tehtävä | Aika |
|---------|------|
| Flutter-asennus | 45 min |
| Projektin luonti | 30 min |
| UI-toteutus | 60 min |
| Ongelmanratkaisu | 45 min |
| API-yritykset | 30 min |
| Dokumentointi | 10 min |
| **Yhteensä** | **~3h 20min** |

### Tekninen yhteenveto

**Käytetyt työkalut:**
- Flutter 3.16.0
- Dart 3.2.0
- VS Code + Flutter extension
- PowerShell
- Chrome DevTools

**Riippuvuudet:**
- flutter_map: 6.1.0
- dio: 5.4.0
- flutter_riverpod: 2.4.9
- go_router: 13.0.0
- geolocator: 11.0.0

**Koodirivit:** ~800+  
**Tiedostot:** 15+  
**Commitit:** 0 (ei vielä versionhallinnassa)

### Reflektio

Päivä oli intensiivinen mutta antoisa. Flutter osoittautui yllättävän helpoksi oppia, vaikka se oli täysin uusi teknologia. Hot reload -ominaisuus on uskomaton - muutokset näkyvät välittömästi ilman uudelleenkäynnistystä.

Suurin haaste oli web-version rajoitukset API-kutsujen kanssa. Tuotannossa tämä ei ole ongelma, koska sovellus ajetaan Android/iOS-laitteilla, mutta kehitysvaiheessa se hidasti etenemistä.

Olen tyytyväinen tulokseen - toimiva UI ja navigointi on hyvä pohja jatkokehitykselle. Seuraavalla kerralla keskityn API-integraation korjaamiseen ja oikean reitin näyttämiseen.

**Kokonaisarvio:** 8/10 - Hyvä edistyminen, mutta API-integraatio jäi kesken.

## 2025-12-11 - Backend-korjaukset ja API-integraatio

### Työaika
- **Aloitus:** 11:00
- **Lopetus:** 12:00
- **Yhteensä:** ~1 tunti

### Tehdyt tehtävät

#### 1. Backendin Zombie-prosessit ja Portti 8000
- **Ongelma:** Backend ei käynnistynyt, virhe `[Errno 10048] address already in use`.
- **Syy:** Vanhat Python-prosessit olivat jääneet taustalle roikkumaan ja varasivat portin 8000.
- **Ratkaisu:** Pakotettiin alas kaikki Python-prosessit (`taskkill /F /IM python.exe`) ja varmistettiin portin vapautuminen `netstat`illa.

#### 2. Geocoding API (404 Not Found)
- **Ongelma:** Sovellus sai 404-virheen hakiessa osoitetta.
- **Syy:** Mobiilisovellus yritti kutsua vanhaa polkua `/maps/geocode`, mutta käynnissä ollut (vanhentunut) palvelin vastasi vain polkuun `/maps/api/geocode`.
- **Ratkaisu:** Palautettiin backend ja frontend käyttämään yhtenäistä `/maps/geocode` -rakennetta ja käynnistettiin palvelin uudelleen oikeasta `api/main.py` -tiedostosta.

#### 3. Reititys API (405 Method Not Allowed & 400 Bad Request)
- **Ongelma 1:** Reittihaku epäonnistui `405 Method Not Allowed`.
  - **Syy:** Client käytti `GET`-pyyntöä, mutta backend vaatii `POST`.
  - **Ratkaisu:** Muutettiin `api_client.dart` käyttämään `POST`-metodia.
- **Ongelma 2:** Tämän jälkeen tuli `400 Bad Request` HERE API:lta.
  - **Syy 1:** Backend käytti vanhentunutta parameteria `routingMode="fastest"` (HERE v8 vaatii `"fast"`).
  - **Syy 2:** Aikaleimat sisälsivät mikrosekunteja, joita HERE API ei hyväksy.
  - **Ratkaisu:** Korjattiin `here_client.py` käyttämään oikeita parametreja ja strippaamaan mikrosekunnit.

#### 4. Uvicorn Logging -kaatuminen
- **Ongelma:** Palvelin kaatui käynnistyksessä virheeseen `'PrintLogger' object has no attribute 'isatty'`.
- **Syy:** Kustomoitu logger-luokka ei toteuttanut `isatty`-metodia, jota Uvicorn tarvitsee väritetyn tulosteen päättelyyn.
- **Ratkaisu:** Lisättiin puuttuva metodi `api/logger.py`-tiedostoon.

### Tulokset
✅ **Backend pyörii vakaasti** portissa 8000.
✅ **Geocoding toimii** (Helsinki -> 60.17...).
✅ **Reititys toimii** (Reittipisteet ja polyline saadaan HERE API:sta).
⏳ **Kesken:** AI-analyysi ja Digitraffic-visualisointi (siirretty iltaan).

### Iltapäivä & Ilta (klo 18:00 - 20:45)

#### Tehdyt tehtävät

1. **Digitraffic-integraatio (Valmis)**
   - Toteutettiin backend-endpointit (`/digitraffic/...`) tukemaan sekä reitti- että sijaintipohjaisia hakuja.
   - Lisättiin `flexpolyline`-tuki tarkkaa reittisuodatusta varten -> kamerat ja sääasemat näkyvät nyt vain juuri reitin varrella.
   - Toteutettiin mobiilissa "Tasot" (Layers) -valikko:
     - Kelikamerat
     - Tiesääasemat
     - Liikennetiedotteet (varoitukset)
     - HERE Traffic Flow (liikenneruuhkat)

2. **Mini-Map Etusivulle**
   - Lisättiin `MiniMapWidget` etusivulle antamaan visuaalinen ilme ja nopea pääsy karttaan.

3. **Laadunvarmistus**
   - Korjattiin `getWeatherCameras` tyyppivirhe (Map vs List).
   - Varmennettiin, että data latautuu oikein sekä reitillä että vapaassa selaustilassa.

#### Tulokset
✅ Sovellus on nyt visuaalisesti näyttävä ja dataa on runsaasti.
✅ Reittihaku tuo aidosti hyödyllistä, reittiin sidottua dataa.

### Seuraavat askeleet (Phase 3)
1. **AI-reittianalyysin integrointi**
   - Backend-endpointin luonti (`/analyze/route`).
   - UI-komponentit analyysin näyttämiseen.
2. **Android-testaus**
   - APK:n rakentaminen ja ajo oikealla laitteella.

## 2025-12-12 - Traffic Visualization Debugging & AI Planning

### Työaika
- **Aloitus:** 15:00
- **Lopetus:** 16:00
- **Yhteensä:** ~1 tunti

### Tehdyt tehtävät

#### 1. HERE Traffic Tiles 404/502 -ongelman ratkaisu
- **Ongelma:** "Liikennehäiriöt"-taso antoi 404- tai 502-virheitä backendin konsoliin.
- **Syy 1 (404):** Reititys/Mounting-ongelma. `maps_api.py` määritteli polun `/maps/tiles/...` ja se liitettiin `/maps` alle -> `/maps/maps/tiles/...`.
    - **Korjaus:** Poistettiin ylimääräinen prefix `maps_api.py`:stä.
- **Syy 2 (502):** Pythonin `requests` ei käsitellyt striimausta optimaalisesti upstream-virheiden kanssa.
- **Syy 3 (404 Upstream):** HERE API palauttaa 404, jos tiilellä ei ole liikennetietoa. Tämä on ominaisuus, ei virhe, mutta se sotki lokit.
    - **Korjaus:** Backend palauttaa nyt **läpinäkyvän 1x1 PNG-kuvan**, jos HERE vastaa 404. Sovellus pysyy tyytyväisenä.

#### 2. Digitraffic Häiriöiden Varmistus
- Varmennettu, että `traffic_messages_near_route` toimii logiikaltaan oikein.
- Häiriöiden puuttuminen johtui yksinkertaisesti siitä, että reitillä ei ollut aktiivisia tiedotteita testaushetkellä.

#### 3. HERE Route Incidents (Mobiili)
- Toteutettu logiikka, joka parsii reittidatasta `incidents`-listan.
- Piirretään kartalle punaisina varoitusmerkkeinä (🚫).
- Klikkaamalla näkee häiriön tyypin ja kuvauksen.

#### 4. Phase 3 Suunnittelu (AI Route Analysis)
- Suunniteltu arkkitehtuuri AI-analyysille:
    - **Backend:** `GeminiRouteAnalyzer` + `/analyze/route` endpoint.
    - **Frontend:** Info-kortti kartan alalaitaan + "Analysoi"-nappi.
    - **Tarkoitus:** Tiivistää reitin riskit ja sääolosuhteet käyttäjälle selkokielellä.

#### 5. Debuggaus & Korjaukset
- **CORS-virhe (XMLHttpRequest):** `api/main.py` puuttui globaali `CORSMiddleware`. Lisätty `allow_origins=["*"]`.
- **UI Assertion Failed (box.dart):** `RouteInfoCard` käytti `SizedBox(width: double.infinity)`, mikä aiheutti layout-virheen Pinossa (Stack). Vaihdettu `CrossAxisAlignment.stretch`.

### Tulokset
✅ Liikennehäiriöt (HERE) toimivat nyt ilman virheilmoituksia.
✅ Backend on vakaa ja "puhdas" debug-koodista.
✅ Selkeä suunnitelma seuraavaan vaiheeseen.

### Seuraavat askeleet
1. Toteuta `RouteInfoCard` mobiiliin (Stack-layout).
2. Integroi Gemini API backendiin.

## 2025-12-14 - AI Route Analyzer Testaus ja Ongelmat

### Työaika
- **Päivämäärä:** Lauantai 14.12.2025
- **Aika:** Iltapäivä/Ilta
- **Yhteensä:** ~2-3 tuntia

### Tehdyt tehtävät

#### 1. AI-analyysin testaus
- Testattiin AI-reittianalyysiä Flutter-sovelluksessa
- Havaittiin, että AI-analyysi ei toimi
- Tutkittiin eri Gemini-malleja:
  - `gemini-2.5-flash` - Ei toiminut (quota/model not found)
  - `gemini-flash-latest` - Ei toiminut aluksi
  - `gemini-2.0-flash-lite-preview-02-05` - Testattiin
  - `gemini-2.0-flash-001` - Testattiin

#### 2. Ongelmat
- AI-analyysi palautti virheitä
- Epäselvää, mikä malli toimii
- API-avain ja konfiguraatio epäselvä

### Tulokset
❌ AI-analyysi ei toiminut
⏳ Ongelma jäi ratkaisematta - siirretty seuraavaan päivään

## 2025-12-15 - AI Route Analyzer Korjaus

### Työaika
- **Päivämäärä:** Sunnuntai 15.12.2025
- **Aloitus:** 10:39
- **Lopetus:** 10:54
- **Yhteensä:** ~15 minuuttia (+ jatkuu)

### Tehdyt tehtävät

#### 1. Ongelman diagnosointi
- Tutkittiin AI-analyysin toimintaa systemaattisesti
- Löydettiin useita ongelmia:

**Ongelma 1: Backend-palvelin ei ollut käynnissä**
- API-kutsu epäonnistui: `Connection refused`
- Ratkaisu: Käynnistettiin backend-palvelin

**Ongelma 2: Duplikaatti endpoint `/analyze/route`**
- `api/maps_api.py` sisälsi kaksi samaa endpointia:
  - Rivi 251: Ensimmäinen määrittely (vaati `RouteResponse` Pydantic-mallin)
  - Rivi 421: Toinen määrittely (vaati `Dict[str, Any]`)
- FastAPI käytti vain ensimmäistä, mikä aiheutti 422-virheen
- Ratkaisu: Poistettiin ensimmäinen duplikaatti (rivit 251-271)

**Ongelma 3: Python cache**
- `__pycache__` -kansiot sisälsivät vanhaa koodia
- Ratkaisu: Tyhjennettiin cache-kansiot

#### 2. Testaus ja varmistus
- Luotiin testiskripti `debug/test_ai_endpoint.py`
- Testattiin Gemini-mallit: `gemini-flash-latest` toimii ✅
- Varmistettiin, että `google-generativeai` on asennettu
- Varmistettiin API-avaimen olemassaolo

#### 3. Korjaukset
- Poistettu duplikaatti endpoint `api/maps_api.py`:stä
- Tyhjennetty Python cache
- Dokumentoitu ongelma ja ratkaisu

### Tekninen yhteenveto

**Löydetyt ongelmat:**
1. Backend ei ollut käynnissä
2. Duplikaatti API-endpoint aiheutti 422 Unprocessable Entity -virheen
3. Python cache sisälsi vanhaa koodia

**Tehdyt korjaukset:**
- ✅ Poistettu duplikaatti endpoint
- ✅ Tyhjennetty cache
- ⏳ Backend täytyy käynnistää uudelleen muutosten aktivoimiseksi

**Toimivat komponentit:**
- ✅ Gemini API-avain konfiguroitu oikein
- ✅ `gemini-flash-latest` malli toimii
- ✅ `google-generativeai` paketti asennettu
- ✅ Backend-koodi korjattu

### Tulokset
✅ Ongelma diagnosoitu ja korjattu
✅ AI-analyysi toimii erinomaisesti!
✅ Flutter-sovelluksen UI-parannukset tehty

### Seuraavat askeleet (päivitetty klo 11:22)
1. ✅ Backend-palvelin uudelleenkäynnistetty
2. ✅ AI-analyysi testattu ja toimii
3. ✅ UI-parannukset toteutettu
4. ✅ Branding päivitetty

---

## 2025-12-15 (jatkuu) - UI-parannukset ja Branding

### Työaika
- **Aloitus:** 10:54
- **Lopetus:** 11:22
- **Yhteensä:** ~28 minuuttia

### Tehdyt tehtävät

#### 1. AI-analyysin testaus ja vahvistus
- ✅ AI-analyysi toimii erinomaisesti!
- Käyttäjä vahvisti toimivuuden
- Backend-palvelin käynnissä ja toimii

#### 2. UI-korjaukset ja parannukset

**Kelikameran kuvien näyttö:**
- Lisätty `loadingBuilder` - näyttää latausanimaation kuvan latautuessa
- Lisätty `errorBuilder` - näyttää virheilmoituksen jos kuva ei lataudu
- Lisätty `SingleChildScrollView` - mahdollistaa isompien kuvien scrollauksen
- Lisätty sijaintitieto (lat/lon) dialogiin
- Tiedosto: `map_screen.dart`

**Liikennehäiriöiden näyttö:**
- Korjattu toggle-toiminto kutsumaan `_fetchLayers()`
- Punaiset virhe-ikonit (HERE API) näkyvät nyt kartalla
- Tiedosto: `map_screen.dart`

#### 3. Branding-päivitys

**Sovelluksen nimi vaihdettu:**
- Vanha: "Reitti Pro"
- Uusi: "🐧 Pingut Reitti Pro"

**Päivitetyt tiedostot:**
- `main.dart` - Pääotsikko
- `home_screen.dart` - Etusivun otsikko
- `map_screen.dart` - Karttanäkymän otsikko

#### 4. Aloitussivun ominaisuuslista

**Muutos:**
- ❌ Poistettu: "Sääennusteet" (☁️)
- ✅ Lisätty: "AI reittinalyysi" (⭐)

**Lopullinen lista:**
- Interaktiivinen kartta
- Kelikamerat
- Tiesää
- Liikennetiedotteet
- AI reittinalyysi

#### 5. Digitraffic-tiedotteiden toiminnan varmistus

**Testaus:**
- Testattu API:n toimivuus suoraan
- Vahvistettu että backend palauttaa dataa oikein
- Testattu useilla reiteillä (Helsinki-Tampere, Turku-Kotka, Salo)

**Tulos:**
- ✅ API toimii oikein
- ✅ Flutter-koodi toimii oikein
- ℹ️ Ei aktiivisia häiriöitä testatuilla reiteillä = ei mitään näytettävää (normaalia!)

**Löydetyt aktiiviset häiriöt:**
- Salo (Tie 110) - siltatyöt
- Isojoki, Mikkeli, Kuopio, Lappeenranta, Hämeenlinna

### Tekninen yhteenveto

**Muokatut tiedostot:**
1. `reitti_pro_mobile/lib/presentation/screens/map_screen.dart`
   - Kelikameradialogi parannettu
   - Liikennehäiriöt-toggle korjattu
   - Otsikko päivitetty

2. `reitti_pro_mobile/lib/main.dart`
   - App title päivitetty

3. `reitti_pro_mobile/lib/presentation/screens/home_screen.dart`
   - Otsikko päivitetty
   - Ominaisuuslista päivitetty

**Luodut testiskriptit:**
- `debug/test_traffic_messages.py` - Digitraffic API:n testaus
- `debug/test_route_messages.py` - Reittipohjainen testaus
- `debug/test_point_messages.py` - Pistekohtainen testaus
- `debug/test_turku_kotka.py` - Turku-Kotka reitin testaus

### Tulokset

✅ **Kaikki toimii erinomaisesti:**
- AI-analyysi toimii täydellisesti
- Kelikamerakuvat latautuvat oikein
- Liikennehäiriöt näkyvät kartalla (kun niitä on)
- Branding päivitetty kaikkialla
- Aloitussivu heijastaa oikeita ominaisuuksia

### Oppimiskokemukset

**Flutter UI-kehitys:**
- `loadingBuilder` ja `errorBuilder` parantavat käyttökokemusta merkittävästi
- Toggle-toimintojen pitää kutsua päivitysfunktioita eksplisiittisesti
- SingleChildScrollView estää overflow-virheet

**API-integraatio:**
- Digitraffic palauttaa vain aktiiviset häiriöt
- Tyhjä tulos ei tarkoita virhettä - se tarkoittaa että kaikki on hyvin!
- Testaus eri alueilla auttaa ymmärtämään datan saatavuutta

**Branding:**
- Emoji-tuki toimii hyvin Flutter-sovelluksissa
- Johdonmukainen branding kaikissa näkymissä tärkeää

### Seuraavat kehityskohteet

1. **Android APK** - Rakentaminen ja testaus oikealla laitteella
2. **Lisää AI-ominaisuuksia** - Ehkä reittiehdotuksia tai vaihtoehtoisia reittejä
3. **Käyttäjäasetukset** - Tallenna suosikkipaikat, oletusasetukset
4. **Offline-tuki** - Karttatiilien välimuisti

### Reflektio

Päivä oli erittäin tuottelias! AI-analyysin korjaaminen oli tärkeä milestone - nyt sovellus tarjoaa todellista lisäarvoa käyttäjille. UI-parannukset tekevät sovelluksesta ammattimaisemman näköisen ja Pingut-branding antaa sille oman identiteetin.

Digitraffic-tiedotteiden "ongelma" osoittautui ominaisuudeksi - kun kartalla ei näy varoituksia, se tarkoittaa että reitti on turvallinen! Tämä on hyvä esimerkki siitä miten tärkeää on ymmärtää datan luonne ennen kuin päättelee että jotain on rikki.

**Kokonaisarvio:** 10/10 - Kaikki tavoitteet saavutettu ja enemmänkin!


## 15.12.2025 - Android APK ja "Quick Wins" 🐧🚀

### Tavoitteet
- [x] Android APK:n rakentaminen ja testaus
- [x] Backendin saaminen toimimaan lähiverkossa (oikea laite)
- [x] Suosikkipaikat (Tallenna/Lataa)
- [x] Reitin jakaminen (Share Sheet)

### Toteutetut muutokset

**1. Android ja Backend Infra**
- **Gradle päivitys:** 7.5 -> 8.3 + AGP 8.13.2. Tämä korjasi Java 21 yhteensopivuusongelmat.
- **Backend Importit:** Korjattu `ModuleNotFoundError` useassa tiedostossa (`api/main.py`, `graph_api.py`, `gcal_api.py`, `maps_api.py`) vaihtamalla suhteelliset importit absoluuttisiin (`from api.utils...`).
- **Verkkoasetukset:**
    - Backend käynnistyy nyt `0.0.0.0` (kuuntelee kaikkia), jotta puhelin saa yhteyden.
    - Mobiiliappi käyttää tietokoneen IP:tä `192.168.1.130` (Asetettu `.env` ja `assets/.env` tiedostoihin).
    - AndroidManifest.xml:ään lisätty `INTERNET` ja `ACCESS_FINE_LOCATION` oikeudet.

**2. UI & Ominaisuudet**
- **Branding:** Nimi päivitetty "🐧 Pingut AI Route Planner".
- **Suosikit:** Lisätty tähdet ⭐ lähtö/määränpää kenttiin. Klikkaamalla saa valita listasta.
- **Jako:** Reittikortissa on nyt "Jaa reitti" nappi, joka avaa puhelimen natiivin jakovalikon.

### Ongelmat ja Ratkaisut
- **APK ei toiminut aluksi:** Syynä oli `assets/.env` tiedosto, joka pakotti `localhost`-osoitteen. Korjattu osoittamaan lähiverkon IP:hen.
- **Backend ei käynnistynyt:** Pythonin importit hajosivat kun ajettiin juuresta. Korjattu lisäämällä `api.` etuliitteet.
- **Build-virheet:** CLI:n kautta tuli `jlink` virhe. Ratkaistu käyttämällä Android Studion build-työkalua.

### Lopputulos
APK asennettu fyysiseen laitteeseen ja **TOIMII!** Kartta latautuu, reitit löytyvät, AI analysoi ja suosikit tallentuvat.

**Kokonaisarvio:** 10/10 - Iso tekninen harppaus dev-ympäristöstä tuotantotyyppiseen testaukseen!


## 15.12.2025 (jatkuu) - Android Build, Vaihtoehtoiset Reitit ja Bugikorjaukset 📱🛠️

### Työaika
- **Aloitus:** 15:30
- **Lopetus:** 20:00
- **Yhteensä:** ~4.5 tuntia

### Tehdyt tehtävät

#### 1. Vaihtoehtoiset Reitit (Multiple Routes) 🛣️
- **Backend:** `maps_api.py` tukee nyt `alternatives` parametria ja palauttaa listan reiteistä.
- **Frontend:**
  - Kartta piirtää pääreitin (sininen/paksu) ja vaihtoehtoiset reitit (harmaa/katkoviiva/läpinäkyvä).
  - Yläreunassa "Reitti 1", "Reitti 2" -valintanapit (Chips).
  - Valinta päivittää kartan lisäksi myös **infokortin tiedot** (matka, aika) reaaliajassa.
  - Visuaalisuutta parannettu: vaihtoehtoiset reitit selkeämmin erottuvia (opacity 0.8, width 5.0).

#### 2. Android APK Build & Fixes 🔧
- **Build-ongelmat ratkottu:**
  - **MSAL:** `ModuleNotFoundError` korjattu asentamalla msal backendiin.
  - **NDK:** Määritelty versio `27.0.12077973` build.gradleen.
  - **Proguard:** Luotu puuttuva `proguard-rules.pro`.
  - **Code Generation:** Ajettu `build_runner` korjaamaan `flutter clean`in poistamat tiedostot.
  - **Versioning:** Nostettu versio `1.0.0+2` asennuskonfliktien ratkaisemiseksi.
  - **Syntaksivirheet:** Korjattu `map_screen.dart`:in ylimääräiset ja puuttuvat aaltosulkeet.

#### 3. Testaus & Käyttöönotto 🚀
- **Emulaattori/Laite:** Debugattu USB-yhteyden kautta (`flutter run --release`).
- **Asennusongelmat:** "App not installed" selätetty (versionosto + adb install).
- **Lopputulos:** Toimiva release-build fyysisessä laitteessa, jossa toimivat:
  - Kartta & Reitit
  - AI-analyysi
  - Kelikamerat
  - Reitin valinta

### Tulokset
✅ Sovellus on täysin toimiva ja asennettavissa.
✅ Käyttäjä voi valita parhaan reitin (nopea vs. lyhyt).
✅ UI reagoi valintoihin oikein.

### Seuraavat askeleet
- Koodin siivous ja refaktorointi tarvittaessa.
- Mahdolliset lisäominaisuudet (esim. tarkemmat ruuhkatiedot reiteille).

## 17.12.2025 - Streamlit Dockeraus, Android-korjaukset ja Yhteysongelmat 🛠️📱🐳

### Työaika
- **Aloitus:** 15:30
- **Lopetus:** 20:00
- **Yhteensä:** ~4.5 tuntia

### Tehdyt tehtävät

#### 1. Streamlit App & Docker 🐳
- **Tavoite:** Saada `strmlt`-sovellus (erityisesti `main.py` ja `ai_route_demo.py`) toimimaan sekä lokaalisti että Dockerissa.
- **Haaste:** `here-streamlit` Docker-image oli vanhentunut -> puuttui `main.py` ja uudet riippuvuudet (`streamlit-calendar`, `python-dotenv`).
- **Ratkaisu:**
  - Ajettiin kontti mounttaamalla paikallinen kansio (`-v c:/...:/app`), jolloin koodimuutokset näkyvät heti.
  - Asennettiin puuttuvat paketit ajonaikaisesti kontin sisään.
  - Varmistettiin, että `ai_route_demo.py` on navigaatiossa mukana.

#### 2. Android App Kaatuminen (Geolocator) 📍💥
- **Ongelma:** Sovellus kaatui heti käynnistyksessä tai fokuksen kadotessa ("Lost connection to device"). Lokit: `Detaching Geolocator`.
- **Syy:** Android 10+ vaatii `ACCESS_BACKGROUND_LOCATION` -luvan, jos sijaintia käytetään backgroundissa, ja `FOREGROUND_SERVICE` -luvan palveluille. Nämä puuttuivat manifestista.
- **Ratkaisu:** Lisättiin puuttuvat luvat `android/app/src/main/AndroidManifest.xml`:ään.
- **Oppiminen:** Mobiilikehityksessä luvat ovat kriittisiä ja käyttöjärjestelmä tappaa sovelluksen armotta, jos ne puuttuvat.

#### 3. Backend Yhteysongelma (Android -> PC) 🔌
- **Ongelma:** Android-sovellus sai `Connection timeout` -virheen, vaikka IP oli oikein (`192.168.1.130`).
- **Diagnostiikka:**
  - `netstat` paljasti, että backend kuunteli vain `127.0.0.1` (localhost), johon ulkoa ei pääse.
  - Lisäksi portissa 8000 roikkui "zombie"-prosessi.
  - Uudelleenkäynnistysyritys epäonnistui `ModuleNotFoundError: msal` -virheeseen.
- **Syy (MSAL):** `uvicorn`-komento ajettiin globaalista ympäristöstä, ei virtuaaliympäristöstä (`.venv`), jossa `msal` oli asennettuna.
- **Ratkaisu:**
  1. Tappoimme zombie-prosessit.
  2. Käynnistimme backendin **oikeasta ympäristöstä** ja **oikealla hostilla**:
     `.venv\Scripts\python -m uvicorn api.main:app --reload --host 0.0.0.0`
- **Oppiminen:** "It works on my machine" johtuu usein siitä, että kuunnellaan vain localhostia. Mobiilikehityksessä backendin pitää olla avoin verkkoon (`0.0.0.0`).

### Tulokset
✅ Streamlit app toimii Dockerissa ja lokaalisti.
✅ Android-sovellus pysyy pystyssä (ei kaadu).
✅ Android-sovellus saa yhteyden backendiin ja hakee reittejä/säätä.

### Seuraavat askeleet
- Koodin siivous.
- Mahdollisesti Docker-imagen uudelleenrakennus (`docker build`), jotta "purkkavirityksiä" ei tarvita.

## 17.12.2025 (jatkuu) - Phase 5: Viimeistely ja Julkaisu (Release) 🐧📦 ✨

### Työaika
- **Aloitus:** 20:00
- **Lopetus:** 20:30
- **Yhteensä:** ~30 min

### Tehdyt tehtävät

#### 1. "Quick Wins" & Ominaisuudet
- **Asetukset-näkymä (`SettingsScreen`):**
  - Lisätty uusi näyttö, jossa voi tallentaa kotiosoitteen (`SharedPreferences`).
  - Lisätty `/settings` reitti `GoRouter`iin.
- **Koti-pikavalinnat:**
  - Lähtö- ja määränpääkenttiin lisätty "Koti"-ikoni (🏠).
  - Yhdellä painalluksella täyttää tallennetun osoitteen.
- **Penguin Loader:**
  - Korvattu tylsä `CircularProgressIndicator` pyörivällä 🐧-emojilla `HomeScreen`:in hakupainikkeessa.
  - Luotu oma Widget `PenguinLoader`.

#### 2. Release Build (APK)
- **Versionosto:** Nostettu `pubspec.yaml` versio `1.0.0+3`.
- **Clean Build:** Ajettu `flutter clean` varmuuden vuoksi.
- **APK Luonti:** `flutter build apk --release`.
- **Tulos:** 21.8 MB APK-tiedosto (`app-release.apk`).

#### 3. Asennus
- **Komento:** `adb install -r build\app\outputs\flutter-apk\app-release.apk` (päivitysasennus).
- **Vianmääritys:** Jos `adb` ei löydy polusta, `flutter run --release` tekee saman asian (buildaa + asentaa).

### Tulokset
✅ Sovellus on nyt paljon henkilökohtaisempi (Koti-osoite).
✅ Latausanimaatio tuo "Pingut"-brändiä esiin.
✅ Tuotantoversio on asennettu ja toimii vakaasti.

### Seuraavat askeleet
- Käyttäjätestaus (meneekö reitit oikein kotiin?).
- Mahdollisesti iOS-build tulevaisuudessa.
