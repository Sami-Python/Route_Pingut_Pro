## Alustava ominaisuuksien määrittely

Autoilijan opas
- Määritä reitti
- Ilmatieteenlaitos sää + varoitukset
- Fintraff kuvat reitiltä, tienpinta, ennuste
- Ajoneuvojen määrä, keskinopeus
- Tietyöt
- Liikenneonnettomuudet
- Google Maps API ruuhkatilanne?

## Arviointi

Koska toimeksiannot vaihtelevat laajudeltaan ja sisällöltään jonkin verran, kurssi arvioidaan Hyväksytty / Hylätty. Hyväksyttyyn arvosanaan riittävät kriteerit mukailevat Scrum-kehitysprosessia, sekä aiemmissa projekteissa käytettyjä dokumentointikäytäntöjä:

    TYÖAIKA: Projektin kokonaisajankäytön tulee olla välillä 90-150 tuntia per opiskelija, ja työaika tulee olla todennettavissa työajanseurannan avulla (clockify.me).

    TEHTÄVÄT: Riittävä määrä projektin tavoitteiden mukaisia tehtäviä (issues) tulee olla avattu, käsitelty ja suljettu sprinttien aikana. Tehtävien määrä ja laajuus arvioidaan projektin vaatimusten mukaisesti. Hyvä nyrkkisääntö on tehtävä (issue) per työpäivä. Enemmänkin se voi olla.

    DOKUMENTAATIO: Projektin dokumentaation tulee kattaa ainakin työn kulku, valitut teknologiat ja arkkitehtuuri sekä merkittävät päätökset ja perustelut niiden taustalla. Dokumentoitavia asioita ovat:
        vaatimusmäärittely,
        testaussuunnitelma,
        rajapintakuvaus,
        mikropalvelun käyttöohje ja
        Scrum-seremonioiden raportointi ryhmän blogiin (dokumenttipohja)
            suunnittelupalaverit
            dailyt
            muut

    DEMOT: Projektin väli- ja loppudemo, sekä aktiivinen osallistuminen muiden ryhmien demoihin.

    OPPIMISPÄIVÄKIRJA: Jäsenten tulee pitää henkilökohtaista oppimispäiväkirjaa, jossa he reflektoivat oppimiskokemuksia, haasteita ja projektin aikana tehtyjä oivalluksia. Oppimispäiväkirjasta tulee löytyä projektissa käytetty työaika, sekä yhteenveto tekemistäsi tehtävistä.

Dokumentoinnissa ja raportoinnissa pyritään riittävän hyvään - ei lähdetä rakentamaan näistä liian raskasta prosessia.

## Linkkejä

- Ryhmän blogi: https://gitlab.dclabra.fi/wiki/gVgp2Z4WSLugvnE6BPzltw?view

## Arkkitehtuuri

![arkkitehtuuri](./img/arkkitehtuuri.png)

## Kalenteri API demo

HUOM! MkDocs kontti ei toimi tässä haarassa

### Docker

```docker compose up --build -d```

Kaksi konttia käynnistyy. Toisessa fastapi toteutus (localhost:8000) ja toisessa streamlit (localhost:8501)

### FastAPI

FastAPI:n dokumentaatioon pääset käsiksi: http://localhost:8000/docs

### Streamlit

Streamlit ympäristöön pääset käsiksi: http://localhost:8501

### Kalenteri

Voit kokeilla oman lukkarin tiedoston hakua tai käyttää tätä linkkiä esimerkkinä: 
https://lukkarit.kamk.fi/ical.php?hash=E74AC94AE7A19AC99110C39EE535C0DBB0DF8AAE




## MkDocs + Nginx (Docker) lyhyet käyttöohjeet

- Dockerfile rakentaa MkDocs-sivuston (mkdocs build) pakkaa valmiit HTML-sivut Nginx-palvelimeen
- nginx.conf määrittää miten Nginx palvelee staattisia sivuja.
- docker-compose.yml / käyttää automaattista uudelleenkäynnistystä
- käyttää porttia .env-tiedostosa

**Buildaa konntti**
```
docker compose build
```

**Käynnistä Docker**
```
docker compose up -d
```
Localhost ->
```
http://localhost:8080
```

*Kun muokkaat MkDocsia, buildaa ja käynnistä kontti uudellen*

Sammuta
```
docker compose stop
```
Poista kontti
```
docker compose down
```
Mikäli jotain jää kummittelemaan aja
```
docker compose down --volumes --remove-orphans
docker compose build
docker compose up -d
```
