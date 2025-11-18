import requests
import json
from typing import Tuple, Optional, Dict, Any

# ====================================================================

# ajetaan komennolla python API_test.py.

# Asetukset ja API-avain
# HUOM: Korvaa tämä oikealla HERE API -avaimellasi!
HERE_API_KEY = "OQFZ4YGejiwxEtYlxNyHqgebBUb4vdmuER3qYcAzx5A"
# ====================================================================

# --------------------------------------------------------------------
# Asetukset testiajoon
# --------------------------------------------------------------------
TEST_ORIGIN_ADDRESS = "Helsinki"
TEST_DESTINATION_ADDRESS = "Tampere"
TEST_ORIGIN_COORDS = None # Asetetaan geokoodauksen jälkeen
TEST_DESTINATION_COORDS = None # Asetetaan geokoodauksen jälkeen

# --------------------------------------------------------------------
# 1. API-KUTSUFUNKTIOT
# --------------------------------------------------------------------

def geocode(address: str) -> Optional[Tuple[float, float]]:
    """ Muuttaa osoitteen koordinaateiksi ja tarkistaa vastauksen. """
    print(f"\n--- Testaillaan Geokoodausta: {address} ---")
    url = f"https://geocode.search.hereapi.com/v1/geocode?q={address}&limit=1&apiKey={HERE_API_KEY}"
    
    try:
        resp = requests.get(url)
        print(f"Statuskoodi: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            if items:
                position = items[0]["position"]
                print(f"✅ Onnistui. Koordinaatit: ({position['lat']}, {position['lng']})")
                return (position["lat"], position["lng"])
            else:
                print("❌ Epäonnistui. Osoitetta ei löytynyt datasta.")
                return None
        else:
            print(f"❌ Epäonnistui. Virheteksti: {resp.text[:100]}...")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Kutsupoikkeus tapahtui: {e}")
        return None

def route(origin: Tuple[float, float], destination: Tuple[float, float]) -> bool:
    """ Hakee reitin ja tarkistaa vastauksen. Palauttaa True/False. """
    print(f"\n--- Testaillaan Reititystä: {origin} -> {destination} ---")
    
    url = (
        f"https://router.hereapi.com/v8/routes?transportMode=car"
        f"&origin={origin[0]},{origin[1]}"
        f"&destination={destination[0]},{destination[1]}"
        f"&return=polyline,summary,incidents"
        f"&apiKey={HERE_API_KEY}"
    )
    
    try:
        resp = requests.get(url)
        print(f"Statuskoodi: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            if "routes" in data and len(data["routes"]) > 0:
                print("✅ Onnistui. Reittidataa löytyi.")
                
                # Valinnainen: Tarkistetaan löytyikö liikennetiedotteita
                incidents_count = sum(len(section.get("incidents", [])) 
                                      for route in data["routes"] 
                                      for section in route.get("sections", []))
                print(f"   ℹ️ Liikennetiedotteita löydetty: {incidents_count} kpl.")
                
                return True
            else:
                print("❌ Epäonnistui. Status 200, mutta reittiä ei löytynyt vastauksesta.")
                print(f"   ℹ️ Tarkista API-avaimen oikeudet (esim. HERE platform).")
                return False
        else:
            print(f"❌ Epäonnistui. Virheteksti: {resp.text[:100]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Kutsupoikkeus tapahtui: {e}")
        return False

# --------------------------------------------------------------------
# 2. PÄÄOHJELMA
# --------------------------------------------------------------------

def test_api_endpoints():
    """ Ajaa testit Geokoodaukselle ja Reititykselle. """
    global TEST_ORIGIN_COORDS
    global TEST_DESTINATION_COORDS
    
    print("=" * 50)
    print("      HERE API TESTI ALKAA      ")
    print("=" * 50)
    
    # 1. TESTAA GEOKOODAUS
    print("\n--- Vaihe 1/2: Geokoodaustesti ---")
    TEST_ORIGIN_COORDS = geocode(TEST_ORIGIN_ADDRESS)
    TEST_DESTINATION_COORDS = geocode(TEST_DESTINATION_ADDRESS)
    
    if not TEST_ORIGIN_COORDS or not TEST_DESTINATION_COORDS:
        print("\n==================================================")
        print("🛑 TESTI EPÄONNISTUI (GEOKOODAUS)")
        print("Tarkista API-avain ja internet-yhteys.")
        print("==================================================")
        return
    
    # 2. TESTAA REITITYS
    print("\n--- Vaihe 2/2: Reititystesti ---")
    if route(TEST_ORIGIN_COORDS, TEST_DESTINATION_COORDS):
        print("\n==================================================")
        print("🎉 TESTI ONNISTUI TÄYSIN! 🎉")
        print("API-avaimesi on kelvollinen reititykseen.")
        print("==================================================")
    else:
        print("\n==================================================")
        print("⚠️ TESTI EPÄONNISTUI (REITITYS)")
        print("Tarkista API-avain, erityisesti liikennetietojen oikeudet.")
        print("==================================================")

if __name__ == "__main__":
    test_api_endpoints()