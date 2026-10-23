"""Generate a realistic SYNTHETIC cricket dataset so the app works offline.

Names are real players for readability, but every statistic is randomly generated.
Run:  python -m database.seed_data
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.db_connection import DB_PATH, get_connection, init_db  # noqa: E402

random.seed(42)
FORMATS = ["Test", "ODI", "T20I"]
SR_BASE = {"Test": 55, "ODI": 85, "T20I": 128}
MEAN_RUNS = {"Test": 34, "ODI": 31, "T20I": 21}

TEAMS = {
    "India": ["Rohit Sharma", "Shubman Gill", "Virat Kohli", "Shreyas Iyer", "KL Rahul", "Hardik Pandya",
              "Ravindra Jadeja", "Kuldeep Yadav", "Mohammed Shami", "Jasprit Bumrah", "Mohammed Siraj"],
    "Australia": ["David Warner", "Travis Head", "Steve Smith", "Marnus Labuschagne", "Alex Carey",
                  "Glenn Maxwell", "Mitchell Marsh", "Pat Cummins", "Mitchell Starc", "Adam Zampa", "Josh Hazlewood"],
    "England": ["Jason Roy", "Jonny Bairstow", "Joe Root", "Ben Stokes", "Jos Buttler", "Moeen Ali",
                "Liam Livingstone", "Sam Curran", "Chris Woakes", "Adil Rashid", "Mark Wood"],
    "Pakistan": ["Fakhar Zaman", "Imam-ul-Haq", "Babar Azam", "Mohammad Rizwan", "Saud Shakeel", "Shadab Khan",
                 "Iftikhar Ahmed", "Shaheen Afridi", "Naseem Shah", "Haris Rauf", "Hasan Ali"],
    "South Africa": ["Quinton de Kock", "Temba Bavuma", "Aiden Markram", "Rassie van der Dussen", "Heinrich Klaasen",
                     "David Miller", "Marco Jansen", "Kagiso Rabada", "Keshav Maharaj", "Lungi Ngidi", "Anrich Nortje"],
    "New Zealand": ["Devon Conway", "Will Young", "Kane Williamson", "Daryl Mitchell", "Tom Latham", "Glenn Phillips",
                    "Mitchell Santner", "Trent Boult", "Tim Southee", "Matt Henry", "Lockie Ferguson"],
}
# roles by squad slot: 0-4 batters (4 = keeper), 5-6 all-rounders, 7-10 bowlers
ROLES = ["Batsman"] * 4 + ["Wicket-keeper"] + ["All-rounder"] * 2 + ["Bowler"] * 4
VENUES = [
    ("Narendra Modi Stadium", "Ahmedabad", "India", 132000), ("Eden Gardens", "Kolkata", "India", 66000),
    ("Wankhede Stadium", "Mumbai", "India", 33000), ("Melbourne Cricket Ground", "Melbourne", "Australia", 100024),
    ("Sydney Cricket Ground", "Sydney", "Australia", 48000), ("Lord's", "London", "England", 31100),
    ("The Oval", "London", "England", 27500), ("Gaddafi Stadium", "Lahore", "Pakistan", 34000),
    ("National Stadium", "Karachi", "Pakistan", 34228), ("Newlands", "Cape Town", "South Africa", 25000),
    ("Wanderers Stadium", "Johannesburg", "South Africa", 34000), ("Eden Park", "Auckland", "New Zealand", 50000),
    ("Basin Reserve", "Wellington", "New Zealand", 11600),
]


def seed() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    today = date.today()
    with get_connection() as c:
        team_ids, squads = {}, {}
        for i, name in enumerate(TEAMS, 1):
            c.execute("INSERT INTO teams VALUES (?,?,?,?)", (i, name, name, name[:3].upper()))
            team_ids[name] = i
        venue_rows = []
        for i, (n, city, country, cap) in enumerate(VENUES, 1):
            c.execute("INSERT INTO venues VALUES (?,?,?,?,?)", (i, n, city, country, cap))
            venue_rows.append((i, country))
        pid = 0
        skill = {}
        for team, names in TEAMS.items():
            squads[team_ids[team]] = []
            for slot, nm in enumerate(names):
                pid += 1
                role = ROLES[slot]
                bat = random.choice(["Right-hand bat", "Left-hand bat"])
                bowl = ("-" if role in ("Batsman", "Wicket-keeper") and random.random() < .8 else
                        random.choice(["Right-arm fast", "Right-arm medium", "Left-arm fast", "Off break",
                                       "Leg break", "Left-arm orthodox"]))
                c.execute("INSERT INTO players VALUES (?,?,?,?,?,?,?)", (pid, nm, team, team_ids[team], role, bat, bowl))
                skill[pid] = {"Batsman": 1.25, "Wicket-keeper": 1.1, "All-rounder": .95, "Bowler": .45}[role] * random.uniform(.8, 1.2)
                squads[team_ids[team]].append(pid)
                for f in FORMATS:   # career tables
                    m = random.randint(25, 140) if f != "Test" else random.randint(15, 110)
                    inns = int(m * random.uniform(.85, 1.0))
                    avg = round(MEAN_RUNS[f] * skill[pid] * random.uniform(.85, 1.15), 2)
                    runs = int(avg * inns * .85)
                    c.execute("INSERT INTO career_batting VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (pid, f, m, inns, runs, avg, round(SR_BASE[f] * random.uniform(.85, 1.1), 2),
                               int(min(264, random.randint(60, 120) + avg * random.uniform(0, 3.5))),
                               int(runs / 600 * random.uniform(.5, 1.2)), int(runs / 250 * random.uniform(.5, 1.2))))
                    wk = {"Bowler": 2.2, "All-rounder": 1.1}.get(role, .05)
                    c.execute("INSERT INTO career_bowling VALUES (?,?,?,?,?,?)",
                              (pid, f, m, int(m * wk * random.uniform(.8, 1.4) * (1.3 if f == "Test" else 1)),
                               round(random.uniform(22, 38), 2),
                               round(random.uniform(2.6, 3.4) if f == "Test" else random.uniform(4.6, 5.8) if f == "ODI"
                                     else random.uniform(7.2, 8.8), 2)))
                    c.execute("INSERT INTO fielding_stats VALUES (?,?,?,?)",
                              (pid, f, int(m * random.uniform(.2, .8)),
                               int(m * random.uniform(.2, .6)) if role == "Wicket-keeper" else 0))
        # series + matches
        tids = list(team_ids.values())
        mid = sid = 0
        for k in range(130):
            sid += 1
            a, b = random.sample(tids, 2)
            fmt = random.choice(FORMATS)
            vid, vcountry = random.choice(venue_rows)
            host = vcountry
            start = today - timedelta(days=random.randint(0, 365 * 6 + 200)) if k > 8 else today - timedelta(days=random.randint(1, 25))
            n_games = random.choice([2, 3, 3, 5]) if fmt != "T20I" else random.choice([3, 3, 5])
            c.execute("INSERT INTO series VALUES (?,?,?,?,?,?)",
                      (sid, f"{list(TEAMS)[a-1]} vs {list(TEAMS)[b-1]} {fmt} Series {start.year}", host, fmt,
                       start.isoformat(), n_games))
            for g in range(n_games):
                mid += 1
                d = start + timedelta(days=g * (5 if fmt == "Test" else 3))
                if d > today:
                    d = today
                t1, t2 = (a, b) if random.random() < .5 else (b, a)
                vid2 = vid if random.random() < .7 else random.choice(venue_rows)[0]
                toss = random.choice([t1, t2])
                dec = random.choice(["bat", "bowl"]) if fmt != "Test" else "bat"
                first = toss if dec == "bat" else (t2 if toss == t1 else t1)
                second = t2 if first == t1 else t1
                desc = f"{g+1}{'st' if g==0 else 'nd' if g==1 else 'rd' if g==2 else 'th'} {fmt}"
                c.execute("INSERT INTO matches VALUES (?,?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,'Complete')",
                          (mid, sid, desc, fmt, t1, t2, vid2, d.isoformat(), toss, dec))
                totals, ids = {}, {}
                for team in (first, second):
                    total = 0
                    for pos, pl in enumerate(squads[team][:8], 1):
                        s = skill[pl] * random.uniform(.8, 1.2)
                        runs = int(min(200, random.expovariate(1 / (MEAN_RUNS[fmt] * s))))
                        sr = SR_BASE[fmt] * random.uniform(.6, 1.5)
                        balls = max(1, int(runs / sr * 100)) if runs else random.randint(1, 8)
                        total += runs
                        c.execute("INSERT INTO batting_innings (match_id,player_id,team_id,innings_no,batting_position,runs,balls,fours,sixes,strike_rate) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                  (mid, pl, team, 1 if team == first else 2, pos, runs, balls,
                                   int(runs * .08), int(runs * .03) if fmt != "Test" else 0, round(runs / balls * 100, 2)))
                    totals[team] = total
                    ids[team] = total
                for team, opp in ((first, second), (second, first)):   # bowlers from fielding side
                    attackers = squads[opp][5:] if True else []
                    for pl in random.sample(squads[team][5:], 5):
                        ov = random.randint(4, 10) if fmt == "ODI" else random.randint(2, 4) if fmt == "T20I" else random.randint(8, 25)
                        eco = random.uniform(2.4, 3.6) if fmt == "Test" else random.uniform(4.2, 6.5) if fmt == "ODI" else random.uniform(6.5, 9.8)
                        r = int(ov * eco)
                        c.execute("INSERT INTO bowling_innings (match_id,player_id,team_id,overs,runs_conceded,wickets,economy) VALUES (?,?,?,?,?,?,?)",
                                  (mid, pl, team, ov, r, min(6, int(random.expovariate(1.1) * (1.5 if skill[pl] < .6 else .9))), round(r / ov, 2)))
                winner = first if totals[first] > totals[second] else second
                if totals[first] == totals[second]:
                    winner = first
                if winner == first:
                    vt, margin = "runs", max(1, totals[first] - totals[second])
                else:
                    vt, margin = "wickets", random.randint(1, 9)
                c.execute("UPDATE matches SET winner_id=?, victory_margin=?, victory_type=? WHERE match_id=?",
                          (winner, margin, vt, mid))
    print(f"Seeded {DB_PATH}")


if __name__ == "__main__":
    seed()
