import requests
import os
import flexpolyline
from dotenv import load_dotenv
from typing import Tuple, List, Optional, Dict, Any

# 1. Ladataan ympäristömuuttujat
load_dotenv()

# 2. Haetaan avain .env-tiedostosta
HERE_API_KEY = os.getenv("HERE_API_KEY")

if not HERE_API_KEY:
    print("VAROITUS: HERE_API_KEY puuttuu .env-tiedostosta!")

# --------------------------------------------------------------------
# 1. HERE API - FUNKTIOT
# --------------------------------------------------------------------

def geocode(address: str) -> Optional[Tuple[float, float]]:
    """Muuttaa osoitteen koordinaateiksi (lat, lon)."""
    url = "https://geocode.search.hereapi.com/v1/geocode"
    params = {
        "q": address,
        "limit": 1,
        "apiKey": HERE_API_KEY
    }
    try:
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            if items:
                position = items[0]["position"]
                return (position["lat"], position["lng"])
        else:
            print(f"DEBUG: Geocode virhe: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"DEBUG: Geocode exception: {e}")
    return None

def route(origin: Tuple[float, float], 
          destination: Tuple[float, float], 
          departure_time: str = None, 
          routing_mode: str = "fastest", 
          avoid_features: List[str] = None,
          alternatives: int = 0) -> Optional[Dict[str, Any]]:
    """
    Hakee reitin HERE Routing v8 API:sta.
    Tukee nyt myös reititysasetuksia (mode, avoid) ja vaihtoehtoisia reittejä.
    """
    url = "https://router.hereapi.com/v8/routes"
    
    params = {
        "transportMode": "car",
        "origin": f"{origin[0]},{origin[1]}",
        "destination": f"{destination[0]},{destination[1]}",
        # 'spans' mukana, jotta parse_traffic_incidents toimii
        "return": "polyline,summary,incidents,elevation", 
        "spans": "incidents", 
        "apiKey": HERE_API_KEY,
        "routingMode": routing_mode,
        "alternatives": alternatives
    }

    # Jos lähtöaika on annettu
    if departure_time:
        params["departureTime"] = departure_time

    # Jos on vältettäviä asioita (esim. ["tollRoad", "ferry"])
    if avoid_features:
        params["avoid[features]"] = ",".join(avoid_features)

    try:
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"HERE API Error: {resp.status_code} - {resp.text}")
            return {"error": True, "status_code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"error": True, "status_code": 500, "message": str(e)}

def parse_traffic_incidents(route_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parsii häiriöt yhdistämällä reittiviivan (polyline) ja spans-tiedot.
    """
    incidents_list = []
    
    if not route_data or "routes" not in route_data:
        return []

    for route_obj in route_data["routes"]:
        for section in route_obj.get("sections", []):
            
            # 1. Puretaan tämän sectionin reittiviiva koordinaateiksi
            poly_str = section.get("polyline")
            if not poly_str:
                continue
            
            decoded_coords = flexpolyline.decode(poly_str)
            
            # 2. Haetaan häiriöiden määritelmät
            incident_defs = section.get("incidents", [])
            
            # 3. Käydään läpi SPANS
            for span in section.get("spans", []):
                
                offset = span.get("offset", 0)
                span_inc_indices = span.get("incidents", [])
                
                if span_inc_indices and offset < len(decoded_coords):
                    # Sijainti reitillä
                    lat, lon, *rest = decoded_coords[offset] # flexpolyline voi palauttaa (lat, lon, elev)
                    
                    for inc_idx in span_inc_indices:
                        if isinstance(inc_idx, int) and inc_idx < len(incident_defs):
                            inc = incident_defs[inc_idx]
                            
                            description = "Ei kuvausta"
                            if "description" in inc:
                                val = inc["description"]
                                description = val.get("text", val) if isinstance(val, dict) else str(val)

                            itype = inc.get("type", "INCIDENT")
                            criticality = inc.get("criticality", "minor")

                            incidents_list.append({
                                "tyyppi": itype,
                                "kuvaus": description,
                                "taso": criticality,
                                "lat": float(lat),
                                "lon": float(lon),
                                "paikka": f"Indeksi: {offset}"
                            })

    return incidents_list

