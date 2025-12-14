# Arkkitehtuuri

![alt text](./img/arkkitehtuuri.png)

Järjestelmä on toteutettu mikropalveluarkkitehtuurin periaatteiden mukaisesti siten, että käyttöliittymä, taustapalvelut ja ulkoiset tietolähteet on erotettu toisistaan selkeiksi kokonaisuuksiksi. Arkkitehtuuri koostuu käyttöliittymäkerroksesta, rajapintakerroksesta sekä ulkoisista palveluista. Tämä rakenne tukee skaalautuvuutta, ylläpidettävyyttä ja palveluiden itsenäistä kehittämistä.

## Käyttöliittymäkerros (Front)

Käyttöliittymäkerros muodostuu Streamlit-pohjaisesta web-käyttöliittymästä sekä autentikointikomponentista. Streamlit vastaa käyttäjän kanssa tapahtuvasta vuorovaikutuksesta ja esittää sovelluksen tarjoaman tiedon selkeässä ja visuaalisessa muodossa. Käyttöliittymä toimii kevyenä front-end-ratkaisuna, joka kommunikoi taustapalveluiden kanssa rajapintojen kautta.

Autentikointikomponentti huolehtii käyttäjän tunnistamiseen liittyvistä toiminnoista. Vaikka MVP-versiossa ei ole varsinaista käyttäjätunnistusta, arkkitehtuuri on suunniteltu siten, että autentikointi voidaan tarvittaessa ottaa käyttöön myöhemmässä kehitysvaiheessa ilman merkittäviä muutoksia muuhun järjestelmään.

## Rajapintakerros ja API Gateway

Käyttöliittymä kommunikoi taustajärjestelmän kanssa API Gatewayn kautta. API Gateway toimii keskitettynä rajapintana, jonka kautta kaikki ulkoiset ja sisäiset API-kutsut kulkevat. Tämä mahdollistaa liikenteen hallinnan, yhtenäisen rajapintarakenteen sekä tietoturvan keskittämisen yhteen kerrokseen.

API Gatewayn kautta järjestelmä hyödyntää useita ulkoisia tietolähteitä, kuten Ilmatieteen laitoksen säädataa (FMI), Fintrafficin liikennedataa, kartta- ja reitityspalveluita (Maps). Näiden palveluiden eriyttäminen rajapintakerrokseen vähentää käyttöliittymän riippuvuuksia ja parantaa järjestelmän joustavuutta.

## Ulkoiset palvelut ja tietolähteet

Ulkoiset palvelut tarjoavat järjestelmälle ajantasaista tietoa liikenne- ja sääolosuhteista. Kukin palvelu on itsenäinen kokonaisuus, johon järjestelmä ottaa yhteyden standardoitujen rajapintojen kautta. Tämä mahdollistaa sen, että yksittäinen palvelu voidaan tarvittaessa vaihtaa tai päivittää ilman, että koko järjestelmän toiminta vaarantuu.

Tietolähteiden käyttö perustuu avoimiin rajapintoihin, ja niiden tarjoama data käsitellään mikropalvelussa ennen kuin se välitetään käyttöliittymälle käyttäjälle esitettäväksi.


## Tiedonkulku kokonaisuudessaan

Käyttäjä tekee toimintoja Streamlit-käyttöliittymässä, joka välittää pyynnöt API Gatewayn kautta taustapalveluille. Taustapalvelut hakevat tarvittavan datan ulkoisista rajapinnoista, käsittelevät sen ja palauttavat tulokset käyttöliittymälle. Kaikki osat toimivat löyhästi kytkettyinä, mikä tukee mikropalveluarkkitehtuurin perusperiaatteita.