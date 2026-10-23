"""Cricbuzz LiveStats - Streamlit entry point. Run: streamlit run app.py"""
import streamlit as st

from utils.db_connection import db_is_ready, init_db

st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")
init_db()

nav = st.navigation([
    st.Page("pages/home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/live_matches.py", title="Live Matches", icon="⚡"),
    st.Page("pages/top_stats.py", title="Top Player Stats", icon="📊"),
    st.Page("pages/sql_queries.py", title="SQL Analytics", icon="🔍"),
    st.Page("pages/crud_operations.py", title="CRUD Operations", icon="🛠"),
])
if not db_is_ready():
    st.sidebar.warning("Database is empty. Run `python -m database.seed_data` for sample data.")
nav.run()
