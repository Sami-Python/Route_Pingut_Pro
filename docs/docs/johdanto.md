# Johdanto
## Projektin tausta

Tämän projektin taustalla on kurssin tavoite perehdyttää opiskelijat mikropalveluarkkitehtuuriin perustuvan sovelluksen suunnitteluun ja toteutukseen. Projektissa kehitetään nykyaikaisia ohjelmistoteknologioita hyödyntävä mikropalvelu, jonka tarkoituksena on tukea opiskelijan tai korkeakouluyhteisön arkea konkreettisella ja käytännönläheisellä tavalla. Työssä korostuvat mikropalveluarkkitehtuurin perusperiaatteet, kuten selkeä vastuunjako, rajapintapohjainen viestintä ja järjestelmän laajennettavuus.

## Projektin tavoite

Projektissa tarkasteltiin useita mikropalveluideoita, jotka on suunniteltu helpottamaan korkeakouluyhteisön ja opiskelijoiden arkea avoimen datan ja digitaalisten palveluiden avulla. Tiimin kehittämät ideat perustuivat todellisiin käyttötarpeisiin sekä mikropalveluarkkitehtuurin hyödyntämiseen osana modernia ohjelmistokehitystä. Tarkasteltavana olivat Tiellä liikkujan mikropalvelu, korkeakoulumateriaalin talteenottoon liittyvä palvelu sekä harjoittelupaikkojen seurantaan tarkoitettu ratkaisu.

Näistä vaihtoehdoista tiimi valitsi toteutettavaksi Tiellä liikkujan mikropalvelun. Palvelun tavoitteena on hyödyntää avointa liikenne- ja säädataa matkustusolosuhteiden arviointiin sekä tarjota käyttäjälle ajantasaista tietoa reittiolosuhteista ja lähdön ajankohtaan liittyvistä muistutuksista. Projektin tavoitteena on toteuttaa toimiva, skaalautuva ja helposti laajennettava mikropalvelu, joka demonstroi mikropalveluarkkitehtuurin keskeisiä periaatteita käytännössä.

## Projektitiimi ja työskentelytavat

Projektin toteutuksesta vastaa viiden hengen opiskelijatiimi, johon kuuluvat Sami Hiedanpää, Reetta Ilomäki, Minna Imporanta, Joonas Kitunen ja Mika Kylmäniemi. Tiimi työskentelee ketterästi Scrum-menetelmää hyödyntäen, ja työ etenee sprinttien kautta siten, että tehtävät ja vastuualueet jakautuvat mahdollisimman tasaisesti tiimin jäsenten kesken.

Yhteistyössä ja viestinnässä painotetaan avoimuutta ja läpinäkyvyyttä. Kaikki keskeiset päätökset, sprinttien tuotokset sekä projektin aikana esiin nousseet haasteet dokumentoidaan GitLabin issue-järjestelmään ja tiimin blogiin. Viestintäkäytännöt tukevat kannustavaa, ratkaisukeskeistä ja jatkuvaan parantamiseen tähtäävää työskentelytapaa.

## Rajaukset ja oletukset

Projektin laajuus on rajattu yhden mikropalvelun toteutukseen, joka on nimeltään Tiellä liikkujan mikropalvelu. Projektissa toteutettava MVP-versio tukee ainoastaan autoilureittejä ja toimii yksinkertaisena web-sovelluksena ilman käyttäjätunnistusta tai kirjautumista.

Projektin toteutuksessa oletetaan, että käyttäjällä on käytössään toimiva internet-yhteys sekä sovelluksen toiminnan kannalta tarvittavat sijaintiluvat. Lisäksi oletuksena on, että palvelu hyödyntää avoimia ja luotettavia rajapintoja, joihin järjestelmällä on esteetön pääsy. Näiden oletusten varaan rakentuvat sekä palvelun toiminnallisuus että tekniset ratkaisut.

## Laadunvarmistus ja testaus

Laadun varmistamiseksi palvelun toiminnallisuus testataan automatisoiduilla yksikkötesteillä ja koodin laatua seurataan staattisen koodianalyysin avulla. Näiden käytäntöjen avulla pyritään tuottamaan ylläpidettävä, luotettava ja teknisesti kestävä kokonaisuus, joka vastaa kurssin asettamia vaatimuksia sekä hyviä ohjelmistokehityskäytäntöjä.