import streamlit as st
import streamlit_calendar  as st_calendar
from icalevents.icaldownload import ICalDownload
from icalevents.icalevents import events
import icalendar
import datetime as dt
import json
import pytz
import requests

URL = "https://lukkarit.kamk.fi/ical.php?hash=E74AC94AE7A19AC99110C39EE535C0DBB0DF8AAE"




st.set_page_config(layout="wide")
st.title("Hello world")

url = st.text_input("ical url")

st.write("Testi")

while st.button("get events", key="get_events"):
    response = requests.get(f"http://api:8000/events?url={url}")
    events = json.loads(response.text)

    st.write(events)

