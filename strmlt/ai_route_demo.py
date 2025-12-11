import streamlit as st
import requests
import pydeck as pdk
import flexpolyline
import pandas as pd
from typing import Optional, Tuple, List, Dict, Any
import dotenv
import os
dotenv.load_dotenv()

# ====================================================================
# CONFIG
# ====================================================================
API_BASE_URL = "http://api:8000/maps"

st.set_page_config(layout="wide", page_title="AI Route Planner")

# ====================================================================
# API CLIENT FUNCTIONS
# ====================================================================

def get_geocode(address: str) -> Optional[Tuple[float, float]]:
    """Fetch coordinates for an address."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/geocode",
            params={"address": address}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["latitude"], data["longitude"]
    except Exception as e:
        st.error(f"Geotagging error: {e}")
    return None

def get_route(origin: Tuple[float, float], dest: Tuple[float, float]) -> Optional[Dict]:
    """Fetch route from Origin to Destination."""
    payload = {
        "origin_lat": origin[0],
        "origin_lon": origin[1],
        "dest_lat": dest[0],
        "dest_lon": dest[1],
        "routing_mode": "fast",
        "avoid_features": []
    }
    try:
        response = requests.post(f"{API_BASE_URL}/api/route", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Route API Error: {response.text}")
    except Exception as e:
        st.error(f"Route connection error: {e}")
    return None

def get_weather_forecast(bbox: Tuple[float, float, float, float]) -> List[Dict]:
    """Fetch weather forecast for a bounding box area."""
    try:
        # Construct BBOX query
        params = {
            "min_lon": bbox[0],
            "min_lat": bbox[1],
            "max_lon": bbox[2],
            "max_lat": bbox[3],
            "hours": 2 # Short forecast for demo
        }
        response = requests.get(f"{API_BASE_URL}/api/forecast/weather", params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            st.warning(f"Weather API error: {response.text}")
    except Exception as e:
        st.warning(f"Weather connection error: {e}")
    return []

def get_ai_summary(api_url: str, prompt: str):
    """Get journey summary from LLM with streaming."""
    llm_prompt = os.getenv("LLM_PROMPT")
    try:
        # User provides base URL like http://localhost:1234/v1
        # We append the chat completions endpoint
        url = f"{api_url.rstrip('/')}/chat/completions"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "messages": [
                {"role": "system", "content": llm_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": -1, # Let nature take its course
            "stream": True
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60, stream=True)
        if response.status_code == 200:
            import json
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            json_data = json.loads(data_str)
                            delta = json_data['choices'][0]['delta']
                            if 'content' in delta:
                                yield delta['content']
                        except Exception:
                            continue
        else:
            yield f"LLM Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        yield f"LLM Connection Error: {e}. Ensure LLM Studio is running and accessible."

# ====================================================================
# HELPERS
# ====================================================================

def decode_route(polyline_str: str) -> List[List[float]]:
    """Decode flexpolyline to list of [lon, lat] for Deck.gl."""
    # flexpolyline.decode returns (lat, lon, elev)
    # We need to swap to (lon, lat) for PyDeck/GeoJSON
    coords = flexpolyline.decode(polyline_str)
    return [[c[1], c[0]] for c in coords]

def get_route_bbox(path: List[List[float]]) -> Tuple[float, float, float, float]:
    """Calculate min/max lon/lat for the route path."""
    lons = [p[0] for p in path]
    lats = [p[1] for p in path]
    return (min(lons), min(lats), max(lons), max(lats))

def get_weather_icon(symbol_id: int) -> str:
    """Return a simple URL or emoji based on Open-Meteo WMO code."""
    # Simplified mapping
    if symbol_id == 1: return "☀️"
    if symbol_id in [31, 80, 81]: return "🌧️"
    if symbol_id in [51, 71, 73, 75]: return "❄️"
    return "☁️"

# ====================================================================
# APP UI
# ====================================================================

st.title("🚗 AI Route Planner with Weather 🌤️")

with st.sidebar:
    st.header("⚙️ Asetukset")
    # Default to host.docker.internal for Docker -> Host communication
    llm_api_url = st.text_input(
        "LLM API Base URL", 
        value="http://host.docker.internal:1234/v1",
        help="URL to your local LLM (e.g., LM Studio). Use http://host.docker.internal:1234/v1 if running in Docker."
    )

col1, col2 = st.columns(2)
with col1:
    start_addr = st.text_input("Lähtöpaikka", "Helsinki")
with col2:
    end_addr = st.text_input("Määränpää", "Tampere")

if st.button("Hae Reitti"):
    with st.spinner("Lasketaan reittiä..."):
        # 1. Geocode
        start_coords = get_geocode(start_addr)
        end_coords = get_geocode(end_addr)

        if start_coords and end_coords:
            # 2. Get Route
            route_data = get_route(start_coords, end_coords)
            
            if route_data and route_data.get("success"):
                polyline = route_data["polyline"]
                distance = route_data["distance_km"]
                duration = route_data["duration_hours"]

                st.success(f"Reitti: {distance:.1f} km, {duration:.1f} h")

                # 3. Process Path
                path_coords = decode_route(polyline)
                
                # 4. Get Weather for Route BBox
                # Add some buffer to bbox
                min_lon, min_lat, max_lon, max_lat = get_route_bbox(path_coords)
                bbox = (min_lon - 0.5, min_lat - 0.5, max_lon + 0.5, max_lat + 0.5)
                
                weather_data = get_weather_forecast(bbox)
                
                # Display Weather Metrics along the route
                if weather_data and path_coords:
                    st.subheader("Sääolosuhteet reitin varrella")
                    
                    # Sample 5 points along the route
                    fractions = [0.0, 0.25, 0.5, 0.75, 1.0]
                    indices = sorted(list(set([int(f * (len(path_coords) - 1)) for f in fractions])))
                    
                    cols = st.columns(len(indices))
                    
                    for i, idx in enumerate(indices):
                        col = cols[i]
                        pt = path_coords[idx] # [lon, lat]
                        
                        # Find closest weather point
                        closest = min(weather_data, key=lambda w: (w['lon'] - pt[0])**2 + (w['lat'] - pt[1])**2)
                        
                        label_text = f"{int(fractions[i]*100)}% matkasta"
                        if i == 0: label_text = "Lähtö"
                        elif i == len(indices)-1: label_text = "Määränpää"
                        
                        col.metric(
                            label=label_text,
                            value=f"{closest['temperature']:.1f}°C",
                            delta=f"Sade: {closest.get('precipitation', 0):.1f} mm",
                            delta_color="off"
                        )
                    
                    # 4b. AI Summary
                    if llm_api_url:
                        st.subheader("🤖 Tekoälyn yhteenveto")
                        # Create a placeholder for the streaming output
                        summary_placeholder = st.empty()
                        full_response = ""
                        
                        # Construct prompt
                        weather_samples_str = "\n".join([
                            f"- At {int(fractions[i]*100)}% of trip: {min(weather_data, key=lambda w: (w['lon']-path_coords[idx][0])**2 + (w['lat']-path_coords[idx][1])**2)['temperature']:.1f}°C, Precip: {min(weather_data, key=lambda w: (w['lon']-path_coords[idx][0])**2 + (w['lat']-path_coords[idx][1])**2).get('precipitation', 0):.1f} mm"
                            for i, idx in enumerate(indices)
                        ])
                        
                        prompt = f"""
                        The user is driving from {start_addr} to {end_addr}.
                        Total Distance: {distance:.1f} km.
                        Estimated Duration: {duration:.1f} hours.
                        
                        Weather samples along the route:
                        {weather_samples_str}
                        
                        Please summarize the journey and weather conditions.
                        """
                        
                        # Consume the stream
                        for chunk in get_ai_summary(llm_api_url, prompt):
                            full_response += chunk
                            summary_placeholder.info(full_response + "▌")
                        
                        # Final update without cursor
                        summary_placeholder.info(full_response)
                        
                # 5. Visualize
                view_state = pdk.ViewState(
                    latitude=(start_coords[0] + end_coords[0]) / 2,
                    longitude=(start_coords[1] + end_coords[1]) / 2,
                    zoom=7
                )

                layers = [
                    # Route Line
                    pdk.Layer(
                        "PathLayer",
                        data=[{"path": path_coords}],
                        pickable=True,
                        get_color=[0, 100, 255],
                        width_scale=20,
                        width_min_pixels=2,
                        get_path="path",
                    ),
                ]



                # Start/End Markers
                layers.append(pdk.Layer(
                    "ScatterplotLayer",
                    data=[
                        {"pos": [start_coords[1], start_coords[0]], "color": [0, 255, 0], "radius": 500},
                        {"pos": [end_coords[1], end_coords[0]], "color": [255, 0, 0], "radius": 500},
                    ],
                    get_position="pos",
                    get_color="color",
                    get_radius="radius",
                ))

                st.pydeck_chart(pdk.Deck(
                    map_style=None,
                    initial_view_state=view_state,
                    layers=layers,
                    # tooltip={"text": "{temp}\nPrecip: {precip} mm"} # Removed as we don't have weather points
                ))

            else:
                st.error("Reitin haku epäonnistui.")
        else:
            st.error("Osoitteita ei löytynyt.")
