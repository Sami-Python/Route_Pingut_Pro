# Testaussuunnitelma

## 8 Rajapintakuvaus
### 8.1 API-rakenne ja endpointit




| **Komponentti / Rajapinta** | **Tarkoitus** | **Protokolla / Muoto** | **Autentikointi** | **Päivitystiheys / Vasteaika** | **Huomiot** |
|------------------------------|---------------|--------------------------|--------------------|-------------------------------|--------------|
| **Käyttäjäautentikointi (OAuth2 / JWT)** | Käyttäjän kirjautuminen ja käyttöoikeudet | HTTPS / JSON | OAuth2 (Google, Microsoft) + JWT-sessio | reaaliaikainen | Token-pohjainen; tukee kalenteripalveluiden kirjautumista |
| <span style="color:red">**Kalenterisovellukset – Outlook (Microsoft Graph)** | Hakee tulevat tapahtumat ja paikat | REST / JSON | OAuth2 (Microsoft Identity) | reaaliaikainen | `GET /me/events`, `GET /me/calendarView` |
| **Kalenterisovellukset – Gmail (Google Calendar)** | Hakee tulevat tapahtumat ja paikat | REST / JSON | OAuth2 (Google Cloud) | reaaliaikainen | `GET /calendar/v3/calendars/primary/events` |
| **Kalenterisovellukset – Muut (Apple / iCal / ICS)** | Lukee iCalendar-tiedostoja | HTTPS / ICS | Julkinen / ei kirjautumista | vaihtelee | Vain tapahtuman aika ja paikka luetaan |
| <span style="color:red">**Ilmatieteen laitos (FMI Open Data)** | Sääennusteet, varoitukset ja tiesää | REST / XML / JSON | API-avain (FMI) | 5–10 min välein | Käytetään WFS-rajapintaa, esim. `fmi::forecast::harmonie` |
| <span style="color:red">**Digitraffic / Fintraffic** | Liikennetilanteet, häiriöt, tietyöt, kamerat | REST / JSON | Avoin (ei avainta) | 1–5 min välein | `traffic-message`, `maintenance`, `weather`, `cameras` |
| **Karttapalvelu – Google Maps** | Reititys, ajoaika, ruuhkat | REST / JSON | API-avain | reaaliaikainen | `Directions API`, `Distance Matrix API` |
| **Karttapalvelu – HERE Developer** | Reititys, liikenne, sää | REST / JSON | API-avain | reaaliaikainen | `Routing API v8`, `Traffic API`, `Weather API` |
| **Karttapalvelu – OpenStreetMap / OSRM / Mapbox** | Avoin reititys ja kartat | REST / JSON | Ei vaadi / valinnainen avain | vaihtelee | Kevyt ja kustannustehokas vaihtoehto |
| **Tietokanta – DuckDB (tai PostgreSQL)** | Tallentaa matkat, riskit, asetukset ja käyttäjät | SQL | Sovellustason autentikointi | paikallinen / välitön | Helppo integrointi Polarsin tai Pandasin kanssa |
| **Ilmoituspalvelu (Web Push / Email / SMS)** | Hälytykset ja muistutukset käyttäjälle | HTTPS / JSON / SMTP | Token / API-avain | reaaliaikainen | Web Push (VAPID), Email (SMTP), SMS (Gateway) |
| **Käyttöliittymä – Streamlit / Web App** | Käyttöliittymä reittien ja hälytysten hallintaan | HTTPS / WebSocket | Käyttäjätunnistus (JWT) | reaaliaikainen | Kevyt UI, hyödyntää REST-pintaa ja välimuistia |

---

### Yhteenveto

- **Autentikointi:** OAuth2 (Google, Microsoft), JWT-sessio sovelluksen sisällä.  
- **Päärajapinnat:** FMI (sää), Fintraffic (liikenne), Google/HERE (reititys), Outlook/Gmail (kalenterit).  
- **Tietovarasto:** DuckDB MVP-vaiheessa (lokaalisti)
- **Tietovirta:**  
  Käyttäjä → (kalenteri / sijainti) → Reittianalyysi (FMI + Fintraffic + kartta) → Hälytykset (push/email).  

### 8.2 Datan syötteet ja palautteet
### 8.3 Rajapintojen dokumentointi 
### 8.4 Integraatiot ulkoisiin palveluihin

## 9 Testaussuunnitelma: Matkahälytysportaali / App
    
### 9.1 Testauksen tavoitteet ja periaatteet

Tämän testaussuunnitelman tarkoituksena on varmistaa, että Matkahälytysportaalin MVP-versio toimii määrittelyjen mukaisesti ja täyttää toiminnalliset ja ei-toiminnalliset vaatimukset.  
Erityisesti testataan reittien asettaminen, hälytysten muodostus ja ilmoitusmekanismit.

**Tavoitteet:**
- Varmistaa reittien asetus, laskenta ja muistutukset toimivat luotettavasti.  
- Testata rajapintaintegraatioiden (FMI, Fintraffic, kalenterit, karttapalvelut) toimintaa.  
- Tarkistaa hälytysten ja suositusten oikeellisuus sekä viestinnän toimivuus (push, email, SMS).  
- Todentaa tietoturva- ja suorituskykyvaatimusten täyttyminen.

### Testauksen kohde
Testauksen kohteena on Matkahälytysportaalin MVP-versio, joka sisältää:

- Käyttöliittymän (Web / mobiili)
- Reitinlaskenta- ja hälytyspalvelun
- Tietolähdeintegraatiot (FMI, Fintraffic, kalenterit)
- Tietokannan (DuckDB / PostgreSQL)
- Ilmoituspalvelut (Push, Email, SMS    
    
### 9.2 Testausympäristö ja -työkalut

| Komponentti | Kuvaus |
|--------------|--------|
| Käyttöjärjestelmä | Linux, Win, iOS |
| Backend | Python 3.12, FastAPI / Flask |
| Tietokanta | DuckDB (paikallinen), tai muu |
| Rajapinnat | FMI, Fintraffic, Google Calendar, Outlook Graph API |
| Karttapalvelut | Google Maps / HERE Routing API (?) |
| Testityökalut | määritellään myöhemmin |
| Ilmoituspalvelu | Web Push, SMTP, SMS Gateway |

    
### Testausmenetelmät
- Manuaalinen testaus käyttöliittymässä (toiminnallisuudet UC01–UC08).
- Automaattiset yksikkö- ja integraatiotestit pytest tai vastaava
- Rajapintojen vasteaikatestit JMeter tai vastaava
- Käytettävyystestaus pienellä testiryhmällä (3–5 käyttäjää).
- Tietoturvatarkastus (OAuth2, JWT, API-avaimet, salatut yhteydet).
    
### 9.3 Testitapaukset ja hyväksymiskriteerit
    

| ID | Käyttötapaus | Testitapaus | Syöte / Toimenpide | Odotettu tulos |
|----|---------------|-------------|--------------------|----------------|
| TC01 | UC01 | Luo matka manuaalisesti | Syötä lähtö- ja määränpää | Matka tallentuu ja muistutus luodaan |
| TC02 | UC01 | Luo matka kalenterista | Valitse tapahtuma Outlookista | Matka lisätään automaattisesti |
| TC03 | UC02 | Testaa muistutusta | Aseta lähtö 5 min päähän | Push-ilmoitus saapuu oikeaan aikaan |
| TC04 | UC03 | API-haku epäonnistuu | Katkaise Fintraffic API | Käytetään välimuistitietoja |
| TC05 | UC04 | Tarkista varoitukset | Simuloi huono sää | Näytetään varoitus ja suositus |
| TC06 | UC07 | Peru kalenterilupa | Poista lupa asetuksista | Järjestelmä ei enää käytä kalenteritietoja |

### Hyväksymiskriteerit
Testaus katsotaan onnistuneeksi, kun:
- 95 % testitapauksista läpäisee.  
- Kaikki kriittiset virheet on korjattu.  
- Reitin laskenta toimii alle 5 sekunnissa.  
- Push-ilmoitukset ja email-hälytykset saapuvat oikeaan aikaan.  
    
### Riskit ja varautuminen
    
| Riski | Vaikutus | Varautuminen |
|--------|-----------|---------------|
| API-yhteys epäonnistuu | Hälytykset viivästyvät | Käytetään välimuistitietoja |
| Sijaintilupa evätty | Reittiä ei voi laskea | Pyydetään manuaalinen lähtöpiste |
| Kalenterirajapinta muuttuu | Automaattinen reittien luonti ei toimi | Päivitetään rajapintakutsu |
| Push-palvelu ei toimi | Käyttäjä ei saa ilmoituksia | Varmistetaan varakanava (email/SMS) |