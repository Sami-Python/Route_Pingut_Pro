import streamlit as st
import folium
from streamlit_folium import st_folium
import flexpolyline
import requests
import json 
from typing import Tuple, List, Optional, Dict, Any

# ====================================================================
# Asetukset ja API-avain
# HUOM: Korvaa tämä oikealla HERE API -avaimellasi!
HERE_API_KEY = "OQFZ4YGejiwxEtYlxNyHqgebBUb4vdmuER3qYcAzx5A"
# ====================================================================

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
    Hakee reitin ja palauttaa LIIKENNETIEDOT (incidents) Routing API:n kautta.
    """
    url = (
        f"https://router.hereapi.com/v8/routes?transportMode=car"
        f"&origin={origin[0]},{origin[1]}"
        f"&destination={destination[0]},{destination[1]}"
        f"&return=polyline,summary,incidents" # Sisältää liikennetiedot
        f"&apiKey={HERE_API_KEY}"
    )
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return data
        else:
            # Palautetaan virheobjekti, jos statuskoodi ei ole 200
            return {"error": True, "status_code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"error": True, "status_code": 500, "message": str(e)}

def parse_traffic_incidents(route_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Etsii, parsii ja poimii koordinaatit liikennetiedotteista käyttäen robustia hakua.
    """
    incidents = []
    if route_data and "routes" in route_data and route_data["routes"]:
        for route_obj in route_data["routes"]:
            for section in route_obj.get("sections", []):
                for incident in section.get("incidents", []):
                    
                    # ---- KOORDINAATTIEN HAKU (PARANNELTU) ----
                    # Yritetään löytää koordinaatit 'point' tai 'startPoint' avaimen alta
                    location_data = incident.get("location", {})
                    
                    lat = location_data.get("point", {}).get("lat") or \
                          location_data.get("startPoint", {}).get("lat")
                    lon = location_data.get("point", {}).get("lng") or \
                          location_data.get("startPoint", {}).get("lng")
                    
                    description = location_data.get("description", "Tuntematon sijainti")
                    
                    # Luo sijainnille teksti koordinaateista, jos sijaintia ei ole määritetty
                    if description == "Tuntematon sijainti" and lat and lon:
                        description = f"Koordinaatit: {lat:.4f}, {lon:.4f}"
                    # ----------------------------------------------------

                    incidents.append({
                        "tyyppi": incident.get("type", "Ei tyyppiä"),
                        "kuvaus": incident.get("description", "Ei kuvausta"),
                        "paikka": description, 
                        "taso": incident.get("trafficFlowImpact", "Tuntematon"),
                        "lat": lat, 
                        "lon": lon, 
                        "tieto": incident 
                    })
    return incidents

# --------------------------------------------------------------------
# 2. DIGITRAFFIC PLACEHOLDERS
# --------------------------------------------------------------------

def tms_near_route(coords: List[Tuple[float, float]]) -> List[str]:
    """ Placeholder sääasemille. """
    if not coords:
        return []
    return ["Digitrafficin TMS (sääasema) tiedon haku vaatii erillisen Bounding Box -kutsun."]

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

# --------------------------------------------------------------------
# 3. STREAMLIT APP
# --------------------------------------------------------------------

st.set_page_config(page_title="Reitti- ja liikennetiedot", layout="wide")
st.title("Reitti- ja liikennetiedot 🗺️")

# --- ALUSTUS (TALLENNETAAN TILAAN) ---
if 'coords' not in st.session_state:
    st.session_state.coords = []
if 'route_data' not in st.session_state: 
    st.session_state.route_data = None
if 'origin_coords' not in st.session_state:
    st.session_state.origin_coords = None
if 'dest_coords' not in st.session_state:
    st.session_state.dest_coords = None
if 'here_incidents' not in st.session_state:
    st.session_state.here_incidents = None

# --- KÄYTTÖLIITTYMÄ ---
col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("Lähtö", value="Helsinki")
with col2:
    destination = st.text_input("Määränpää", value="Tampere")

# --------------------------------------------------------------------
# TOIMINTO 1: HAE REITTI & TALLENNA DATA TILAAN
# --------------------------------------------------------------------
if st.button("Hae reitti ja liikennetiedot (HERE)"):
    if origin and destination:
        with st.spinner("Haetaan reittiä..."):
            origin_coords = geocode(origin)
            destination_coords = geocode(destination)

            if not origin_coords or not destination_coords:
                st.error("Lähtö- tai määränpääosoitetta ei löytynyt.")
            else:
                st.session_state.origin_coords = origin_coords
                st.session_state.dest_coords = destination_coords

                route_data = route(origin_coords, destination_coords)
                st.session_state.route_data = route_data 
                
                # TARKISTA VIRHE
                if route_data and route_data.get("error"):
                    st.error(f"❌ API-kutsu epäonnistui! HTTP-statuskoodi: **{route_data['status_code']}**")
                    with st.expander("Näytä virheen tiedot"):
                        st.code(route_data['message'])
                    st.session_state.coords = []
                    st.session_state.here_incidents = None

                # KÄSITTELE ONNISTUNUT VASTAUS
                elif route_data and "routes" in route_data and len(route_data["routes"]) > 0:
                    try:
                        # 3. Puretaan Polyline
                        polyline_str = route_data["routes"][0]["sections"][0]["polyline"]
                        st.session_state.coords = flexpolyline.decode(polyline_str)
                        
                        # 4. Parsitaan ja TALLENNETAAN Liikennetiedotteet
                        st.session_state.here_incidents = parse_traffic_incidents(route_data)
                        
                        st.success("Reitti haettu onnistuneesti! Liikennetiedotteet näytetään ja merkitään kartalle.")
                        
                        # Debug-tieto
                        with st.expander("Näytä raaka HERE Routing API-vastaus"):
                            st.json(route_data)

                    except Exception as e:
                        st.error(f"Virhe reittiviivan purkamisessa tai tietojen käsittelyssä: {e}")
                else:
                    st.error("Reittidataa ei saatu. Tarkista API-avain.")
    else:
        st.warning("Anna lähtö ja määränpää.")

# --------------------------------------------------------------------
# HERE LIIKENNETIEDOT (ESITYS) - Riippumaton napin painalluksesta
# --------------------------------------------------------------------

if st.session_state.here_incidents is not None:
    st.divider()
    st.subheader("⚠️ HERE Liikennetiedotteet (reitin varrelta)")
    
    traffic_incidents = st.session_state.here_incidents
    
    if traffic_incidents:
        for incident in traffic_incidents:
            level = incident['taso'].lower()
            icon = "🚨" if level in ["critical", "major"] else "🚧"
            
            with st.expander(f"{icon} **{incident['tyyppi']}** - {incident['kuvaus']}"):
                st.write(f"**Sijainti:** {incident['paikka']}") # Nyt paranneltu sijaintiteksti
                st.write(f"**Vaikutus:** {incident['taso']}")
    else:
        st.info("Ei merkittäviä liikennetiedotteita (incidents) tällä reitillä (HERE).")


# --------------------------------------------------------------------
# KARTTA JA LISÄTIEDOT (RENDERÖIDÄÄN AINA JOS COORDS ON MUISTISSA)
# --------------------------------------------------------------------

# --- KARTAN PIIRTÄMINEN ---
if st.session_state.coords:
    st.divider()
    
    # Lasketaan kartan keskipiste reitin perusteella
    mid_idx = len(st.session_state.coords) // 2
    center_point = st.session_state.coords[mid_idx]

    m = folium.Map(location=center_point, zoom_start=7)

    # Lähtö- ja päätepisteet
    if st.session_state.origin_coords:
        folium.Marker(st.session_state.origin_coords, popup="Lähtö", icon=folium.Icon(color='green')).add_to(m)
    if st.session_state.dest_coords:
        folium.Marker(st.session_state.dest_coords, popup="Määränpää", icon=folium.Icon(color='red')).add_to(m)

    # Reittiviiva
    folium.PolyLine(st.session_state.coords, color="blue", weight=5, opacity=0.8).add_to(m)

    # ---- LIIKENNETIEDOT MARKERIT ----
    if st.session_state.here_incidents:
        for incident in st.session_state.here_incidents:
            # Tarkista, että meillä on koordinaatit kartalle merkintää varten
            if incident['lat'] and incident['lon']:
                
                # Valitaan ikonin väri vakavuuden/tyypin perusteella
                icon_color = 'orange'
                icon_name = 'info'
                
                if incident['taso'].lower() in ['critical', 'major']:
                    icon_color = 'red'
                    icon_name = 'times-circle'
                elif 'maintenance' in incident['tyyppi'].lower() or 'roadworks' in incident['tyyppi'].lower():
                    icon_color = 'cadetblue'
                    icon_name = 'wrench'
                
                popup_text = f"**{incident['tyyppi']}**<br>{incident['kuvaus']}<br>Vaikutus: {incident['taso']}<br>Sijainti: {incident['paikka']}"
                
                folium.Marker(
                    [incident['lat'], incident['lon']], 
                    popup=popup_text, 
                    icon=folium.Icon(icon=icon_name, 
                                     color=icon_color,
                                     prefix='fa')
                ).add_to(m)
    # ------------------------------------
    
    st.subheader("Reitti kartalla")
    st_folium(m, width=800, height=500)


# --- TOIMINTO 2: DIGITRAFFIC PLACEHOLDER-TIEDOT ---
st.divider()
st.subheader("Lisätiedot (Digitraffic Placeholderit)")

if st.button("Hae DigiTraffic-placeholder tiedot", key="digitraffic_btn"):
    if st.session_state.coords: 
        with st.spinner("Haetaan placeholder-dataa..."):
            
            coords = st.session_state.coords
            
            tms = tms_near_route(coords)
            messages = traffic_messages_near_route(coords)

            col_a, col_b = st.columns(2)
            
            with col_a:
                st.info(f"Digitraffic Liikennehäiriöt (placeholder): {len(messages)}")
                for msg in messages:
                    with st.expander(f"⚠️ {msg['otsikko']}"):
                        st.write(f"**Sijainti:** {msg['sijainti']}")
                        st.write(f"**Kuvaus:** {msg['kuvaus']}")
                        st.caption(f"Alkoi: {msg['aika']}")
            
            with col_b:
                st.info("Digitraffic Sääasemat (placeholder)")
                if tms:
                    st.write(tms)
                else:
                    st.write("Ei dataa tai toteutus puuttuu.")

    else:
        st.warning("Hae ensin reitti 'Hae reitti ja liikennetiedot (HERE)' -napilla.")