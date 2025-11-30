import streamlit as st
import flexpolyline
from typing import Tuple, List, Optional, Dict, Any
import datetime
import time
import math
import pydeck as pdk
from pydeck.data_utils import compute_view
from dotenv import load_dotenv
import os
from streamlit_js_eval import get_geolocation
import requests

# 1. Ladataan ympäristömuuttujat
load_dotenv()

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
pdk.settings.mapbox_api_key = MAPBOX_TOKEN

# 2. Tuodaan funktiot
from here_client import geocode, route, parse_traffic_incidents
from digitraffic_client import get_weather_cameras, traffic_messages_near_route

# ====================================================================
# API WRAPPERS
# ====================================================================

@st.cache_data(ttl=600)
def get_cached_route(origin: Tuple[float, float], 
                     dest: Tuple[float, float], 
                     dep_time: str,
                     mode: str,
                     avoid_list: List[str]):
    return route(origin, dest, departure_time=dep_time, routing_mode=mode, avoid_features=avoid_list)

@st.cache_data(ttl=3600)
def geocode_cached(query: str):
    return geocode(query)

def extract_route_summary(route_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    try:
        section = route_data["routes"][0]["sections"][0]
        summary = section["summary"]
        return summary["length"] / 1000.0, summary["duration"] / 3600.0
    except Exception:
        return None

# ====================================================================
# MAP CREATION
# ====================================================================

def create_map(coords, incidents, car_pos, origin_coords, dest_coords, cameras, layer_settings, map_style):
    layers = []

    # 1. REITTI
    if layer_settings.get("show_route") and coords:
        layers.append(pdk.Layer(
            "PathLayer",
            data=[{"path": [[p[1], p[0]] for p in coords]}],
            id="route",
            get_path="path",
            get_color=[60, 160, 255],
            width_scale=20,
            width_min_pixels=3,
            opacity=0.8,
        ))

    # 2. KELIKAMERAT
    if layer_settings.get("show_cameras") and cameras:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=cameras,
            id="cameras", 
            get_position="[lon, lat]",
            get_color=[255, 220, 0], 
            get_radius=800,
            radius_min_pixels=8, 
            pickable=True,       
            stroked=True,
            get_line_color=[0,0,0],
            line_width_min_pixels=1,
            auto_highlight=True
        ))

    # 3. PISTEET
    point_data = []
    if origin_coords: point_data.append({"pos": [origin_coords[1], origin_coords[0]], "color": [0, 255, 100], "name": "Lähtö"})
    if dest_coords: point_data.append({"pos": [dest_coords[1], dest_coords[0]], "color": [255, 50, 50], "name": "Määränpää"})
    
    if point_data:
        layers.append(pdk.Layer(
            "ScatterplotLayer", 
            data=point_data, 
            id="endpoints",
            get_position="pos", 
            get_color="color", 
            get_radius=800, 
            radius_min_pixels=6, 
            pickable=True, 
            stroked=True, 
            get_line_color=[255, 255, 255], 
            line_width_min_pixels=2
        ))

    # 4. HÄIRIÖT
    if layer_settings.get("show_incidents") and incidents:
        incident_points = [{"pos": [i['lon'], i['lat']], "color": [200, 0, 0] if 'critical' in str(i['taso']) else [255, 140, 0], "name": i['tyyppi']} for i in incidents if i.get('lat')]
        if incident_points:
            layers.append(pdk.Layer(
                "ScatterplotLayer", 
                data=incident_points, 
                id="incidents",
                get_position="pos", 
                get_color="color", 
                get_radius=600, 
                pickable=True, 
                stroked=True, 
                get_line_color=[255, 255, 255], 
                line_width_min_pixels=1
            ))

    # 5. AUTO
    if layer_settings.get("show_car") and car_pos:
        layers.append(pdk.Layer(
            "ScatterplotLayer", 
            data=[{"pos": [car_pos[1], car_pos[0]], "name": "Auto"}],
            id="car",
            get_position="pos", 
            get_color=[0, 100, 255], 
            get_radius=1000, 
            radius_min_pixels=8, 
            pickable=True, 
            stroked=True, 
            get_line_color=[255, 255, 255], 
            line_width_min_pixels=2
        ))

    # NÄKYMÄ
    if coords:
        formatted_points = [[p[1], p[0]] for p in coords]
        view_state = compute_view(formatted_points, view_proportion=0.9)
        view_state.pitch = 0
    else:
        view_state = pdk.ViewState(latitude=61.92, longitude=25.74, zoom=6)

    tooltip = {"text": "{name}"}

    return pdk.Deck(map_style=map_style, initial_view_state=view_state, layers=layers, api_keys={"mapbox": MAPBOX_TOKEN}, tooltip=tooltip)

def clear_search():
    keys = ["coords", "cameras", "here_incidents", "digitraffic_messages", "route_summary", "selected_camera"]
    for k in keys:
        st.session_state[k] = [] if k != "route_summary" else None

# ====================================================================
# UI
# ====================================================================

st.set_page_config(page_title="Reitti Pro", layout="wide")

keys = ["coords", "cameras", "route_summary", "origin_coords", "dest_coords", "current_location", "dep_dt", "here_incidents", "digitraffic_messages", "selected_camera"]
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ["coords", "cameras", "here_incidents", "digitraffic_messages"] else None

if "ui_default_time" not in st.session_state:
    st.session_state.ui_default_time = (datetime.datetime.now() + datetime.timedelta(minutes=10)).time()

st.title("Reitti ja Liikenne Pingut Pro 🚗")

if not MAPBOX_TOKEN:
    st.warning("⚠️ MAPBOX_TOKEN puuttuu.")

# --- SIDEBAR (KAMERA) ---
with st.sidebar:
    if st.session_state.selected_camera:
        cam = st.session_state.selected_camera
        st.success(f"📸 {cam.get('name', 'Kelikamera')}")
        
        img_url = cam.get("imageUrl")
        if img_url:
            try:
                # KORJAUS: Lisätään User-Agent ja käsitellään virheet
                with st.spinner("Ladataan kuvaa..."):
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    resp = requests.get(img_url, headers=headers, timeout=5)
                    
                    if resp.status_code == 200:
                        st.image(resp.content, width="stretch", caption=f"ID: {cam.get('id')}")
                    else:
                        st.error(f"Kameran vastaus: {resp.status_code}")
                        st.caption(f"URL: {img_url}")
            except Exception as e:
                st.error("Yhteysvirhe kameraan.")
        else:
            st.warning("Ei kuvalinkkiä.")
        
        if st.button("Sulje kuva", type="primary"):
            st.session_state.selected_camera = None
            st.rerun()
        st.divider()
    else:
        st.info("💡 Klikkaa keltaista palloa kartalla nähdäksesi kuvan tässä.")

    st.header("🗺️ Asetukset")
    map_style = st.selectbox("Karttatyyli", ["mapbox://styles/mapbox/streets-v12", "mapbox://styles/mapbox/satellite-streets-v12", "mapbox://styles/mapbox/dark-v11"])
    
    st.subheader("Reititys")
    routing_mode = st.radio("Optimointi", ["fast", "short"], format_func=lambda x: "Nopein" if x=="fast" else "Lyhin")
    
    avoid_options = []
    if st.checkbox("Vältä moottoriteitä"): avoid_options.append("controlledAccessHighway")
    if st.checkbox("Vältä tietulleja"): avoid_options.append("tollRoad")
    
    st.subheader("Tasot")
    layer_settings = {
        "show_route": st.checkbox("Reittiviiva", True),
        "show_incidents": st.checkbox("Häiriöt", True),
        "show_cameras": st.checkbox("Kelikamerat 📷", True),
        "show_car": st.checkbox("Auto", True),
    }

# --- INPUTS ---
c1, c2, c3 = st.columns(3)
search_disabled = False

with c1:
    use_gps = st.checkbox("Käytä GPS-sijaintia")
    if use_gps:
        if st.session_state.current_location:
             lat, lon = st.session_state.current_location
             st.caption(f"✅ GPS: {lat:.4f}, {lon:.4f}")
        else:
             loc = get_geolocation()
             if loc and loc.get("coords"):
                 st.session_state.current_location = (loc["coords"]["latitude"], loc["coords"]["longitude"])
                 st.rerun()
             else:
                 st.caption("⏳ Odotetaan GPS...")
                 search_disabled = True
    origin = st.text_input("Lähtö", "Helsinki", disabled=use_gps)

with c2:
    dest = st.text_input("Määränpää", "Tampere")

with c3:
    col_d, col_t = st.columns(2)
    with col_d: date_val = st.date_input("Päivä", datetime.date.today())
    with col_t: time_val = st.time_input("Kello", st.session_state.ui_default_time, key="time_sel")
    dep_dt_naive = datetime.datetime.combine(date_val, time_val)
    dep_iso = dep_dt_naive.astimezone().isoformat(timespec="seconds")

st.divider()

# --- BUTTONS ---
b1, b2 = st.columns([1, 4])
with b1:
    if st.button("Hae reitti 🚀", type="primary", disabled=search_disabled):
        with st.spinner("Suunnitellaan..."):
            
            o_c = st.session_state.current_location if use_gps else geocode_cached(origin)
            d_c = geocode_cached(dest)
            
            if o_c and d_c:
                st.session_state.origin_coords = o_c
                st.session_state.dest_coords = d_c
                st.session_state.dep_dt = dep_dt_naive
                
                r_data = get_cached_route(o_c, d_c, dep_iso, routing_mode, avoid_options)
                
                if r_data and "routes" in r_data:
                    poly = r_data["routes"][0]["sections"][0]["polyline"]
                    st.session_state.coords = flexpolyline.decode(poly)
                    st.session_state.route_summary = extract_route_summary(r_data)
                    st.session_state.here_incidents = parse_traffic_incidents(r_data)
                    st.session_state.cameras = get_weather_cameras(st.session_state.coords)
                    st.session_state.digitraffic_messages = traffic_messages_near_route(st.session_state.coords)
                    st.session_state.selected_camera = None
                    st.rerun()
                else:
                    st.error("Ei reittiä.")
            else:
                st.error("Osoitevirhe.")

with b2:
    st.button("Tyhjennä", on_click=clear_search)

# --- RESULTS ---
if st.session_state.coords:
    coords = st.session_state.coords
    dist, dur = st.session_state.route_summary if st.session_state.route_summary else (0,0)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Matka", f"{dist:.1f} km")
    m2.metric("Ajoaika", f"{int(dur)}h {int((dur%1)*60)}min")
    m3.metric("Lähtö", st.session_state.dep_dt.strftime("%H:%M"))
    m4.metric("Perillä", (st.session_state.dep_dt + datetime.timedelta(hours=dur)).strftime("%H:%M"))

    col_map, col_chart = st.columns([2, 1])
    
    with col_map:
        map_placeholder = st.empty()
        c_play, c_slider = st.columns([1, 4])
        with c_play: play = st.button("Play ▶️")
        total_mins = int(dur * 60)
        if total_mins < 1: total_mins = 1
        with c_slider: t_val = st.slider("Eteneminen", 0, total_mins, 0, label_visibility="collapsed")
        
        idx = int((t_val / total_mins) * (len(coords) - 1))
        car_pos = coords[idx]

        deck = create_map(coords, st.session_state.here_incidents, car_pos, st.session_state.origin_coords, st.session_state.dest_coords, st.session_state.cameras, layer_settings, map_style)
        
        # --- KARTTA & VALINTA ---
        selection = map_placeholder.pydeck_chart(
            deck, 
            width="stretch",
            on_select="rerun", 
            selection_mode="single-object"
        )
        
        # --- VALINNAN LUKU ---
        if selection.selection:
            found_index = None
            def get_idx(v):
                if isinstance(v, (list, tuple)) and len(v) > 0: return v[0]
                if isinstance(v, set) and len(v) > 0: return list(v)[0]
                if isinstance(v, int): return v
                return None

            if "cameras" in selection.selection:
                found_index = get_idx(selection.selection["cameras"])
            
            # Fallback: objekti
            if found_index is None and "objects" in selection.selection:
                 objs = selection.selection["objects"]
                 if "cameras" in objs and objs["cameras"]:
                     # Valinta onnistui suoraan object-tilassa
                     new_cam = objs["cameras"][0]
                     if st.session_state.selected_camera != new_cam:
                        st.session_state.selected_camera = new_cam
                        st.rerun()
            
            # Fallback: indeksi
            if found_index is None:
                for k, v in selection.selection.items():
                    if k != "objects":
                        val = get_idx(v)
                        if val is not None: 
                            found_index = val
                            break
            
            if found_index is not None and found_index < len(st.session_state.cameras):
                new_cam = st.session_state.cameras[found_index]
                if st.session_state.selected_camera != new_cam:
                    st.session_state.selected_camera = new_cam
                    st.rerun()

        # Animaatio
        if play:
            step_size = max(1, total_mins // 50)
            for t in range(0, total_mins + 1, step_size):
                idx = int((t / total_mins) * (len(coords) - 1))
                car_pos = coords[idx]
                deck = create_map(coords, st.session_state.here_incidents, car_pos, st.session_state.origin_coords, st.session_state.dest_coords, st.session_state.cameras, layer_settings, map_style)
                map_placeholder.pydeck_chart(deck, width="stretch")
                time.sleep(0.05)

    with col_chart:
        st.subheader("Profiili")
        chart_data = []
        has_elevation = len(coords[0]) > 2
        for p in coords:
            val = p[2] if has_elevation else 0
            chart_data.append(val)
        if has_elevation:
            st.area_chart(chart_data, color="#ffaa00", width="stretch")
        else:
            st.info("Ei korkeusdataa.")
            st.progress(t_val / total_mins)

    # --- LISTAT ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.session_state.here_incidents:
            st.subheader("Häiriöt")
            for inc in st.session_state.here_incidents:
                with st.expander(f"{inc.get('tyyppi')}"):
                    st.write(inc.get("kuvaus"))
    with c2:
        if st.session_state.digitraffic_messages:
            st.subheader("Digitraffic tiedotteet")
            for msg in st.session_state.digitraffic_messages:
                with st.expander(f"🇫🇮 {msg.get('otsikko')}"):
                    st.write(msg.get("kuvaus"))