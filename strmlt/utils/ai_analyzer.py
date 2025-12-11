"""
AI Route Analyzer Module
Analysoi reitin käyttäen Google Gemini API:a.
"""

import google.generativeai as genai
from typing import Dict, Any, Tuple
import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GeminiRouteAnalyzer:
    """Analysoi reitti käyttäen Google Gemini API:a"""
    
    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        """
        Args:
            api_key: Google Gemini API-avain (tai haetaan GEMINI_API_KEY env varista)
            model: Käytettävä malli (gemini-2.5-flash, gemini-1.5-pro)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("❌ GEMINI_API_KEY ei löydy ympäristömuuttujista!")
            print(f"Tarkista .env tiedosto. Nykyiset env vars: {list(os.environ.keys())[:5]}...")
            raise ValueError("GEMINI_API_KEY puuttuu! Aseta se .env tiedostoon.")
        
        print(f"✅ API-avain löytyi (pituus: {len(self.api_key)} merkkiä)")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
    
    def test_connection(self) -> bool:
        """Testaa yhteys Gemini API:in"""
        try:
            # Kokeile yksinkertainen kysymys
            response = self.model.generate_content("Testi")
            return bool(response.text)
        except Exception as e:
            print(f"❌ Yhteysvirhe Gemini API:in: {e}")
            return False
    
    def analyze_route(self, route_data: str, route_summary: Tuple[float, float, float], 
                     departure_time: datetime.datetime, origin: str = "", dest: str = "") -> str:
        """
        Analysoi reitti AI:lla
        
        Args:
            route_data: Tiivistetty reittidatan kuvaus
            route_summary: (pituus_km, kesto_h, base_kesto_h)
            departure_time: Lähtöaika
            origin: Lähtöpaikka (valinnainen)
            dest: Määränpää (valinnainen)
        
        Returns:
            AI:n analyysi tekstinä
        """
        
        distance_km, duration_h, base_duration_h = route_summary
        
        # Laske viive
        delay_minutes = (duration_h - base_duration_h) * 60 if base_duration_h > 0 else 0
        
        prompt = self._build_prompt(
            route_data, 
            distance_km, 
            duration_h, 
            delay_minutes,
            departure_time,
            origin,
            dest
        )
        
        try:
            response = self._call_gemini(prompt)
            return response
        except Exception as e:
            return f"❌ Virhe AI-analyysissä: {e}\n\nTarkista että GEMINI_API_KEY on asetettu oikein."
    
    def _build_prompt(self, data: str, distance: float, duration: float, 
                     delay_minutes: float, departure: datetime.datetime,
                     origin: str, dest: str) -> str:
        """Rakentaa strukturoidun promptin AI:lle"""
        
        # Muodosta reittiotsikko
        route_title = ""
        if origin and dest:
            route_title = f"{origin} → {dest}"
        
        # Muodosta viivetieto
        delay_info = ""
        if delay_minutes > 5:
            delay_info = f"- Arvioitu viive: +{delay_minutes:.0f} minuuttia normaaliin ajoaikaan verrattuna"
        
        prompt = f"""Olet kokenut liikenneanalyytikko Suomessa. Analysoi seuraava ajoreitti ja anna käytännölliset, konkreettiset suositukset suomeksi.

REITTI: {route_title}

PERUSTIEDOT:
- Matka: {distance:.1f} km
- Arvioitu ajoaika: {duration:.1f} tuntia ({duration*60:.0f} minuuttia)
{delay_info}
- Lähtöaika: {departure.strftime('%d.%m.%Y klo %H:%M')}
- Arvioitu perillä: {(departure + datetime.timedelta(hours=duration)).strftime('%d.%m.%Y klo %H:%M')}

REITIN TILANNE:
{data}

Anna lyhyt ja ytimekäs analyysi seuraavista:

1. TODELLINEN AJOAIKA
   Anna arvio muodossa "Xh Ymin" (esim. "11h 42min").
   Kerro TARKASTI mihin arvio perustuu:
   - Miten liikenne näyttää reitillä ajoajan aikana
   - Miten sää vaikuttaa (lämpötila, sade, tien kunto)
   - Mitkä tekijät hidastavat tai nopeuttavat matkaa
   - Vertaa arviotasi annettuun ajoaikaan

2. RISKIT JA HUOMIOT
   Listaa 2-3 tärkeintä asiaa joihin kiinnittää huomiota.

3. SUOSITUKSET
   Anna 2-3 konkreettista neuvoa (esim. lähtöaika, varusteet, pysähdykset).

4. KRIITTISET KOHDAT
   Mainitse tärkeimmät kohdat reitillä joissa olla varovainen.

TÄRKEÄÄ:
- Vastaa VAIN suomeksi
- Ole lyhyt ja ytimekäs (max 300 sanaa)
- ÄLÄ käytä emojeja
- Älä toista annettuja tietoja, vaan ANALYSOI niitä
- Anna KONKREETTISIA neuvoja, ei yleisluontoisia
- Ajoaika AINA muodossa "Xh Ymin"
- Perustele ajoaika-arvio TARKASTI

Aloita suoraan analyysillä, älä toista otsikkoa."""

        return prompt
    
    def _call_gemini(self, prompt: str, max_retries: int = 2) -> str:
        """
        Kutsuu Gemini API:a
        
        Args:
            prompt: Prompti AI:lle
            max_retries: Maksimi uudelleenyritykset
        
        Returns:
            AI:n vastaus
        """
        
        for attempt in range(max_retries + 1):
            try:
                print(f"🤖 Kutsutaan Gemini API:a...")
                
                # Gemini API kutsu
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'top_k': 40,
                        'max_output_tokens': 2048,  # Increased from 1024 to allow longer responses
                    }
                )
                
                ai_response = response.text.strip()
                
                if not ai_response:
                    raise ValueError("Tyhjä vastaus AI:lta")
                
                print(f"✅ AI-analyysi valmis ({len(ai_response)} merkkiä)")
                return ai_response
                
            except Exception as e:
                if attempt < max_retries:
                    print(f"⚠️ Virhe, yritetään uudelleen: {e}")
                    continue
                return f"❌ Virhe AI-kutsussa: {str(e)}"
        
        return "❌ AI-analyysi epäonnistui useiden yritysten jälkeen."
