# Sami - Oppimispäiväkirja

## 2025-12-10 - Flutter Mobile App Kehitys

### Työaika
- **Aloitus:** 20:00
- **Lopetus:** 23:07
- **Yhteensä:** ~3 tuntia

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
