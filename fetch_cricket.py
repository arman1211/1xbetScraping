import requests
import json
from datetime import datetime
import pytz

# --- Configuration ---
# API_URL = "https://1xbet.com/LineFeed/Get1x2_VZip"
API_URL = "https://tepowue7.xyz/service-api/LineFeed/Get1x2_VZip"
OUTPUT_FILE = "cricket_matches.json"
TARGET_TIMEZONE = 'America/New_York' # For US standard time

# API parameters
params = {
    'sports': 66,       # 66 is the ID for Cricket
    'count': 50,        # Number of matches to fetch
    'lng': 'en',
    'tz': 6,            # Your local timezone for the request
    'mode': 4,
    'country': 19,
    'getEmpty': True,
    'gr': 70
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
}

def parse_misc_info(misc_array):
    """Converts the MIS array into a readable dictionary."""
    MIS_KEY_MAP = {
        1: "round_stage", 2: "venue", 3: "match_format_alt", 9: "temperature_celsius", 
        11: "country", 21: "weather_condition", 27: "humidity_percent", 
        25: "pressure_mmhg", 35: "precipitation_percent"
    }
    details = {}
    if misc_array:
        for item in misc_array:
            key = MIS_KEY_MAP.get(item.get('K'))
            if key:
                details[key] = item.get('V')
    return details

# --- Main Script ---
print("🚀 Fetching cricket match data...")

try:
    response = requests.get(API_URL, params=params, headers=headers)
    response.raise_for_status()
    raw_matches = response.json().get('Value', [])
except Exception as e:
    print(f"❌ Failed to fetch data: {e}")
    exit()

print(f"✅ Data fetched. Now organizing {len(raw_matches)} matches...")

# Process and format each match
formatted_matches = []
tz = pytz.timezone(TARGET_TIMEZONE)

for match in raw_matches:
    # Main match info is often in the MIO object
    match_info_obj = match.get('MIO', {})

    # Extract team and league info
    team1 = match.get('O1')
    team2 = match.get('O2')
    league_name = match.get('L')

    # Convert timestamp to US timezone
    start_timestamp = match.get('S')
    dt_utc = datetime.fromtimestamp(start_timestamp, tz=pytz.utc)
    dt_target = dt_utc.astimezone(tz)
    date_str = dt_target.strftime('%m-%d-%Y')
    time_str = dt_target.strftime('%I:%M %p')

    # Extract main odds (Win1/Draw/Win2)
    odds = {}
    for event in match.get('E', []):
        if event.get('G') == 1:  # Market Group 1 is for match result
            if event.get('T') == 1:
                odds['team1_win'] = event.get('C')
            elif event.get('T') == 2:
                odds['draw'] = event.get('C')
            elif event.get('T') == 3:
                odds['team2_win'] = event.get('C')

    # Use the pre-calculated Win Probability if available
    win_prob_raw = match.get('WP')
    win_probability = None
    if win_prob_raw:
        win_probability = {
            "team1_percent": win_prob_raw.get('P1', 0) * 100,
            "team2_percent": win_prob_raw.get('P2', 0) * 100,
            "draw_percent": win_prob_raw.get('PX', 0) * 100
        }

    # Parse details and venue
    misc_details = parse_misc_info(match.get('MIS'))
    venue = match_info_obj.get('Loc') or misc_details.pop('venue', "N/A")
    match_format = match_info_obj.get('MaF')
    
    # Combine all info into a clean structure
    formatted_match = {
        "league": league_name,
        "match_format": match_format,
        "match_description": match.get('DI') or match_info_obj.get('TSt'),
        "team1": team1,
        "team2": team2,
        "date_us": date_str,
        "time_us": time_str,
        "venue": venue,
        "odds": odds or None,
        "win_probability": win_probability,
        "details": misc_details or None
    }
    formatted_matches.append(formatted_match)

# Save the final organized data to a file
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(formatted_matches, f, indent=4, ensure_ascii=False)

print(f"\n🎉 Success! Organized data for {len(formatted_matches)} matches saved to '{OUTPUT_FILE}'.")