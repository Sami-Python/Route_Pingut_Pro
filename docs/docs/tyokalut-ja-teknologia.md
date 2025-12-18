# Työkalut ja teknologiat

## Kehitysympäristö

Projektin kehitys toteutetaan mikropalveluarkkitehtuurin periaatteiden mukaisesti kontitetussa ympäristössä. Kontitus mahdollistaa yhtenäisen ja toistettavan kehitysympäristön kaikille tiimin jäsenille sekä helpottaa sovelluksen siirrettävyyttä eri ympäristöjen välillä. Kehitysympäristö tukee mikropalvelun eriyttämistä omaksi kokonaisuudekseen ja mahdollistaa sen hallitun testaamisen ja jatkokehittämisen.

## Versionhallinta ja dokumentointi

Projektin versionhallinta toteutetaan GitLab-alustalla, johon kaikki lähdekoodi, dokumentaatio ja konfiguraatiot tallennetaan keskitetysti. Jokaisella tiimin jäsenellä on oma kehityshaara/kehityshaarat, ja muutokset yhdistetään päähaaraan vasta tarkistuksen ja testauksen jälkeen. GitLabin Issues- ja Merge Request -toimintoja hyödynnetään sprinttien tehtävien hallintaan, katselmointiin ja muutosten arviointiin. Commit-viestit kirjoitetaan yhdenmukaisella ja kuvaavalla tavalla, mikä parantaa muutosten jäljitettävyyttä.

Dokumentaatio tuotetaan Markdown-muodossa ja säilytetään osana projektin versionhallintaa. Tekniseen dokumentaatioon käytetään tätä MkDocs-työkalua, jonka avulla dokumentaatio voidaan esittää selkeänä ja helposti navigoitavana kokonaisuutena. Ryhmän sisäiseen yhteiskirjoittamiseen ja kokousmuistioihin hyödynnetään HedgeDocia, ja projektin yleinen dokumentaatio pidetään saatavilla myös GitLab Wikissä. Työajanseurantaan käytetään Clockify-työkalua, jonka avulla projektin ajankäyttöä voidaan seurata ja arvioida.

Rajapintojen tekninen dokumentaatio laaditaan Swagger/OpenAPI-standardin mukaisesti. Tämä varmistaa rajapintojen läpinäkyvyyden, selkeyden ja helpon integroitavuuden muihin järjestelmiin sekä tukee mikropalvelun jatkokehitystä.

## Työkalut ja kirjastot

Kehitystyössä hyödynnetään useita ohjelmistotyökaluja ja kirjastoja, jotka tukevat mikropalvelun toteutusta, viestintää ja dokumentointia. Kontitukseen ja kehitysympäristön hallintaan käytetään Dockeria, ja versionhallinta sekä jatkuva integraatio toteutetaan GitLabin avulla. Tiimin sisäisessä viestinnässä käytetään Microsoft Teamsia ja Discordia, jotka tukevat sekä suunnittelua että päivittäistä yhteistyötä.

Mikropalvelun rajapinnat ja sovelluslogiikka toteutetaan Python-pohjaisilla teknologioilla. FastAPI toimii REST-rajapintojen kehityskehyksenä ja Uvicorn ASGI-palvelimena. Web-käyttöliittymän toteutuksessa hyödynnetään Streamlitia. Ulkoisten palveluiden kanssa kommunikointi toteutetaan HTTP-pyyntöjen avulla, ja datan käsittelyssä hyödynnetään Pandas- ja NumPy-kirjastoja. Kartta- ja reittitietojen visualisointiin käytetään Pydeck- ja Plotly-kirjastoja, ja HERE Maps -palvelun reittidatan käsittelyssä hyödynnetään Flexpolyline-kirjastoa.

Sovellus hyödyntää useita avoimia ja kaupallisia rajapintoja, kuten HERE Maps -kartta- ja reitityspalvelua, Open-Meteo-säärajapintaa sekä Fintrafficin avointa liikennedataa. Lisäksi käytössä ovat Google Calendar API ja Microsoft Graph API, joiden avulla palvelu voidaan integroida käyttäjän kalenteripalveluihin. Ympäristömuuttujien hallinnassa käytetään python-dotenv-kirjastoa ja päivämäärä- sekä aikakäsittelyssä python-dateutil-kirjastoa.

## Linkit
Docker - Kontitus ja kehitysympäristö  
[Dokumentaatio](https://docs.docker.com/)

GitLab - Versionhallinta ja CI/CD  
[Dokumentaatio](https://docs.gitlab.com/)

Microsoft Teams - Tiimin viestintä  
[Dokumentaatio](https://docs.microsoft.com/en-us/microsoftteams/)

Discord - Reaaliaikainen kommunikaatio
[Dokumentaatio](https://discord.com/developers/docs)

HedgeDoc - Yhteiskirjoittaminen
[Dokumentaatio](https://docs.hedgedoc.org/)

MkDocs - Tekninen dokumentaatio
[Dokumentaatio](https://www.mkdocs.org/)

GitLab Wiki - Projektidokumentaatio
[Dokumentaatio](https://docs.gitlab.com/ee/user/project/wiki/)

HERE Maps - Kartta- ja reitityspalvelut
[Dokumentaatio](https://developer.here.com/documentation)

Open-Meteo - Säädata
[Dokumentaatio](https://open-meteo.com/en/docs)

Google Calendar API - Kalenteriintegraatio
[Dokumentaatio](https://developers.google.com/calendar)

Microsoft Graph API (Outlook) - Outlook-integraatio
[Dokumentaatio](https://docs.microsoft.com/en-us/graph/)

Fintraffic - Liikennedata
[Dokumentaatio](https://www.fintraffic.fi/fi/fintrafficin-avoin-data)

**Python-kirjastot**

| Kirjasto | Käyttötarkoitus | Dokumentaatio |
|----------|-----------------|---------------|
| FastAPI | REST API -kehys | [Dokumentaatio](https://fastapi.tiangolo.com/) |
| Uvicorn | ASGI-palvelin | [Dokumentaatio](https://www.uvicorn.org/) |
| Streamlit | Web-käyttöliittymä | [Dokumentaatio](https://docs.streamlit.io/) |
| Requests | HTTP-pyynnöt | [Dokumentaatio](https://docs.python-requests.org/) |
| Pandas | Datan käsittely | [Dokumentaatio](https://pandas.pydata.org/docs/) |
| NumPy | Numeerinen laskenta | [Dokumentaatio](https://numpy.org/doc/) |
| Pydeck | Karttavisualisoinnit | [Dokumentaatio](https://pydeck.gl/) |
| Plotly | Interaktiiviset visualisoinnit | [Dokumentaatio](https://plotly.com/python/) |
| Flexpolyline | HERE Maps polyline-dekoodaus | [Dokumentaatio](https://pypi.org/project/flexpolyline/) |
| Python-dotenv | Ympäristömuuttujat | [Dokumentaatio](https://pypi.org/project/python-dotenv/) |
| Python-dateutil | Päivämääräkäsittely | [Dokumentaatio](https://dateutil.readthedocs.io/) |
