"""Top Player Stats page: API rankings with local-DB leaderboards as fallback."""
import pandas as pd
import streamlit as st

from utils import api_client as api
from utils.db_connection import run_query

st.title("📊 Top Player Stats")
tab_api, tab_db = st.tabs(["ICC Rankings (API)", "Career leaders (DB)"])

with tab_api:
    c1, c2 = st.columns(2)
    cat = c1.selectbox("Category", ["batsmen", "bowlers", "allrounders"])
    fmt = c2.selectbox("Format", ["test", "odi", "t20"])
    if not api.has_key():
        st.info("Add RAPIDAPI_KEY to .env to load live rankings.")
    else:
        try:
            df = pd.DataFrame(api.flatten_rankings(api.rankings(cat, fmt))).head(15)
            st.dataframe(df, hide_index=True, use_container_width=True)
            if not df.empty:
                st.bar_chart(df.set_index("name")["rating"].astype(float))
        except api.ApiError as exc:
            st.error(str(exc))

with tab_db:
    fmt = st.selectbox("Format ", ["ODI", "Test", "T20I"])
    metric = st.selectbox("Leaderboard", ["Most runs", "Highest score", "Most wickets", "Best batting average"])
    sqls = {
        "Most runs": ("SELECT p.full_name AS player, cb.runs AS value FROM career_batting cb JOIN players p USING(player_id) "
                      "WHERE match_format=? ORDER BY value DESC LIMIT 10"),
        "Highest score": ("SELECT p.full_name AS player, cb.highest_score AS value FROM career_batting cb JOIN players p USING(player_id) "
                          "WHERE match_format=? ORDER BY value DESC LIMIT 10"),
        "Most wickets": ("SELECT p.full_name AS player, cw.wickets AS value FROM career_bowling cw JOIN players p USING(player_id) "
                         "WHERE match_format=? ORDER BY value DESC LIMIT 10"),
        "Best batting average": ("SELECT p.full_name AS player, cb.average AS value FROM career_batting cb JOIN players p USING(player_id) "
                                 "WHERE match_format=? ORDER BY value DESC LIMIT 10"),
    }
    df = run_query(sqls[metric], (fmt,))
    st.dataframe(df, hide_index=True, use_container_width=True)
    st.bar_chart(df.set_index("player")["value"])
