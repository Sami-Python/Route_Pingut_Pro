import streamlit as st
import flexpolyline
from typing import Tuple, List, Optional, Dict, Any
import datetime
import time
import pydeck as pdk
from dotenv import load_dotenv
import os

# 1. Ladataan ympäristömuuttujat
load_dotenv()

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
# Asetetaan token globaalisti varmuuden vuoksi
pdk.settings.mapbox_api_key = MAPBOX_TOKEN

# 2. Tuodaan funktiot (varmista että tiedostot ovat samassa kansiossa)
from here_client import geocode, route, parse_traffic_incidents
from digitraffic_client import calculate_bbox, traffic_messages_near_route, tms_near_route

# ====================================================================
# HELPER-FUNKTIOT
# ====================================================================

def extract_route_summary(route_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """Hakee matkan pituuden (km) ja keston (h)."""
    try:
        route_obj = route_data["routes"][0]
        section = route_obj["sections"][0]
        summary = section.get("summary", {})
        length_m = summary.get("length")
        duration_s = summary.get("duration") 
        if length_m is None or duration_s is None: return None
        return length_m / 1000.0, duration_s / 3600.0
    except Exception:
        return None

def create_map(coords, incidents, car_position, origin_coords, dest_coords):
    """
    Luo Pydeck Deck -objektin. 
    Sisältää kerrokset: Reitti, Pisteet, Häiriöt, Auto.
    """
    n_points = len(coords)
    # Keskitetään kartta reitin puoliväliin tai oletukseen
    if n_points > 0:
        mid = n_points // 2
        center_lat, center_lon = coords[mid]
    else:
        center_lat, center_lon = 61.9241, 25.7482 # Suomen keskipiste

    layers = []

    # 1. Reittiviiva
    route_layer = pdk.Layer(
        "PathLayer",
        data=[{"path": [[lon, lat] for (lat, lon) in coords]}],
        get_path="path",
        get_color=[100, 149, 237], # Cornflower blue
        width_scale=10,
        width_min_pixels=3,
        opacity=0.8,
    )
    layers.append(route_layer)

    # 2. Lähtö- ja määränpääpisteet
    point_data = []
    if origin_coords: point_data.append({"pos": [origin_coords[1], origin_coords[0]], "color": [0, 180, 0], "label": "Lähtö"})
    if dest_coords: point_data.append({"pos": [dest_coords[1], dest_coords[0]], "color": [200, 0, 0], "label": "Määränpää"})
    
    points_layer = pdk.Layer(
        "ScatterplotLayer",
        data=point_data,
        get_position="pos",
        get_color="color",
        get_radius=800,
        radius_min_pixels=5,
        pickable=True,
    )
    layers.append(points_layer)

    # 3. HERE Häiriöt (Incidents)
    if incidents:
        incident_points = []
        for inc in incidents:
            # Väri tason mukaan
            level = str(inc.get("taso", "")).lower()
            
            if level in ["critical", "blocked"]:
                color = [200, 0, 0]     # Punainen
            elif level in ["major"]:
                color = [255, 140, 0]   # Oranssi
            else:
                color = [255, 215, 0]   # Keltainen
            
            # Varmistetaan koordinaatit
            lat = inc.get("lat")
            lon = inc.get("lon")
            
            if lat and lon:
                incident_points.append({
                    "pos": [lon, lat], # Pydeck: [lon, lat]
                    "color": color,
                    "label": f"{inc.get('tyyppi')}: {inc.get('kuvaus')}"
                })
        
        if incident_points:
            incidents_layer = pdk.Layer(
                "ScatterplotLayer",
                data=incident_points,
                get_position="pos",
                get_color="color",
                get_radius=600,       # Koko metreinä
                radius_min_pixels=5,  # Minimikoko pikseleinä
                pickable=True,
                opacity=0.9,
                stroked=True,
                get_line_color=[255, 255, 255],
                line_width_min_pixels=1
            )
            layers.append(incidents_layer)

    # 4. Auto (liikkuva osa)
    if car_position:
        car_layer = pdk.Layer(
            "ScatterplotLayer",
            data=[{"position": [car_position[1], car_position[0]], "label": "Auto"}],
            get_position="position",
            get_color=[0, 0, 255],
            get_radius=400,
            radius_min_pixels=7,
            pickable=True,
        )
        layers.append(car_layer)
    
    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/streets-v12",
        initial_view_state=pdk.ViewState(
            latitude=center_lat, longitude=center_lon, zoom=7, pitch=0
        ),
        layers=layers,
        api_keys={"mapbox": MAPBOX_TOKEN},
        tooltip={"html": "<b>{label}</b>", "style": {"color": "white", "backgroundColor": "rgba(0,0,0,0.8)"}}
    )
    return deck

# ====================================================================
# UI
# ====================================================================
st.set_page_config(page_title="Reitti ja Animaatio", layout="wide")

# Alustetaan sessiotilat (state), jotta data pysyy muistissa päivitysten välillä
if "coords" not in st.session_state: st.session_state.coords = []
if "route_summary" not in st.session_state: st.session_state.route_summary = None
if "here_incidents" not in st.session_state: st.session_state.here_incidents = []
if "departure_dt" not in st.session_state: st.session_state.departure_dt = datetime.datetime.now()
if "digitraffic_messages" not in st.session_state: st.session_state.digitraffic_messages = []

st.title("Reitti ja Liikennetiedot 🚗")

if not MAPBOX_TOKEN:
    st.warning("⚠️ MAPBOX_TOKEN puuttuu .env-tiedostosta. Kartta ei ehkä toimi.")

# --- 1. HAKUVALIKOT ---
c1, c2, c3 = st.columns(3)
with c1: origin = st.text_input("Lähtö", value="Helsinki")
with c2: destination = st.text_input("Määränpää", value="Tampere")
with c3:
    # LÄHTÖAJAN LOGIIKKA (KORJATTU)
    
    # 1. Alustetaan oletusaika sessioon vain KERRAN, jotta se ei resetoidu joka päivityksellä
    if "ui_default_time" not in st.session_state:
        # Oletus: Nyt + 10 min
        st.session_state.ui_default_time = (datetime.datetime.now() + datetime.timedelta(minutes=10)).time()

    # 2. Sidotaan widget sessioon key-parametrilla
    user_time = st.time_input("Lähtöaika", value=st.session_state.ui_default_time, key="time_selector")
    
    # 3. Rakennetaan datetime tämän päivän päivämäärällä
    today = datetime.date.today()
    dep_dt_naive = datetime.datetime.combine(today, user_time)
    
    # 4. Jos valittu aika on menneisyydessä tälle päivälle, siirretään huomiselle
    # (Esim. kello on 18:00 ja käyttäjä valitsee 08:00 -> tarkoittaa huomista aamua)
    if dep_dt_naive < datetime.datetime.now():
        dep_dt_naive = dep_dt_naive + datetime.timedelta(days=1)
        day_str = "Huominen"
    else:
        day_str = "Tänään"

    # 5. TÄRKEÄÄ: Lisätään aikavyöhyketieto (Local Timezone)
    # HERE API vaatii tarkan tiedon, onko kyseessä UTC vai Suomen aika.
    # astimezone() muuttaa "tyhmän" ajan paikalliseksi ajaksi (esim. +02:00 tai +03:00)
    dep_dt_aware = dep_dt_naive.astimezone()
    
    # Muutetaan ISO-formaattiin (sisältää nyt offsetin, esim: 2023-11-20T08:30:00+02:00)
    dep_iso_str = dep_dt_aware.isoformat(timespec='seconds')
    
    st.caption(f"{day_str}: {dep_dt_naive.strftime('%d.%m. klo %H:%M')}")
    # Debug-tuloste (voit poistaa myöhemmin):
    # st.caption(f"API saa: {dep_iso_str}")

if st.button("Hae reitti (HERE API)"):
    with st.spinner("Lasketaan reittiä ja liikennettä..."):
        o_coords = geocode(origin)
        d_coords = geocode(destination)
        
        if o_coords and d_coords:
            # Tallennetaan tiedot muistiin
            st.session_state.origin_coords = o_coords
            st.session_state.dest_coords = d_coords
            # Tallennetaan myös "aware" aika (sisältää aikavyöhykkeen), jotta laskut menevät oikein
            st.session_state.departure_dt = dep_dt_aware 
            
            # Kutsutaan API:a
            route_data = route(o_coords, d_coords, departure_time=dep_iso_str)
            
            if route_data and "routes" in route_data:
                poly = route_data["routes"][0]["sections"][0]["polyline"]
                st.session_state.coords = flexpolyline.decode(poly)
                st.session_state.route_summary = extract_route_summary(route_data)
                st.session_state.here_incidents = parse_traffic_incidents(route_data)
                
                # Nollataan vanha digitraffic-data
                st.session_state.digitraffic_messages = []
                st.success("Reitti haettu!")

                # --- TIETYÖ DEBUG-OSIO ---
                with st.expander("🔍 DEBUG: Näytä API:n raaka häiriödata"):
                    try:
                        # Kaivetaan esiin incidents-lista suoraan API:n JSON-vastauksesta
                        # Rakenne: routes -> 0 -> sections -> 0 -> incidents
                        raw_incidents = route_data["routes"][0]["sections"][0].get("incidents", [])
                        
                        st.write(f"API palautti {len(raw_incidents)} kpl raakaa häiriöobjektia.")
                        st.write("Tässä on niiden tarkka JSON-muoto:")
                        st.json(raw_incidents) 
                    except Exception as e:
                        st.warning(f"Debug-tietoja ei voitu näyttää (rakenne poikkeaa odotetusta): {e}")
                           
                
            else:
                st.error("Reittiä ei löytynyt. Tarkista osoitteet.")
                if route_data.get("error"):
                    st.write(route_data) # Debug info
        else:
             st.error("Osoitteita ei löytynyt.")

st.divider()

# --- 2. TULOKSET JA KARTTA ---
if st.session_state.coords and st.session_state.route_summary:
    coords = st.session_state.coords
    incidents = st.session_state.here_incidents
    dist_km, dur_hours = st.session_state.route_summary
    departure_dt = st.session_state.departure_dt
    
    # Laskennat
    arrival_dt = departure_dt + datetime.timedelta(hours=dur_hours)
    total_minutes = int(dur_hours * 60)

    # Infopalkki (Metrics)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Matka", f"{dist_km:.1f} km")
    k2.metric("Kesto", f"{int(dur_hours)} h {int((dur_hours%1)*60)} min")
    k3.metric("Lähtö", departure_dt.strftime("%H:%M"))
    k4.metric("Saapuminen", arrival_dt.strftime("%H:%M"))

    # KARTAN ASETUKSET
    # Jaetaan sivu: Vasen tyhjä (1), Keski leveä (3 tai 4), Oikea tyhjä (1)
    # Voit muuttaa [1, 4, 1] saadaksesi leveämmän kartan
    col_spacer1, col_map, col_spacer2 = st.columns([1, 4, 1]) 
    
    with col_map:
        st.subheader("Matkan visualisointi")
        
        # Kartan korkeuden säätö
        with st.expander("⚙️ Kartan asetukset", expanded=False):
            map_height = st.slider("Kartan korkeus (px)", min_value=300, max_value=1200, value=600, step=50)
        
        map_placeholder = st.empty()
        
        # Slider auton siirtoon
        elapsed_minutes = st.slider("Siirrä autoa (min)", 0, total_minutes, 0)
        
        # Play-nappi
        if st.button("Play ▶️ Aja reitti"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Optimointi: Jos matka on pitkä, hypätään useampi minuutti kerralla
            step_size = max(1, total_minutes // 50)
            
            for t in range(0, total_minutes + 1, step_size):
                fraction = t / total_minutes
                # Lasketaan indeksi
                idx = int(fraction * (len(coords) - 1))
                car_pos = coords[idx]
                
                # Lasketaan kello
                sim_time = departure_dt + datetime.timedelta(minutes=t)
                
                status_text.caption(f"⏱️ Kello: {sim_time.strftime('%H:%M')} ({t} min)")
                progress_bar.progress(fraction)
                
                # Luodaan ja piirretään kartta
                deck = create_map(coords, incidents, car_pos, st.session_state.origin_coords, st.session_state.dest_coords)
                
                # HUOM: Tässä annetaan height-parametri!
                map_placeholder.pydeck_chart(deck, height=map_height)
                
                time.sleep(0.05) # Animaation nopeus
            
            st.success("Perillä!")
            
        else:
            # Staattinen tila (kun ei ajeta animaatiota)
            fraction = elapsed_minutes / total_minutes if total_minutes > 0 else 0
            idx = int(fraction * (len(coords) - 1))
            car_pos = coords[idx]
            
            deck = create_map(coords, incidents, car_pos, st.session_state.origin_coords, st.session_state.dest_coords)
            map_placeholder.pydeck_chart(deck, height=map_height)

    # --- 3. LISÄTIEDOT JA DIGITRAFFIC ---
    st.divider()
    st.subheader("Lisätiedot")

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.info(f"HERE Häiriöt reitillä: {len(incidents)} kpl")
        if incidents:
            for inc in incidents:
                # Valitaan ikoni
                taso = str(inc.get("taso")).lower()
                icon = "🚨" if taso in ["critical", "blocked", "major"] else "🚧"
                
                with st.expander(f"{icon} {inc.get('tyyppi')} ({inc.get('taso')})"):
                    st.write(inc.get("kuvaus"))
                    st.caption(f"Sijainti: {inc.get('paikka')}")

    with col_d2:
        st.write("### Digitraffic (Fintraffic)")
        st.caption("Hakee kelikamerat ja tiedotteet reitin ympäriltä (BBox).")
        
        if st.button("Hae DigiTraffic-tiedot (BBOX)"):
            if st.session_state.coords:
                with st.spinner("Haetaan Digitraffic-dataa..."):
                    # Lasketaan BBOX
                    bbox = calculate_bbox(st.session_state.coords)
                    
                    # Haetaan viestit
                    messages = traffic_messages_near_route(st.session_state.coords)
                    tms_info = tms_near_route(st.session_state.coords)
                    
                    st.session_state.digitraffic_messages = messages
                    
                    st.write(f"Löydettyjä tiedotteita: {len(messages)}")
            else:
                st.warning("Hae ensin reitti!")

        # Näytetään haetut viestit
        if st.session_state.digitraffic_messages:
            for msg in st.session_state.digitraffic_messages:
                with st.expander(f"🇫🇮 {msg.get('otsikko')}"):
                    st.write(msg.get("kuvaus"))
                    st.write(f"**Sijainti:** {msg.get('sijainti')}")
                    st.caption(f"Aika: {msg.get('aika')}")

# ====================================================================
# END OF FILE
# ====================================================================