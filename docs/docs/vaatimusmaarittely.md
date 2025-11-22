# Vaatimusmäärittely

## 7 Vaatimusmäärittely

### 7.1 Käyttötapaukset ja käyttäjätarinat

**Järjestelmän nimi:** Matkahälytysportaali / App

**Kuvaus:** Käyttäjä näkee tulevaan reittiin ja matkaan liittyvät hälytykset ja huomioitavat asiat sekä saa muistutuksen ennen lähtöä. Sovellus hyödyntää eri tietolähteitä (esim. Fintraffic ja FMI) reittien riskien ja olosuhteiden arviointiin.

**Laajuus:** Mobiili- ja web-versio (?)

**Sidosryhmät:** Loppukäyttäjät, palvelun ylläpitäjät, kalenteripalvelun tarjoajat, sää- ja liikennedatatoimittajat

### 2. Oletukset ja rajaukset

- Käyttäjällä on toimiva internet-yhteys ja sijaintilupa.
- Käyttäjä voi sallia kalenterin käytön reittien automaattiseen luontiin.
- MVP-versiossa tuetaan vain autoilureittejä (ei julkista liikennettä).

### 3. Tekijät

| Tekijä | Tyyppi | Kuvaus |
|--------|--------|--------|
| Käyttäjä | Pääosallinen | Asettaa matkan ja vastaanottaa hälytykset |
| Kalenteripalvelu | Toissijainen | Tarjoaa lähtö- ja määränpäätiedot |
| Sijaintipalvelu | Toissijainen | Antaa nykyisen sijainnin |
| Liikennetilanne-API | Toissijainen | Tuo tiedot onnettomuuksista, ruuhkista, tietyöistä |
| Sää/Kelitieto-API | Toissijainen | Tuo keliolosuhteet ja näkyvyystiedot |
| Joukkoliikenne-API | Valinnainen | Antaa julkisen liikenteen poikkeamatiedot |

### 4. Tietolähteet ja luvat

| Tietolähde | Käyttötarkoitus | API-saatavuus |
|------------|-----------------|---------------|
| Fintraffic / Digitraffic | Liikennetilanne, tietyöt, kelikamerat, tiesää | Avoin API |
| Ilmatieteen laitos (FMI) | Sääennusteet ja tiesää | Avoin API |
| Digitransit / HSL | Joukkoliikennepoikkeamat | Avoin API |

### 5. Käyttötapaukset

| Tunnus | Nimi | Kuvaus |
|--------|------|--------|
| UC01 | Aseta tuleva matka | Käyttäjä syöttää lähtöajan, lähtöpisteen ja määränpään käsin, sijainnista tai kalenterista |
| UC02 | Muistuta lähdön lähestyessä | Sovellus ilmoittaa käyttäjälle lähestyvästä lähdöstä ja näyttää pikatilannekuvan |
| UC03 | Laske reitti & kerää varoitukset | Hakee reitin ja siihen liittyvät liikenne- ja kelitiedot |
| UC04 | Näytä hälytykset & suositukset | Näyttää käyttäjälle yhteenvetona reitin riskit ja mahdolliset suositukset |
| UC05 | Rerouttaa tai säädä lähtöaikaa | Tarjoaa vaihtoehtoisen reitin tai ehdottaa lähtöajan muuttamista |
| UC06 | Aseta ilmoitusten taso & kanavat | Käyttäjä määrittää ilmoitusten tyypin ja kriittisyysrajan |
| UC07 | Hallinnoi lupia & tietolähteitä | Käyttäjä voi hyväksyä tai perua sijainti- ja kalenteriluvat |
| UC08 | Tallenna palaute & paranna mallia | Käyttäjä antaa palautetta hälytysten hyödyllisyydestä |

### 6. Yksityiskohtaiset käyttötapaukset

#### UC01 – Aseta tuleva matka

| Osa | Kuvaus |
|-----|--------|
| **Tavoite** | Käyttäjä määrittää tulevan matkan tiedot |
| **Pääosallinen** | Käyttäjä |
| **Esiehdot** | Sijainti- ja kalenteriluvat on myönnetty |
| **Peruspolku** | 1. Käyttäjä syöttää lähtö- ja määränpään<br>2. Järjestelmä tunnistaa kalenterimerkinnän (jos käytössä)<br>3. Matka tallennetaan järjestelmään |
| **Vaihtoehdot / poikkeukset** | Kalenterimerkintä ei sisällä paikkaa → pyydetään manuaalinen syöttö |
| **Jälkiehdot** | Matka on tallennettu ja muistutus asetettu (UC02) |

#### UC02 – Muistuta lähdön lähestyessä

| Osa | Kuvaus |
|-----|--------|
| **Tavoite** | Käyttäjää muistutetaan lähdöstä ajoissa |
| **Pääosallinen** | Käyttäjä |
| **Esiehdot** | UC01 suoritettu |
| **Peruspolku** | 1. Järjestelmä havaitsee, että lähtöaika lähestyy<br>2. Sovellus hakee reitin tilannekuvan (UC03)<br>3. Käyttäjälle lähetetään push-/äänihälytys |
| **Vaihtoehdot / poikkeukset** | Hälytykset hiljaisessa tilassa → näytetään vain ilmoitus |
| **Jälkiehdot** | Käyttäjä saa ajantasaisen reittitilanteen |

#### UC03 – Laske reitti & kerää varoitukset

| Osa | Kuvaus |
|-----|--------|
| **Tavoite** | Selvittää reitin ja mahdolliset riskit |
| **Pääosallinen** | Järjestelmä |
| **Esiehdot** | UC01 suoritettu, tietolähteet saatavilla |
| **Peruspolku** | 1. Määritetään reitti<br>2. Haetaan liikennetiedot (Fintraffic)<br>3. Haetaan kelitiedot (FMI)<br>4. Arvioidaan riskit ja luokitellaan kriittisyystasot |
| **Vaihtoehdot / poikkeukset** | API ei vastaa → käytetään välimuistia |
| **Jälkiehdot** | Reittitiedot ja varoitukset valmiit UC04:lle |

#### UC04 – Näytä hälytykset & suositukset

| Osa | Kuvaus |
|-----|--------|
| **Tavoite** | Esittää käyttäjälle riskit ja ehdotukset |
| **Pääosallinen** | Käyttäjä |
| **Esiehdot** | UC03 valmis |
| **Peruspolku** | 1. Näytetään reitin tiiviste ja varoitukset<br>2. Näytetään arvioitu viive ja suositukset (UC05) |
| **Jälkiehdot** | Käyttäjä voi reagoida suositukseen tai ohittaa sen |

#### UC05 – Rerouttaa tai säädä lähtöaikaa

| Osa | Kuvaus |
|-----|--------|
| **Tavoite** | Tarjota vaihtoehto reitin tai lähtöajan muutokseen |
| **Pääosallinen** | Käyttäjä |
| **Peruspolku** | 1. Järjestelmä laskee vaihtoehdot<br>2. Käyttäjä valitsee uuden reitin tai lähtöajan<br>3. Päivitetään UC01 ja UC02 |
| **Jälkiehdot** | Reitti ja muistutus päivitetty |

#### UC06 – Aseta ilmoitusten taso & kanavat

| Osa | Kuvaus |
|-----|--------|
| **Tavoite** | Käyttäjä säätää ilmoitusten tasoa |
| **Pääosallinen** | Käyttäjä |
| **Peruspolku** | 1. Käyttäjä valitsee ilmoituskanavat ja kriittisyyskynnyksen<br>2. Asetukset tallennetaan |
| **Jälkiehdot** | Ilmoitukset toimivat asetusten mukaisesti |

#### UC07 – Hallinnoi lupia & tietolähteitä

| Osa | Kuvaus |
|-----|--------|
| **Tavoite** | Käyttäjä hallinnoi kalenteri- ja sijaintilupia |
| **Pääosallinen** | Käyttäjä |
| **Peruspolku** | 1. Käyttäjä tarkastelee käytössä olevia lupia<br>2. Käyttäjä sallii tai poistaa luvat<br>3. Järjestelmä tallentaa muutokset |
| **Jälkiehdot** | Lupatiedot päivitetty |

#### UC08 – Tallenna palaute & paranna mallia

| Osa | Kuvaus |
|-----|--------|
| **Tavoite** | Käyttäjä antaa palautetta hälytysten hyödyllisyydestä |
| **Pääosallinen** | Käyttäjä |
| **Peruspolku** | 1. Käyttäjä arvioi varoituksen (hyödyllinen / ei hyödyllinen)<br>2. Palaute tallennetaan analytiikkaan |
| **Jälkiehdot** | Mallin kehitysdata tallentunut |

### 7.2 Käyttötapauskaavio

![Käyttötapauskaavio](../img/käyttotapauskaavio.png)


### 7.3 Käyttäjä- ja Järjestelmävaatimukset

#### 7.3.1 Käyttäjävaatimukset (luonnos)

Nämä käyttäjävaatimukset ovat toiminnallisia.

| ID | Luotu / Muokattu | Lyhyt nimi | Kuvaus | Prioriteetti | Perustelu | Tila | Hyväksyntäkriteeri |
|----|------------------|------------|--------|--------------|-----------|------|-------------------|
| U-001 | 11.11.25 | Reitin syöttäminen | Käyttäjä voi syöttää web-käyttöliittymään lähtöpaikan ja määränpään (esim. osoitteet) autoilureittiä varten. | Korkea | MVP:n ydintoiminto. | Luonnos | Käyttäjä pystyy syöttämään kaksi osoitetta tekstikenttiin. |
| U-002 | 11.11.25 | Reitin näyttäminen | Käyttäjä näkee haetun reitin visuaalisesti kartalla tai tekstimuotoisena ohjeena web-käyttöliittymässä. | Korkea | MVP:n ydintoiminto. Rajaus: Vain autoilureitit. | Luonnos | Reitti piirtyy kartalle lähtö- ja päätepisteen välille. |
| U-003 | 11.11.25 | Sääolosuhteiden näkeminen | Käyttäjä näkee reitin varrelle tai määränpäähän kohdistuvat ajantasaiset säätiedot ja varoitukset (esim. näkyvyys, sää). | Korkea | Palvelun ydinlupaus (olosuhteiden arviointi). | Luonnos | Reitin yhteydessä näytetään relevantti sääikoni ja lämpötila. |
| U-004 | 11.11.25 | Liikennetietojen näkeminen | Käyttäjä näkee reitin varrella olevat merkittävät liikenne-esteet, kuten tietyöt, onnettomuudet ja kelikameroiden kuvakkeet. | Korkea | Palvelun ydinlupaus (olosuhteiden arviointi). | Luonnos | Kartalla näkyy ikoneita tietyö- ja kamerakohteissa. |
| U-005 | 11.11.25 | Responsiivinen käyttöliittymä | Käyttäjä voi käyttää sovellusta yleisimmillä web-selaimilla (esim. Chrome, Firefox) tietokoneella ja mobiililaitteella. | Keskitaso | MVP:n peruskäytettävyys. | Luonnos | Web-sovellus skaalautuu mobiililaitteen näytölle. |

#### 7.3.2 Järjestelmävaatimukset (luonnos)

Nämä järjestelmävaatimukset ovat toiminnallisia teknisiä toteutuksia, jotka mahdollistavat käyttäjävaatimusten täyttymisen. Nämä keskittyvät Python/REST API -mikropalveluun.

| ID | Luotu / Muokattu | Lyhyt nimi | Kuvaus | Prioriteetti | Perustelu | Tila | Hyväksyntäkriteeri |
|----|------------------|------------|--------|--------------|-----------|------|-------------------|
| S-001 | 11.11.25 | OpenAPI-dokumentaatio | Mikropalvelun rajapinta (API) on määritelty ja dokumentoitu Swagger/OpenAPI-standardin mukaisesti. | Korkea | Projektin tavoite | Luonnos | /api-docs -päätepiste palauttaa validin Swagger UI:n. |
| S-002 | 11.11.25 | Olosuhde-API-päätepiste | Järjestelmä tarjoaa REST API -päätepisteen (esim. /route-conditions), joka ottaa vastaan lähtö- ja päätepisteen. | Korkea | U-001:n tekninen toteutus | Luonnos | API-kutsu palauttaa HTTP 200 -vastauksen validilla datalla. |
| S-003 | 11.11.25 | FMI-integraatio | Järjestelmä hakee sää- ja varoitustiedot Ilmatieteen laitoksen avoimesta rajapinnasta annettujen koordinaattien tai alueen perusteella. | Korkea | Toteuttaa vaatimuksen U-003 | Luonnos | Testikutsulla FMI:n rajapinnasta saadaan dataa. |
| S-004 | 11.11.25 | Fintraffic-integraatio | Järjestelmä hakee liikennetiedot (kamerat, tietöiden, onnettomuudet) Fintrafficin avoimesta rajapinnasta. | Korkea | Toteuttaa vaatimuksen U-004 | Luonnos | Testikutsulla Fintrafficin rajapinnasta saadaan dataa. |
| S-005 | 11.11.25 | Reitityspalvelu-integraatio | Järjestelmä käyttää ulkoista reitityspalvelua (esim. Google Maps) ajoreitin ja reittipisteiden hakemiseen. | Korkea | Toteuttaa vaatimuksen U-002 | Luonnos | Järjestelmä osaa muuntaa osoitteet reitiksi. |
| S-006 | 11.11.25 | Datan yhdistäminen | Mikropalvelu yhdistää reitti-, sää- ja liikennetiedot yhtenäiseksi JSON-vastaukseksi, jonka se palauttaa API-kutsun tekijälle (Streamlit-UI). | Korkea | Palvelun ydintoiminto (U-002, U-003, U-004) | Luonnos | API-vastaus sisältää kentät reitille, säätiedoille ja liikennetiedoille. |
| S-007 | 11.11.25 | Kontitus | Mikropalvelu on paketoitu ja ajettavissa konttina (esim. Docker) kehitysympäristön mukaisesti. | Korkea | Projektin tavoite | Luonnos | docker build ja docker run onnistuvat. |
| S-008 | 11.11.25 | Yksikkötestaus | Palvelun kriittisille logiikkakomponenteille (esim. datan yhdistäminen) on toteutettu automatisoidut yksikkötestit. | Korkea | Projektin tavoite | Luonnos | Testikattavuus (coverage) on yli 75% ja testit ajetaan CI-putkessa. |
| S-009 | 11.11.25 | Versionhallinta | Koodi on GitLab-repositoriossa ja noudattaa sovittuja branch- ja commit-käytäntöjä. | Korkea | Projektin tavoite | Luonnos | Koodi on GitLabissa ja merge requesteja käytetään. |
| S-010 | 11.11.25 | Staattinen koodianalyysi | Koodille ajetaan staattinen koodianalyysi laadun varmistamiseksi. | Keskitaso | Projektin tavoite | Luonnos | CI-putki sisältää lint-vaiheen (esim. Flake8, Black). |

### 7.4 Ei-toiminnalliset vaatimukset (Asiakasvaatimukset)

#### 7.4.1 Käyttäjät ja Roolit

Nämä vaatimukset määrittelevät, ketkä järjestelmää käyttävät ja mitä se heiltä edellyttää. Alustavasti jokaisesta on 3 vaatimusta.

| ID | Luotu / Muokattu | Lyhyt nimi | Kuvaus | Prioriteetti | Perustelu | Tila | Hyväksyntäkriteeri |
|----|------------------|------------|--------|--------------|-----------|------|-------------------|
| NFR-001 | 11.11.25 | Loppukäyttäjän profiili | Järjestelmän ensisijainen käyttäjä on kuka tahansa korkeakouluyhteisön jäsen tai tielläliikkuja, joka tarvitsee reittikohtaisia olosuhdetietoja. | Korkea | Projektin tavoite. | Luonnos | Käyttäjäroolia ei tarvitse erikseen määritellä, käyttö on anonyymiä. |
| NFR-002 | 11.11.25 | Anonyymi käyttö | MVP-version tulee toimia täysin ilman käyttäjätunnistusta tai kirjautumista. Järjestelmä ei saa edellyttää käyttäjätilin luomista. | Korkea | Rajaus. | Luonnos | Kaikki U-vaatimukset (U-001 - U-005) ovat käytettävissä ilman kirjautumista. |
| NFR-003 | 11.11.25 | Ylläpitäjän rooli | Ylläpitäjä on kehitystiimi. Tiimin tulee pystyä seuraamaan palvelun perustilaa ja ajamaan testejä. | Korkea | Projektin vaatimus. | Luonnos | Kehitystiimillä on pääsy GitLab-projektiin, logeihin ja CI/CD-putkiin. |

#### 7.4.2 Luotettavuus ja Ylläpidettävyys (Availability)

Nämä vaatimukset määrittelevät, kuinka vikasietoinen ja käytettävä palvelun tulee olla.

| ID | Luotu / Muokattu | Lyhyt nimi | Kuvaus | Prioriteetti | Perustelu | Tila | Hyväksyntäkriteeri |
|----|------------------|------------|--------|--------------|-----------|------|-------------------|
| NFR-004 | 11.11.25 | Peruskäytettävyys | Palvelun tavoitellaan olevan käytettävissä 24/7. Lyhyet, suunnitellut käyttökatkot päivitysten vuoksi (esim. öisin) ovat hyväksyttäviä. | Keskitaso | MVP:n perusvaatimus. | Luonnos | Palvelu vastaa health-check-kutsuun 99% ajasta kuukauden aikana (pl. suunnitellut katkot). |
| NFR-005 | 11.11.25 | Vikatilanteiden graceful-käsittely | Jos jokin ulkoinen rajapinta (FMI, Fintraffic) ei vastaa tai kaatuu, mikropalvelu ei saa kaatua. Sen tulee palauttaa virhe hallitusti. | Korkea | Järjestelmän vakaus. | Luonnos | Jos FMI-rajapinta on alhaalla, API-kutsu palauttaa HTTP 503 (Service Unavailable) tai 200 (osittaisella datalla ja virheviestillä) eikä HTTP 500. |
| NFR-006 | 11.11.25 | Ylläpitotoimet | Kehitystiimin tulee pystyä päivittämään palvelu uuteen versioon keskitetysti GitLab CI/CD -putken kautta. | Korkea | Projektin vaatimus. | Luonnos | git push päähaaraan käynnistää automaattisen build-, test- ja deploy-putken. |

#### 7.4.3 Suorituskyky (Performance)

Nämä vaatimukset määrittelevät, kuinka nopeasti järjestelmän tulee vastata käyttäjän toimiin.

| ID | Luotu / Muokattu | Lyhyt nimi | Kuvaus | Prioriteetti | Perustelu | Tila | Hyväksyntäkriteeri |
|----|------------------|------------|--------|--------------|-----------|------|-------------------|
| NFR-007 | 11.11.25 | API-vastausaika | Mikropalvelun tulee aggregoida tiedot (FMI, Fintraffic, Maps) ja palauttaa vastaus Streamlit-käyttöliittymälle kohtuullisessa ajassa. | Keskitaso | Käyttäjäkokemus. | Luonnos | 95% (p95) API-kutsuista (esim. /route-conditions) suoriutuu alle 5 sekunnissa normaaliolosuhteissa. |
| NFR-008 | 11.11.25 | Käyttöliittymän latausaika | Streamlit-web-sovelluksen ensimmäisen latauksen (initial load) tulee olla nopea, jotta käyttäjä ei poistu sivulta. | Keskitaso | Käyttäjäkokemus. | Luonnos | Sivu latautuu interaktiiviseksi (Time to Interactive) alle 3 sekunnissa tavallisella internetyhteydellä. |

#### 7.4.4 Data ja Logiikka

Nämä vaatimukset määrittelevät datan käsittelyn ja "tekoälyn" eli tässä tapauksessa datan aggregointilogiikan vaatimukset.

| ID | Luotu / Muokattu | Lyhyt nimi | Kuvaus | Prioriteetti | Perustelu | Tila | Hyväksyntäkriteeri |
|----|------------------|------------|--------|--------------|-----------|------|-------------------|
| NFR-009 | 11.11.25 | Datan aggregointilogiikka | Palvelun ydinlogiikan tulee osata yhdistää reittipisteet (Maps) niitä lähimpänä oleviin sää- (FMI) ja liikennetietoihin (Fintraffic). | Korkea | Palvelun ydinlupaus. | Luonnos | Testitapaus: Reitille Helsinki-Oulu haetaan säädataa vähintään 3 eri pisteestä reitin varrelta (esim. alku, keskikohta, loppu). |
| NFR-010 | 11.11.25 | Datan kerääminen (Käyttäjä) | Järjestelmä ei saa kerätä tai tallentaa mitään henkilökohtaista tunnistettavaa tietoa (PII) käyttäjistä. Reittihaut ovat väliaikaisia. | Korkea | Rajaus, GDPR. | Luonnos | Tietokanta (jos käytössä MVP:ssä) tai lokitiedostot eivät sisällä käyttäjien IP-osoitteita tai muita pysyviä tunnisteita. |
| NFR-011 | 11.11.25 | Datan kerääminen (Ylläpito) | Järjestelmän tulee kerätä anonyymejä operationaalisia lokitietoja (esim. virheilmoitukset, API-vastausajat) vianjäljitystä varten. | Keskitaso | Ylläpidettävyys | Luonnos | Ylläpitäjä (kehitystiimi) näkee sovelluksen lokivirrat (esim. docker logs) ja voi diagnosoida NFR-005-tyypin virheitä. |

#### 7.4.5 Alusta ja Ympäristö

Nämä vaatimukset määrittelevät teknisen ympäristön, jossa sovellusta ajetaan ja käytetään.

| ID | Luotu / Muokattu | Lyhyt nimi | Kuvaus | Prioriteetti | Perustelu | Tila | Hyväksyntäkriteeri |
|----|------------------|------------|--------|--------------|-----------|------|-------------------|
| NFR-012 | 11.11.25 | Ajoalusta | Mikropalvelu (Python/REST) ja käyttöliittymä (Streamlit) ajetaan kontitetussa ympäristössä dclabra-infrastruktuurissa. | Korkea | Projektin vaatimus. | Luonnos | Sovellus on käynnistettävissä docker-compose up (tai vastaavalla) ja toimii GitLab-ympäristössä. |
| NFR-013 | 11.11.25 | Tuetut selaimet | Web-käyttöliittymän (Streamlit) tulee toimia ja näyttää tiedot oikein yleisimmillä moderneilla selaimilla. | Keskitaso | Käytettävyys. | Luonnos | Sovellus on testattu toimivaksi vähintään Chromen ja Firefoxin uusimmilla desktop-versioilla. |

#### 7.4.6 Turvallisuus (jos halutaan se määritellä)

| ID | Luotu / Muokattu | Lyhyt nimi | Kuvaus | Prioriteetti | Perustelu | Tila | Hyväksyntäkriteeri |
|----|------------------|------------|--------|--------------|-----------|------|-------------------|
| NFR-014 | 11.11.25 | API:n suojaus (Rate Limit) | Mikropalvelun julkiset API-päätepisteet suojataan massakyselyiltä nopeusrajoituksella (Rate Limiting). | Keskitaso | Palvelun vakauden (NFR-004) ja ulkoisten API-kustannusten hallinta. | Luonnos | API-päätepiste (S-002) sallii max 100 kutsua / minuutti / IP-osoite. |

