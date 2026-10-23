"""Home page: project overview and navigation help."""
import streamlit as st

from utils.db_connection import db_is_ready, run_query

st.title("🏏 Cricbuzz LiveStats")
st.caption("Real-time cricket insights & SQL-based analytics")
st.markdown("""
A multi-page analytics dashboard that combines the **Cricbuzz REST API** with a **SQL database**.

| Page | What it does |
|---|---|
| ⚡ Live Matches | Live/recent scorecards from the Cricbuzz API |
| 📊 Top Player Stats | Rankings and leaders (API, with DB fallback) |
| 🔍 SQL Analytics | 25 practice queries + a read-only custom SQL box |
| 🛠 CRUD Operations | Create, read, update and delete player records |

**Stack:** Python · Streamlit · SQLite (portable to MySQL/PostgreSQL) · pandas · requests
""")
if db_is_ready():
    c1, c2, c3, c4 = st.columns(4)
    for col, label, table in [(c1, "Players", "players"), (c2, "Matches", "matches"),
                              (c3, "Teams", "teams"), (c4, "Venues", "venues")]:
        col.metric(label, int(run_query(f"SELECT COUNT(*) AS n FROM {table}").iloc[0, 0]))
st.info("Set `RAPIDAPI_KEY` in `.env` to enable live data. Without it the app runs on the bundled sample database.")
