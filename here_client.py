import requests
import os
from dotenv import load_dotenv
from typing import Tuple, List, Optional, Dict, Any
import flexpolyline

# 1. Ladataan ympäristömuuttujat .env-tiedostosta
load_dotenv()

# 2. Haetaan avain .env-tiedostosta
HERE_API_KEY = os.getenv("HERE_API_KEY")

# Varmistus
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

def route(origin: Tuple[float, float], destination: Tuple[float, float], departure_time: str = None) -> Optional[Dict[str, Any]]:
    """
    Hakee reitin.
    HUOM: Palautettu 'spans', jotta saamme sijainnin häiriöille, joilta puuttuu geometry.
    """
    url = "https://router.hereapi.com/v8/routes"
    
    params = {
        "transportMode": "car",
        "origin": f"{origin[0]},{origin[1]}",
        "destination": f"{destination[0]},{destination[1]}",
        # TÄRKEÄÄ: 'spans' on mukana, jotta voimme linkittää häiriöt reittipisteisiin
        "return": "polyline,summary,incidents", 
        "spans": "incidents", 
        "apiKey": HERE_API_KEY
    }

    # Jos lähtöaika on annettu, lisätään se pyyntöön
    if departure_time:
        params["departureTime"] = departure_time

    try:
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": True, "status_code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"error": True, "status_code": 500, "message": str(e)}

def parse_traffic_incidents(route_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parsii häiriöt yhdistämällä reittiviivan (polyline) ja spans-tiedot.
    Tämä takaa, että saamme koordinaatit myös häiriöille, joissa API ei niitä suoraan kerro.
    """
    incidents_list = []
    
    if not route_data or "routes" not in route_data:
        return []

    for route_obj in route_data["routes"]:
        for section in route_obj.get("sections", []):
            
            # 1. Puretaan tämän sectionin reittiviiva koordinaateiksi
            # Tarvitaan flexpolyline-kirjasto
            poly_str = section.get("polyline")
            if not poly_str:
                continue
            
            # decoded_coords on lista [(lat, lon), (lat, lon), ...]
            decoded_coords = flexpolyline.decode(poly_str)
            
            # 2. Haetaan häiriöiden määritelmät (lista, johon spans viittaa indekseillä)
            incident_defs = section.get("incidents", [])
            
            # 3. Käydään läpi SPANS, joka kertoo missä kohtaa viivaa häiriö on
            for span in section.get("spans", []):
                
                # 'offset' kertoo monesko piste reittiviivalla (indeksi)
                offset = span.get("offset", 0)
                
                # 'incidents' on lista indeksejä, jotka viittaavat incident_defs -listaan
                span_inc_indices = span.get("incidents", [])
                
                # Varmistetaan että offset on järkevä
                if span_inc_indices and offset < len(decoded_coords):
                    
                    # Nyt tiedämme tarkan sijainnin reitillä!
                    lat, lon = decoded_coords[offset]
                    
                    for inc_idx in span_inc_indices:
                        # Varmistetaan indeksin oikeellisuus
                        if isinstance(inc_idx, int) and inc_idx < len(incident_defs):
                            inc = incident_defs[inc_idx]
                            
                            # Luetaan tiedot turvallisesti
                            description = "Ei kuvausta"
                            if "description" in inc:
                                val = inc["description"]
                                # Joskus description on objekti {text: "foo"}, joskus string
                                description = val.get("text", val) if isinstance(val, dict) else str(val)

                            itype = inc.get("type", "INCIDENT")
                            criticality = inc.get("criticality", "minor")

                            # Lisätään listaan
                            incidents_list.append({
                                "tyyppi": itype,
                                "kuvaus": description,
                                "taso": criticality,
                                "lat": float(lat),
                                "lon": float(lon),
                                "paikka": f"Reittipiste: {offset}" # Debug-tieto
                            })

    return incidents_list

def traffic_messages_near_route(coords: List[Tuple[float, float]]) -> List[Dict[str, str]]:
    """ Placeholder DigiTraffic-liikennehäiriöille. """
    if not coords:
        return []
    return [{
        "otsikko": "Digitraffic: Tiekäytön rajoitus (PLASEHOLDER)",
        "sijainti": "Valtatie 9 (Tampereen suunta)",
        "kuvaus": "Rajoitettu ajonopeus tietyömaan vuoksi. Voimassa 24/7.",
        "aika": "2025-11-18 00:00:00"
    }]

def tms_near_route(coords: List[Tuple[float, float]]) -> List[str]:
    """ Placeholder sääasemille. """
    if not coords:
        return []
    return ["Digitrafficin TMS (sääasema) tiedon haku vaatii erillisen Bounding Box -kutsun."]

def slice_polyline(polyline_coords: List[Tuple[float, float]], start_index: int, end_index: int) -> List[Tuple[float, float]]:
    """Leikkaa reittiviivan koordinaatit annettujen indeksien mukaan."""
    if start_index is None or end_index is None:
        return []
        
    start_index = int(start_index)
    end_index = int(end_index)

    max_index = len(polyline_coords)
    end_slice = min(end_index, max_index)
    start_slice = max(0, min(start_index, end_slice))

    return polyline_coords[start_slice:end_slice]