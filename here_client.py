import requests
from typing import Tuple, List, Optional, Dict, Any
import flexpolyline

# HUOM: API-AVAIN TÄYTYY MÄÄRITELLÄ TAI TUODA ERILLISESTI
HERE_API_KEY = "OQFZ4YGejiwxEtYlxNyHqgebBUb4vdmuER3qYcAzx5A"

# --------------------------------------------------------------------
# 1. HERE API - FUNKTIOT
# --------------------------------------------------------------------

def geocode(address: str) -> Optional[Tuple[float, float]]:
    """Muuttaa osoitteen koordinaateiksi (lat, lon)."""
    url = f"https://geocode.search.hereapi.com/v1/geocode?q={address}&limit=1&apiKey={HERE_API_KEY}"
    try:
        resp = requests.get(url)
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

def route(origin: Tuple[float, float], destination: Tuple[float, float]) -> Optional[Dict[str, Any]]:
    """
    Hakee reitin, palauttaa liikennetiedot (incidents) JA span-indeksit.
    """
    url = (
        f"https://router.hereapi.com/v8/routes?transportMode=car"
        f"&origin={origin[0]},{origin[1]}"
        f"&destination={destination[0]},{destination[1]}"
        f"&return=polyline,summary,incidents"
        f"&spans=incidents"
        f"&apiKey={HERE_API_KEY}"
    )
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": True, "status_code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"error": True, "status_code": 500, "message": str(e)}

def parse_traffic_incidents(route_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parsii liikennetiedotteet käyttämällä span-indeksiä viittaamaan 
    varsinaiseen incidents-listaan.
    """
    incidents_list = []
    seen_incident_ids = set()
    
    if route_data and "routes" in route_data and route_data["routes"]:
        for route_obj in route_data["routes"]:
            for section in route_obj.get("sections", []):
                
                # 1. HAE KAIKKI TAPAHTUMAT (FULL DEFINITIONS)
                incident_definitions = section.get("incidents", [])

                # 2. ITEROI SPANS-RAKENNE LÄPI
                for span in section.get("spans", []):
                    span_incident_indices = span.get("incidents", []) # Tässä on lista indeksejä, esim. [0]
                    
                    if span_incident_indices and incident_definitions:
                        
                        start_index = span.get("offset", 0)
                        length = span.get("length", 0)
                        end_index = start_index + length
                        
                        for incident_index in span_incident_indices:
                            
                            # TÄMÄ ON KORJAUS: Noudetaan varsinainen incident-sanakirja indeksillä
                            if isinstance(incident_index, int) and incident_index < len(incident_definitions):
                                incident = incident_definitions[incident_index]
                            else:
                                continue # Ohitetaan, jos indeksi on virheellinen

                            # Varmistetaan uniikki ID
                            incident_id = incident.get("id")
                            # Emme enää estä ID:n toistoa, koska sama ID voi liittyä useampaan spaniin,
                            # mutta pidämme parsintalogiikan turvallisena.

                            location_data = incident.get("location", {})
                            
                            lat = location_data.get("point", {}).get("lat") or location_data.get("startPoint", {}).get("lat")
                            lon = location_data.get("point", {}).get("lng") or location_data.get("startPoint", {}).get("lng")
                            
                            description_text = location_data.get("description", "Tuntematon sijainti")

                            # Fallback sijainti- ja vaikutustiedolle
                            if description_text == "Tuntematon sijainti":
                                road_names = location_data.get("roadNames", [])
                                if road_names:
                                    description_text = f"Tie: {', '.join(road_names)}"
                            if description_text == "Tuntematon sijainti" and lat and lon:
                                description_text = f"Koordinaatit: {lat:.4f}, {lon:.4f}"

                            impact = incident.get("trafficFlowImpact")
                            if not impact: impact = incident.get("criticality", "Tuntematon")
                            
                            # Lisätään tiedote listaan
                            incidents_list.append({
                                "tyyppi": incident.get("type", "Ei tyyppiä"),
                                "kuvaus": incident.get("description", "Ei kuvausta"),
                                "paikka": description_text, 
                                "taso": impact,
                                "lat": lat, 
                                "lon": lon, 
                                "start_index": start_index,
                                "end_index": end_index,
                                "tieto": incident 
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