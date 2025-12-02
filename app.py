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
from weather_client import get_rainviewer_data, get_closest_timestamp

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

@st.cache_data(ttl=300)
def get_cached_weather_data():
    return get_rainviewer_data()

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

# MUUTOS: Lisätty 'digitraffic_incidents' parametri
def create_map(coords, incidents, digitraffic_incidents, car_pos, origin_coords, dest_coords, cameras, layer_settings, map_style, weather_ts, weather_path, weather_host, weather_opacity):
    layers = []

    # 1. SÄÄ (Manual Tiling via BitmapLayers)
    # KORJAUS: Koska TileLayer on rikki, luomme tiilet manuaalisesti Pythonissa
    # MUUTOS: Näytetään sää vaikka reittiä ei olisi (poistettu 'and coords')
    if layer_settings.get("show_weather") and weather_ts and weather_path and weather_host:
        
        # Apu-funktiot tiililaskentaan (Web Mercator)
        def deg2num(lat_deg, lon_deg, zoom):
            lat_rad = math.radians(lat_deg)
            n = 2.0 ** zoom
            xtile = int((lon_deg + 180.0) / 360.0 * n)
            ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
            return (xtile, ytile)

        def num2deg(xtile, ytile, zoom):
            n = 2.0 ** zoom
            lon_deg = xtile / n * 360.0 - 180.0
            lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
            lat_deg = math.degrees(lat_rad)
            return (lat_deg, lon_deg)

        # 1. Määritä alue (Koko Suomi)
        # Käytetään kiinteää bboxia, jotta sää näkyy koko maassa
        min_lat, max_lat = 59.0, 71.0
        min_lon, max_lon = 19.0, 33.0

        # 2. Määritä zoom-taso (RainViewer tukee 6)
        zoom = 6
        
        # 3. Laske tiilialue
        x_min, y_max = deg2num(min_lat, min_lon, zoom) # Huom: y kasvaa etelään
        x_max, y_min = deg2num(max_lat, max_lon, zoom)
        
        # Varmistus järjestyksestä
        x_start, x_end = min(x_min, x_max), max(x_min, x_max)
        y_start, y_end = min(y_min, y_max), max(y_min, y_max)

        # 4. Generoi BitmapLayer jokaiselle tiilelle
        # Rajoitetaan määrää varmuuden vuoksi (ettei tule satoja pyyntöjä)
        max_tiles = 50 
        count = 0
        
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                if count >= max_tiles: break
                
                # Laske tiilen bbox (bounds)
                # num2deg antaa tiilen vasemman yläkulman (NW)
                # Tarvitsemme [west, south, east, north]
                nw_lat, nw_lon = num2deg(x, y, zoom)
                se_lat, se_lon = num2deg(x + 1, y + 1, zoom)
                
                bounds = [nw_lon, se_lat, se_lon, nw_lat]
                
                tile_url = f"{weather_host}{weather_path}/256/{zoom}/{x}/{y}/6/1_1.png"
                
                layers.append(pdk.Layer(
                    "BitmapLayer",
                    id=f"weather-tile-{x}-{y}",
                    image=tile_url,
                    bounds=bounds,
                    opacity=weather_opacity
                ))
                count += 1

    # 2. REITTI
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

    # 3. KELIKAMERAT
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

    # 4. PISTEET
    point_data = []
    if origin_coords: point_data.append({"pos": [origin_coords[1], origin_coords[0]], "color": [0, 255, 100], "name": "Lähtö"})
    if dest_coords: point_data.append({"pos": [dest_coords[1], dest_coords[0]], "color": [255, 50, 50], "name": "Määränpää"})
    
    if point_data:
        layers.append(pdk.Layer("ScatterplotLayer", data=point_data, id="endpoints", get_position="pos", get_color="color", get_radius=800, radius_min_pixels=6, pickable=True, stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=2))

    # 5. HERE HÄIRIÖT (Punainen/Oranssi)
    if layer_settings.get("show_incidents") and incidents:
        incident_points = [{"pos": [i['lon'], i['lat']], "color": [200, 0, 0] if 'critical' in str(i['taso']) else [255, 140, 0], "name": i['tyyppi']} for i in incidents if i.get('lat')]
        if incident_points:
            layers.append(pdk.Layer("ScatterplotLayer", data=incident_points, id="incidents", get_position="pos", get_color="color", get_radius=600, pickable=True, stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=1))

    # 6. DIGITRAFFIC HÄIRIÖT (Syaani - UUSI)
    if layer_settings.get("show_incidents") and digitraffic_incidents:
        dt_points = []
        for d in digitraffic_incidents:
            # Käytetään digitraffic_client.py:n palauttamia avaimia (lat, lon, otsikko)
            if d.get('lat') and d.get('lon'):
                dt_points.append({
                    "pos": [d['lon'], d['lat']],
                    "color": [0, 255, 255], # Syaani
                    "name": f"FI: {d.get('otsikko', 'Tiedote')}"
                })
        
        if dt_points:
            layers.append(pdk.Layer(
                "ScatterplotLayer", 
                data=dt_points, 
                id="dt_incidents", 
                get_position="pos", 
                get_color="color", 
                get_radius=600, 
                pickable=True, 
                stroked=True, 
                get_line_color=[0,0,0], 
                line_width_min_pixels=1
            ))

    # 7. AUTO
    if layer_settings.get("show_car") and car_pos:
        layers.append(pdk.Layer("ScatterplotLayer", data=[{"pos": [car_pos[1], car_pos[0]], "name": "Auto"}], id="car", get_position="pos", get_color=[0, 100, 255], get_radius=1000, radius_min_pixels=8, pickable=True, stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=2))

    if coords:
        formatted_points = [[p[1], p[0]] for p in coords]
        view_state = compute_view(formatted_points, view_proportion=0.9)
        view_state.pitch = 0
    else:
        view_state = pdk.ViewState(latitude=61.92, longitude=25.74, zoom=6)

    tooltip = {"text": "{name}"}

    return pdk.Deck(map_style=map_style, initial_view_state=view_state, layers=layers, api_keys={"mapbox": MAPBOX_TOKEN}, tooltip=tooltip)

def clear_search():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.cache_data.clear()

# ====================================================================
# UI
# ====================================================================

st.set_page_config(page_title="Reitti Pro", layout="wide")

keys = ["coords", "cameras", "route_summary", "origin_coords", "dest_coords", "current_location", "dep_dt", "here_incidents", "digitraffic_messages", "selected_camera", "weather_timestamps", "weather_host", "weather_paths"]
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ["coords", "cameras", "here_incidents", "digitraffic_messages", "weather_timestamps"] else None
        if key == "weather_paths": st.session_state[key] = {}

if "ui_default_time" not in st.session_state:
    st.session_state.ui_default_time = (datetime.datetime.now() + datetime.timedelta(minutes=10)).time()

if st.session_state.coords and (not st.session_state.weather_host or not st.session_state.weather_paths):
    host, ts_dict = get_cached_weather_data()
    st.session_state.weather_timestamps = sorted(list(ts_dict.keys()))
    st.session_state.weather_paths = ts_dict
    st.session_state.weather_host = host
    st.rerun()

st.title("Reitti ja Liikenne Pingut Pro 🚗")

if not MAPBOX_TOKEN:
    st.warning("⚠️ MAPBOX_TOKEN puuttuu.")

# --- SIDEBAR ---
with st.sidebar:
    if st.session_state.selected_camera:
        cam = st.session_state.selected_camera
        st.success(f"📸 {cam.get('name', 'Kelikamera')}")
        img_url = cam.get("imageUrl")
        if img_url:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(img_url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    st.image(resp.content, width="stretch", caption=f"ID: {cam.get('id')}")
                else:
                    st.error(f"Virhe: {resp.status_code}")
            except Exception as e:
                st.error("Yhteysvirhe.")
        if st.button("Sulje kuva", type="primary"):
            st.session_state.selected_camera = None
            st.rerun()
        st.divider()

    st.header("🗺️ Asetukset")
    map_style = st.selectbox("Karttatyyli", ["mapbox://styles/mapbox/dark-v11", "mapbox://styles/mapbox/streets-v12", "mapbox://styles/mapbox/satellite-streets-v12"])
    
    st.subheader("Reititys")
    routing_mode = st.radio("Optimointi", ["fast", "short"], format_func=lambda x: "Nopein" if x=="fast" else "Lyhin")
    
    avoid_options = []
    if st.checkbox("Vältä moottoriteitä"): avoid_options.append("controlledAccessHighway")
    if st.checkbox("Vältä tietulleja"): avoid_options.append("tollRoad")
    
    st.subheader("Tasot")
    layer_settings = {
        "show_route": st.checkbox("Reittiviiva", True),
        "show_weather": st.checkbox("Sade-ennuste", True),
        "show_incidents": st.checkbox("Häiriöt", True),
        "show_cameras": st.checkbox("Kelikamerat 📷", True),
        "show_car": st.checkbox("Auto", True),
    }
    
    weather_opacity = 0.0
    if layer_settings["show_weather"]:
        weather_opacity = st.slider("Sään läpinäkyvyys", 0.0, 1.0, 0.6, step=0.1)
    
    # DEBUG MODE REMOVED

    st.divider()
    with st.expander("🛠️ Debug: Säädata"):
        if st.session_state.weather_timestamps:
            st.write(f"Ladattu {len(st.session_state.weather_timestamps)} aikaleimaa.")
            if len(st.session_state.weather_timestamps) > 0:
                ts = st.session_state.weather_timestamps[-1]
                st.write(f"Viimeisin TS: {ts}")
                
                host = st.session_state.weather_host
                path = st.session_state.weather_paths.get(ts)
                
                if host and path:
                    test_url = f"{host}{path}/256/6/36/19/6/1_1.png"
                    st.markdown(f"[Testaa tiili selaimessa]({test_url})")
                else:
                    st.warning("Host tai polku puuttuu.")
            else:
                st.warning("Ei aikaleimoja.")
        else:
            st.warning("Ei säädataa.")
        
        st.write("---")
        st.write(f"Host: {st.session_state.weather_host}")
        st.write(f"Paths count: {len(st.session_state.weather_paths) if st.session_state.weather_paths else 0}")

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
                    
                    # Haetaan säädata
                    host, ts_dict = get_cached_weather_data()
                    st.session_state.weather_timestamps = sorted(list(ts_dict.keys()))
                    st.session_state.weather_paths = ts_dict
                    st.session_state.weather_host = host
                    
                    st.session_state.selected_camera = None
                    st.rerun()
                else:
                    st.error("Ei reittiä.")
            else:
                st.error("Osoitevirhe.")

with b2:
    if st.button("Tyhjennä haku"):
        clear_search()
        st.rerun()

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
        with c_slider: t_val = st.slider("Matka etenee", 0, total_mins, 0, label_visibility="collapsed")
        
        idx = int((t_val / total_mins) * (len(coords) - 1))
        car_pos = coords[idx]
        
        sim_dt = st.session_state.dep_dt + datetime.timedelta(minutes=t_val)
        sim_ts = int(sim_dt.timestamp())
        w_ts = None
        w_path = None
        if st.session_state.weather_timestamps:
            w_ts = get_closest_timestamp(sim_ts, st.session_state.weather_timestamps)
            if w_ts and st.session_state.weather_paths:
                w_path = st.session_state.weather_paths.get(w_ts)
            st.caption(f"Sääkartta: {datetime.datetime.fromtimestamp(w_ts).strftime('%H:%M')}")

        # MUUTOS: Välitetään digitraffic_messages create_map:iin
        dt_msgs = st.session_state.get("digitraffic_messages", [])

        deck = create_map(coords, 
                          st.session_state.here_incidents, 
                          dt_msgs, # <--- UUSI
                          car_pos, 
                          st.session_state.origin_coords, 
                          st.session_state.dest_coords, 
                          st.session_state.cameras, 
                          layer_settings, 
                          map_style, 
                          w_ts, 
                          w_path, 
                          st.session_state.weather_host, 
                          weather_opacity)
        
        selection = map_placeholder.pydeck_chart(deck, width="stretch", on_select="rerun", selection_mode="single-object")
        
        if selection.selection:
            found_index = None
            def get_idx(v):
                if isinstance(v, (list, tuple)) and len(v) > 0: return v[0]
                if isinstance(v, set) and len(v) > 0: return list(v)[0]
                if isinstance(v, int): return v
                return None

            if "objects" in selection.selection:
                objs = selection.selection["objects"]
                if "cameras" in objs and objs["cameras"]:
                    new_cam = objs["cameras"][0]
                    if st.session_state.selected_camera != new_cam:
                        st.session_state.selected_camera = new_cam
                        st.rerun()
            else:
                if "cameras" in selection.selection: found_index = get_idx(selection.selection["cameras"])
                if found_index is None:
                    for v in selection.selection.values():
                        val = get_idx(v)
                        if val is not None: found_index = val; break
                
                if found_index is not None and found_index < len(st.session_state.cameras):
                    new_cam = st.session_state.cameras[found_index]
                    if st.session_state.selected_camera != new_cam:
                        st.session_state.selected_camera = new_cam
                        st.rerun()

        if play:
            step_size = max(1, total_mins // 50)
            for t in range(0, total_mins + 1, step_size):
                idx = int((t / total_mins) * (len(coords) - 1))
                car_pos = coords[idx]
                sim_dt = st.session_state.dep_dt + datetime.timedelta(minutes=t)
                w_ts = None
                w_path = None
                if st.session_state.weather_timestamps:
                    w_ts = get_closest_timestamp(int(sim_dt.timestamp()), st.session_state.weather_timestamps)
                    if w_ts and st.session_state.weather_paths:
                        w_path = st.session_state.weather_paths.get(w_ts)

                # MUUTOS: Välitetään digitraffic_messages myös silmukassa
                deck = create_map(coords, st.session_state.here_incidents, dt_msgs, car_pos, st.session_state.origin_coords, st.session_state.dest_coords, st.session_state.cameras, layer_settings, map_style, w_ts, w_path, st.session_state.weather_host, weather_opacity)
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