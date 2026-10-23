"""Live Matches page: API data with graceful fallback to the local DB."""
import pandas as pd
import streamlit as st

from utils import api_client as api
from utils.db_connection import run_query

st.title("⚡ Live Matches")
mode = st.radio("Source", ["Live", "Recent"], horizontal=True)

if not api.has_key():
    st.warning("No RAPIDAPI_KEY configured - showing the latest matches from the local database instead.")
    st.dataframe(run_query("""
        SELECT m.match_date, m.match_format, t1.team_name AS team1, t2.team_name AS team2,
               w.team_name AS winner, m.victory_margin || ' ' || m.victory_type AS margin, v.venue_name
        FROM matches m JOIN teams t1 ON t1.team_id=m.team1_id JOIN teams t2 ON t2.team_id=m.team2_id
        JOIN teams w ON w.team_id=m.winner_id JOIN venues v ON v.venue_id=m.venue_id
        ORDER BY m.match_date DESC LIMIT 15"""), use_container_width=True, hide_index=True)
    st.stop()

try:
    with st.spinner("Fetching matches..."):
        payload = api.live_matches() if mode == "Live" else api.recent_matches()
    rows = api.flatten_matches(payload)
except api.ApiError as exc:
    st.error(f"Could not load matches: {exc}")
    st.stop()

if not rows:
    st.info("No matches available right now.")
    st.stop()

df = pd.DataFrame(rows)
st.dataframe(df.drop(columns=["match_id"]), use_container_width=True, hide_index=True)

st.subheader("Scorecard")
pick = st.selectbox("Match", df["match_id"], format_func=lambda i: f"{df.loc[df.match_id == i, 'team1'].iloc[0]} vs "
                    f"{df.loc[df.match_id == i, 'team2'].iloc[0]} - {df.loc[df.match_id == i, 'description'].iloc[0]}")
if st.button("Load scorecard"):
    try:
        card = api.scorecard(int(pick))
        for inn in card.get("scoreCard", []):
            bat = inn.get("batTeamDetails", {})
            st.markdown(f"**{bat.get('batTeamName', 'Innings')}** - "
                        f"{inn.get('scoreDetails', {}).get('runs', '-')}/{inn.get('scoreDetails', {}).get('wickets', '-')}")
            batsmen = [{"Batter": b.get("batName"), "R": b.get("runs"), "B": b.get("balls"), "4s": b.get("fours"),
                        "6s": b.get("sixes"), "Out": b.get("outDesc")} for b in bat.get("batsmenData", {}).values()]
            st.dataframe(pd.DataFrame(batsmen), hide_index=True, use_container_width=True)
            bowl = [{"Bowler": b.get("bowlName"), "O": b.get("overs"), "R": b.get("runs"), "W": b.get("wickets"),
                     "Econ": b.get("economy")} for b in inn.get("bowlTeamDetails", {}).get("bowlersData", {}).values()]
            st.dataframe(pd.DataFrame(bowl), hide_index=True, use_container_width=True)
    except api.ApiError as exc:
        st.error(str(exc))
