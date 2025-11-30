import streamlit as st
import flexpolyline
from typing import Tuple, List, Optional, Dict, Any
import datetime
import time
import pydeck as pdk
from dotenv import load_dotenv
import os
from streamlit_js_eval import get_geolocation
import requests

# 1. Ladataan ympäristömuuttujat
load_dotenv()

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
# Asetetaan token globaalisti
pdk.settings.mapbox_api_key = MAPBOX_TOKEN

# 2. Tuodaan funktiot
from here_client import geocode, route, parse_traffic_incidents
from digitraffic_client import calculate_bbox, traffic_messages_near_route, tms_near_route

# ====================================================================
# VÄLIMUISTITETUT API-KUTSUJEN KÄÄREET (CACHING)
# ====================================================================

@st.cache_data(ttl=600)
def get_cached_route(origin, dest, dep_time):
    """Käärii HERE API -kutsun välimuistiin."""
    return route(origin, dest, departure_time=dep_time)

# ====================================================================
# HELPER-FUNKTIOT
# ====================================================================

def extract_route_summary(route_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
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

def create_map(coords, incidents, car_position, origin_coords, dest_coords, layer_settings):
    """Luo Pydeck Deck -objektin."""
    n_points = len(coords)
    if n_points > 0:
        mid = n_points // 2
        center_lat, center_lon = coords[mid]
    else:
        center_lat, center_lon = 61.9241, 25.7482

    layers = []

    # 1. REITTI
    if layer_settings.get("show_route"):
        route_layer = pdk.Layer(
            "PathLayer",
            data=[{"path": [[lon, lat] for (lat, lon) in coords]}],
            get_path="path",
            get_color=[100, 149, 237],
            width_scale=10,
            width_min_pixels=3,
            opacity=0.8,
        )
        layers.append(route_layer)

    # 2. PISTEET
    point_data = []
    if origin_coords: point_data.append({"pos": [origin_coords[1], origin_coords[0]], "color": [0, 180, 0], "label": "Lähtö"})
    if dest_coords: point_data.append({"pos": [dest_coords[1], dest_coords[0]], "color": [200, 0, 0], "label": "Määränpää"})
    
    if point_data:
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

    # 3. HÄIRIÖT
    if layer_settings.get("show_incidents") and incidents:
        incident_points = []
        for inc in incidents:
            level = str(inc.get("taso", "")).lower()
            color = [200, 0, 0] if level in ["critical", "blocked"] else \
                    [255, 140, 0] if level == "major" else [255, 215, 0]
            lat, lon = inc.get("lat"), inc.get("lon")
            if lat and lon:
                incident_points.append({
                    "pos": [lon, lat],
                    "color": color,
                    "label": f"{inc.get('tyyppi')}: {inc.get('kuvaus')}"
                })
        
        if incident_points:
            incidents_layer = pdk.Layer(
                "ScatterplotLayer",
                data=incident_points,
                get_position="pos",
                get_color="color",
                get_radius=600,
                radius_min_pixels=5,
                pickable=True,
                opacity=0.9,
                stroked=True,
                get_line_color=[255, 255, 255],
                line_width_min_pixels=1
            )
            layers.append(incidents_layer)

    # 4. AUTO
    if layer_settings.get("show_car") and car_position:
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
        initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7, pitch=0),
        layers=layers,
        api_keys={"mapbox": MAPBOX_TOKEN},
        tooltip={"html": "<b>{label}</b>", "style": {"color": "white", "backgroundColor": "rgba(0,0,0,0.8)"}}
    )
    return deck

# ====================================================================
# CALLBACKS (Resetointi)
# ====================================================================
def clear_search_results():
    """Nollaa hakutulokset, mutta jättää inputit ennalleen muokkausta varten."""
    st.session_state.coords = []
    st.session_state.route_summary = None
    st.session_state.here_incidents = []
    st.session_state.digitraffic_messages = []
    # Emme nollaa origin/destination tekstikenttiä, jotta niitä on helppo muokata

# ====================================================================
# UI
# ====================================================================
st.set_page_config(page_title="Reitti & Liikenne", layout="wide")

# State Initialization
if "coords" not in st.session_state: st.session_state.coords = []
if "route_summary" not in st.session_state: st.session_state.route_summary = None
if "here_incidents" not in st.session_state: st.session_state.here_incidents = []
if "departure_dt" not in st.session_state: st.session_state.departure_dt = datetime.datetime.now()
if "digitraffic_messages" not in st.session_state: st.session_state.digitraffic_messages = []
if "origin_coords" not in st.session_state: st.session_state.origin_coords = None

st.title("Reitti ja Liikenne 🚗")

if not MAPBOX_TOKEN:
    st.warning("⚠️ MAPBOX_TOKEN puuttuu .env-tiedostosta.")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Karttatasot")
    layer_settings = {
        "show_route": st.checkbox("Näytä reitti", value=True),
        "show_incidents": st.checkbox("Näytä liikennehäiriöt", value=True),
        "show_car": st.checkbox("Näytä auto animaatiossa", value=True),
    }

# --- INPUT SECTION ---
c1, c2, c3 = st.columns(3)

with c1:
    use_current_location = st.checkbox("Käytä nykyistä sijaintia", value=False)
    
    current_location_data = None
    if use_current_location:
        current_location_data = get_geolocation()
        if current_location_data:
            st.caption("✅ Sijainti löytyi")
        else:
            st.caption("⏳ Odotetaan sijaintia...")
            
    origin = st.text_input("Lähtö", value="Helsinki", disabled=use_current_location)

with c2:
    destination = st.text_input("Määränpää", value="Tampere")

with c3:
    if "ui_default_time" not in st.session_state:
        st.session_state.ui_default_time = (datetime.datetime.now() + datetime.timedelta(minutes=10)).time()
    
    user_time = st.time_input("Lähtöaika", value=st.session_state.ui_default_time, key="time_selector")
    today = datetime.date.today()
    dep_dt_naive = datetime.datetime.combine(today, user_time)
    
    if dep_dt_naive < datetime.datetime.now():
        dep_dt_naive = dep_dt_naive + datetime.timedelta(days=1)
        day_str = "Huominen"
    else:
        day_str = "Tänään"
        
    dep_dt_aware = dep_dt_naive.astimezone()
    dep_iso_str = dep_dt_aware.isoformat(timespec="seconds")
    st.caption(f"{day_str}: {dep_dt_naive.strftime('%d.%m. klo %H:%M')}")

st.divider()

# --- ACTION BUTTONS (Uusi järjestys) ---
col_btn1, col_btn2 = st.columns([1, 4])

with col_btn1:
    # HAE REITTI
    if st.button("Hae reitti (HERE API)", type="primary"):
        with st.spinner("Lasketaan reittiä..."):
            o_coords = None

            if use_current_location:
                if current_location_data and current_location_data.get("coords"):
                    o_coords = (current_location_data["coords"]["latitude"], current_location_data["coords"]["longitude"])
                    st.success(f"Sijainti: {o_coords[0]:.4f}, {o_coords[1]:.4f}")
                else:
                    st.error("Sijaintitietoa ei saatu. Tarkista selaimen luvat.")
                    st.stop()
            else:
                o_coords = geocode(origin)

            d_coords = geocode(destination)

            if o_coords and d_coords:
                st.session_state.origin_coords = o_coords
                st.session_state.dest_coords = d_coords
                st.session_state.departure_dt = dep_dt_aware

                # API-kutsu
                route_data = get_cached_route(o_coords, d_coords, dep_iso_str)

                if route_data and "routes" in route_data:
                    poly = route_data["routes"][0]["sections"][0]["polyline"]
                    st.session_state.coords = flexpolyline.decode(poly)
                    st.session_state.route_summary = extract_route_summary(route_data)
                    st.session_state.here_incidents = parse_traffic_incidents(route_data)
                    st.session_state.digitraffic_messages = []
                    st.success("Reitti haettu!")
                    st.rerun() # Pakotetaan päivitys
                else:
                    st.error("Reittiä ei löytynyt.")
            else:
                 st.error("Osoitteita ei löytynyt.")

with col_btn2:
    # TYHJENNÄ HAKU
    # Tämä nappi ajaa funktion, joka nollaa tulokset, mutta jättää tekstit.
    st.button("Tyhjennä haku", on_click=clear_search_results)


# --- RESULTS & MAP ---
# Tämä osio näkyy vain, jos coords on olemassa (eli haku on tehty eikä tyhjennetty)
if st.session_state.coords and st.session_state.route_summary:
    coords = st.session_state.coords
    dist_km, dur_hours = st.session_state.route_summary
    departure_dt = st.session_state.departure_dt
    arrival_dt = departure_dt + datetime.timedelta(hours=dur_hours)
    total_minutes = int(dur_hours * 60)

    # Metrics
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Matka", f"{dist_km:.1f} km")
    k2.metric("Kesto", f"{int(dur_hours)} h {int((dur_hours % 1) * 60)} min")
    k3.metric("Lähtö", departure_dt.strftime("%H:%M"))
    k4.metric("Saapuminen", arrival_dt.strftime("%H:%M"))

    # Map Layout
    col_spacer1, col_map, col_spacer2 = st.columns([1, 6, 1])
    
    with col_map:
        st.subheader("Kartta")
        with st.expander("⚙️ Asetukset", expanded=False):
            map_height = st.slider("Korkeus", 300, 1200, 600, 50)

        map_placeholder = st.empty()
        elapsed_minutes = st.slider("Simulaatio (min)", 0, total_minutes, 0)

        if st.button("Play ▶️"):
            step_size = max(1, total_minutes // 50)
            progress_bar = st.progress(0)
            status = st.empty()

            for t in range(0, total_minutes + 1, step_size):
                fraction = t / total_minutes
                idx = int(fraction * (len(coords) - 1))
                car_pos = coords[idx]
                sim_time = departure_dt + datetime.timedelta(minutes=t)
                
                status.caption(f"⏱️ {sim_time.strftime('%H:%M')}")
                progress_bar.progress(fraction)
                
                deck = create_map(
                    coords, st.session_state.here_incidents, car_pos,
                    st.session_state.origin_coords, st.session_state.dest_coords,
                    layer_settings
                )
                map_placeholder.pydeck_chart(deck, height=map_height)
                time.sleep(0.05)
            st.success("Perillä!")
        else:
            fraction = elapsed_minutes / total_minutes if total_minutes > 0 else 0
            idx = int(fraction * (len(coords) - 1))
            car_pos = coords[idx]
            
            deck = create_map(
                coords, st.session_state.here_incidents, car_pos,
                st.session_state.origin_coords, st.session_state.dest_coords,
                layer_settings
            )
            map_placeholder.pydeck_chart(deck, height=map_height)

    # --- EXTRA INFO ---
    st.divider()
    c_inc, c_digi = st.columns(2)
    
    with c_inc:
        st.info(f"Liikennehäiriöt: {len(st.session_state.here_incidents)}")
        for inc in st.session_state.here_incidents:
            icon = "🚨" if str(inc.get("taso")).lower() in ["critical", "blocked"] else "🚧"
            with st.expander(f"{icon} {inc.get('tyyppi')}"):
                st.write(inc.get("kuvaus"))

    with c_digi:
        st.write("### Digitraffic")
        if st.button("Hae tiedotteet (BBOX)"):
            if coords:
                with st.spinner("Haetaan..."):
                    msgs = traffic_messages_near_route(coords)
                    st.session_state.digitraffic_messages = msgs
                    st.write(f"Tiedotteita: {len(msgs)}")
        
        for msg in st.session_state.digitraffic_messages:
            with st.expander(f"🇫🇮 {msg.get('otsikko')}"):
                st.write(msg.get("kuvaus"))