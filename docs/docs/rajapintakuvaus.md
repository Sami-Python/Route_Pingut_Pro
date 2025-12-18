# Rajapintakuvaus

Tässä luvussa kuvataan Matkahälytysportaalin MVP-version käyttämät sisäiset ja ulkoiset rajapinnat, niiden käyttötarkoitukset, tietovirrat sekä tekniset reunaehdot. Rajapintakuvaus toimii pohjana järjestelmän toteutukselle, testaukselle ja jatkokehitykselle. MVP-versiossa järjestelmä ei sisällä käyttäjätunnistusta, kalenteri-integraatioita, ilmoituspalveluita eikä pysyvää tietovarastoa.

## Rajapintojen yleiskuva

Matkahälytysportaali on toteutettu mikropalveluna, joka toimii rajapintojen yhdistäjänä. Käyttöliittymä kommunikoi ainoastaan oman backend-rajapinnan kanssa, joka puolestaan hakee ja yhdistää tiedot ulkoisista liikenne-, sää- ja karttapalveluista.

Kaikki rajapinnat käyttävät HTTPS-yhteyttä ja JSON-muotoista tiedonsiirtoa.

| Komponentti / rajapinta  | Tarkoitus                              | Protokolla        | Autentikointi     | Päivitystiheys | Huomiot                         |
| ------------------------ | -------------------------------------- | ----------------- | ----------------- | -------------- | ------------------------------- |
| Streamlit Web UI         | Käyttöliittymä                         | HTTPS             | Ei autentikointia | Reaaliaikainen | MVP ilman käyttäjätiliä         |
| Backend API (FastAPI)    | Reitti- ja olosuhdetiedon yhdistäminen | REST / JSON       | Ei autentikointia | Reaaliaikainen | API Gateway                     |
| HERE Maps API            | Reititys ja geokoodaus                 | REST / JSON       | API-avain         | Reaaliaikainen | Autoilureitit                   |
| Fintraffic / Digitraffic | Liikenne- ja tiesäätiedot              | REST / JSON       | Avoin             | 1–5 min        | Onnettomuudet, tietyöt, kamerat |
| Ilmatieteen laitos (FMI) | Sää- ja tiesäädata                     | REST / XML / JSON | Avoin             | 5–10 min       | Ennusteet ja varoitukset        |

## API-rakenne ja yhdyskäytävä (API Gateway)

Backend toimii keskitettynä API Gatewayna, joka kokoaa eri ulkoisista rajapinnoista saadun datan ja palauttaa sen käyttöliittymälle yhtenäisessä muodossa.

Päärajapinnan toteutus sijaitsee tiedostossa api/main.py.

| Metodi | Polku     | Kuvaus                                                        |
| ------ | --------- | ------------------------------------------------------------- |
| GET    | `/`       | Palauttaa API:n metatiedot ja saatavilla olevat endpointit    |
| GET    | `/health` | Tarkistaa palvelun ja ulkoisten rajapintojen saavutettavuuden |

## Reititys- ja karttarajapinta (HERE Maps)

Tiedosto: api/here_maps_api.py
Polku: /here

Tämä rajapinta vastaa osoitteiden muuntamisesta koordinaateiksi sekä autoilureittien laskemisesta.

| Metodi | Polku           | Parametrit                                         | Kuvaus                              |
| ------ | --------------- | -------------------------------------------------- | ----------------------------------- |
| GET    | `/here/geocode` | `address`                                          | Muuntaa osoitteen koordinaateiksi   |
| POST   | `/here/route`   | `origin_lat`, `origin_lon`, `dest_lat`, `dest_lon` | Laskee reitin, keston ja etäisyyden |


## Liikennetietorajapinta (Fintraffic / Digitraffic)

Tiedosto: api/digitraffic_api.py
Polku: /traffic

Rajapinta hakee liikennetiedot reitin varrelta Digitrrafficin avoimesta rajapinnasta.

| Metodi | Polku                   | Parametrit     | Kuvaus                           |
| ------ | ----------------------- | -------------- | -------------------------------- |
| GET    | `/traffic/messages`     | `route_coords` | Liikennehäiriöt ja onnettomuudet |
| GET    | `/traffic/maintenance`  | `route_coords` | Tietyöt ja kunnossapito          |
| GET    | `/traffic/cameras`      | `route_coords` | Kelikamerat                      |
| GET    | `/traffic/road-weather` | `route_coords` | Tiesääasemat                     |

Reitin koordinaatit annetaan muodossa lat1,lon1;lat2,lon2;....

## Säärajapinta (Ilmatieteen laitos)

Tiedosto: api/weather_api.py
Polku: /weather

Säärajapinta hakee sääennusteet ja varoitukset reitin alku- ja loppupisteille sekä tarvittaessa reitin varrelta.

| Metodi | Polku            | Parametrit                                 | Kuvaus                           |
| ------ | ---------------- | ------------------------------------------ | -------------------------------- |
| GET    | `/weather/point` | `lat`, `lon`                               | Sääennuste koordinaattipisteelle |
| GET    | `/weather/route` | `from_lat`, `from_lon`, `to_lat`, `to_lon` | Sääennuste reitin päihin         |

Säädataa käytetään osana riskitason arviointia, mutta MVP-versiossa ei tehdä käyttäjäkohtaisia päätöksiä tai pitkäaikaista ennusteseurantaa.

## Datan yhdistäminen ja vasteformaatti

Backend yhdistää HERE Mapsin reittidatan, Fintrafficin liikennetiedot ja FMI:n säädatan yhdeksi JSON-vastaukseksi, joka palautetaan käyttöliittymälle.

Vaste sisältää:
– reitin perustiedot (kesto, etäisyys)
– reitin varrella havaitut liikennepoikkeamat
– sääolosuhteet ja mahdolliset varoitukset
– yksinkertaisen riskiluokituksen (esim. matala / kohonnut / korkea)

Kaikki data käsitellään reaaliaikaisesti, eikä sitä tallenneta pysyvästi.

## Jatkokehitys (ei MVP)

Arkkitehtuuri tukee seuraavia laajennuksia tulevaisuudessa:
– käyttäjätunnistusta (OAuth2 / JWT)
– kalenteri-integraatioita (Google, Outlook, iCal)
– ilmoituspalveluita (push, email, SMS)
– pysyvää tietovarastoa käyttäjäasetuksille ja historiatiedolle

Näitä rajapintoja ei kuitenkaan käytetä eikä testata MVP-versiossa.
