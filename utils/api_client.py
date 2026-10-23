"""Thin Cricbuzz (RapidAPI) client with timeout, retry/backoff and safe JSON parsing.

Endpoint paths follow the RapidAPI 'cricbuzz-cricket' playground; confirm them there
for your plan, as providers occasionally change paths.
"""
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()
HOST = os.getenv("RAPIDAPI_HOST", "cricbuzz-cricket.p.rapidapi.com")
BASE = f"https://{HOST}"


class ApiError(Exception):
    """Raised for any API failure with a readable message."""


def has_key() -> bool:
    return bool(os.getenv("RAPIDAPI_KEY"))


def _get(path: str, params: dict | None = None, retries: int = 3, timeout: int = 10) -> dict:
    key = os.getenv("RAPIDAPI_KEY")
    if not key:
        raise ApiError("RAPIDAPI_KEY is not set. Add it to your .env file.")
    headers = {"x-rapidapi-key": key, "x-rapidapi-host": HOST}
    last = None
    for attempt in range(retries):
        try:
            resp = requests.get(f"{BASE}{path}", headers=headers, params=params, timeout=timeout)
            if resp.status_code == 429:           # rate limited -> back off
                time.sleep(2 ** attempt)
                last = "Rate limit reached (HTTP 429)."
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.JSONDecodeError as exc:
            raise ApiError("API returned invalid JSON.") from exc
        except requests.exceptions.RequestException as exc:
            last = str(exc)
            time.sleep(2 ** attempt)
    raise ApiError(f"API request failed after {retries} attempts: {last}")


def live_matches() -> dict:
    return _get("/matches/v1/live")


def recent_matches() -> dict:
    return _get("/matches/v1/recent")


def scorecard(match_id: int) -> dict:
    return _get(f"/mcenter/v1/{match_id}/scard")


def rankings(category: str = "batsmen", fmt: str = "odi") -> dict:
    """category: batsmen | bowlers | allrounders | teams ; fmt: test | odi | t20"""
    return _get(f"/stats/v1/rankings/{category}", {"formatType": fmt})


def international_teams() -> dict:
    return _get("/teams/v1/international")


def team_players(team_id: int) -> dict:
    return _get(f"/teams/v1/{team_id}/players")


def flatten_matches(payload: dict) -> list[dict]:
    """Flatten the nested typeMatches -> seriesMatches -> matches structure."""
    rows = []
    for tm in payload.get("typeMatches", []):
        for sm in tm.get("seriesMatches", []):
            wrapper = sm.get("seriesAdWrapper", {})
            for m in wrapper.get("matches", []):
                info, score = m.get("matchInfo", {}), m.get("matchScore", {})
                t1, t2 = info.get("team1", {}), info.get("team2", {})
                venue = info.get("venueInfo", {})

                def fmt_score(s):
                    i = (s or {}).get("inngs1", {})
                    return f"{i.get('runs', '-')}/{i.get('wickets', '-')} ({i.get('overs', '-')} ov)" if i else "Yet to bat"

                rows.append({
                    "match_id": info.get("matchId"), "series": wrapper.get("seriesName"),
                    "description": info.get("matchDesc"), "format": info.get("matchFormat"),
                    "team1": t1.get("teamName"), "team1_score": fmt_score(score.get("team1Score")),
                    "team2": t2.get("teamName"), "team2_score": fmt_score(score.get("team2Score")),
                    "status": info.get("status"), "state": info.get("state"),
                    "venue": f"{venue.get('ground', '')}, {venue.get('city', '')}".strip(", "),
                })
    return rows


def flatten_rankings(payload: dict) -> list[dict]:
    return [{"rank": r.get("rank"), "name": r.get("name"), "country": r.get("country"),
             "rating": r.get("rating")} for r in payload.get("rank", [])]
