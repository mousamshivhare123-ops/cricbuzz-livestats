"""The 25 practice queries (SQLite dialect). Each entry: (level, title, sql)."""

# Reusable CTE: one row per team per match with home/away + win flag.
_TEAM_MATCH = """
team_match AS (
    SELECT m.match_id, m.team1_id AS team_id, v.country AS venue_country, (m.winner_id = m.team1_id) AS won FROM matches m JOIN venues v USING(venue_id)
    UNION ALL
    SELECT m.match_id, m.team2_id, v.country, (m.winner_id = m.team2_id) FROM matches m JOIN venues v USING(venue_id)
)"""

QUERIES = {
1: ("Beginner", "Players who represent India", """
SELECT full_name, playing_role, batting_style, bowling_style
FROM players WHERE country = 'India' ORDER BY full_name;"""),

2: ("Beginner", "Matches played in the last 30 days", """
SELECT m.description, t1.team_name AS team1, t2.team_name AS team2,
       v.venue_name || ', ' || v.city AS venue, m.match_date
FROM matches m
JOIN teams t1 ON t1.team_id = m.team1_id
JOIN teams t2 ON t2.team_id = m.team2_id
JOIN venues v ON v.venue_id = m.venue_id
WHERE m.match_date >= date('now', '-30 day')
ORDER BY m.match_date DESC;"""),

3: ("Beginner", "Top 10 ODI run scorers", """
SELECT p.full_name, cb.runs, cb.average AS batting_average, cb.centuries
FROM career_batting cb JOIN players p USING(player_id)
WHERE cb.match_format = 'ODI'
ORDER BY cb.runs DESC LIMIT 10;"""),

4: ("Beginner", "Venues with capacity above 50,000", """
SELECT venue_name, city, country, capacity
FROM venues WHERE capacity > 50000 ORDER BY capacity DESC;"""),

5: ("Beginner", "Matches won by each team", """
SELECT t.team_name, COUNT(*) AS total_wins
FROM matches m JOIN teams t ON t.team_id = m.winner_id
GROUP BY t.team_id, t.team_name ORDER BY total_wins DESC;"""),

6: ("Beginner", "Players per playing role", """
SELECT playing_role, COUNT(*) AS player_count
FROM players GROUP BY playing_role ORDER BY player_count DESC;"""),

7: ("Beginner", "Highest individual score per format", """
SELECT match_format, MAX(highest_score) AS highest_score
FROM career_batting GROUP BY match_format;"""),

8: ("Beginner", "Series that started in 2024", """
SELECT series_name, host_country, match_type, start_date, total_matches
FROM series WHERE strftime('%Y', start_date) = '2024' ORDER BY start_date;"""),

9: ("Intermediate", "All-rounders with 1000+ runs and 50+ wickets", """
SELECT p.full_name, cb.runs AS total_runs, cw.wickets AS total_wickets, cb.match_format
FROM players p
JOIN career_batting cb ON cb.player_id = p.player_id
JOIN career_bowling cw ON cw.player_id = p.player_id AND cw.match_format = cb.match_format
WHERE p.playing_role = 'All-rounder' AND cb.runs > 1000 AND cw.wickets > 50
ORDER BY cb.runs DESC;"""),

10: ("Intermediate", "Last 20 completed matches with result", """
SELECT m.description, t1.team_name AS team1, t2.team_name AS team2, w.team_name AS winner,
       m.victory_margin, m.victory_type, v.venue_name
FROM matches m
JOIN teams t1 ON t1.team_id = m.team1_id
JOIN teams t2 ON t2.team_id = m.team2_id
JOIN teams w  ON w.team_id  = m.winner_id
JOIN venues v ON v.venue_id = m.venue_id
WHERE m.status = 'Complete'
ORDER BY m.match_date DESC, m.match_id DESC LIMIT 20;"""),

11: ("Intermediate", "Cross-format performance (players with 2+ formats)", """
SELECT p.full_name,
       SUM(CASE WHEN cb.match_format='Test' THEN cb.runs END) AS test_runs,
       SUM(CASE WHEN cb.match_format='ODI'  THEN cb.runs END) AS odi_runs,
       SUM(CASE WHEN cb.match_format='T20I' THEN cb.runs END) AS t20i_runs,
       ROUND(SUM(cb.average * cb.innings) / SUM(cb.innings), 2) AS overall_batting_avg
FROM career_batting cb JOIN players p USING(player_id)
GROUP BY p.player_id, p.full_name
HAVING COUNT(DISTINCT cb.match_format) >= 2
ORDER BY overall_batting_avg DESC;"""),

12: ("Intermediate", "Home vs away wins per team", f"""
WITH {_TEAM_MATCH}
SELECT t.team_name,
       SUM(CASE WHEN tm.venue_country = t.country AND tm.won THEN 1 ELSE 0 END) AS home_wins,
       SUM(CASE WHEN tm.venue_country <> t.country AND tm.won THEN 1 ELSE 0 END) AS away_wins,
       SUM(tm.venue_country = t.country) AS home_matches,
       SUM(tm.venue_country <> t.country) AS away_matches
FROM team_match tm JOIN teams t USING(team_id)
GROUP BY t.team_id, t.team_name ORDER BY home_wins + away_wins DESC;"""),

13: ("Intermediate", "Consecutive batsmen with 100+ combined runs", """
SELECT p1.full_name AS batter_1, p2.full_name AS batter_2,
       b1.runs + b2.runs AS partnership_runs, b1.innings_no AS innings, b1.match_id
FROM batting_innings b1
JOIN batting_innings b2 ON b2.match_id = b1.match_id AND b2.team_id = b1.team_id
     AND b2.innings_no = b1.innings_no AND b2.batting_position = b1.batting_position + 1
JOIN players p1 ON p1.player_id = b1.player_id
JOIN players p2 ON p2.player_id = b2.player_id
WHERE b1.runs + b2.runs >= 100
ORDER BY partnership_runs DESC LIMIT 100;"""),

14: ("Intermediate", "Bowling at venues (3+ matches, 4+ overs each)", """
SELECT p.full_name, v.venue_name,
       ROUND(AVG(bi.economy), 2) AS avg_economy, SUM(bi.wickets) AS total_wickets,
       COUNT(DISTINCT bi.match_id) AS matches_played
FROM bowling_innings bi
JOIN matches m ON m.match_id = bi.match_id
JOIN venues v ON v.venue_id = m.venue_id
JOIN players p ON p.player_id = bi.player_id
WHERE bi.overs >= 4
GROUP BY p.player_id, p.full_name, v.venue_id, v.venue_name
HAVING COUNT(DISTINCT bi.match_id) >= 3
ORDER BY avg_economy ASC;"""),

15: ("Intermediate", "Performance in close matches", """
WITH close_matches AS (
    SELECT match_id, winner_id FROM matches
    WHERE (victory_type = 'runs' AND victory_margin < 50)
       OR (victory_type = 'wickets' AND victory_margin < 5)
)
SELECT p.full_name, ROUND(AVG(b.runs), 2) AS avg_runs,
       COUNT(DISTINCT b.match_id) AS close_matches_played,
       COUNT(DISTINCT CASE WHEN cm.winner_id = b.team_id THEN b.match_id END) AS close_matches_won
FROM batting_innings b
JOIN close_matches cm ON cm.match_id = b.match_id
JOIN players p ON p.player_id = b.player_id
GROUP BY p.player_id, p.full_name
ORDER BY avg_runs DESC;"""),

16: ("Intermediate", "Yearly batting trend since 2020 (5+ matches/year)", """
SELECT p.full_name, strftime('%Y', m.match_date) AS year,
       ROUND(AVG(b.runs), 2) AS avg_runs_per_match,
       ROUND(AVG(b.strike_rate), 2) AS avg_strike_rate,
       COUNT(DISTINCT b.match_id) AS matches
FROM batting_innings b
JOIN matches m ON m.match_id = b.match_id
JOIN players p ON p.player_id = b.player_id
WHERE m.match_date >= '2020-01-01'
GROUP BY p.player_id, p.full_name, year
HAVING COUNT(DISTINCT b.match_id) >= 5
ORDER BY p.full_name, year;"""),

17: ("Advanced", "Does winning the toss help?", """
SELECT toss_decision,
       COUNT(*) AS matches,
       SUM(toss_winner_id = winner_id) AS toss_winner_won,
       ROUND(100.0 * SUM(toss_winner_id = winner_id) / COUNT(*), 2) AS win_pct
FROM matches WHERE toss_winner_id IS NOT NULL AND winner_id IS NOT NULL
GROUP BY toss_decision
UNION ALL
SELECT 'overall', COUNT(*), SUM(toss_winner_id = winner_id),
       ROUND(100.0 * SUM(toss_winner_id = winner_id) / COUNT(*), 2)
FROM matches WHERE toss_winner_id IS NOT NULL AND winner_id IS NOT NULL;"""),

18: ("Advanced", "Most economical limited-overs bowlers", """
SELECT p.full_name,
       ROUND(SUM(bi.runs_conceded) / SUM(bi.overs), 2) AS economy_rate,
       SUM(bi.wickets) AS total_wickets,
       COUNT(DISTINCT bi.match_id) AS matches,
       ROUND(AVG(bi.overs), 2) AS avg_overs
FROM bowling_innings bi
JOIN matches m ON m.match_id = bi.match_id
JOIN players p ON p.player_id = bi.player_id
WHERE m.match_format IN ('ODI', 'T20I')
GROUP BY p.player_id, p.full_name
HAVING COUNT(DISTINCT bi.match_id) >= 10 AND AVG(bi.overs) >= 2
ORDER BY economy_rate ASC;"""),

19: ("Advanced", "Most consistent batsmen since 2022", """
SELECT p.full_name, COUNT(*) AS innings,
       ROUND(AVG(b.runs), 2) AS avg_runs,
       ROUND(SQRT(AVG(b.runs * b.runs) - AVG(b.runs) * AVG(b.runs)), 2) AS std_dev_runs
FROM batting_innings b
JOIN matches m ON m.match_id = b.match_id
JOIN players p ON p.player_id = b.player_id
WHERE m.match_date >= '2022-01-01' AND b.balls >= 10
GROUP BY p.player_id, p.full_name
HAVING COUNT(*) >= 5
ORDER BY std_dev_runs ASC;"""),

20: ("Advanced", "Matches and batting average by format (20+ matches)", """
SELECT p.full_name,
       SUM(CASE WHEN cb.match_format='Test' THEN cb.matches END) AS test_matches,
       SUM(CASE WHEN cb.match_format='ODI'  THEN cb.matches END) AS odi_matches,
       SUM(CASE WHEN cb.match_format='T20I' THEN cb.matches END) AS t20_matches,
       MAX(CASE WHEN cb.match_format='Test' THEN cb.average END) AS test_avg,
       MAX(CASE WHEN cb.match_format='ODI'  THEN cb.average END) AS odi_avg,
       MAX(CASE WHEN cb.match_format='T20I' THEN cb.average END) AS t20_avg
FROM career_batting cb JOIN players p USING(player_id)
GROUP BY p.player_id, p.full_name
HAVING SUM(cb.matches) >= 20
ORDER BY p.full_name;"""),

21: ("Advanced", "Weighted all-round performance ranking (top 5 per format)", """
WITH scored AS (
    SELECT p.full_name, cb.match_format,
        (cb.runs * 0.01) + (cb.average * 0.5) + (cb.strike_rate * 0.3) AS batting_pts,
        COALESCE((cw.wickets * 2) + ((50 - cw.average) * 0.5) + ((6 - cw.economy) * 2), 0) AS bowling_pts,
        COALESCE((f.catches * 3) + (f.stumpings * 5), 0) AS fielding_pts
    FROM career_batting cb
    JOIN players p ON p.player_id = cb.player_id
    LEFT JOIN career_bowling cw ON cw.player_id = cb.player_id AND cw.match_format = cb.match_format
    LEFT JOIN fielding_stats f  ON f.player_id  = cb.player_id AND f.match_format  = cb.match_format
), ranked AS (
    SELECT *, batting_pts + bowling_pts + fielding_pts AS total_score,
           RANK() OVER (PARTITION BY match_format ORDER BY batting_pts + bowling_pts + fielding_pts DESC) AS rnk
    FROM scored
)
SELECT match_format, rnk AS rank, full_name, ROUND(batting_pts,1) AS batting_pts,
       ROUND(bowling_pts,1) AS bowling_pts, ROUND(fielding_pts,1) AS fielding_pts, ROUND(total_score,1) AS total_score
FROM ranked WHERE rnk <= 5 ORDER BY match_format, rnk;"""),

22: ("Advanced", "Head-to-head team analysis (5+ matches in last 3 years)", """
WITH h2h AS (
    SELECT m.*, MIN(team1_id, team2_id) AS a, MAX(team1_id, team2_id) AS b,
           CASE WHEN toss_decision = 'bat' THEN toss_winner_id
                ELSE CASE WHEN toss_winner_id = team1_id THEN team2_id ELSE team1_id END END AS bat_first
    FROM matches m
    WHERE match_date >= date('now', '-3 year') AND winner_id IS NOT NULL
)
SELECT ta.team_name AS team_a, tb.team_name AS team_b, COUNT(*) AS matches,
       SUM(winner_id = a) AS wins_a, SUM(winner_id = b) AS wins_b,
       ROUND(AVG(CASE WHEN winner_id = a THEN victory_margin END), 1) AS avg_margin_a,
       ROUND(AVG(CASE WHEN winner_id = b THEN victory_margin END), 1) AS avg_margin_b,
       ROUND(100.0 * SUM(winner_id = a) / COUNT(*), 1) AS win_pct_a,
       ROUND(100.0 * SUM(winner_id = b) / COUNT(*), 1) AS win_pct_b,
       SUM(bat_first = a AND winner_id = a) AS a_wins_batting_first,
       SUM(bat_first <> a AND winner_id = a) AS a_wins_chasing,
       SUM(bat_first = b AND winner_id = b) AS b_wins_batting_first,
       SUM(bat_first <> b AND winner_id = b) AS b_wins_chasing
FROM h2h JOIN teams ta ON ta.team_id = a JOIN teams tb ON tb.team_id = b
GROUP BY a, b HAVING COUNT(*) >= 5 ORDER BY matches DESC;"""),

23: ("Advanced", "Recent form and momentum (last 10 innings)", """
WITH recent AS (
    SELECT b.player_id, b.runs, b.strike_rate,
           ROW_NUMBER() OVER (PARTITION BY b.player_id ORDER BY m.match_date DESC, b.id DESC) AS rn
    FROM batting_innings b JOIN matches m USING(match_id)
), agg AS (
    SELECT player_id,
           AVG(CASE WHEN rn <= 5 THEN runs END) AS avg_last5,
           AVG(runs) AS avg_last10,
           AVG(CASE WHEN rn <= 5 THEN strike_rate END) AS sr_last5,
           AVG(CASE WHEN rn > 5 THEN strike_rate END) AS sr_prev5,
           SUM(runs >= 50) AS scores_50_plus,
           SQRT(AVG(runs * runs) - AVG(runs) * AVG(runs)) AS std_dev
    FROM recent WHERE rn <= 10 GROUP BY player_id HAVING COUNT(*) = 10
)
SELECT p.full_name, ROUND(avg_last5,1) AS avg_last5, ROUND(avg_last10,1) AS avg_last10,
       ROUND(sr_last5 - sr_prev5, 1) AS sr_trend, scores_50_plus,
       ROUND(std_dev,1) AS consistency_std_dev,
       CASE WHEN avg_last5 >= 45 THEN 'Excellent Form'
            WHEN avg_last5 >= 30 THEN 'Good Form'
            WHEN avg_last5 >= 18 THEN 'Average Form' ELSE 'Poor Form' END AS form
FROM agg JOIN players p USING(player_id) ORDER BY avg_last5 DESC;"""),

24: ("Advanced", "Best batting partnerships (consecutive positions, 5+ together)", """
WITH pairs AS (
    SELECT MIN(b1.player_id, b2.player_id) AS pa, MAX(b1.player_id, b2.player_id) AS pb,
           b1.runs + b2.runs AS runs
    FROM batting_innings b1
    JOIN batting_innings b2 ON b2.match_id = b1.match_id AND b2.team_id = b1.team_id
         AND b2.innings_no = b1.innings_no AND b2.batting_position = b1.batting_position + 1
)
SELECT p1.full_name AS player_1, p2.full_name AS player_2, COUNT(*) AS partnerships,
       ROUND(AVG(runs), 1) AS avg_runs, SUM(runs > 50) AS over_50, MAX(runs) AS highest,
       ROUND(100.0 * SUM(runs > 50) / COUNT(*), 1) AS success_rate_pct
FROM pairs JOIN players p1 ON p1.player_id = pa JOIN players p2 ON p2.player_id = pb
GROUP BY pa, pb HAVING COUNT(*) >= 5
ORDER BY success_rate_pct DESC, avg_runs DESC LIMIT 25;"""),

25: ("Advanced", "Quarterly performance evolution & career phase", """
WITH q AS (
    SELECT b.player_id, strftime('%Y', m.match_date) || '-Q' || ((CAST(strftime('%m', m.match_date) AS INTEGER) - 1) / 3 + 1) AS quarter,
           AVG(b.runs) AS avg_runs, AVG(b.strike_rate) AS avg_sr, COUNT(DISTINCT b.match_id) AS n
    FROM batting_innings b JOIN matches m USING(match_id)
    GROUP BY b.player_id, quarter HAVING COUNT(DISTINCT b.match_id) >= 3
), t AS (
    SELECT *, LAG(avg_runs) OVER (PARTITION BY player_id ORDER BY quarter) AS prev_runs,
           ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY quarter) AS rn,
           COUNT(*) OVER (PARTITION BY player_id) AS cnt
    FROM q
), s AS (
    SELECT player_id, MAX(cnt) AS quarters,
           AVG(CASE WHEN rn <= 3 THEN avg_runs END) AS early_avg,
           AVG(CASE WHEN rn > cnt - 3 THEN avg_runs END) AS recent_avg,
           SUM(avg_runs > prev_runs) AS improving_q, SUM(avg_runs < prev_runs) AS declining_q
    FROM t GROUP BY player_id HAVING MAX(cnt) >= 6
)
SELECT p.full_name, quarters, ROUND(early_avg,1) AS early_avg_runs, ROUND(recent_avg,1) AS recent_avg_runs,
       improving_q, declining_q,
       CASE WHEN recent_avg > early_avg * 1.10 THEN 'Career Ascending'
            WHEN recent_avg < early_avg * 0.90 THEN 'Career Declining'
            ELSE 'Career Stable' END AS career_phase
FROM s JOIN players p USING(player_id) ORDER BY recent_avg - early_avg DESC;"""),
}
