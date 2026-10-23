"""CRUD page: manage player records with validation and error handling."""
import streamlit as st

from utils.db_connection import DatabaseError, execute, run_query

ROLES = ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"]
st.title("🛠 CRUD Operations - Players")
teams = run_query("SELECT team_id, team_name FROM teams ORDER BY team_name")
team_map = dict(zip(teams.team_name, teams.team_id))


def clean(name: str) -> str:
    return " ".join(name.split())


tab_r, tab_c, tab_u, tab_d = st.tabs(["Read", "Create", "Update", "Delete"])

with tab_r:
    q = st.text_input("Search by name")
    st.dataframe(run_query("""SELECT p.player_id, p.full_name, p.country, t.team_name, p.playing_role,
                              p.batting_style, p.bowling_style FROM players p LEFT JOIN teams t USING(team_id)
                              WHERE p.full_name LIKE ? ORDER BY p.player_id DESC""", (f"%{q}%",)),
                 use_container_width=True, hide_index=True)

with tab_c:
    with st.form("create", clear_on_submit=True):
        name = st.text_input("Full name")
        team = st.selectbox("Team", list(team_map))
        role = st.selectbox("Role", ROLES)
        bat = st.selectbox("Batting style", ["Right-hand bat", "Left-hand bat"])
        bowl = st.text_input("Bowling style", "-")
        if st.form_submit_button("Add player"):
            name = clean(name)
            if len(name) < 3:
                st.error("Name must be at least 3 characters.")
            else:
                try:
                    execute("INSERT INTO players (full_name,country,team_id,playing_role,batting_style,bowling_style) "
                            "VALUES (?,?,?,?,?,?)", (name, team, team_map[team], role, bat, bowl.strip() or "-"))
                    st.success(f"Added {name}.")
                except DatabaseError as exc:
                    st.error(f"Could not add player: {exc}")

players = run_query("SELECT player_id, full_name, team_id, playing_role, batting_style, bowling_style FROM players ORDER BY full_name")
labels = {int(r.player_id): f"{r.full_name} (#{r.player_id})" for r in players.itertuples()}

with tab_u:
    if not labels:
        st.info("No players yet.")
    else:
        pid = st.selectbox("Player", list(labels), format_func=labels.get, key="upd")
        cur = players[players.player_id == pid].iloc[0]
        with st.form("update"):
            name = st.text_input("Full name", cur.full_name)
            role = st.selectbox("Role", ROLES, index=ROLES.index(cur.playing_role))
            bowl = st.text_input("Bowling style", cur.bowling_style or "-")
            team = st.selectbox("Team", list(team_map), index=list(team_map.values()).index(cur.team_id)
                                if cur.team_id in team_map.values() else 0)
            if st.form_submit_button("Save changes"):
                if len(clean(name)) < 3:
                    st.error("Name must be at least 3 characters.")
                else:
                    try:
                        execute("UPDATE players SET full_name=?, playing_role=?, bowling_style=?, team_id=?, country=? "
                                "WHERE player_id=?", (clean(name), role, bowl, team_map[team], team, int(pid)))
                        st.success("Updated.")
                    except DatabaseError as exc:
                        st.error(f"Update failed: {exc}")

with tab_d:
    if labels:
        pid = st.selectbox("Player", list(labels), format_func=labels.get, key="del")
        st.warning("Deleting a player also removes their batting, bowling and career records.")
        if st.checkbox("I understand") and st.button("Delete player", type="primary"):
            try:
                execute("DELETE FROM players WHERE player_id=?", (int(pid),))
                st.success("Deleted. Refresh the page to update lists.")
            except DatabaseError as exc:
                st.error(f"Delete failed: {exc}")
