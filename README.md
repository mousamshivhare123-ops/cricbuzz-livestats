# 🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics

Streamlit dashboard combining the Cricbuzz REST API (via RapidAPI) with a SQL database.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # add your RAPIDAPI_KEY
python -m database.seed_data                          # builds data/cricbuzz.db with SYNTHETIC sample data
streamlit run app.py
```
Without an API key the Live/Top-stats pages fall back to the local database.

## Structure
```
app.py                  entry point + navigation
pages/                  home, live_matches, top_stats, sql_queries, crud_operations
utils/db_connection.py  centralised DB access (context manager, rollback, DatabaseError)
utils/api_client.py     RapidAPI client: timeout, retry/backoff, JSON parsing
database/schema.sql     tables, constraints, indexes
database/seed_data.py   synthetic data generator (offline demo)
sql/queries.py          the 25 SQL questions
notebooks/              (optional) API fetching experiments
```

## API setup
1. Subscribe to "Cricbuzz Cricket" on RapidAPI, copy the key into `.env` (`RAPIDAPI_KEY`).
2. Check endpoint paths in `utils/api_client.py` against the RapidAPI playground.
3. Keys live only in `.env` (git-ignored).

## Database
SQLite by default (`DB_PATH` in `.env`). Schema is ANSI-style; for MySQL/PostgreSQL change only `utils/db_connection.py`
and swap `AUTOINCREMENT`, `strftime`, `date('now', ...)` for the dialect equivalents.
Tables: teams, venues, players, series, matches, batting_innings, bowling_innings, career_batting, career_bowling, fielding_stats.

## Notes
- Seed data uses real player names with RANDOM statistics, for demonstration only.
- Q13/Q24 treat consecutive batting positions as partnerships, as the brief specifies.

## Screenshots
_Add screenshots of each page here before submission._

## Future improvements
Sync API results into the DB on a schedule, team/venue comparison charts, authentication for CRUD, Docker deployment.
