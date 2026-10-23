"""SQL Analytics page: run the 25 practice queries or a read-only custom query."""
import re

import streamlit as st

from sql.queries import QUERIES
from utils.db_connection import DatabaseError, run_query

st.title("🔍 SQL Analytics")
level = st.segmented_control("Level", ["All", "Beginner", "Intermediate", "Advanced"], default="All")
options = [k for k, (lvl, _, _) in QUERIES.items() if level in (None, "All") or lvl == level]
qid = st.selectbox("Question", options, format_func=lambda k: f"Q{k}. {QUERIES[k][1]}  ({QUERIES[k][0]})")
lvl, title, sql = QUERIES[qid]
sql = sql.strip()

with st.expander("View SQL", expanded=False):
    st.code(sql, language="sql")
try:
    df = run_query(sql)
    st.caption(f"{len(df)} rows")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Download CSV", df.to_csv(index=False), f"q{qid}.csv", "text/csv")
except DatabaseError as exc:
    st.error(f"Query failed: {exc}")

st.divider()
st.subheader("Custom query (read-only)")
custom = st.text_area("SELECT ...", "SELECT * FROM players LIMIT 10;", height=120)
if st.button("Run"):
    stmt = custom.strip().rstrip(";")
    if not re.match(r"(?is)^\s*(select|with)\b", stmt) or ";" in stmt or \
            re.search(r"(?i)\b(insert|update|delete|drop|alter|create|attach|pragma|replace)\b", stmt):
        st.error("Only a single SELECT/WITH statement is allowed here.")
    else:
        try:
            st.dataframe(run_query(stmt), use_container_width=True, hide_index=True)
        except DatabaseError as exc:
            st.error(f"Query failed: {exc}")
