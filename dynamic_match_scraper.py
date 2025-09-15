import requests
import json
from datetime import datetime
import pytz
import sys

# --- Configuration ---
API_URL = "https://1xbet.com/LineFeed/Get1x2_VZip"
SPORTS_INFO_FILE = 'sports_all_languages.json'
TARGET_TIMEZONE = 'America/New_York' 

def load_sports_data():
    """Loads the sports reference file and creates a quick-lookup map."""
    try:
        with open(SPORTS_INFO_FILE, 'r', encoding='utf-8') as f:
            sports_list = json.load(f)
        return {sport['sports_id']: sport for sport in sports_list}
    except FileNotFoundError:
        print(f"❌ CRITICAL ERROR: The reference file '{SPORTS_INFO_FILE}' was not found.")
        print("Please make sure it's in the same directory as this script.")
        sys.exit()
    except json.JSONDecodeError:
        print(f"❌ CRITICAL ERROR: Could not parse '{SPORTS_INFO_FILE}'. Make sure it is a valid JSON file.")
        sys.exit()

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

# --- Main Execution ---
if __name__ == "__main__":
    sports_map = load_sports_data()
    

    try:
        sport_id_input = int(input("▶️ Please enter the Sports ID to fetch (e.g., 1 for Football): "))
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        sys.exit()

    sport_info = sports_map.get(sport_id_input)
    if not sport_info:
        print(f"❌ Error: Sport ID '{sport_id_input}' not found in '{SPORTS_INFO_FILE}'.")
        sys.exit()

    sport_name = sport_info.get('name_eng', f'sport_{sport_id_input}')
    output_filename = f"{sport_name.lower().replace(' ', '_')}_matches.json"
    
    print(f"👍 Sport found: {sport_name}. Data will be saved to '{output_filename}'")

    # 3. Set up API parameters dynamically
    params = {
        'sports': sport_id_input,
        'count': 50,
        'lng': 'en',
        'tz': 6,
        'mode': 4,
        'country': 19,
        'getEmpty': True,
        'gr': 70
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # 4. Fetch data from the API
    print(f"🚀 Fetching match data for {sport_name}...")
    try:
        response = requests.get(API_URL, params=params, headers=headers)
        response.raise_for_status()
        raw_matches = response.json().get('Value', [])
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        sys.exit()

    print(f"✅ Data fetched. Now organizing {len(raw_matches)} matches...")

    # 5. Process and format each match
    formatted_matches = []
    tz = pytz.timezone(TARGET_TIMEZONE)

    for match in raw_matches:
        team1 = match.get('O1')
        team2 = match.get('O2')
        league_name = match.get('L')
        match_info_obj = match.get('MIO', {})

        start_timestamp = match.get('S')
        dt_utc = datetime.fromtimestamp(start_timestamp, tz=pytz.utc)
        dt_target = dt_utc.astimezone(tz)
        date_str = dt_target.strftime('%m-%d-%Y')
        time_str = dt_target.strftime('%I:%M %p')

        time_for_slug = time_str.replace(':', '').replace(' ', '_')
        slug_parts = [
            str(team1).replace(' ', '_'), 'vs', str(team2).replace(' ', '_'),
            str(sport_name).replace(' ', '_'), date_str, time_for_slug
        ]
        slug = '_'.join(filter(None, slug_parts)).lower().replace('-', '_')

        odds = {}
        for event in match.get('E', []):
            if event.get('G') == 1:
                if event.get('T') == 1: odds['team1_win'] = event.get('C')
                elif event.get('T') == 2: odds['draw'] = event.get('C')
                elif event.get('T') == 3: odds['team2_win'] = event.get('C')

        win_prob_raw = match.get('WP')
        win_probability = None
        if win_prob_raw:
            win_probability = {
                "team1_percent": win_prob_raw.get('P1', 0) * 100,
                "team2_percent": win_prob_raw.get('P2', 0) * 100,
                "draw_percent": win_prob_raw.get('PX', 0) * 100
            }

        misc_details = parse_misc_info(match.get('MIS'))
        venue = match_info_obj.get('Loc') or misc_details.pop('venue', "N/A")
        
        formatted_match = {
            "slug": slug,
            "league": league_name,
            "match_format": match_info_obj.get('MaF'),
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

    # 6. Save the final data to the dynamically named file
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(formatted_matches, f, indent=4, ensure_ascii=False)

    print(f"\n🎉 Success! Organized data for {len(formatted_matches)} matches saved to '{output_filename}'.")
