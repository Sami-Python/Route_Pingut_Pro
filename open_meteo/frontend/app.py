"""Streamlit frontend for Open-Meteo weather visualization with dual maps."""

import streamlit as st
import requests
import pydeck as pdk
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://backend:8081"

# Temperature regions - 12x12 grid gives ~12-15km spacing for each
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

FINLAND_BBOX = {
    "min_lon": 22.0,   # Western coast
    "min_lat": 59.5,   # Southern tip
    "max_lon": 28.0,   # Eastern border
    "max_lat": 62.5    # Central Finland (covers most traffic)
}

# Full Finland bbox for precipitation (works well with HeatmapLayer)
PRECIPITATION_BBOX = {
    "min_lon": 20.5,
    "min_lat": 59.5,
    "max_lon": 31.5,
    "max_lat": 70.1
}

# Temperature color scale
TEMP_COLORS = {
    -30: [139, 0, 139], -20: [0, 0, 255], -10: [0, 191, 255],
    0: [173, 216, 230], 5: [255, 255, 255], 10: [255, 255, 200],
    15: [255, 255, 0], 20: [255, 200, 0], 25: [255, 165, 0],
    30: [255, 100, 0], 35: [255, 0, 0]
}


def get_color_for_temperature(temp: float) -> List[int]:
    """Get RGB color for temperature.
    
    Parameters
    ----------
    temp : float
        Temperature in Celsius.
    
    Returns
    -------
    List[int]
        RGB color values [R, G, B].
    """
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


def fetch_temperature_data(start_time: datetime, hours: int = 6, bbox: Dict = None) -> Optional[Dict]:
    """Fetch temperature data from backend for selected region.
    
    12x12 grid (~12km spacing) is optimal for regional views.
    Shows temperature for highway driving within the region.
    
    Parameters
    ----------
    start_time : datetime
        Start time for forecast.
    hours : int
        Number of forecast hours.
    bbox : Dict
        Bounding box for the region. If None, uses default Southern Finland.
    
    Returns
    -------
    Optional[Dict]
        Temperature forecast data or None if failed.
    """
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
        response = requests.get(f"{BACKEND_URL}/api/forecast/temperature", params=params, timeout=120)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch temperature: {e}")
        return None


def fetch_precipitation_data(start_time: datetime, hours: int = 6) -> Optional[Dict]:
    """Fetch precipitation data from backend for whole Finland.
    
    Uses full Finland bbox because precipitation HeatmapLayer
    works well with sparse 15x15 grid over large area.
    
    Parameters
    ----------
    start_time : datetime
        Start time for forecast.
    hours : int
        Number of forecast hours.
    
    Returns
    -------
    Optional[Dict]
        Precipitation forecast data or None if failed.
    """
    try:
        params = {
            "min_lon": PRECIPITATION_BBOX["min_lon"],
            "min_lat": PRECIPITATION_BBOX["min_lat"],
            "max_lon": PRECIPITATION_BBOX["max_lon"],
            "max_lat": PRECIPITATION_BBOX["max_lat"],
            "start_time": start_time.isoformat(),
            "hours": hours
        }
        response = requests.get(f"{BACKEND_URL}/api/forecast/weather", params=params, timeout=120)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch precipitation: {e}")
        return None


def create_temperature_layer(data: List[Dict], selected_time: str) -> Optional[pdk.Layer]:
    """Create temperature scatterplot layer with dense coverage.
    
    15x15 grid over Southern Finland = ~10km spacing between points.
    Dense enough for good visualization with ScatterplotLayer.
    
    Parameters
    ----------
    data : List[Dict]
        Temperature data points.
    selected_time : str
        Selected timestamp to filter data.
    
    Returns
    -------
    Optional[pdk.Layer]
        PyDeck ScatterplotLayer or None if no data.
    """
    if not data:
        return None
    
    filtered = [d for d in data if d.get('time', '').startswith(selected_time[:13])]
    if not filtered:
        return None
    
    df = pd.DataFrame(filtered)
    df['color'] = df['temperature'].apply(lambda t: get_color_for_temperature(t) + [220])
    df['latitude'] = df['lat']
    df['longitude'] = df['lon']
    
    # Format time for tooltip
    df['formatted_time'] = df['time'].apply(
        lambda t: datetime.fromisoformat(t.replace('Z', '')).strftime('%Y-%m-%d %H:%M')
    )
    
    return pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=14000,  # 14km radius for 12x12 grid (~12km spacing)
        pickable=True,
        opacity=0.85,
        filled=True,
    )


def create_precipitation_layer(data: List[Dict], selected_time: str) -> Optional[pdk.Layer]:
    """Create precipitation heatmap layer with automatic interpolation.
    
    HeatmapLayer shows smooth precipitation gradients even with sparse 15x15 grid.
    
    Parameters
    ----------
    data : List[Dict]
        Precipitation data points.
    selected_time : str
        Selected timestamp to filter data.
    
    Returns
    -------
    Optional[pdk.Layer]
        PyDeck HeatmapLayer or None if no precipitation.
    """
    if not data:
        return None
    
    precip_data = []
    for d in data:
        if d.get('time', '').startswith(selected_time[:13]):
            precip = d.get('precipitation', 0)
            if precip and precip > 0.01:  # Show all precipitation
                temp = d.get('temperature', 0)
                
                # Format time for tooltip
                time_str = d.get('time', '')
                formatted_time = datetime.fromisoformat(time_str.replace('Z', '')).strftime('%Y-%m-%d %H:%M')
                
                precip_data.append({
                    'lat': d['lat'],
                    'lon': d['lon'],
                    'latitude': d['lat'],
                    'longitude': d['lon'],
                    'temperature': temp,
                    'precipitation': precip,
                    'weight': min(precip / 5.0, 1.0),  # Normalize to 0-1 (5mm = max)
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
        radiusPixels=100,  # Large radius for smooth precipitation areas
        intensity=3,
        threshold=0.02,
        opacity=0.6,
        colorRange=[
            [200, 220, 255],  # Light blue (light rain)
            [100, 150, 255],  # Medium blue
            [50, 100, 255],   # Darker blue
            [0, 50, 200],     # Dark blue
            [0, 0, 150],      # Very dark blue (heavy rain)
        ],
    )


def get_unique_times(data: List[Dict]) -> List[str]:
    """Extract unique timestamps from data.
    
    Parameters
    ----------
    data : List[Dict]
        Data points with time field.
    
    Returns
    -------
    List[str]
        Sorted list of unique timestamps.
    """
    if not data:
        return []
    return sorted(set(d.get('time', '') for d in data if d.get('time')))


def main():
    st.set_page_config(page_title="Open-Meteo Saa", layout="wide")
    
    st.title("Open-Meteo Saaennuste - Suomi")
    
    # Sidebar
    with st.sidebar:
        st.header("Asetukset")
        
        # Region selection for temperature
        st.subheader("🗺️ Lämpötila-alue")
        selected_region = st.selectbox(
            "Valitse alue:",
            list(TEMPERATURE_REGIONS.keys()),
            index=0,
            help="Valitse alue josta haluat nähdä lämpötilaennusteen"
        )
        region_info = TEMPERATURE_REGIONS[selected_region]
        st.caption(f"📍 {region_info['description']}")
        
        st.markdown("---")
        
        selected_date = st.date_input(
            "Paivamaara",
            value=datetime.now().date(),
            min_value=datetime.now().date(),
            max_value=(datetime.now() + timedelta(days=2)).date()
        )
        
        selected_hour = st.slider("Tunti", 0, 23, datetime.now().hour, 1)
        
        selected_datetime = datetime.combine(selected_date, datetime.min.time()).replace(hour=selected_hour)
        st.write(f"Valittu: {selected_datetime.strftime('%Y-%m-%d %H:00')}")
        
        st.markdown("---")
        fetch_button = st.button("Hae saadata", type="primary", use_container_width=True)
    
    # Fetch data
    if fetch_button or 'temp_data' not in st.session_state or st.session_state.get('selected_region') != selected_region:
        # Get bbox for selected region
        temp_bbox = region_info['bbox']
        
        with st.spinner(f"Haetaan lampotiladataa alueelta {selected_region}..."):
            temp_data = fetch_temperature_data(selected_datetime, hours=6, bbox=temp_bbox)
            if temp_data:
                st.session_state['temp_data'] = temp_data
                st.session_state['selected_region'] = selected_region
                st.session_state['region_info'] = region_info
                data_points = len(temp_data.get('data', []))
                st.success(f"Lampotila: {data_points} pistetta ({selected_region})")
                logger.info(f"Temperature data points: {data_points}")
        
        with st.spinner("Haetaan sadedataa..."):
            precip_data = fetch_precipitation_data(selected_datetime, hours=6)
            if precip_data:
                st.session_state['precip_data'] = precip_data
                data_points = len(precip_data.get('data', []))
                st.success(f"Sade: {data_points} pistetta")
                logger.info(f"Precipitation data points: {data_points}")
    
    # Get times
    available_times = []
    if 'temp_data' in st.session_state:
        available_times = get_unique_times(st.session_state['temp_data'].get('data', []))
    
    # DEBUG: Show what we got
    with st.expander("🔍 Debug: Data info"):
        if 'temp_data' in st.session_state:
            st.write(f"**Lampotilapisteet:** {len(st.session_state['temp_data'].get('data', []))}")
        if 'precip_data' in st.session_state:
            st.write(f"**Sadepisteet:** {len(st.session_state['precip_data'].get('data', []))}")
        st.write(f"**Aikapisteet:** {len(available_times)}")
        if available_times:
            st.write(f"**Ajat:** {', '.join([t[:16] for t in available_times])}")
        else:
            st.warning("⚠️ EI AIKAPISTEITÄ - API ei palauttanut dataa!")
    
    if not available_times:
        st.error("⚠️ Ei ennustedataa saatavilla. Open-Meteo API ei palauttanut dataa valitulle ajalle.")
        st.info("Yrita valita nykyhetki tai lahitulevaisuus.")
        return
    
    # Temperature legend
    st.markdown("### Lampotila-asteikko (C)")
    temp_cols = st.columns(len(TEMP_COLORS))
    for i, (temp, color) in enumerate(TEMP_COLORS.items()):
        with temp_cols[i]:
            st.markdown(
                f"<div style='background-color: rgb({color[0]}, {color[1]}, {color[2]}); "
                f"height: 25px; text-align: center; color: {'white' if temp < 5 else 'black'}; "
                f"line-height: 25px; font-size: 11px;'>{temp}C</div>",
                unsafe_allow_html=True
            )
    
    st.markdown("---")
    
    # Time selection with animation
    st.subheader("Aikajana")
    
    # Initialize session state
    if 'time_index' not in st.session_state:
        st.session_state['time_index'] = 0
    if 'is_playing' not in st.session_state:
        st.session_state['is_playing'] = False
    
    col1, col2, col3 = st.columns([1, 8, 1])
    
    with col1:
        if st.button("▶ Toista", use_container_width=True, key="play_button"):
            st.session_state['is_playing'] = True
    
    with col2:
        # Slider controls time index
        time_index = st.slider(
            "Valitse aika",
            0,
            len(available_times) - 1,
            st.session_state['time_index'],
            key='time_slider_display',
            label_visibility="collapsed"
        )
        # Update session state when slider moves
        if time_index != st.session_state['time_index']:
            st.session_state['time_index'] = time_index
            st.session_state['is_playing'] = False  # Stop playing when user moves slider
    
    with col3:
        if st.button("⏸ Pysayta", use_container_width=True, key="pause_button"):
            st.session_state['is_playing'] = False
    
    # Animation logic - runs AFTER buttons
    if st.session_state.get('is_playing', False):
        # Advance to next frame
        if st.session_state['time_index'] < len(available_times) - 1:
            st.session_state['time_index'] += 1
            import time
            time.sleep(0.8)  # Delay between frames
            st.rerun()
        else:
            # Reached end, stop and loop
            st.session_state['is_playing'] = False
            st.session_state['time_index'] = 0
            st.rerun()
    
    selected_time = available_times[st.session_state['time_index']]
    display_time = datetime.fromisoformat(selected_time.replace('Z', ''))
    st.write(f"**Aika: {display_time.strftime('%Y-%m-%d %H:%M')}**")
    
    # Two maps side by side
    col1, col2 = st.columns(2)
    
    # Dynamic view based on selected region
    if 'region_info' in st.session_state:
        region = st.session_state['region_info']
        view_state = pdk.ViewState(
            latitude=region['center']['lat'],
            longitude=region['center']['lon'],
            zoom=region['zoom'],
            pitch=0
        )
    else:
        # Default: Southern Finland
        view_state = pdk.ViewState(latitude=61.0, longitude=25.0, zoom=6.5, pitch=0)
    
    with col1:
        st.subheader("Lampotila")
        if 'selected_region' in st.session_state:
            st.info(f"📍 Alue: {st.session_state['selected_region']}")
        
        if 'temp_data' in st.session_state:
            temp_layer = create_temperature_layer(
                st.session_state['temp_data'].get('data', []),
                selected_time
            )
            
            deck = pdk.Deck(
                layers=[temp_layer] if temp_layer else [],
                initial_view_state=view_state,
                map_style="mapbox://styles/mapbox/dark-v10",
                tooltip={
                    "html": "<b>Aika:</b> {formatted_time}<br/><b>Lampotila:</b> {temperature}°C<br/><b>Sijainti:</b> ({latitude:.2f}, {longitude:.2f})",
                    "style": {"backgroundColor": "rgba(0,0,0,0.8)", "color": "white"}
                }
            )
            st.pydeck_chart(deck, use_container_width=True)
            
            # Temperature statistics
            temp_points = [d for d in st.session_state['temp_data'].get('data', []) 
                          if d.get('time', '').startswith(selected_time[:13])]
            if temp_points:
                temps = [d['temperature'] for d in temp_points if d.get('temperature') is not None]
                if temps:
                    st.metric("Keskiarvo", f"{sum(temps)/len(temps):.1f}°C")
                    col_min, col_max = st.columns(2)
                    with col_min:
                        st.metric("Min", f"{min(temps):.1f}°C")
                    with col_max:
                        st.metric("Max", f"{max(temps):.1f}°C")
    
    with col2:
        st.subheader("Sade")
        if 'precip_data' in st.session_state:
            precip_layer = create_precipitation_layer(
                st.session_state['precip_data'].get('data', []),
                selected_time
            )
            
            deck = pdk.Deck(
                layers=[precip_layer] if precip_layer else [],
                initial_view_state=view_state,
                map_style="mapbox://styles/mapbox/dark-v10",
                tooltip={
                    "html": "<b>Aika:</b> {formatted_time}<br/><b>Sade:</b> {precipitation} mm/h<br/><b>Lampotila:</b> {temperature}°C<br/><b>Sijainti:</b> ({latitude:.2f}, {longitude:.2f})",
                    "style": {"backgroundColor": "rgba(0,0,0,0.8)", "color": "white"}
                }
            )
            st.pydeck_chart(deck, use_container_width=True)
            
            # Color legend for precipitation
            st.markdown("**Värit:**")
            st.markdown("""
            <div style='font-size: 0.9em; line-height: 1.8;'>
            🔵 <span style='color: #6496FF;'>Vaalean sininen</span> - Kevyt sade (0.1-1 mm/h)<br/>
            🔵 <span style='color: #3264FF;'>Sininen</span> - Kohtalainen sade (1-3 mm/h)<br/>
            🔵 <span style='color: #0032C8;'>Tumman sininen</span> - Runsas sade (>3 mm/h)<br/>
            </div>
            """, unsafe_allow_html=True)
            st.caption("💡 Sade/räntä/lumi määräytyy lämpötilan mukaan")
            
            # Precipitation statistics
            precip_points = [d for d in st.session_state['precip_data'].get('data', [])
                           if d.get('time', '').startswith(selected_time[:13]) and d.get('precipitation', 0) > 0]
            if precip_points:
                precips = [d['precipitation'] for d in precip_points]
                st.metric("Keskiarvo", f"{sum(precips)/len(precips):.2f} mm/h")
                col_min, col_max = st.columns(2)
                with col_min:
                    st.metric("Min", f"{min(precips):.2f} mm/h")
                with col_max:
                    st.metric("Max", f"{max(precips):.2f} mm/h")
            else:
                st.info("Ei sadetta")
    
    st.markdown("---")
    st.caption("Lahde: Open-Meteo (FMI HARMONIE-malli) | CC BY 4.0")


if __name__ == "__main__":
    main()

