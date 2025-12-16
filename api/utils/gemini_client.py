
import os
import google.generativeai as genai
from typing import Dict, Any, Optional

class GeminiRouteAnalyzer:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GOOGLE_API_KEY not found. AI analysis will fail.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            # Use a model that was verified to exist in the user's environment
            # Fallback chain could be implemented, but let's pick the most capable/fastest available one.
            self.model = genai.GenerativeModel('gemini-flash-latest')

    def analyze_route(self, route_summary: Dict[str, Any], incidents: list, weather: list) -> str:
        """
        Analyzes route data and returns a short, safe, and helpful summary.
        """
        if not self.model:
            return "Virhe: AI-avain puuttuu konfiguraatiosta."

        # Construct a prompt context
        duration_min = round(route_summary.get("duration", 0) / 60)
        distance_km = round(route_summary.get("length", 0) / 1000, 1)
        
        # Summarize incidents
        incident_text = "Ei merkittäviä ohiöitä."
        if incidents:
            incident_types = [i.get("tyyppi", "Muu") for i in incidents]
            incident_text = f"{len(incidents)} häiriötä: " + ", ".join(set(incident_types))

        # Summarize weather (simple logic for now)
        weather_text = "Normaali keli."
        if weather:
            # Assuming weather is a list of camera stations or road weather points
            # Ideally we'd parse meaningful data, but for now just count availability
            weather_text = f"Säätietoja saatavilla {len(weather)} pisteestä."

        prompt = f"""
        Olet liikenneassistentti nimeltä 'Pingut'. Analysoi seuraava ajoreitti ja anna tiivis, hyödyllinen yhteenveto kuljettajalle.
        
        REITIN TIEDOT:
        - Matka: {distance_km} km
        - Kesto: {duration_min} min
        - Liikennehäiriöt: {incident_text}
        - Sää: {weather_text}

        OHJEET:
        1. Kerro arvioitu ajokeli ja mahdolliset riskit.
        2. Jos on häiriöitä, varoita niistä.
        3. Ole ytimekäs ja selkeä (max 3-4 lausetta).
        4. Käytä rentoa mutta asiallista sävyä suomeksi.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return "Pahoittelut, en voinut analysoida reittiä juuri nyt."
