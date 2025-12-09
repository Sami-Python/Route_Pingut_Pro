import streamlit as st

pages = ["cal_demo.py", "maps_app.py"]

pg = st.navigation(pages)

pg.run()