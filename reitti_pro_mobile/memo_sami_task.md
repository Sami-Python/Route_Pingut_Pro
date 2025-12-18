# 🐧 Pingut Reitti Pro - Kehityssuunnitelma

**Päivitetty:** 2025-12-15 klo 20:00  
**Tila:** Aktiivinen kehitys

---

## 📋 Nykytilanne

### ✅ Valmiit ominaisuudet
- Reittihaku (HERE Maps API)
- Interaktiivinen kartta (OpenStreetMap)
- Kelikamerat (Digitraffic)
- Tiesääasemat (Digitraffic)
- Liikennetiedotteet (Digitraffic)
- Liikennehäiriöt (HERE API)
- LAM-pisteet (liikennemäärät)
- **AI-reittinalyysi (Google Gemini)** ⭐
- GPS-sijainnin haku
- Lähtö-/saapumisajan valinta
- **Android APK (Toimiva build)** ✅
- **Suosikkipaikat (Local Storage)** ✅
- **Reitin jakaminen** ✅
- **Vaihtoehtoiset reitit (3 kpl)** ✅

### 🎨 Branding
- Nimi: **🐧 Pingut Reitti Pro**
- Värimaailma: Material 3 Design
- Emoji-tuki kaikissa näkymissä

---

## 🎯 Kehitysehdotukset (Prioriteetit)

---

## 1️⃣ KRIITTINEN - Android APK Rakentaminen ✅ VALMIS

### Tavoite
Rakentaa toimiva Android-sovellus ja testata oikealla laitteella.

### Miksi tärkeä?
- Sovellus on nyt vain web-versiossa
- Todellinen käyttö tapahtuu puhelimessa
- GPS toimii paremmin natiivissa
- Parempi suorituskyky

### Toimenpiteet
1. **Rakenna APK**
   ```bash
   cd reitti_pro_mobile
   flutter build apk --release
   ```

2. **Testaa laitteella**
   - Asenna APK puhelimeen
   - Testaa GPS-toiminnallisuus
   - Varmista kartan toiminta
   - Testaa AI-analyysi
   - Tarkista kelikamerakuvien lataus

3. **Korjaa mahdolliset ongelmat**
   - Android-oikeudet (GPS, internet)
   - API-avainten toiminta
   - Suorituskyky-optimoinnit

### Arvioitu aika
- **1-2 tuntia** (ensimmäinen build + testaus)

### Prioriteetti
🔴 **KRIITTINEN** - Tehtävä ensin!

---

## 2️⃣ KORKEA - Käyttäjäkokemus & Visuaalisuus ⭐⭐

---

### 2A. Reitin yksityiskohdat kartalla

#### Tavoite
Näyttää reitin vaiheet ja yksityiskohdat selkeästi.

#### Ominaisuudet
- **Matkan vaiheet**
  - "Käänny vasemmalle Mannerheimintielle"
  - "Jatka suoraan 15 km"
  - Nuoli-ikonit kääntyville

- **Reaaliaikainen saapumisaika**
  - Päivittyy matkan aikana
  - Huomioi liikennetilanteen
  - "Perillä klo 15:42 (5 min myöhässä)"

- **Värikoodattu reitti**
  - 🟢 Vihreä = Sujuva liikenne
  - 🟡 Keltainen = Hidasta
  - 🔴 Punainen = Ruuhka
  - Käytä HERE Traffic Flow dataa

#### Toteutus
- HERE API palauttaa jo `sections` ja `actions`
- Lisää `ListView` reitin vaiheille
- Integroidi Traffic Flow -data värikoodaukseen

#### Arvioitu aika
- **2-3 tuntia**

#### Prioriteetti
🟠 **KORKEA**

---

### 2B. Offline-tuki

#### Tavoite
Sovellus toimii rajoitetusti ilman nettiä.

#### Ominaisuudet
- **Viimeisen reitin tallennus**
  - Tallenna reitti local storage:en
  - Näytä viimeisin reitti offline-tilassa
  - "Tallennettu reitti (ei reaaliaikaista dataa)"

- **Karttatiilien välimuisti**
  - Lataa karttatilet etukäteen
  - Tallenna 50-100 tileä
  - Näytä cached-kartta offline-tilassa

- **Offline-indikaattori**
  - Näytä banneri: "Offline-tila - rajoitettu toiminnallisuus"
  - Disabloi AI-analyysi, kelikamerat, jne.

#### Toteutus
- `shared_preferences` tai `hive` local storage:lle
- `flutter_map` tukee tile caching:ia
- `connectivity_plus` verkkoyhteyden tarkistukseen

#### Arvioitu aika
- **3-4 tuntia**

#### Prioriteetti
🟠 **KORKEA**

---

### 2C. Suosikkipaikat ✅ VALMIS

#### Tavoite
Tallenna usein käytetyt osoitteet nopeaa hakua varten.

#### Ominaisuudet
- **Suosikkien tallennus**
  - "Koti", "Työ", "Mökki" -pikavalinnat
  - Tallenna nimi + koordinaatit
  - Muokkaa/poista suosikkeja

- **Nopea haku**
  - Dropdown-valikko lähtö/määränpää -kentissä
  - "Viimeisimmät reitit" -lista
  - Yksi klikkaus → reitti haettu

- **Reittiehdotukset historiasta**
  - "Yleensä ajat tähän aikaan Helsinkiin"
  - Ehdota yleisimpiä reittejä

#### Toteutus
- `shared_preferences` suosikkien tallennukseen
- JSON-muoto: `{"name": "Koti", "lat": 60.17, "lon": 24.94}`
- UI: `DropdownButton` tai `ListView`

#### Arvioitu aika
- **2-3 tuntia**

#### Prioriteetti
🟠 **KORKEA**

---

## 3️⃣ KESKITASO - AI-ominaisuuksien laajentaminen ⭐

---

### 3A. Älykkäät reittiehdotukset

#### Tavoite
AI ehdottaa parempia lähtöaikoja ja vaihtoehtoisia reittejä.

#### Ominaisuudet
- **Ruuhka-ajan varoitukset**
  ```
  "⚠️ Ruuhka-aika! Ehdotan lähtöä 30 min aiemmin tai myöhemmin."
  "Paras lähtöaika: klo 14:15 (välttää pahimman ruuhkan)"
  ```

- **Vaihtoehtoiset reitit** ✅ VALMIS
  ```
  "🔄 Vaihtoehtoinen reitti säästää 15 min"
  "Reitti 2: Välttää Kehä III:a (+5 km, -10 min)"
  ```

- **Kustannusarvio**
  ```
  "💰 Arvioitu polttoainekulu: 12.50 €"
  "🌱 CO2-päästöt: 8.5 kg (vs. juna: 2.1 kg)"
  ```

#### Toteutus
- Laajenna Gemini-promptia
- Lisää `route_data` useita reittivaihtoehtoja
- HERE API: `alternatives=3` parametri

#### Arvioitu aika
- **2-3 tuntia**

#### Prioriteetti
🟡 **KESKITASO**

---

### 3B. Sääennuste reitille ✅ VALMIS

#### Tavoite
Näytä sääennuste reitin varrella ja varoita huonosta säästä.

#### Ominaisuudet
- **Sääennuste aikajaksolla**
  ```
  "☁️ Pilvistä koko matkan ajan"
  "🌧️ Sadetta odotettavissa klo 14-16 Tampereen kohdalla"
  "❄️ Lumisadetta Mikkelin jälkeen - aja varovasti!"
  ```

- **Kelikamerakuvien automaattinen näyttö**
  - Näytä kelikamerat automaattisesti jos sää huono
  - "Tarkista kelikamerat - liukasta!"

- **Lämpötilavaroitukset**
  ```
  "🧊 Lämpötila alle 0°C - jäätä mahdollista"
  "🌡️ Kuuma päivä (28°C) - muista juomapullo"
  ```

#### Toteutus
- Backend: Open-Meteo API jo käytössä!
- Hae säädata reitin koordinaateille
- Lisää Gemini-promptiin säätieto
- UI: Sää-ikoni reitin infokortissa

#### Arvioitu aika
- **3-4 tuntia**

#### Prioriteetti
🟡 **KESKITASO**

---

### 3C. Proaktiiviset varoitukset

#### Tavoite
Push-notifikaatiot tärkeistä tapahtumista.

#### Ominaisuudet
- **Häiriövaroitukset**
  ```
  📱 "Uusi liikennehäiriö reitilläsi: Tie 3, Tampere"
  📱 "Ruuhka lisääntynyt - matka-aika +15 min"
  ```

- **Säävaroitukset**
  ```
  📱 "Lumisade alkamassa - lähde 20 min aiemmin"
  📱 "Kelikamera näyttää liukasta - aja varovasti"
  ```

- **Lähtömuistutukset**
  ```
  📱 "Muistutus: Lähtö Turkuun klo 14:00 (30 min)"
  📱 "Tankkaa ennen lähtöä - seuraava asema 120 km päässä"
  ```

#### Toteutus
- `firebase_messaging` push-notifikaatioille
- Backend: Tarkista häiriöt 15 min välein
- Tallenna aktiiviset reitit tietokantaan
- Lähetä notifikaatio jos muutoksia

#### Arvioitu aika
- **4-5 tuntia** (Firebase-setup mukaan lukien)

#### Prioriteetti
🟡 **KESKITASO**

---

## 4️⃣ MATALA - Lisäominaisuudet

---

### 4A. Reitin jakaminen ✅ VALMIS

#### Tavoite
Jaa reitti helposti muille.

#### Ominaisuudet
- **Jaa tekstiviestillä/WhatsAppilla**
  ```
  "Olen matkalla Turkuun. Perillä klo 15:30.
  Seuraa matkaani: https://pingut.app/route/abc123"
  ```

- **Live-seuranta**
  - Jaa linkki joka näyttää sijaintisi reaaliajassa
  - "Sami on nyt Lahdessa (45 km jäljellä)"
  - Päivittyy automaattisesti

#### Toteutus
- `share_plus` paketti jakamiseen
- Backend: Tallenna reitti uniikilla ID:llä
- Web-sivu: Näytä reitti kartalla

#### Arvioitu aika
- **2-3 tuntia**

#### Prioriteetti
⚪ **MATALA**

---

### 4B. Multi-stop reitit

#### Tavoite
Lisää useita välipysähdyksiä reitille.

#### Ominaisuudet
- **Useat kohteet**
  ```
  Helsinki → Lahti → Mikkeli → Joensuu
  ```

- **Järjestyksen optimointi**
  - "Optimoi järjestys" -nappi
  - AI ehdottaa parasta järjestystä
  - Säästä aikaa ja polttoainetta

- **Pysähdysajat**
  - Lisää tauko 15 min Lahdessa
  - Huomioi pysähdykset kokonaisajassa

#### Toteutus
- HERE API: `via` parametri välipysähdyksille
- UI: Drag-and-drop järjestyksen muuttamiseen
- Gemini: Optimoi järjestys

#### Arvioitu aika
- **4-5 tuntia**

#### Prioriteetti
⚪ **MATALA**

---

### 4C. Tilastot ja historia

#### Tavoite
Näytä käyttäjälle mielenkiintoisia tilastoja.

#### Ominaisuudet
- **Matkatilastot**
  ```
  📊 "Olet ajanut 1,234 km tällä sovelluksella"
  📊 "Keskimääräinen matka-aika: 45 min"
  📊 "Pisin matka: Helsinki → Rovaniemi (834 km)"
  ```

- **CO2-säästölaskuri**
  ```
  🌱 "Olet säästänyt 45 kg CO2:ta verrattuna lentämiseen"
  🌱 "Tämä vastaa 3 puuta vuodessa"
  ```

- **Reittien historia**
  - Kalenterinäkymä: "Matkat joulukuussa"
  - Kartta: "Kaikki ajamasi reitit"
  - Exporttaa CSV/JSON

#### Toteutus
- Tallenna jokainen reitti local storage:en
- Laske tilastot lennossa
- UI: Graafeja `fl_chart` paketilla

#### Arvioitu aika
- **3-4 tuntia**

#### Prioriteetti
⚪ **MATALA**

---

## 🎨 Bonus: Pienet viilaukset

### Dark Mode
- **Miksi:** Yöajoon parempi, säästää akkua
- **Aika:** 1-2 tuntia
- **Toteutus:** Material 3 tukee valmiiksi

### Ääni-ilmoitukset
- **Miksi:** Hands-free käyttö ajon aikana
- **Aika:** 2-3 tuntia
- **Toteutus:** `flutter_tts` paketti

### Home Screen Widget
- **Miksi:** Nopea pääsy seuraavaan matkaan
- **Aika:** 3-4 tuntia
- **Toteutus:** `home_widget` paketti

### Kielituki
- **Miksi:** Laajempi käyttäjäkunta
- **Aika:** 2-3 tuntia
- **Toteutus:** `flutter_localizations`, englanti + ruotsi

---

## 🚀 Suositellut toteutusjärjestykset

### Vaihtoehto A: Nopea voitto (1-2h)
**Tavoite:** Saada sovellus käyttöön nopeasti

1. ✅ **Android APK** - Rakenna ja testaa
2. ✅ **Suosikkipaikat** - Yksinkertainen local storage
3. ✅ **Reitin jako** - Share-toiminto

**Hyöty:** Sovellus käytössä puhelimessa + käytännölliset ominaisuudet

---

### Vaihtoehto B: Suurempi parannus (3-4h)
**Tavoite:** Erottua kilpailijoista

1. ✅ **Android APK** - Rakenna ja testaa
2. ✅ **Sääennuste reitille** - Käytä olemassa olevaa Open-Meteo API:a
3. ✅ **AI-reittiehdotukset** - Laajenna Gemini-promptia

**Hyöty:** Uniikkeja ominaisuuksia (AI + sää) joita muilla ei ole

---

### Vaihtoehto C: Wow-efekti (5-6h)
**Tavoite:** Ammattitason sovellus

1. ✅ **Android APK** - Rakenna ja testaa
2. ✅ **Reaaliaikainen reitin seuranta** - Päivitä sijainti kartalla
3. ✅ **Proaktiiviset varoitukset** - Push-notifikaatiot
4. ✅ **Offline-tuki** - Karttatiilien cache

**Hyöty:** Täysin toimiva, kilpailukykyinen sovellus

---

## 💡 Lopullinen suositus

### 🥇 Aloita: **Vaihtoehto A**
**Perustelu:**
- ✅ Nopea toteuttaa (1-2h)
- ✅ Suuri käyttöarvo heti
- ✅ Hyvä pohja jatkokehitykselle
- ✅ Sovellus käytössä oikealla laitteella

### 🥈 Jatka: **Vaihtoehto B**
**Perustelu:**
- ✅ Hyödyntää olemassa olevaa infraa
- ✅ Erottuu kilpailijoista (AI + sää)
- ✅ Parantaa käyttökokemusta merkittävästi
- ✅ Kohtuullinen työmäärä

### 🥉 Viimeistele: **Vaihtoehto C**
**Perustelu:**
- ✅ Ammattitason sovellus
- ✅ Kaikki tärkeät ominaisuudet
- ✅ Valmis julkaistavaksi
- ✅ Wow-efekti käyttäjille

---

## 📝 Muistiinpanot

- Kaikki ajat ovat arvioita - voi vaihdella kokemuksen mukaan
- Prioriteetit voivat muuttua käyttäjäpalautteen perusteella
- Testaa jokainen ominaisuus huolellisesti ennen seuraavaan siirtymistä
- Dokumentoi kaikki muutokset `memo_sami.md` tiedostoon

---

**Seuraava päivitys:** 17.12.2025

---

## 5️⃣ Phase 5 - Ammattimainen Viimeistely (17.12.2025 Roadmap) 🚀

Nämä perustuvat nykyiseen tilaan (Android-build toimii, AI toimii, backend toimii).

### 5A. "Quick Wins" (Nopeat voitot) ⚡
Parantavat käyttökokemusta heti ja hyödyntävät jo asennettuja kirjastoja (`shared_preferences`, `hive`).

- **Asetukset-näkymä (`SettingsScreen`):** ✅ VALMIS
  - Tallenna "Koti", "Työpaikka" ja "Oletuskulkuneuvo" (Auto/Julkiset).
  - Mahdollistaa nopeamman haun.
- **Loading-tilat (Skeletons):** ✅ VALMIS
  - Reittihakuun "luuranko"-animaatio tai pyörivä pingviini.
  - Poistaa "tyhjän ruudun" efektin odotusaikana.
- **Virheiden käsittely (Offline-tila):**
  - "Ei verkkoyhteyttä" -ilmoitus kaatumisen sijaan.

### 5B. Ominaisuuksien Syventäminen 🧠
- **Puheohjaus / AI Ääni:**
  - AI kertoo reittianalyysin ääneen (`flutter_tts`).
  - "Huomio: Reitilläsi on sumua Turun kohdalla".
- **Reittihistoria:**
  - Tallenna aiemmat haut paikallisesti (Hive-tietokanta).
  - "Viimeisimmät haut" -lista etusivulle.
- **Reaaliaikainen seuranta (Navigointi-lite):**
  - Päivitä "Olet tässä" -pallo reitillä sijainnin muuttuessa.

### 5C. Tekninen Ammattimaisuus (DevOps) 🛠️
- **Docker-imagen "kovetus":**
  - Päivitä `Dockerfile` ja `requirements.txt` sisältämään kaikki riippuvuudet (`msal`, `streamlit-calendar` jne).
  - Poistaa tarpeen ajaa `pip install` kontin sisällä.
- **Automaattiset testit:**
  - Lisää Flutter yksikkötestejä (`flutter test`) kriittisille komponenteille.
