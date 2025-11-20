from nba_api.stats.endpoints import leaguedashplayerclutch
import pandas as pd

from nba_api.stats.library.http import NBAStatsHTTP

NBAStatsHTTP.HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Connection": "keep-alive",
}

SEASON = "2025-26"

clutch = leaguedashplayerclutch.LeagueDashPlayerClutch(
    season=SEASON,
    season_type_all_star="Regular Season",
    per_mode_detailed="Totals",
    measure_type_detailed_defense="Base",
    clutch_time="Last 5 Minutes",
    ahead_behind="Ahead or Behind",
    point_diff="5",
    plus_minus="Y"
)

df = clutch.get_data_frames()[0]
df.to_csv("clutch_totals_2025_26.csv", index=False)
print("Saved clutch_totals_2025_26.csv")
