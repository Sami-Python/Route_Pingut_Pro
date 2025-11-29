import streamlit as st
import requests
import json
from streamlit_calendar import calendar

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
        # Map API response to FullCalendar event object
        # API: title, start, end, location
        evt = {
            "title": event.get("title", "No Title"),
            "start": event.get("start"),
            "end": event.get("end"),
            # Add location to extendedProps or title if needed
            "extendedProps": {
                "location": event.get("location")
            }
        }
        # Optional: Append location to title for visibility
        if event.get("location"):
            evt["title"] += f" (@ {event.get('location')})"
        
        events.append(evt)
    return events

@st.cache_data
def _add_ical_events():
    events = []
    for event in st.session_state["ical_events_data"]:
        # Map API response to FullCalendar event object
        # API: title, start, end, location
        evt = {
            "title": event.get("title", "No Title"),
            "start": event.get("start"),
            "end": event.get("end"),
            # Add location to extendedProps or title if needed
            "extendedProps": {
                "location": event.get("location")
            }
        }
        # Optional: Append location to title for visibility
        if event.get("location"):
            evt["title"] += f" (@ {event.get('location')})"
        
        events.append(evt)
    return events

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
            # Note: We now use the /cal prefix because of the mount in api/main.py
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
with st.expander("Graph API Demo", expanded=True):
    st.subheader("Microsoft Graph Calendar")
    
    # Check for token in query params
    if "access_token" in st.query_params:
        st.session_state["access_token"] = st.query_params["access_token"]
        st.query_params.clear()
        st.rerun()

    st.info("To use this, you first need to authenticate and get a token.")
    
    # 1. Login Link
    # This link points to localhost because it's accessed by the user's browser
    login_url = "http://localhost:8000/graph/login"
    st.markdown(f"👉 **[Click here to Login]({login_url})**", unsafe_allow_html=True)
    st.caption("After logging in, the token will be automatically populated below.")
    
    # 2. Token Input
    default_token = st.session_state.get("access_token", "")
    token = st.text_input("Access Token", value=default_token, type="password")
    
    # 3. Fetch Data
    if st.button("Get My Calendar Events", key="get_graph_events"):
        if not token:
            st.warning("Please enter a token first.")
        else:
            try:
                # Call the API container
                # The graph_api expects 'token' as a query parameter
                response = requests.get(f"{API_BASE_URL}/graph/calendar", params={"token": token})
                
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


# 4. Calendar Visualization
available_calendars = _get_available_calendars()
if not available_calendars:
    st.warning("No calendars available.")
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
    # Clean up title if we appended location
    if " (@" in title:
        title = title.split(" (@")[0]   
    @st.dialog(f"Event Details: {title}")
    def show_event_details():
        st.write(f"**Start:** {start}")
        st.write(f"**End:** {end}")
        st.write(f"**Location:** {location}")
    show_event_details()
            

