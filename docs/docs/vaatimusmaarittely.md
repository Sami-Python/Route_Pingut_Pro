# Vaatimusmäärittely

## 7 Vaatimusmäärittely

### 7.1 Käyttötapaukset ja käyttäjätarinat


Järjestelmän nimi: Matkahälytysportaali / App
Kuvaus: Käyttäjä näkee tulevaan reittiin ja matkaan liittyvät hälytykset ja huomioitavat asiat sekä saa muistutuksen ennen lähtöä. Sovellus hyödyntää eri tietolähteitä (esim. Fintraffic ja FMI) reittien riskien ja olosuhteiden arviointiin.
Laajuus: Mobiili- ja web-versio (?)
Sidosryhmät: Loppukäyttäjät, palvelun ylläpitäjät, kalenteripalvelun tarjoajat, sää- ja liikennedatatoimittajat

**2. Oletukset ja rajaukset**

Käyttäjällä on toimiva internet-yhteys ja sijaintilupa.

Käyttäjä voi sallia kalenterin käytön reittien automaattiseen luontiin.

MVP-versiossa tuetaan vain autoilureittejä (ei julkista liikennettä).

**3. Tekijät**

| Tekijä              | Tyyppi       | Kuvaus                                             |
| :------------------ | :----------- | :------------------------------------------------- |
| Käyttäjä            | Pääosallinen | Asettaa matkan ja vastaanottaa hälytykset          |
| Kalenteripalvelu    | Toissijainen | Tarjoaa lähtö- ja määränpäätiedot                  |
| Sijaintipalvelu     | Toissijainen | Antaa nykyisen sijainnin                           |
| Liikennetilanne-API | Toissijainen | Tuo tiedot onnettomuuksista, ruuhkista, tietyöistä |
| Sää/Kelitieto-API   | Toissijainen | Tuo keliolosuhteet ja näkyvyystiedot               |
| Joukkoliikenne-API  | Valinnainen  | Antaa julkisen liikenteen poikkeamatiedot          |


**4. Tietolähteet ja luvat**

| Tietolähde               | Käyttötarkoitus                               | API-saatavuus |
| :----------------------- | :-------------------------------------------- | :------------ |
| Fintraffic / Digitraffic | Liikennetilanne, tietyöt, kelikamerat, tiesää | ✅ Avoin API   |
| Ilmatieteen laitos (FMI) | Sääennusteet ja tiesää                        | ✅ Avoin API   |
| Digitransit / HSL        | Joukkoliikennepoikkeamat                      | ✅ Avoin API   |


**5. Käyttötapaukset**

| Tunnus | Nimi                              | Kuvaus                                                                                     |
| :----- | :-------------------------------- | :----------------------------------------------------------------------------------------- |
| UC01   | Aseta tuleva matka                | Käyttäjä syöttää lähtöajan, lähtöpisteen ja määränpään käsin, sijainnista tai kalenterista |
| UC02   | Muistuta lähdön lähestyessä       | Sovellus ilmoittaa käyttäjälle lähestyvästä lähdöstä ja näyttää pikatilannekuvan           |
| UC03   | Laske reitti & kerää varoitukset  | Hakee reitin ja siihen liittyvät liikenne- ja kelitiedot                                   |
| UC04   | Näytä hälytykset & suositukset    | Näyttää käyttäjälle yhteenvetona reitin riskit ja mahdolliset suositukset                  |
| UC05   | Rerouttaa tai säädä lähtöaikaa    | Tarjoaa vaihtoehtoisen reitin tai ehdottaa lähtöajan muuttamista                           |
| UC06   | Aseta ilmoitusten taso & kanavat  | Käyttäjä määrittää ilmoitusten tyypin ja kriittisyysrajan                                  |
| UC07   | Hallinnoi lupia & tietolähteitä   | Käyttäjä voi hyväksyä tai perua sijainti- ja kalenteriluvat                                |
| UC08   | Tallenna palaute & paranna mallia | Käyttäjä antaa palautetta hälytysten hyödyllisyydestä                                      |

**6. Yksityiskohtaiset käyttötapaukset**

**UC01 – Aseta tuleva matka**

| Osa                           | Kuvaus                                                                                                                                        |
| :---------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------- |
| **Tavoite**                   | Käyttäjä määrittää tulevan matkan tiedot                                                                                                      |
| **Pääosallinen**              | Käyttäjä                                                                                                                                      |
| **Esiehdot**                  | Sijainti- ja kalenteriluvat on myönnetty                                                                                                      |
| **Peruspolku**                | 1. Käyttäjä syöttää lähtö- ja määränpään<br>2. Järjestelmä tunnistaa kalenterimerkinnän (jos käytössä)<br>3. Matka tallennetaan järjestelmään |
| **Vaihtoehdot / poikkeukset** | Kalenterimerkintä ei sisällä paikkaa → pyydetään manuaalinen syöttö                                                                           |
| **Jälkiehdot**                | Matka on tallennettu ja muistutus asetettu (UC02)                                                                                             |

**UC02 – Muistuta lähdön lähestyessä**

| Osa                           | Kuvaus                                                                                                                                           |
| :---------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Tavoite**                   | Käyttäjää muistutetaan lähdöstä ajoissa                                                                                                          |
| **Pääosallinen**              | Käyttäjä                                                                                                                                         |
| **Esiehdot**                  | UC01 suoritettu                                                                                                                                  |
| **Peruspolku**                | 1. Järjestelmä havaitsee, että lähtöaika lähestyy<br>2. Sovellus hakee reitin tilannekuvan (UC03)<br>3. Käyttäjälle lähetetään push-/äänihälytys |
| **Vaihtoehdot / poikkeukset** | Hälytykset hiljaisessa tilassa → näytetään vain ilmoitus                                                                                         |
| **Jälkiehdot**                | Käyttäjä saa ajantasaisen reittitilanteen                                                                                                        |

**UC03 – Laske reitti & kerää varoitukset**

| Osa                           | Kuvaus                                                                                                                                                  |
| :---------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Tavoite**                   | Selvittää reitin ja mahdolliset riskit                                                                                                                  |
| **Pääosallinen**              | Järjestelmä                                                                                                                                             |
| **Esiehdot**                  | UC01 suoritettu, tietolähteet saatavilla                                                                                                                |
| **Peruspolku**                | 1. Määritetään reitti<br>2. Haetaan liikennetiedot (Fintraffic)<br>3. Haetaan kelitiedot (FMI)<br>4. Arvioidaan riskit ja luokitellaan kriittisyystasot |
| **Vaihtoehdot / poikkeukset** | API ei vastaa → käytetään välimuistia                                                                                                                   |
| **Jälkiehdot**                | Reittitiedot ja varoitukset valmiit UC04:lle                                                                                                            |


**UC04 – Näytä hälytykset & suositukset**

| Osa              | Kuvaus                                                                                           |
| :--------------- | :----------------------------------------------------------------------------------------------- |
| **Tavoite**      | Esittää käyttäjälle riskit ja ehdotukset                                                         |
| **Pääosallinen** | Käyttäjä                                                                                         |
| **Esiehdot**     | UC03 valmis                                                                                      |
| **Peruspolku**   | 1. Näytetään reitin tiiviste ja varoitukset<br>2. Näytetään arvioitu viive ja suositukset (UC05) |
| **Jälkiehdot**   | Käyttäjä voi reagoida suositukseen tai ohittaa sen                                               |


**UC05 – Rerouttaa tai säädä lähtöaikaa**

| Osa              | Kuvaus                                                                                                              |
| :--------------- | :------------------------------------------------------------------------------------------------------------------ |
| **Tavoite**      | Tarjota vaihtoehto reitin tai lähtöajan muutokseen                                                                  |
| **Pääosallinen** | Käyttäjä                                                                                                            |
| **Peruspolku**   | 1. Järjestelmä laskee vaihtoehdot<br>2. Käyttäjä valitsee uuden reitin tai lähtöajan<br>3. Päivitetään UC01 ja UC02 |
| **Jälkiehdot**   | Reitti ja muistutus päivitetty                                                                                      |
**UC06 – Aseta ilmoitusten taso & kanavat**

| Osa              | Kuvaus                                                                                    |
| :--------------- | :---------------------------------------------------------------------------------------- |
| **Tavoite**      | Käyttäjä säätää ilmoitusten tasoa                                                         |
| **Pääosallinen** | Käyttäjä                                                                                  |
| **Peruspolku**   | 1. Käyttäjä valitsee ilmoituskanavat ja kriittisyyskynnyksen<br>2. Asetukset tallennetaan |
| **Jälkiehdot**   | Ilmoitukset toimivat asetusten mukaisesti                                                 |

**UC07 – Hallinnoi lupia & tietolähteitä**

| Osa              | Kuvaus                                                                                                                      |
| :--------------- | :-------------------------------------------------------------------------------------------------------------------------- |
| **Tavoite**      | Käyttäjä hallinnoi kalenteri- ja sijaintilupia                                                                              |
| **Pääosallinen** | Käyttäjä                                                                                                                    |
| **Peruspolku**   | 1. Käyttäjä tarkastelee käytössä olevia lupia<br>2. Käyttäjä sallii tai poistaa luvat<br>3. Järjestelmä tallentaa muutokset |
| **Jälkiehdot**   | Lupatiedot päivitetty     |

**UC08 – Tallenna palaute & paranna mallia**

| Osa              | Kuvaus                                                                                                 |
| :--------------- | :----------------------------------------------------------------------------------------------------- |
| **Tavoite**      | Käyttäjä antaa palautetta hälytysten hyödyllisyydestä                                                  |
| **Pääosallinen** | Käyttäjä                                                                                               |
| **Peruspolku**   | 1. Käyttäjä arvioi varoituksen (hyödyllinen / ei hyödyllinen)<br>2. Palaute tallennetaan analytiikkaan |
| **Jälkiehdot**   | Mallin kehitysdata tallentunut                                                                         |

### 7.4 Ei-toiminnalliset vaatimukset

| Kategoria        | Vaatimus                                   |
| :--------------- | :----------------------------------------- |
| **Suorituskyky** | Reitin laskenta < 5 s API-kutsujen jälkeen |
| **Käytettävyys** | Käyttäjän toiminnot max 2 napautusta       |
| **Luotettavuus** | Offline-tila käyttää välimuistitietoja     |
| **Tietoturva**   | GDPR-noudatus, salatut yhteydet            |
| **Lokitus**      | Virhelokit ja anonyymianalytiikka käytössä |



### 7.2 Käyttötapauskaavio

![](https://gitlab.dclabra.fi/wiki/uploads/29f6badb-b518-4a3c-b96f-05e037865394.png)
