# Työkalut ja teknologiat

## 3 Työkalut ja teknologiat
### 3.1 Kehitysympäristö
Projektin kehitys toteutetaan mikropalveluarkkitehtuurin periaatteiden mukaisesti kontitetussa ympäristössä.

### 3.2 Versionhallinta ja dokumentointi
- **GitLab:** Projektin versionhallinta. Kaikki koodi, dokumentaatio ja konfiguraatiot tallennetaan ja hallitaan keskitetysti. Jokaisella tiimin jäsenellä on oma kehityshaara (branch), ja muutokset yhdistetään päähaaraan (main) vasta tarkistuksen ja testauksen jälkeen.GitLabin Issues- ja Merge Request -toiminnot tukevat sprinttien tehtävien hallintaa ja katselmointia. Kaikki commit-viestit kirjoitetaan kuvaavasti ja yhdenmukaisella käytännöllä.
- **HedgeDoc:** Dokumentaatio tuotetaan Markdown-muodossa (README, Wiki) ja säilytetään GitLabissa. Ryhmän sisäistä dokumentointia ja kokousmuistioita varten käytetään HedgeDocia. 
- **Clockify:** Työajanseuranta
- **Swagger/OpenAPI:** Rajapintojen tekninen dokumentaatio laaditaan Swagger/OpenAPI-muodossa, mikä varmistaa rajapintojen läpinäkyvyyden ja helpon integroitavuuden muihin järjestelmiin.

### 3.3 Työkalut ja kirjastot

**Kehitysympäristö ja versionhallinta**

Docker - Kontitus ja kehitysympäristö  
[Dokumentaatio](https://docs.docker.com/)

GitLab - Versionhallinta ja CI/CD  
[Dokumentaatio](https://docs.gitlab.com/)

**Kommunikaatio**

Microsoft Teams - Tiimin viestintä  
[Dokumentaatio](https://docs.microsoft.com/en-us/microsoftteams/)

Discord - Reaaliaikainen kommunikaatio
[Dokumentaatio](https://discord.com/developers/docs)

**Dokumentaatio**

HedgeDoc - Yhteiskirjoittaminen
[Dokumentaatio](https://docs.hedgedoc.org/)

MkDocs - Tekninen dokumentaatio
[Dokumentaatio](https://www.mkdocs.org/)

GitLab Wiki - Projektidokumentaatio
[Dokumentaatio](https://docs.gitlab.com/ee/user/project/wiki/)

**API-integraatiot**

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
