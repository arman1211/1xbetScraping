import requests
import json
from datetime import datetime
import pytz  # For timezone conversion

# --- Configuration ---
# The number of top games you want to fetch
GAME_LIMIT = 5000
# The American timezone for date/time conversion (e.g., 'America/New_York' for EST/EDT)
TARGET_TIMEZONE = "America/New_York"
# The output filename
OUTPUT_FILE = "top_games_formatted.json"


def calculate_percentages(odds_data):
    """Calculates implied winning percentages from odds, normalized to 100%."""
    if not odds_data or len(odds_data) != 3:
        return None, None, None

    try:
        odds1 = float(odds_data["team1_win"])
        odds_draw = float(odds_data["draw"])
        odds2 = float(odds_data["team2_win"])

        p1 = 1 / odds1
        p_draw = 1 / odds_draw
        p2 = 1 / odds2

        # The sum of raw probabilities is > 1 due to the bookmaker's margin.
        # We normalize it to get a clearer picture of relative chances.
        total_probability = p1 + p_draw + p2

        p1_normalized = round((p1 / total_probability) * 100, 2)
        p_draw_normalized = round((p_draw / total_probability) * 100, 2)
        p2_normalized = round((p2 / total_probability) * 100, 2)

        return p1_normalized, p_draw_normalized, p2_normalized

    except (ValueError, ZeroDivisionError):
        return None, None, None


def parse_misc_info(misc_array):
    """Converts the MIS array into a readable dictionary."""
    # Mapping of known 'K' keys to human-readable names
    MIS_KEY_MAP = {
        1: "round",
        2: "venue",
        9: "temperature_celsius",
        21: "weather_condition",
        22: "wind_direction_deg",
        23: "wind_speed_ms",
        24: "wind_description",
        25: "pressure_mmhg",
        26: "pressure_unit",
        27: "humidity_percent",
        28: "humidity_unit",
        35: "precipitation_percent",
        36: "precipitation_unit",
    }
    details = {}
    if misc_array:
        for item in misc_array:
            key = MIS_KEY_MAP.get(item.get("K"))
            if key:
                details[key] = item.get("V")
    return details


# --- Main Script ---
print(f"🚀 Fetching {GAME_LIMIT} top games...")

# 1. Fetch the data from the API
api_url = "https://1xbet.com/LineFeed/GetTopGamesStatZip"
params = {"lng": "en", "gr": 70, "limit": GAME_LIMIT}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(api_url, params=params, headers=headers)
    response.raise_for_status()
    raw_games = response.json().get("Value", [])
except Exception as e:
    print(f"❌ Failed to fetch data: {e}")
    exit()

print(f"✅ Data fetched. Now formatting {len(raw_games)} games...")

# 2. Process and format each game
formatted_games = []
tz = pytz.timezone(TARGET_TIMEZONE)

for game in raw_games:
    # Basic Info
    team1 = game.get("O1")
    team2 = game.get("O2")
    league_name = game.get("L")
    sport_name = game.get("SN")

    # Time Conversion
    start_timestamp = game.get("S")
    dt_utc = datetime.fromtimestamp(start_timestamp, tz=pytz.utc)
    dt_target = dt_utc.astimezone(tz)
    date_str = dt_target.strftime("%m-%d-%Y")
    time_str = dt_target.strftime("%I:%M %p")  # e.g., 03:30 PM

    # Odds Parsing
    odds = {}
    for event in game.get("E", []):
        if event.get("G") == 1:  # Market Group 1 is for '1X2' match result
            if event.get("T") == 1:
                odds["team1_win"] = event.get("C")
            elif event.get("T") == 2:
                odds["draw"] = event.get("C")
            elif event.get("T") == 3:
                odds["team2_win"] = event.get("C")

    # Calculate Percentages
    team1_win_pct, draw_pct, team2_win_pct = calculate_percentages(odds)

    # Miscellaneous Info Parsing
    misc_details = parse_misc_info(game.get("MIS"))
    venue = misc_details.pop(
        "venue", None
    )  # Get venue and remove it from the main details dict

    # Slug Generation
    slug_parts = [
        str(team1).replace(" ", "_"),
        "vs",
        str(team2).replace(" ", "_"),
        str(sport_name).replace(" ", "_"),
        date_str,
        time_str.replace(" ", "_"),
    ]
    slug = "_".join(slug_parts).lower().replace("-", "_")

    # Assemble the final formatted object
    formatted_game = {
        "slug": slug,
        "sport": sport_name,
        "league": league_name,
        "team1": team1,
        "team2": team2,
        "date_us": date_str,
        "time_us": time_str,
        "venue": venue,
        "odds": odds or None,
        "winning_percentage": (
            {"team1": team1_win_pct, "draw": draw_pct, "team2": team2_win_pct}
            if team1_win_pct is not None
            else None
        ),
        "details": misc_details or None,
    }
    formatted_games.append(formatted_game)

# 3. Save the formatted data to a new JSON file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(formatted_games, f, indent=4, ensure_ascii=False)

print(
    f"\n🎉 Success! Formatted data for {len(formatted_games)} games saved to '{OUTPUT_FILE}'."
)
