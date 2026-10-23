-- Cricbuzz LiveStats schema (SQLite; ANSI-friendly so it ports to MySQL/PostgreSQL)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    team_id    INTEGER PRIMARY KEY,
    team_name  TEXT NOT NULL UNIQUE,
    country    TEXT NOT NULL,
    short_name TEXT
);
CREATE TABLE IF NOT EXISTS venues (
    venue_id   INTEGER PRIMARY KEY,
    venue_name TEXT NOT NULL,
    city       TEXT,
    country    TEXT NOT NULL,
    capacity   INTEGER CHECK (capacity IS NULL OR capacity >= 0)
);
CREATE TABLE IF NOT EXISTS players (
    player_id     INTEGER PRIMARY KEY,
    full_name     TEXT NOT NULL,
    country       TEXT NOT NULL,
    team_id       INTEGER REFERENCES teams(team_id),
    playing_role  TEXT CHECK (playing_role IN ('Batsman','Bowler','All-rounder','Wicket-keeper')),
    batting_style TEXT,
    bowling_style TEXT
);
CREATE TABLE IF NOT EXISTS series (
    series_id      INTEGER PRIMARY KEY,
    series_name    TEXT NOT NULL,
    host_country   TEXT,
    match_type     TEXT CHECK (match_type IN ('Test','ODI','T20I')),
    start_date     DATE,
    total_matches  INTEGER
);
CREATE TABLE IF NOT EXISTS matches (
    match_id       INTEGER PRIMARY KEY,
    series_id      INTEGER REFERENCES series(series_id),
    description    TEXT,
    match_format   TEXT NOT NULL CHECK (match_format IN ('Test','ODI','T20I')),
    team1_id       INTEGER NOT NULL REFERENCES teams(team_id),
    team2_id       INTEGER NOT NULL REFERENCES teams(team_id),
    venue_id       INTEGER REFERENCES venues(venue_id),
    match_date     DATE NOT NULL,
    toss_winner_id INTEGER REFERENCES teams(team_id),
    toss_decision  TEXT CHECK (toss_decision IN ('bat','bowl')),
    winner_id      INTEGER REFERENCES teams(team_id),
    victory_margin INTEGER,
    victory_type   TEXT CHECK (victory_type IN ('runs','wickets')),
    status         TEXT DEFAULT 'Complete'
);
CREATE TABLE IF NOT EXISTS batting_innings (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id         INTEGER NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    player_id        INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    team_id          INTEGER NOT NULL REFERENCES teams(team_id),
    innings_no       INTEGER NOT NULL DEFAULT 1,
    batting_position INTEGER NOT NULL,
    runs             INTEGER NOT NULL DEFAULT 0,
    balls            INTEGER NOT NULL DEFAULT 0,
    fours            INTEGER DEFAULT 0,
    sixes            INTEGER DEFAULT 0,
    strike_rate      REAL
);
CREATE TABLE IF NOT EXISTS bowling_innings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id      INTEGER NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    player_id     INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    team_id       INTEGER NOT NULL REFERENCES teams(team_id),
    overs         REAL NOT NULL,
    runs_conceded INTEGER NOT NULL,
    wickets       INTEGER NOT NULL DEFAULT 0,
    economy       REAL
);
CREATE TABLE IF NOT EXISTS career_batting (
    player_id     INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    match_format  TEXT NOT NULL,
    matches       INTEGER, innings INTEGER, runs INTEGER,
    average       REAL, strike_rate REAL, highest_score INTEGER,
    centuries     INTEGER, fifties INTEGER,
    PRIMARY KEY (player_id, match_format)
);
CREATE TABLE IF NOT EXISTS career_bowling (
    player_id    INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    match_format TEXT NOT NULL,
    matches      INTEGER, wickets INTEGER, average REAL, economy REAL,
    PRIMARY KEY (player_id, match_format)
);
CREATE TABLE IF NOT EXISTS fielding_stats (
    player_id    INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    match_format TEXT NOT NULL,
    catches      INTEGER DEFAULT 0,
    stumpings    INTEGER DEFAULT 0,
    PRIMARY KEY (player_id, match_format)
);

CREATE INDEX IF NOT EXISTS idx_matches_date    ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_venue   ON matches(venue_id);
CREATE INDEX IF NOT EXISTS idx_matches_winner  ON matches(winner_id);
CREATE INDEX IF NOT EXISTS idx_bat_match       ON batting_innings(match_id, team_id, batting_position);
CREATE INDEX IF NOT EXISTS idx_bat_player      ON batting_innings(player_id);
CREATE INDEX IF NOT EXISTS idx_bowl_player     ON bowling_innings(player_id, match_id);
CREATE INDEX IF NOT EXISTS idx_players_country ON players(country);
