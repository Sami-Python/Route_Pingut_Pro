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

```mermaid
%%{init: { "fontFamily": "GitLab Sans" }}%%
architecture-beta
    group api(cloud)[API gateway]
    group front(internet)[Front]
    group storage(disk)[Storage]
    
    service ui(internet)[Streamlit]in front
    service auth(internet)[Autentikointi]in front

    service db(database)[Database] in storage
    
    service fmi(server)[FMI] in api
    service fintraf(server)[Fintraffic] in api
    service hsl(server)[HSL] in api
    service maps(server)[Maps] in api
    
    ui:R -- L:auth
    auth{group}:B -- T:db{group}
    ui{group}:L -- R:fmi{group}
```