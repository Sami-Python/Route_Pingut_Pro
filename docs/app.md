# Reitti Pro - Sovelluksen kehityshistoria

## Nykyiset ominaisuudet ✅

### Kartta ja visualisointi
- ✅ **3D-karttanäkymä** Pydeck + Mapbox
- ✅ **Dynaaminen reititys** HERE API:lla
- ✅ **Autoanimaatio** reitin varrella
- ✅ **Korkeuprofiili** reitille
- ✅ **Useita karttapohjia** (dark, streets, satellite)

### Liikenne ja häiriöt
- ✅ **HERE-häiriötiedot** (punainen/oranssi)
- ✅ **Digitraffic-tiedotteet** (syaani)
- ✅ **Kelikamerat** klikkaamalla (keltainen)
- ✅ **Reaaliaikainen kamerakuva** sivupalkissa

### Sää
- ✅ **Sade-ennuste** koko Suomen alueelle
- ✅ **RainViewer-integraatio** manuaalisella tiilauksella
- ✅ **Aikaleima-synkronointi** reitin kanssa
- ✅ **Säädatan läpinäkyvyys** säädettävissä

### Käyttöliittymä
- ✅ **GPS-sijainti** selaimesta
- ✅ **Reititysasetukset** (nopein/lyhin, vältä moottoriteitä/tietulleja)
- ✅ **Tasovalinnat** (reitti, sää, häiriöt, kamerat, auto)
- ✅ **Lähtöajan valinta** (päivä + kello)
- ✅ **Matkan yhteenveto** (matka, aika, lähtö, perillä)

## Kehityshistoria

### 2.12.2024 - Sade-ennuste koko Suomelle
**Ongelma:** Sääkartta näkyi vain reitin varrella, ei koko Suomessa.

**Ratkaisu:**
- Muutettiin `app.py`:ssä säätiilien laskenta käyttämään kiinteää bounding boxia Suomelle (lat: 59-71, lon: 19-33)
- Poistettu reitin riippuvuus säädatan näyttämisestä
- Sää näkyy nyt myös ilman reittiä

**Tekniset yksityiskohdat:**
- Zoom-taso: 6 (RainViewer-yhteensopiva)
- Tiilimäärä rajoitettu 50:een suorituskyvyn vuoksi
- Manual tiling Web Mercator -projektiolla

### 30.11.2024 - Kelikamerat
**Lisätty:**
- Kelikamerat Digitraffic API:sta
- Klikkaus tunnistaa kameran
- Kuva ladataan server-side (CORS-ongelma kierretty)
- Sivupalkki näyttää kamerakuvan

**Tekniset haasteet:**
1. **CORS-ongelma:** Selaimet estävät suoran latauksen → Ratkaisu: `requests.get()` Pythonilla
2. **Klikkauksen tunnistus:** Pydeck-versioiden erot → Fallback-logiikka
3. **UI-päivitys:** `st.rerun()` kriittinen sivupalkin päivitykseen

### Marraskuu 2024 - Digitraffic-integraatio
**Lisätty:**
- Liikennetiedotteet Digitraffic API:sta
- Shapely-pohjainen geometrinen suodatus
- Syaanit markerit kartalla

**Tekniset yksityiskohdat:**
- Bbox-rajoitus API-kutsuissa
- Fallback ilman bboxia jos API palauttaa 400/413
- Buffer-etäisyys: 500m (tiedotteet), 1000m (kamerat)

### Lokakuu 2024 - HERE API -integraatio
**Lisätty:**
- Geokoodaus (osoite → koordinaatit)
- Reititys (fast/short)
- Häiriötiedot (incidents)
- Flexpolyline-dekoodaus
- Korkeusdatan tuki

**API-parametrit:**
- `return`: polyline, summary, incidents, elevation
- `spans`: incidents (häiriöiden sijainti)
- `routingMode`: fast/short
- `avoid[features]`: tollRoad, controlledAccessHighway

### Syyskuu 2024 - Projektin aloitus
**Perusominaisuudet:**
- Streamlit-sovellus
- Pydeck-kartta
- HERE API -avainten hallinta (.env)

## Arkkitehtuuri

### Tiedostorakenne
```
app.py                    # Pääsovellus (Streamlit UI)
├── here_client.py        # HERE API (reititys, geokoodaus)
├── digitraffic_client.py # Digitraffic (kamerat, tiedotteet)
└── weather_client.py     # RainViewer (säätilit)
```

### Datavirta
1. **Käyttäjä** syöttää lähtö ja määränpää
2. **Geokoodaus** muuttaa osoitteet koordinaateiksi
3. **Reititys** hakee reitin HERE API:sta
4. **Häiriöt** haetaan kahdesta lähteestä:
   - HERE API (reitin mukana)
   - Digitraffic API (geometrinen suodatus)
5. **Kelikamerat** haetaan Digitrafficista (Shapely-suodatus)
6. **Säädata** haetaan RainViewerista
7. **Kartta** renderöidään Pydeckillä

### Caching
- `@st.cache_data(ttl=600)` - Reititys (10 min)
- `@st.cache_data(ttl=3600)` - Geokoodaus (1h)
- `@st.cache_data(ttl=300)` - Säädata (5 min)

## Tunnetut rajoitukset

### Sääkartta
- TileLayer ei toimi Pydeckissä → Käytetään BitmapLayeriä
- Tiilimäärä rajoitettu 50:een
- Zoom-taso kiinteä (6)

### Digitraffic API
- Bbox-rajoitus voi epäonnistua suurilla alueilla
- Fallback hakee koko Suomen datan

### Kelikamerat
- Kuvien lataus voi olla hidasta
- Timeout 5 sekuntia
- User-Agent -header pakollinen

## Tulevaisuuden kehitysideat

- [ ] Usean reitin vertailu
- [ ] Tallennetut suosikit
- [ ] Historiadata (aikaisemmat reitit)
- [ ] Push-ilmoitukset häiriöistä
- [ ] Offline-tuki
- [ ] Mobiilisovellus

