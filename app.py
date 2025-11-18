import streamlit as st
import folium
from streamlit_folium import st_folium
import flexpolyline
from typing import Tuple, List, Optional, Dict, Any

from dotenv import load_dotenv
import os

load_dotenv()

# ====================================================================
# TUODAAN FUNKTIOT ERILLISESTÄ TIEDOSTOSTA
# ====================================================================
from here_client import geocode, route, parse_traffic_incidents, slice_polyline
from digitraffic_client import calculate_bbox, traffic_messages_near_route, tms_near_route


# ====================================================================
# HELPER-FUNKTIO: Reitin pituus ja kesto HERE Routing API -vastauksesta
# ====================================================================
def extract_route_summary(route_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """
    Palauttaa (distance_km, duration_hours) — tai None jos ei saatavilla.
    length = metreinä, duration = sekunteina (HERE Routing API)
    """
    try:
        route_obj = route_data["routes"][0]
        section = route_obj["sections"][0]
        summary = section.get("summary", {})

        length_m = summary.get("length")      # metrit
        duration_s = summary.get("duration")  # sekunnit

        if length_m is None or duration_s is None:
            return None

        distance_km = length_m / 1000.0
        duration_hours = duration_s / 3600.0  # muutetaan tunneiksi

        return distance_km, duration_hours
    except Exception:
        return None


# ====================================================================
# STREAMLIT UI
# ====================================================================

st.set_page_config(page_title="Reitti- ja liikennetiedot", layout="wide")
st.title("Reitti- ja liikennetiedot 🗺️")

# Alusta tila
if "coords" not in st.session_state:
    st.session_state.coords = []
if "route_data" not in st.session_state:
    st.session_state.route_data = None
if "origin_coords" not in st.session_state:
    st.session_state.origin_coords = None
if "dest_coords" not in st.session_state:
    st.session_state.dest_coords = None
if "here_incidents" not in st.session_state:
    st.session_state.here_incidents = None
if "digitraffic_messages" not in st.session_state:
    st.session_state.digitraffic_messages = []
# Matka ja aika talteen tilaan (km, h)
if "route_summary" not in st.session_state:
    st.session_state.route_summary = None  # (distance_km, duration_hours)


# ----- UI -----
col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("Lähtö", value="Helsinki")
with col2:
    destination = st.text_input("Määränpää", value="Tampere")


# --------------------------------------------------------------------
# TOIMINTO: HAE REITTI HERE API:STA
# --------------------------------------------------------------------
if st.button("Hae reitti ja liikennetiedot (HERE)"):
    if origin and destination:
        with st.spinner("Haetaan reittiä..."):
            origin_coords = geocode(origin)
            destination_coords = geocode(destination)

            if not origin_coords or not destination_coords:
                st.error("Lähtö- tai määränpääosoitetta ei löytynyt.")
                st.session_state.route_summary = None
            else:
                st.session_state.origin_coords = origin_coords
                st.session_state.dest_coords = destination_coords

                route_data = route(origin_coords, destination_coords)
                st.session_state.route_data = route_data

                if route_data and route_data.get("error"):
                    st.error(
                        f"❌ API-kutsu epäonnistui! HTTP-statuskoodi: {route_data['status_code']}"
                    )
                    with st.expander("Näytä virheen tiedot"):
                        st.code(route_data["message"])
                    st.session_state.coords = []
                    st.session_state.here_incidents = None
                    st.session_state.route_summary = None

                elif route_data and "routes" in route_data and len(route_data["routes"]) > 0:
                    try:
                        polyline_str = route_data["routes"][0]["sections"][0]["polyline"]
                        decoded_coords = flexpolyline.decode(polyline_str)
                        st.session_state.coords = decoded_coords

                        st.session_state.here_incidents = parse_traffic_incidents(route_data)

                        # Tallennetaan matka & aika (km, h) tilaan
                        summary = extract_route_summary(route_data)
                        st.session_state.route_summary = summary

                        st.success("Reitti haettu onnistuneesti!")
                    except Exception as e:
                        st.error(f"⚠️ Datan käsittelyvirhe: {e}")
                        st.session_state.route_summary = None
                else:
                    st.error("Reittidataa ei saatu. Tarkista API-avain.")
                    st.session_state.route_summary = None
    else:
        st.warning("Anna lähtö ja määränpää.")
        st.session_state.route_summary = None


# --------------------------------------------------------------------
# Matka & aika (näytetään napista riippumatta, jos tilassa on arvo)
# --------------------------------------------------------------------
if st.session_state.route_summary:
    distance_km, duration_hours = st.session_state.route_summary
    colA, colB = st.columns(2)
    with colA:
        st.metric("Matka", f"{distance_km:.1f} km")
    with colB:
        st.metric("Arvioitu matka-aika", f"{duration_hours:.1f} h")

st.divider()

# --------------------------------------------------------------------
# Näytä HERE raaka data
# --------------------------------------------------------------------
if st.session_state.route_data is not None:
    with st.expander("Näytä raaka HERE Routing API-vastaus"):
        st.json(st.session_state.route_data)
    st.divider()


# --------------------------------------------------------------------
# HERE Liikennetiedotteiden lista
# --------------------------------------------------------------------
if st.session_state.here_incidents is not None:
    st.subheader("⚠️ HERE Liikennetiedotteet (reitin varrelta)")

    incidents = st.session_state.here_incidents
    if incidents:
        for inc in incidents:
            level = str(inc.get("taso", "")).lower()
            icon = "🚨" if level in ["critical", "major"] else "🚧"

            location_text = inc.get("paikka")
            if (
                location_text == "Tuntematon sijainti"
                and inc.get("lat") is not None
                and inc.get("lon") is not None
            ):
                location_text = f"Koordinaatit: {inc['lat']:.4f}, {inc['lon']:.4f}"

            with st.expander(f"{icon} {inc.get('kuvaus')}"):
                st.write(f"**Tyyppi:** {inc.get('tyyppi')}")
                st.write(f"**Taso:** {inc.get('taso')}")
                st.write(f"**Sijainti:** {location_text}")
                if inc.get("start_index") is not None:
                    st.caption(
                        f"Reittiosuus (indeksit): {inc['start_index']} - {inc['end_index']}"
                    )
    else:
        st.info("Ei liikennetiedotteita.")


# --------------------------------------------------------------------
# KARTTA
# --------------------------------------------------------------------
if st.session_state.coords:
    st.divider()
    st.subheader("Reitti kartalla")

    try:
        mid = len(st.session_state.coords) // 2
        m = folium.Map(location=st.session_state.coords[mid], zoom_start=7)

        # Lähtö- ja määränpäämarkkerit takaisin kartalle ✅
        if st.session_state.origin_coords:
            folium.Marker(
                st.session_state.origin_coords,
                popup="Lähtö",
                icon=folium.Icon(color="green"),
            ).add_to(m)

        if st.session_state.dest_coords:
            folium.Marker(
                st.session_state.dest_coords,
                popup="Määränpää",
                icon=folium.Icon(color="red"),
            ).add_to(m)

        # Koko reitti
        folium.PolyLine(
            st.session_state.coords,
            color="gray",
            weight=5,
            opacity=0.6
        ).add_to(m)

        # HERE-incidents korostuksina ja markkereina
        if st.session_state.here_incidents:
            for inc in st.session_state.here_incidents:
                level = str(inc.get("taso", "")).lower()
                color = "red" if level in ["critical", "major"] else "orange"
                popup_text = f"<b>{inc.get('tyyppi')}</b><br>{inc.get('kuvaus')}"

                s_index = inc.get("start_index")
                e_index = inc.get("end_index")

                # Reittiosuuden korostus
                if (
                    s_index is not None
                    and e_index is not None
                    and s_index != e_index
                ):
                    try:
                        highlight_coords = slice_polyline(
                            st.session_state.coords, int(s_index), int(e_index)
                        )
                        if highlight_coords:
                            folium.PolyLine(
                                locations=highlight_coords,
                                color=color,
                                weight=8,
                                opacity=0.9,
                                popup=popup_text,
                            ).add_to(m)
                    except Exception as slice_err:
                        print(f"Slice error: {slice_err}")

                # Markkeri
                marker_lat = inc.get("lat")
                marker_lon = inc.get("lon")

                if (
                    marker_lat is None
                    and marker_lon is None
                    and s_index is not None
                    and e_index is not None
                    and s_index == e_index
                ):
                    try:
                        if 0 <= s_index < len(st.session_state.coords):
                            marker_lat, marker_lon = st.session_state.coords[s_index]
                    except IndexError:
                        marker_lat, marker_lon = None, None

                if marker_lat is not None and marker_lon is not None:
                    folium.Marker(
                        [marker_lat, marker_lon],
                        popup=popup_text,
                        icon=folium.Icon(
                            icon="exclamation-triangle",
                            color=color,
                            prefix="fa",
                        ),
                    ).add_to(m)

        st_folium(m, width=900, height=500)
    except Exception as e:
        st.error("❌ Virhe kartan piirtämisessä.")
        st.exception(e)


# --------------------------------------------------------------------
# DIGITRAFFIC HAKU
# --------------------------------------------------------------------
st.divider()
st.subheader("Lisätiedot (Digitraffic API)")

if st.button("Hae DigiTraffic-tiedot (Reaaliaikainen)"):
    if st.session_state.coords:
        with st.spinner("Haetaan Digitraffic-dataa..."):
            bbox = calculate_bbox(st.session_state.coords)
            if bbox:
                st.caption(f"BBox (debug): {bbox}")

            messages = traffic_messages_near_route(st.session_state.coords)
            tms_info = tms_near_route(st.session_state.coords)

            st.session_state.digitraffic_messages = messages

            col_a, col_b = st.columns(2)

            with col_a:
                st.info(f"Liikennetiedotteita: {len(messages)} kpl")
                for msg in messages:
                    with st.expander(f"⚠️ {msg.get('otsikko')}"):
                        st.write(f"**Sijainti:** {msg.get('sijainti')}")
                        st.write(f"**Kuvaus:** {msg.get('kuvaus')}")
                        st.caption(f"Aika: {msg.get('aika')}")

            with col_b:
                st.info("Digitraffic sääasemat")
                st.write(tms_info if tms_info else "Ei dataa.")
    else:
        st.warning("Hae ensin reitti.")

# ====================================================================
# END OF FILE
# ====================================================================
