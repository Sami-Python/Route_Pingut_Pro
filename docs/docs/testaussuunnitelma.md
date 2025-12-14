# Testaussuunnitelma: Matkahälytysportaali
## Testauksen tavoitteet ja periaatteet

Testauksen tavoitteena on varmistaa, että Matkahälytysportaalin MVP-versio täyttää sille asetetut toiminnalliset ja ei-toiminnalliset vaatimukset. Testaus keskittyy erityisesti mikropalvelun ydintoiminnallisuuksiin, ulkoisten rajapintojen integraatioihin sekä käyttöliittymän toimivuuteen web-ympäristössä.

MVP-versiossa testaus kohdistuu reaaliaikaiseen tiedonhakuun ja käsittelyyn. Järjestelmä ei sisällä pysyvää tietovarastoa, käyttäjätunnistusta eikä ilmoitusten toimitusta erillisten viestikanavien kautta. Testaus tukee jatkuvaa kehitystä ja laadunvarmistusta osana CI/CD-putkea.

### Testauksen päätavoitteet
- Varmistaa, että reittien asetus, laskenta ja muistutukset toimivat luotettavasti.
- Testata ulkoisten rajapintojen integraatiot (FMI, Fintraffic, kalenterit, karttapalvelut).
- Todentaa hälytysten oikeellisuus ja niiden toimitus eri kanavissa (push, email, SMS).
- Varmistaa tietoturvan, autentikoinnin ja käyttöoikeuksien toimivuus.
- Tukea jatkuvaa kehitystä CI/CD-putken kautta.

### Testauksen kohde

Testauksen kohteena ovat:
- Web-käyttöliittymä
- Reitinlaskenta- ja riskitasopalvelu
- Kalenteri-integraatiot
- Sää- ja liikennetieto-integraatiot
- Ilmoituspalvelut
- Tietokanta (DuckDB / PostgreSQL) (Huom! Ei osta MVP:tä)

## Testausympäristö ja työkalut
| Osa-alue           | Kuvaus                                               |
| ------------------ | ---------------------------------------------------- |
| Käyttöjärjestelmät | Linux, Windows, macOS, iOS/Android selaimet          |
| Backend            | Python 3.12, FastAPI / Flask                         |
| Tietokanta         | DuckDB (MVP), vaihtoehtoisesti PostgreSQL            |
| Rajapinnat         | FMI, Fintraffic, Google Calendar, Outlook Graph API  |
| Karttapalvelut     | Google Maps API / HERE Routing API                   |
| Testityökalut      | pytest, pytest-cov, requests-mock, JMeter, GitLab CI |
| Ilmoituspalvelu    | Web Push, SMTP, SMS Gateway                          |

## Testausmenetelmät
### 1. Staattinen analyysi (pylint)
- Suoritetaan kehittäjän koneella ja CI/CD-putkessa.
- ERROR-luokan virheet estävät merge requestin hyväksymisen.

### 2. Yksikkötestit (pytest)
- Testataan reitityslogiikka, aggregointi, virhetilanteiden käsittely ja tietomallit.
- Ulkoiset API:t mockataan.

### 3. Integraatiotestit
Testaavat yhteistyötä seuraavien kanssa:
- Outlook / Google Calendar
- FMI ja Digitaffic
- Karttapalvelut (Google/HERE)

### 4. E2E-testit (docker-compose)
Simuloidaan koko prosessi:
- Reitti asetetaan
- Tiedot haetaan
- Riskitaso lasketaan
- Hälytys muodostuu ja toimitetaan

### 5. Manuaalinen UI-testaus
- Reitin asetus ja muokkaus
- Kartan ja varoitusten näyttäminen
- Hälytysten hallinta

## Testitapaukset ja hyväksymiskriteerit
| ID   | Käyttötapaus | Testitapaus             | Syöte / Toimenpide        | Odotettu tulos                         |
| ---- | ------------ | ----------------------- | ------------------------- | -------------------------------------- |
| TC01 | UC01         | Luo matka manuaalisesti | Syötä lähtö ja määränpää  | Matka tallentuu, hälytys luodaan       |
| TC02 | UC01         | Luo matka kalenterista  | Valitse Outlook-tapahtuma | Matka lisätään automaattisesti         |
| TC03 | UC02         | Testaa lähtömuistutus   | Aseta lähtö 5 min päähän  | Push-ilmoitus saapuu ajoissa           |
| TC04 | UC03         | Fintraffic offline      | Katkaise yhteys APIin     | Käytetään välimuistia                  |
| TC05 | UC04         | Huono sää               | Simuloi FMI-varoitus      | Riskitaso nousee ja varoitus esitetään |
| TC06 | UC07         | Peru kalenterilupa      | Poista Outlook-lupa       | Järjestelmä ei käytä kalenteria        |

### Hyväksymiskriteerit
- ≥ 95 % testitapauksista läpäisee
- Kaikki kriittiset virheet korjattu
- Reitti lasketaan < 5 s
- Push/email/SMS-hälytykset toimitetaan oikeaan aikaan
- Rajapintojen vasteet ovat skeeman mukaisia

## Riskit ja varautuminen
| Riski                               | Vaikutus                           | Varautuminen                      |
| ----------------------------------- | ---------------------------------- | --------------------------------- |
| API-yhteys katkeaa                  | Hälytykset voivat viivästyä        | Välimuistitiedot / fallback       |
| Sijaintilupa evätty                 | Reittiä ei voi laskea              | Pyydetään manuaalinen lähtöpiste  |
| Kalenterirajapinnan muutos          | Matkat eivät synny automaattisesti | Versionhallinta, monitorointi     |
| Push-palvelu epäonnistuu            | Hälytys ei saavu                   | Email/SMS varakanavana            |
| Sää- tai liikennedata puutteellista | Riskitaso epätarkka                | Konservatiivinen default-logiikka |

## Testiprosessi CI/CD-putkessa
'''
stages:
  - lint
  - test
  - build
  - deploy
'''
