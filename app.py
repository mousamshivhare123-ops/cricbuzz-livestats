"""Cricbuzz LiveStats - Streamlit entry point."""
import streamlit as st

from utils.db_connection import db_is_ready, init_db

st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")


@st.cache_resource(show_spinner="Building sample database...")
def setup_database() -> bool:
    """Create tables and seed sample data once per server run."""
    init_db()
    if not db_is_ready():
        from database.seed_data import seed
        seed()
    return True


setup_database()

nav = st.navigation([
    st.Page("pages/home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/live_matches.py", title="Live Matches", icon="⚡"),
    st.Page("pages/top_stats.py", title="Top Player Stats", icon="📊"),
    st.Page("pages/sql_queries.py", title="SQL Analytics", icon="🔍"),
    st.Page("pages/crud_operations.py", title="CRUD Operations", icon="🛠"),
])
nav.run()
