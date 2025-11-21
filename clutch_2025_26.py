import requests
import pandas as pd
from datetime import datetime

SEASON = "2025-26"
CLUTCH_MAX_SCORE_DIFF = 5
CLUTCH_TIME_SECONDS = 5 * 60  # 5 minutes

# ----------------------------------------------------------
# Helper: Load full NBA schedule from CDN
# ----------------------------------------------------------
def load_schedule():
    print("🔄 Loading NBA 2025-26 schedule...")

    url = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_2025.json"
    r = requests.get(url, timeout=30)
    data = r.json()

    game_ids = []

    # Iterate through game dates
    for item in data["leagueSchedule"]["gameDates"]:
        # Each item contains a list of games; no seasonYear field exists
        for game in item["games"]:
            game_ids.append(game["gameId"])

    print(f"✔ Loaded {len(game_ids)} games")
    return game_ids



# ----------------------------------------------------------
# Helper: Convert time "MM:SS" to total seconds
# ----------------------------------------------------------
def to_seconds(timestr):
    if not timestr or ":" not in timestr:
        return None
    m, s = timestr.split(":")
    return int(m) * 60 + int(s)


# ----------------------------------------------------------
# Extract clutch plays for a single game
# ----------------------------------------------------------
def extract_clutch_for_game(game_id):
    pbp_url = f"https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{game_id}.json"

    try:
        data = requests.get(pbp_url, timeout=30).json()
    except Exception:
        return []  # skip failed game

    actions = data.get("game", {}).get("actions", [])
    if not actions:
        return []

    clutch_rows = []

    for play in actions:
        period = play.get("period", 0)
        clock = play.get("clock", None)
        home_score = play.get("homeScore")
        away_score = play.get("awayScore")
        player_id = play.get("personId", None)

        if not clock or home_score is None or away_score is None:
            continue

        # Only Q4 or OT
        if period < 4:
            continue

        # Score differential filter
        diff = abs(home_score - away_score)
        if diff > CLUTCH_MAX_SCORE_DIFF:
            continue

        # Time remaining in period
        remaining = to_seconds(clock)
        if remaining is None or remaining > CLUTCH_TIME_SECONDS:
            continue

        # Valid clutch play
        clutch_rows.append(play)

    return clutch_rows


# ----------------------------------------------------------
# Accumulate clutch stats across season
# ----------------------------------------------------------
def accumulate_stats(clutch_plays):
    rows = []

    for play in clutch_plays:
        player_id = play.get("personId", None)
        if not player_id:
            continue

        action_type = play.get("actionType", "")
        shot_result = play.get("shotResult", "")
        points = play.get("scoreValue", 0)
        team_id = play.get("teamId", None)

        rows.append({
            "playerId": player_id,
            "teamId": team_id,
            "actionType": action_type,
            "shotResult": shot_result,
            "points": points
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Totals like nba.com (simple aggregation)
    summary = df.groupby("playerId").agg(
        FGA=("shotResult", "count"),
        FGM=("shotResult", lambda s: (s == "Made").sum()),
        PTS=("points", "sum"),
    ).reset_index()

    return summary


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------
def main():
    print(f"🔍 Loading NBA {SEASON} schedule...")
    game_ids = load_schedule()
    print(f"Found {len(game_ids)} completed games.")

    all_clutch_plays = []

    for gid in game_ids:
        plays = extract_clutch_for_game(gid)
        all_clutch_plays.extend(plays)

    print(f"Total clutch plays found: {len(all_clutch_plays)}")

    df = accumulate_stats(all_clutch_plays)

    # Save
    out_path = "clutch_totals_2025_26.csv"
    df.to_csv(out_path, index=False)
    print(f"✅ Saved {out_path}")


if __name__ == "__main__":
    main()
