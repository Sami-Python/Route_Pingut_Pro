# Käyttöohje: Matkahälytysportaali (MVP)

Tarkemmat käyttöohjeet löytyvät myös README.md -tiedostosta. 

## Palvelun tarkoitus

Matkahälytysportaali on web-pohjainen mikropalvelu, joka auttaa autoilijaa arvioimaan tulevan matkan olosuhteita. Palvelu kokoaa yhteen reitin varrella vaikuttavat sää- ja liikennetiedot ja esittää ne selkeänä kokonaisuutena ennen matkaa. Palvelu toimii ilman kirjautumista eikä tallenna käyttäjätietoja.

## Palvelun avaaminen

Palvelu avataan selaimessa sille määritellyssä osoitteessa. Sovellus toimii yleisimmillä moderneilla selaimilla sekä tietokoneella, että mobiililaitteilla. Erillistä asennusta ei tarvita. Kun sivu latautuu, käyttäjälle avautuu näkymä, jossa reitin tiedot voidaan syöttää ja tuloksia tarkastella.

## Reitin syöttäminen

Käyttäjä syöttää lähtöpaikan ja määränpään niille varattuihin kenttiin yhdessä lähtöajan kanssa. Syötteet voivat olla paikkojen nimiä. Palvelu muuntaa syötetyt tiedot automaattisesti koordinaateiksi ja käyttää niitä reitin laskentaan.

MVP-versiossa reititys tukee ainoastaan autoilureittejä. Julkista liikennettä tai yhdistelmäreittejä ei käsitellä.

Kun lähtö- ja määränpää on syötetty, käyttäjä käynnistää reitin haun.

## Reitin ja olosuhteiden haku

Reitin haun jälkeen palvelu laskee autoilureitin ulkoisen karttapalvelun avulla. Samanaikaisesti järjestelmä hakee reitin varrella vaikuttavat liikenne- ja säätiedot.

Liikennetiedot, kuten tietyöt, liikenneonnettomuudet ja kelikamerat, haetaan Fintrafficin avoimista rajapinnoista. Säätiedot ja mahdolliset säävaroitukset haetaan Ilmatieteen laitoksen rajapinnoista. Kaikki tiedot haetaan reaaliaikaisesti.

## Tulosten tarkastelu

Käyttäjälle näytetään karttanäkymä, jossa reitti on esitetty visuaalisesti. Reitin yhteydessä esitetään keskeiset olosuhdetiedot, kuten mahdolliset liikennepoikkeamat, sääolosuhteet ja yksinkertainen riskitason arvio.

Riskitason tarkoituksena on antaa käyttäjälle nopea yleiskuva siitä, kuinka haastavat olosuhteet matkalla voivat olla. Tarkemmat tiedot ovat nähtävissä kartalla ja tekstimuotoisina kuvauksina.

Tulokset päivittyvät aina uuden reittihaun yhteydessä.

## Virhetilanteet

Mikäli jokin ulkoinen rajapinta ei ole käytettävissä tai palauttaa puutteellista dataa, palvelu ilmoittaa tästä käyttäjälle. Tällöin osa tiedoista voi puuttua, mutta sovellus pyrkii silti esittämään saatavilla olevan tiedon.

Jos lähtö- tai määränpää on virheellinen tai sitä ei voida tunnistaa, käyttäjää pyydetään tarkistamaan syöte ja yrittämään uudelleen.

Palvelun käyttö edellyttää toimivaa internet-yhteyttä.

## Käytön päättäminen

Palvelun käyttö voidaan lopettaa sulkemalla selaimen välilehti tai ikkuna. Koska palvelu ei sisällä käyttäjätunnistusta eikä tallenna tietoja, erillisiä uloskirjautumistoimia ei tarvita.

## Rajoitteet MVP-versiossa

Kaikki reittihaut ovat hetkellisiä, eikä tietoja tallenneta pysyvästi.

## Jatkokehitys

Palvelu on suunniteltu siten, että siihen voidaan myöhemmissä kehitysvaiheissa lisätä esimerkiksi käyttäjätilit, automaattiset hälytykset sekä laajempi riskianalyysi. Nämä ominaisuudet eivät kuitenkaan kuulu MVP-versioon.