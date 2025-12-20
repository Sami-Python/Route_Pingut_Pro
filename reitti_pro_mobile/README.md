# 🐧 Pingut Reitti Pro Mobile

**Pingut Reitti Pro** on autoilijan älykäs matkakumppani, joka yhdistää reittioppaan, reaaliaikaiset kelikamerat, liikenssätiedot ja tekoälypohjaisen reittianalyysin yhteen helppokäyttöiseen mobiilisovellukseen.

## ✨ Ominaisuudet

### 🗺️ Reititys & Kartta
- **Reittihaku:** Tehokas reittihaku HERE Maps API:n avulla.
- **Interaktiivinen kartta:** OpenStreetMap-pohjainen kartta (Flutter Map).
- **Vaihtoehtoiset reitit:** Näyttää jopa 3 reittivaihtoehtoa valittavaksi.
- **Reitin jakaminen:** Jaa reittisi helposti ystäville.

### 🚗 Liikenne & Olosuhteet
- **Kelikamerat:** Reaaliaikaiset kuvat reitin varrelta (Digitraffic).
- **Tiesääasemat:** Tarkat säätiedot tieltä.
- **Liikennetiedotteet:** Varoitukset tietyöistä, onnettomuuksista ja ruuhkista.
- **LAM-pisteet:** Ajoneuvojen määrät ja keskinopeudet mittauspisteistä.

### 🤖 Älykäs Analyysi
- **AI-reittianalyysi:** Google Gemini 1.5 Flash analysoi reitin olosuhteet, sään ja liikenteen, ja antaa sanallisen yhteenvedon ja suosituksia.

### 📱 Käyttökokemus
- **Suosikkipaikat:** Tallenna usein käytetyt kohteet (Koti, Työ, jne.) nopeaa hakua varten.
- **Material 3 Design:** Moderni ja selkeä käyttöliittymä.
- **Android APK:** Valmis tuotantokelpoinen Android-sovellus.

---

## 🛠️ Asennus ja Käynnistys

### Vaatimukset
- **Flutter SDK** (3.x tai uudempi)
- **Python 3.9+** (Backendille)
- **Android Studio / VS Code**
- **Android-laite tai emulaattori**

### 1. Backendin Käynnistys
Sovellus tarvitsee toimiakseen Python-pohjaisen backendin (Pingut API).

**Vaihtoehto A: Manuaalinen käynnistys (Suositeltu kehitykseen)**
```bash
# Projektin juuressa (c:\Users....)
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Vaihtoehto B: Docker**
```bash
docker compose up -d api
```

### 2. Mobiilisovelluksen Käynnistys

1. **Siirry mobiilikansioon:**
   ```bash
   cd reitti_pro_mobile
   ```

2. **Luo `.env` tiedosto:**
   Luo tiedosto `reitti_pro_mobile/.env` ja määritä seuraavat muuttujat:
   ```env
   # Android-emulaattorille:
   API_URL=http://10.0.2.2:8000
   
   # Oikealle laitteelle (vaihda IP-osoite tietokoneesi lähiverkon IP:ksi):
   # API_URL=http://192.168.1.X:8000
   
   HERE_API_KEY=<sinun_here_api_key>
   MAPBOX_TOKEN=<sinun_mapbox_token> 
   GEMINI_API_KEY=<sinun_gemini_api_key>
   ```

3. **Asenna riippuvuudet:**
   ```bash
   flutter pub get
   ```

4. **Käynnistä sovellus:**
   ```bash
   flutter run
   ```

---

## 📁 Projektin Rakenne (`lib/`)

- **`main.dart`**: Sovelluksen käynnistyspiste.
- **`core/`**: Yleiset apuohjelmat, teemat ja reititys (`AppRouter`, `AppTheme`).
- **`data/`**: Tietoliikenne ja tallennus (`ApiClient`, `StorageService`).
- **`presentation/`**: Käyttöliittymä.
  - **`screens/`**: Näytöt (`HomeScreen`, `MapScreen`, `RouteDetailsScreen`).
  - **`widgets/`**: Uudelleenkäytettävät komponentit.

---

## 🔧 Vianmääritys

**Ongelma: "Connection refused" / Backend ei vastaa**
- Jos käytät emulaattoria, varmista että `API_URL` on `http://10.0.2.2:8000`.
- Jos käytät fyysistä laitetta, varmista että puhelin on samassa WiFi-verkossa ja `API_URL` osoittaa tietokoneesi IP-osoitteeseen (esim. `http://192.168.1.50:8000`). Tarkista myös Windowsin palomuuri.

**Ongelma: Kartta ei lataudu**
- Tarkista internet-yhteys.
- Varmista että API-avaimet (`HERE_API_KEY`, `MAPBOX_TOKEN`) ovat oikein `.env` tiedostossa.
