import streamlit as st

pages = ["cal_demo.py", "maps_app.py", "ai_route_demo.py"]

pg = st.navigation(pages)

pg.run()