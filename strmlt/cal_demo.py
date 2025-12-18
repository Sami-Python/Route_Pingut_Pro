import streamlit as st
import requests
import json
from streamlit_calendar import calendar
import pydeck as pdk
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_available_calendars(): 
    """
    Get the available calendars.
    """
    cals = []
    if "outlook_events_data" in st.session_state:
        cals.append("Outlook")
    if "ical_events_data" in st.session_state:
        cals.append("iCal")
    return cals

@st.cache_data
def _add_outlook_events():
    events = []
    for event in st.session_state["outlook_events_data"]:
        evt = {
            "title": event.get("title", "No Title"),
            "start": event.get("start"),
            "end": event.get("end"),
            "extendedProps": {
                "location": event.get("location")
            }
        }
        if event.get("location"):
            evt["title"] += f" (@ {event.get('location')})"
        
        events.append(evt)
    return events

@st.cache_data
def _add_ical_events():
    events = []
    for event in st.session_state["ical_events_data"]:
        evt = {
            "title": event.get("title", "No Title"),
            "start": event.get("start"),
            "end": event.get("end"),
            "extendedProps": {
                "location": event.get("location")
            }
        }
        if event.get("location"):
            evt["title"] += f" (@ {event.get('location')})"
        
        events.append(evt)
    return events

def _fetch_route_weather(from_city: str, to_city: str, hours: int = 6):
    """Fetch weather for route from API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/weather/route",
            params={"from": from_city, "to": to_city, "hours": hours},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Sään haku epäonnistui: {e}")
        return None

# Weather maps functions
METEO_BACKEND_URL = "http://meteo-backend:8081"

TEMPERATURE_REGIONS = {
    "Etelä-Suomi": {
        "bbox": {"min_lon": 22.0, "min_lat": 59.5, "max_lon": 28.0, "max_lat": 62.5},
        "center": {"lat": 61.0, "lon": 25.0},
        "zoom": 6.5,
        "description": "Helsinki, Tampere, Turku, Lappeenranta"
    },
    "Länsi-Suomi": {
        "bbox": {"min_lon": 21.5, "min_lat": 61.0, "max_lon": 25.5, "max_lat": 64.0},
        "center": {"lat": 62.5, "lon": 23.5},
        "zoom": 6.5,
        "description": "Vaasa, Seinäjoki, Kokkola"
    },
    "Itä-Suomi": {
        "bbox": {"min_lon": 26.0, "min_lat": 61.5, "max_lon": 31.0, "max_lat": 64.5},
        "center": {"lat": 63.0, "lon": 28.5},
        "zoom": 6.5,
        "description": "Kuopio, Joensuu, Kajaani"
    },
    "Pohjois-Suomi": {
        "bbox": {"min_lon": 23.0, "min_lat": 65.0, "max_lon": 29.0, "max_lat": 68.5},
        "center": {"lat": 66.5, "lon": 26.0},
        "zoom": 6.0,
        "description": "Oulu, Rovaniemi, Kemi"
    },
}

PRECIPITATION_BBOX = {
    "min_lon": 20.5,
    "min_lat": 59.5,
    "max_lon": 31.5,
    "max_lat": 70.1
}

TEMP_COLORS = {
    -30: [139, 0, 139], -20: [0, 0, 255], -10: [0, 191, 255],
    0: [173, 216, 230], 5: [255, 255, 255], 10: [255, 255, 200],
    15: [255, 255, 0], 20: [255, 200, 0], 25: [255, 165, 0],
    30: [255, 100, 0], 35: [255, 0, 0]
}

def get_color_for_temperature(temp: float) -> List[int]:
    """Get RGB color for temperature."""
    temps = sorted(TEMP_COLORS.keys())
    if temp <= temps[0]:
        return TEMP_COLORS[temps[0]]
    if temp >= temps[-1]:
        return TEMP_COLORS[temps[-1]]
    
    for i in range(len(temps) - 1):
        if temps[i] <= temp <= temps[i + 1]:
            lower_temp, upper_temp = temps[i], temps[i + 1]
            lower_color, upper_color = TEMP_COLORS[lower_temp], TEMP_COLORS[upper_temp]
            ratio = (temp - lower_temp) / (upper_temp - lower_temp)
            return [int(lower_color[j] + ratio * (upper_color[j] - lower_color[j])) for j in range(3)]
    return [255, 255, 255]

def fetch_map_temperature_data(start_time: datetime, hours: int = 6, bbox: Dict = None) -> Optional[Dict]:
    """Fetch temperature data for map visualization."""
    if bbox is None:
        bbox = TEMPERATURE_REGIONS["Etelä-Suomi"]["bbox"]
    
    try:
        params = {
            "min_lon": bbox["min_lon"],
            "min_lat": bbox["min_lat"],
            "max_lon": bbox["max_lon"],
            "max_lat": bbox["max_lat"],
            "start_time": start_time.isoformat(),
            "hours": hours
        }
        response = requests.get(f"{METEO_BACKEND_URL}/api/forecast/temperature", params=params, timeout=120)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch temperature for maps: {e}")
        return None

def fetch_map_precipitation_data(start_time: datetime, hours: int = 6) -> Optional[Dict]:
    """Fetch precipitation data for map visualization."""
    try:
        params = {
            "min_lon": PRECIPITATION_BBOX["min_lon"],
            "min_lat": PRECIPITATION_BBOX["min_lat"],
            "max_lon": PRECIPITATION_BBOX["max_lon"],
            "max_lat": PRECIPITATION_BBOX["max_lat"],
            "start_time": start_time.isoformat(),
            "hours": hours
        }
        response = requests.get(f"{METEO_BACKEND_URL}/api/forecast/weather", params=params, timeout=120)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch precipitation for maps: {e}")
        return None

def create_temperature_layer(data: List[Dict], selected_time: str) -> Optional[pdk.Layer]:
    """Create temperature scatterplot layer."""
    if not data:
        return None
    
    filtered = [d for d in data if d.get('time', '').startswith(selected_time[:13])]
    if not filtered:
        return None
    
    df = pd.DataFrame(filtered)
    df['color'] = df['temperature'].apply(lambda t: get_color_for_temperature(t) + [220])
    df['latitude'] = df['lat']
    df['longitude'] = df['lon']
    df['formatted_time'] = df['time'].apply(
        lambda t: datetime.fromisoformat(t.replace('Z', '')).strftime('%Y-%m-%d %H:%M')
    )
    
    return pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=14000,
        pickable=True,
        opacity=0.85,
        filled=True,
    )

def create_precipitation_layer(data: List[Dict], selected_time: str) -> Optional[pdk.Layer]:
    """Create precipitation heatmap layer."""
    if not data:
        return None
    
    precip_data = []
    for d in data:
        if d.get('time', '').startswith(selected_time[:13]):
            precip = d.get('precipitation', 0)
            if precip and precip > 0.01:
                temp = d.get('temperature', 0)
                time_str = d.get('time', '')
                formatted_time = datetime.fromisoformat(time_str.replace('Z', '')).strftime('%Y-%m-%d %H:%M')
                
                precip_data.append({
                    'lat': d['lat'],
                    'lon': d['lon'],
                    'latitude': d['lat'],
                    'longitude': d['lon'],
                    'temperature': temp,
                    'precipitation': precip,
                    'weight': min(precip / 5.0, 1.0),
                    'formatted_time': formatted_time
                })
    
    if not precip_data:
        return None
    
    df = pd.DataFrame(precip_data)
    
    return pdk.Layer(
        "HeatmapLayer",
        data=df,
        get_position='[lon, lat]',
        get_weight='weight',
        radiusPixels=100,
        intensity=3,
        threshold=0.02,
        opacity=0.6,
        colorRange=[
            [200, 220, 255],
            [100, 150, 255],
            [50, 100, 255],
            [0, 50, 200],
            [0, 0, 150],
        ],
    )

def get_unique_times(data: List[Dict]) -> List[str]:
    """Extract unique timestamps."""
    if not data:
        return []
    return sorted(set(d.get('time', '') for d in data if d.get('time')))

# Constants
API_BASE_URL = "http://api:8000"

st.set_page_config(layout="wide")
st.title("API Gateway Demo")

st.write("This app demonstrates interacting with the unified API gateway.")

# --- iCal API Demo ---
with st.expander("iCal API Demo", expanded=False):
    st.subheader("Public Calendar (iCal)")
    url = st.text_input("iCal URL", value="https://lukkarit.kamk.fi/ical.php?hash=E74AC94AE7A19AC99110C39EE535C0DBB0DF8AAE")

    if st.button("Get Events", key="get_ical_events"):
        try:
            response = requests.get(f"{API_BASE_URL}/ical/events", params={"url": url})
            if response.status_code == 200:
                events_data = response.json()
                st.success(f"Found {len(events_data)} events")
                st.json(events_data)
                st.session_state["ical_events_data"] = events_data
            else:
                st.error(f"Error: {response.status_code}")
                st.write(response.text)
        except Exception as e:
            st.error(f"Connection error: {e}")

# --- Graph API Demo ---
with st.expander("Graph API Demo", expanded=False):
    st.subheader("Microsoft Graph Calendar")
    
    if "access_token" in st.query_params:
        st.session_state["access_token"] = st.query_params["access_token"]
        st.query_params.clear()
        st.rerun()

    st.info("To use this, you first need to authenticate and get a token.")
    
    login_url = "http://localhost:8000/graph/login"
    st.markdown(f"👉 **[Click here to Login]({login_url})**", unsafe_allow_html=True)
    st.caption("After logging in, the token will be automatically populated below.")
    
    default_token = st.session_state.get("access_token", "")
    token = st.text_input("Access Token", value=default_token, type="password", key="graph_token_input")
    
    if st.button("Get My Calendar Events", key="get_graph_events"):
        if not token:
            st.warning("Please enter a token first.")
        else:
            try:
                response = requests.get(f"{API_BASE_URL}/graph/events", params={"token": token})
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("Successfully fetched events!")
                    st.session_state["outlook_events_data"] = data
                    with st.expander("Raw Data"):
                        st.json(data)
                else:
                    st.error(f"Error: {response.status_code}")
                    st.json(response.json())
            except Exception as e:
                st.error(f"Connection error: {e}")
                
    if st.button("Get My Calendars", key="get_graph_calendars"):
        if not token:
            st.warning("Please enter a token first.")
        else:
            try:
                response = requests.get(f"{API_BASE_URL}/graph/calendars", params={"token": token})
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("Successfully fetched calendars!")
                    with st.expander("Raw Data"):
                        st.json(data)
                else:
                    st.error(f"Error: {response.status_code}")
                    st.json(response.json())
            except Exception as e:
                st.error(f"Connection error: {e}")

with st.expander("Google Calendar demo", expanded=False):
    st.subheader("Google Calendar")
    
    # Check for token in query params
    if "gcal_access_token" in st.query_params:
        token = st.query_params["gcal_access_token"]
        st.session_state["gcal_access_token"] = token
        # Clear the token from URL to clean it up
        st.query_params.clear()
        st.rerun()

    login_url = "http://localhost:8000/gcal/login?redirect_url=http://localhost:8501/cal_demo"
    st.markdown(f"👉 **[Click here to Login]({login_url})**", unsafe_allow_html=True)
    st.caption("After logging in, the token will be automatically populated below.")
    
    # Use session state token if available, otherwise default blank
    default_token = st.session_state.get("gcal_access_token", st.session_state.get("access_token", ""))
    token = st.text_input("Access Token", value=default_token, type="password", key="gcal_token_input")
    
    if st.button("Get My Calendar Events", key="get_gcal_events"):
        if not token:
            st.warning("Please enter a token first.")
        else:
            try:
                response = requests.get(f"{API_BASE_URL}/gcal/events", params={"token": token})
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("Successfully fetched events!")
                    st.session_state["outlook_events_data"] = data
                    with st.expander("Raw Data"):
                        st.json(data)
                else:
                    st.error(f"Error: {response.status_code}")
                    st.json(response.json())
            except Exception as e:
                st.error(f"Connection error: {e}")
    if st.button("Get Google Calendars", key="get_gcal_calendars"):
        if not token:
            st.warning("Please enter a token first.")
        else:
            try:
                response = requests.get(f"{API_BASE_URL}/gcal/calendars", params={"token": token})
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("Successfully fetched calendars!")
                    st.session_state["outlook_calendars_data"] = data
                    with st.expander("Raw Data"):
                        st.json(data)
                else:
                    st.error(f"Error: {response.status_code}")
                    st.json(response.json())
            except Exception as e:
                st.error(f"Connection error: {e}")

# --- Weather API Demo ---
with st.expander("Sää-API Demo", expanded=True):
    st.subheader("Sää reitillä")
    st.caption("Testaa sää-API:a valitsemalla lähtö- ja määränpääkaupunki")
    
    col1, col2 = st.columns(2)
    with col1:
        from_city = st.selectbox(
            "Lähtökaupunki", 
            ["Helsinki", "Tampere", "Turku", "Oulu", "Rovaniemi", "Jyväskylä", "Kuopio"],
            key="weather_from"
        )
    with col2:
        to_city = st.selectbox(
            "Määränpää", 
            ["Tampere", "Helsinki", "Turku", "Oulu", "Rovaniemi", "Jyväskylä", "Kuopio"],
            key="weather_to"
        )
    
    if st.button("Hae sää reitille", type="primary"):
        weather_data = _fetch_route_weather(from_city, to_city)
        if weather_data:
            st.session_state["weather_data"] = weather_data
    
    # Display weather if available
    if "weather_data" in st.session_state:
        data = st.session_state["weather_data"]
        
        st.markdown("---")
        st.markdown("### 📍 Sää reittisi varrella")
        
        # Current weather boxes
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Lähtö: {data['departure']['city']}**")
            current = data['departure']['current']
            
            # Temperature with emoji
            temp = current['temperature']
            temp_emoji = "☀️" if temp > 10 else "⛅" if temp > 0 else "❄️"
            
            st.metric(
                "Lämpötila",
                f"{temp_emoji} {temp:+d}°C"
            )
            st.write(f"**Sää:** {current['weather']}")
            if current['precipitation'] > 0:
                st.write(f"💧 Sadetta: {current['precipitation']} mm/h")
        
        with col2:
            st.markdown(f"**Määränpää: {data['arrival']['city']}**")
            current = data['arrival']['current']
            
            temp = current['temperature']
            temp_emoji = "☀️" if temp > 10 else "⛅" if temp > 0 else "❄️"
            
            st.metric(
                "Lämpötila",
                f"{temp_emoji} {temp:+d}°C"
            )
            st.write(f"**Sää:** {current['weather']}")
            if current['precipitation'] > 0:
                st.write(f"💧 Sadetta: {current['precipitation']} mm/h")
        
        st.markdown("---")
        
        # 6h forecast timeline
        st.markdown("### 📅 6 tunnin ennuste")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**📍 {data['departure']['city']}**")
            for i, forecast in enumerate(data['departure']['forecast']):
                time_label = "Nyt" if i == 0 else f"{i}h"
                
                # Weather icon
                if "sade" in forecast['weather']:
                    icon = "🌧️"
                elif "lumi" in forecast['weather']:
                    icon = "❄️"
                elif "aurinko" in forecast['weather']:
                    icon = "☀️"
                else:
                    icon = "⛅"
                
                st.markdown(f"{time_label} | {icon} **{forecast['temperature']:+d}°C** - {forecast['weather']}")
        
        with col2:
            st.markdown(f"**🏁 {data['arrival']['city']}**")
            for i, forecast in enumerate(data['arrival']['forecast']):
                time_label = "Nyt" if i == 0 else f"{i}h"
                
                if "sade" in forecast['weather']:
                    icon = "🌧️"
                elif "lumi" in forecast['weather']:
                    icon = "❄️"
                elif "aurinko" in forecast['weather']:
                    icon = "☀️"
                else:
                    icon = "⛅"
                
                st.markdown(f"{time_label} | {icon} **{forecast['temperature']:+d}°C** - {forecast['weather']}")

st.markdown("---")

# --- Weather Maps ---
with st.expander("🗺️ Sääkartat (Lämpötila + Sade)", expanded=False):
    st.markdown("### Visuaaliset sääkartat koko Suomelle")
    st.caption("Interaktiiviset kartat lämpötilasta ja sateesta. Valitse alue ja aika.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        map_region = st.selectbox(
            "Valitse alue:",
            list(TEMPERATURE_REGIONS.keys()),
            index=0,
            key="map_region"
        )
        region_info = TEMPERATURE_REGIONS[map_region]
        st.caption(f"📍 {region_info['description']}")
    
    with col2:
        map_hour = st.slider("Tunti", 0, 23, datetime.now().hour, 1, key="map_hour")
    
    map_datetime = datetime.combine(datetime.now().date(), datetime.min.time()).replace(hour=map_hour)
    
    if st.button("Hae sääkartat", type="primary", key="fetch_maps"):
        temp_bbox = region_info['bbox']
        
        with st.spinner("Haetaan karttadataa..."):
            map_temp_data = fetch_map_temperature_data(map_datetime, hours=6, bbox=temp_bbox)
            map_precip_data = fetch_map_precipitation_data(map_datetime, hours=6)
            
            if map_temp_data:
                st.session_state['map_temp_data'] = map_temp_data
                st.session_state['map_region_info'] = region_info
            if map_precip_data:
                st.session_state['map_precip_data'] = map_precip_data
    
    # Display maps if data available
    if 'map_temp_data' in st.session_state and 'map_precip_data' in st.session_state:
        available_times = get_unique_times(st.session_state['map_temp_data'].get('data', []))
        
        if available_times:
            # Time slider
            if 'map_time_index' not in st.session_state:
                st.session_state['map_time_index'] = 0
            
            st.markdown("#### Valitse aika")
            time_index = st.slider(
                "Aikajana",
                0,
                len(available_times) - 1,
                st.session_state['map_time_index'],
                key='map_time_slider',
                label_visibility="collapsed"
            )
            st.session_state['map_time_index'] = time_index
            
            selected_time = available_times[time_index]
            display_time = datetime.fromisoformat(selected_time.replace('Z', ''))
            st.write(f"**Aika: {display_time.strftime('%Y-%m-%d %H:%M')}**")
            
            # Temperature legend
            st.markdown("**Lämpötila-asteikko:**")
            temp_cols = st.columns(len(TEMP_COLORS))
            for i, (temp, color) in enumerate(TEMP_COLORS.items()):
                with temp_cols[i]:
                    st.markdown(
                        f"<div style='background-color: rgb({color[0]}, {color[1]}, {color[2]}); "
                        f"height: 20px; text-align: center; color: {'white' if temp < 5 else 'black'}; "
                        f"line-height: 20px; font-size: 10px;'>{temp}°C</div>",
                        unsafe_allow_html=True
                    )
            
            st.markdown("---")
            
            # View state
            if 'map_region_info' in st.session_state:
                region = st.session_state['map_region_info']
                view_state = pdk.ViewState(
                    latitude=region['center']['lat'],
                    longitude=region['center']['lon'],
                    zoom=region['zoom'],
                    pitch=0
                )
            else:
                view_state = pdk.ViewState(latitude=61.0, longitude=25.0, zoom=6.5, pitch=0)
            
            # Maps
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Lämpötila**")
                temp_layer = create_temperature_layer(
                    st.session_state['map_temp_data'].get('data', []),
                    selected_time
                )
                
                deck = pdk.Deck(
                    layers=[temp_layer] if temp_layer else [],
                    initial_view_state=view_state,
                    map_style="",  # Empty = OpenStreetMap (free, no token needed)
                    tooltip={
                        "html": "<b>Aika:</b> {formatted_time}<br/><b>Lämpötila:</b> {temperature}°C<br/><b>Sijainti:</b> ({latitude:.2f}, {longitude:.2f})",
                        "style": {"backgroundColor": "rgba(0,0,0,0.8)", "color": "white"}
                    }
                )
                st.pydeck_chart(deck, use_container_width=True, height=400)
            
            with col2:
                st.markdown("**Sade**")
                precip_layer = create_precipitation_layer(
                    st.session_state['map_precip_data'].get('data', []),
                    selected_time
                )
                
                deck = pdk.Deck(
                    layers=[precip_layer] if precip_layer else [],
                    initial_view_state=view_state,
                    map_style="",  # Empty = OpenStreetMap (free, no token needed)
                    tooltip={
                        "html": "<b>Aika:</b> {formatted_time}<br/><b>Sade:</b> {precipitation} mm/h<br/><b>Lämpötila:</b> {temperature}°C",
                        "style": {"backgroundColor": "rgba(0,0,0,0.8)", "color": "white"}
                    }
                )
                st.pydeck_chart(deck, use_container_width=True, height=400)
                
                st.markdown("""
                <div style='font-size: 0.85em; line-height: 1.6;'>
                🔵 Vaalean sininen - Kevyt sade<br/>
                🔵 Sininen - Kohtalainen sade<br/>
                🔵 Tumman sininen - Runsas sade
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Ei karttadataa saatavilla")

st.markdown("---")

# Calendar Visualization
available_calendars = _get_available_calendars()
if not available_calendars:
    st.warning("No calendars available.")
else:
    selected_calendars = st.pills("Calendar", available_calendars, selection_mode="multi")
    events = []
    if "iCal" in selected_calendars:
        events.extend(_add_ical_events())
    if "Outlook" in selected_calendars:
        events.extend(_add_outlook_events())
    
    st.markdown("### Calendar View")
    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay",
        },
        "initialView": "timeGridWeek",
        "slotMinTime": "06:00:00",
        "slotMaxTime": "22:00:00",
    }
    calendar_state = calendar(events=events, options=calendar_options)
    if calendar_state.get("eventClick"):
        event_click = calendar_state["eventClick"]["event"]
        title = event_click.get("title", "No Title")
        start = event_click.get("start", "")
        end = event_click.get("end", "")
        location = event_click.get("extendedProps", {}).get("location", "Unknown Location")
        
        if " (@" in title:
            title = title.split(" (@")[0]   
        
        @st.dialog(f"Event Details: {title}")
        def show_event_details():
            st.write(f"**Start:** {start}")
            st.write(f"**End:** {end}")
            st.write(f"**Location:** {location}")
        
        show_event_details()
        