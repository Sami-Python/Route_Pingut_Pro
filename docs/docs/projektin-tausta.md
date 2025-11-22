# Projektin tausta

## 1. Mikropalvelu MVP Projektissamme

MVP eli Minimum Viable Product toimii apuna meidän mikropalvelun kehittämisessä, sillä se auttaa keskittymään olennaiseen ja luo toiminnalle sopivat rajat. Mikropalvelun tuottamisen perusidea on, että luodaan palvelu, joka keskittyy tekemään yhden asian hyvin

Eli MVP:n avulla:

- Keskitymme ydintoiminnan kehittämiseen
- Luomme selkeän ja helppokäyttöisen, mutta kapean API-rajapinnan
- Luomme nopeasti käyttöönotettavan version johon on helppo tehdä testauksia

Tähän konseptointiin liittyy olennaisesti myös oikean MVP-arkkitehtuurin valinta. Vaikka MVP:n tavoitteena on julkaisunopeus, varhaisessa vaiheessa tehty arkkitehtuurivalinta vaikuttaa suoraan tuotteen pitkän aikavälin menestykseen, kuten sen skaalautuvuuteen, kustannustehokkuuteen ja ylläpidettävyyteen [^1].

**Arvolupaus**

"Palvelun ydinlupaus on tarjota autoilijalle reittikohtainen, reaaliaikainen arvio sää- ja liikenneolosuhteista."

**Käyttäjätarina**

Arvolupaus voidaan purkaa konkreettiseksi käyttäjätarinaksi (User Story), joka ohjaa teknistä kehitystä projektissa. Palvelumme ydin voidaan kuvata näin: "Autoilevana korkeakouluyhteisön jäsenenä haluan nähdä yhdellä silmäyksellä tulevan matkani sää- ja liikennetiedot, jotta voin arvioida matkaan kuluvan ajan ja varautua poikkeaviin olosuhteisiin." Tämä käyttäjätarina määrittelee, kuka käyttäjä on (kohdeasiakas), mitä hän haluaa tehdä (toiminnallisuus) ja miksi hän haluaa sen tehdä (saavutettava hyöty).

Seuraavana muutamme käyttäjätarinan pienimmäksi mahdolliseksi ominaisuusjoukoksi (MVP feature set). Yksittäinen käyttäjätarina on usein vielä liian laaja ja epämääräinen kerralla toteutettavaksi. Siksi se pilkotaan ("chunking") pienempiin, itsenäisiin ja testattaviin osiin. Esim. 'säätietojen haku', 'liikennetietojen haku' ja 'reitin muodostaminen' ovat kukin omia, pienempiä "paloja". Tämä pienissä erissä (small batch sizes) työskentely on toimivampaa, sillä se mahdollistaa nopeamman palautteen saamisen ja vähentää riskiä rakentaa vääriä asioita. Lopullinen MVP-kandidaatti muodostuu, kun nämä pienet ominaisuuspalat priorisoidaan sen mukaan, mitkä tuottavat eniten asiakasarvoa (Value) pienimmällä toteutustyöllä (Effort) [^2].

**Tekoälytuotteen kehittäminen MVP:n avulla**

MVP lähestymistapa sopii tämän kaltaiseen projektiin, sillä tekoälyprojektit ovat luonteeltaan kokeellisia ja data-intensiivisiä, mikä tekee niistä riskialttiita. Rakentamalla tekoälyominaisuuden (kuten meidän tapauksessamme datan aggregointilogiikan) omaksi, kapeasti määritellyksi mikropalvelukseen MVP-periaatteella, saavutamme kaksi etua:

- Eristämme monimutkaisen logiikan omaan palveluunsa, mikä vähentää koko järjestelmän riskiä.
- MVP pakottaa meidät aloittamaan yksinkertaisimmalla mahdollisella mallilla tai logiikalla ja keräämään heti palautetta sen tuottamasta arvosta. 

Nämä estävät meitä investoimasta liikaa monimutkaiseen malliin, ennen kuin olemme varmistaneet, että sen tuottama tieto on käyttäjälle aidosti hyödyllistä [^3].

*Lähteet:*

[^1]: SparxIT Solutions. N.d. MVP Architecture Guide: Monolith vs Microservices vs Serverless. [Verkkosivu]. Saatavilla: https://www.sparxitsolutions.com/blog/mvp-architecture/. Viitattu 11.11.2025.

[^2]: Olsen, Dan. 2015. The Lean Product Playbook: How to Innovate with Minimum Viable Products and Rapid Customer Feedback. John Wiley & Sons, Incorporated. Saatavilla: ProQuest Ebook Central, http://ebookcentral.proquest.com/lib/kajaani-ebooks/detail.action?docID=4040191. Viitattu 11.11.2025.

[^3]: RaftLabs. 2024. How to Create an AI MVP: A Full Development Guide. [Verkkosivu]. Saatavilla: https://dev.to/raftlabs/how-to-create-an-ai-mvp-a-full-development-guide-19hb. Viitattu 11.11.2025.