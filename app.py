import streamlit as st
import folium
from streamlit_folium import st_folium
import flexpolyline
import json

# Oletetaan, että nämä moduulit ovat olemassa ja toimivat
from here_client import geocode, route, traffic_along_route
from digitraffic_client import tms_near_route, traffic_messages_near_route

st.set_page_config(page_title="Reitti- ja liikennetiedot", layout="wide")
st.title("Reitti- ja liikennetiedot")

# --- ALUSTUS ---
# Käytetään session_statea, jotta data pysyy muistissa painallusten välillä
if 'coords' not in st.session_state:
    st.session_state.coords = []
if 'route_geometry' not in st.session_state:
    st.session_state.route_geometry = None
if 'origin_coords' not in st.session_state:
    st.session_state.origin_coords = None
if 'dest_coords' not in st.session_state:
    st.session_state.dest_coords = None

# --- KÄYTTÖLIITTYMÄ ---
col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("Lähtö", value="Helsinki")
with col2:
    destination = st.text_input("Määränpää", value="Tampere")

# --- TOIMINTO 1: HAE REITTI ---
if st.button("Hae reitti"):
    if origin and destination:
        with st.spinner("Haetaan reittiä..."):
            # 1. Geokoodaus
            origin_coords = geocode(origin)
            destination_coords = geocode(destination)

            if not origin_coords or not destination_coords:
                st.error("Lähtö- tai määränpääosoitetta ei löytynyt.")
            else:
                # Tallennetaan koordinaatit muistiin
                st.session_state.origin_coords = origin_coords
                st.session_state.dest_coords = destination_coords

                # 2. Reitin haku (HERE API)
                route_data = route(origin_coords, destination_coords)
                st.session_state.route_geometry = route_data 

                if route_data and "routes" in route_data and len(route_data["routes"]) > 0:
                    try:
                        # 3. Puretaan Polyline
                        polyline_str = route_data["routes"][0]["sections"][0]["polyline"]
                        decoded_coords = flexpolyline.decode(polyline_str)
                        st.session_state.coords = decoded_coords
                        st.success("Reitti haettu onnistuneesti!")
                        
                        # Debug-tieto (piilotettu)
                        with st.expander("Näytä raaka API-vastaus"):
                            st.json(route_data)

                    except Exception as e:
                        st.error(f"Virhe reittiviivan purkamisessa: {e}")
                else:
                    st.error("Reittidataa ei saatu. Tarkista API-avain.")
    else:
        st.warning("Anna lähtö ja määränpää.")

# --- KARTAN PIIRTÄMINEN ---
if st.session_state.coords:
    # Lasketaan kartan keskipiste reitin perusteella
    mid_idx = len(st.session_state.coords) // 2
    center_point = st.session_state.coords[mid_idx]

    m = folium.Map(location=center_point, zoom_start=8)

    # Lähtö- ja päätepisteet
    if st.session_state.origin_coords:
        folium.Marker(st.session_state.origin_coords, popup="Lähtö", icon=folium.Icon(color='green')).add_to(m)
    if st.session_state.dest_coords:
        folium.Marker(st.session_state.dest_coords, popup="Määränpää", icon=folium.Icon(color='red')).add_to(m)

    # Reittiviiva
    folium.PolyLine(st.session_state.coords, color="blue", weight=5, opacity=0.8).add_to(m)

    st.subheader("Kartta")
    st_folium(m, width=800, height=500)


# --- TOIMINTO 2: LIIKENNETIEDOT (Digitraffic) ---
st.divider()
st.subheader("Lisätiedot")

# Käytetään uniikkia key-parametria varmuuden vuoksi
if st.button("Hae liikennetiedot reitiltä", key="traffic_data_btn"):
    # TARKISTUS: Onko meillä puretut koordinaatit tallessa?
    if st.session_state.coords: 
        with st.spinner("Haetaan dataa Digitrafficista..."):
            
            # Käytetään coords-lista (Bounding Box laskentaa varten)
            coords = st.session_state.coords
            
            # 1. HERE Traffic (Placeholder)
            traffic = traffic_along_route(coords)
            
            # 2. Digitraffic TMS (Sääasemat)
            tms = tms_near_route(coords)
            
            # 3. Digitraffic Häiriöt
            messages = traffic_messages_near_route(coords)

            # Näytetään tulokset
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.info(f"Liikennehäiriöitä: {len(messages)}")
                for msg in messages:
                    with st.expander(f"⚠️ {msg['otsikko']}"):
                        st.write(f"**Sijainti:** {msg['sijainti']}")
                        st.write(f"**Kuvaus:** {msg['kuvaus']}")
                        st.caption(f"Alkoi: {msg['aika']}")
            
            with col_b:
                st.info(f"Sääasemat: {len(tms) if tms else 0}")
                if tms:
                    st.write(tms)
                else:
                    st.write("Ei dataa tai toteutus puuttuu.")

            with col_c:
                st.info("HERE Traffic")
                st.write(traffic)
    else:
        st.warning("Hae ensin reitti yllä olevasta napista, jotta koordinaatit ovat tiedossa.")

        