import requests
import json
from datetime import datetime, timezone
import time
import argparse
import sys

# --- Configuration ---
API_URL = "https://8unx689.com/api/v3/user/line/list"
# Headers to mimic a real browser request
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'Referer': 'https://8unx689.com/',
}

# --- Main Functions ---

def fetch_data(mode: str):
    """Fetches match data from the API based on the selected mode (live or sportsbook)."""
    if mode == 'live':
        type_param = '2'
        print("🚀 Fetching LIVE data from the API...")
    else:
        type_param = '1'
        print("🚀 Fetching SPORTSBOOK data from the API...")

    params = {
        't[]': type_param,
        'ss': 'all',
        'l': '100',
        'ltr': '0'
    }
    
    try:
        response = requests.get(API_URL, params=params, headers=HEADERS)
        response.raise_for_status()
        print("✅ Data fetched successfully.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred during the API request: {e}")
        return None

def structure_match_data(raw_data):
    """Parses the deeply nested raw JSON and restructures it into a clean, flat list of matches."""
    if not raw_data or 'lines_hierarchy' not in raw_data:
        return []

    print("⚙️  Processing and restructuring the data...")
    structured_matches = []

    for sport_group in raw_data.get('lines_hierarchy', []):
        # Determine the match type from the parent object
        match_type = sport_group.get("line_type_title", "UNKNOWN") 
        
        for sport in sport_group.get('line_category_dto_collection', []):
            for region in sport.get('line_supercategory_dto_collection', []):
                for league in region.get('line_subcategory_dto_collection', []):
                    for line in league.get('line_dto_collection', []):
                        match_info = line.get('match', {})
                        if not match_info:
                            continue

                        # Convert Unix timestamp to a human-readable UTC string
                        start_time_utc = datetime.fromtimestamp(
                            match_info.get('begin_at', 0), tz=timezone.utc
                        ).isoformat() if match_info.get('begin_at') else None

                        # Simplify the live statistics object
                        live_stats = match_info.get('stat', {})
                        live_details = {
                            "status": live_stats.get('status'),
                            "current_score": match_info.get('score'),
                            "current_period": match_info.get('set_number'),
                            "match_time_minutes": live_stats.get('time'),
                            "period_scores": live_stats.get('segment_scores')
                        }

                        # Find the main "Winner" (1x2) betting odds
                        main_odds = {}
                        for outcome in line.get('outcomes', []):
                            if outcome.get('group_alias') == '1x2':
                                alias = outcome.get('alias')
                                odd = outcome.get('odd')
                                if odd: # Ensure odd value exists
                                    try:
                                        if alias == '1':
                                            main_odds['team1_win'] = float(odd)
                                        elif alias == 'x':
                                            main_odds['draw'] = float(odd)
                                        elif alias == '2':
                                            main_odds['team2_win'] = float(odd)
                                    except (ValueError, TypeError):
                                        continue # Skip if odd is not a valid number
                        
                        livestream_url = None
                        for widget in match_info.get('widgets', []):
                            if widget.get('name') == 'LiveStreamWidget':
                                livestream_url = widget.get('url')
                                break
                        
                        match_object = {
                            "match_id": match_info.get('id'),
                            "match_type": match_type,
                            "sport_name": sport.get('title'),
                            "region": region.get('title'),
                            "league_name": league.get('title'),
                            "team1": match_info.get('team1', {}).get('title'),
                            "team2": match_info.get('team2', {}).get('title'),
                            "start_time_utc": start_time_utc,
                            "live_details": live_details if match_type == "LIVE" else None,
                            "main_odds": main_odds or None,
                            "livestream_url": livestream_url
                        }
                        structured_matches.append(match_object)

    print(f"👍 Found and processed {len(structured_matches)} matches.")
    return structured_matches

def save_data_to_file(data, filename):
    """Saves the structured data to a JSON file."""
    print(f"💾 Saving structured data to '{filename}'...")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("🎉 Success! Your file is ready.")
    except IOError as e:
        print(f"❌ Could not write to file '{filename}': {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape live or pre-match (sportsbook) data.",
        epilog="Example: python scraper.py live"
    )
    parser.add_argument(
        'mode', 
        choices=['live', 'sportsbook'], 
        help="The mode to run the scraper in: 'live' for continuous fetching or 'sportsbook' for a one-time fetch."
    )
    args = parser.parse_args()

    if args.mode == 'live':
        output_filename = "live_matches.json"
        while True:
            try:
                raw_data = fetch_data(mode='live')
                if raw_data:
                    clean_data = structure_match_data(raw_data)
                    if clean_data:
                        save_data_to_file(clean_data, output_filename)
                
                print("\n---\n")
                print("🔄 Waiting for 10 seconds before the next refresh... (Press CTRL+C to stop)")
                time.sleep(10)
            except KeyboardInterrupt:
                print("\n🛑 User stopped the script. Exiting.")
                sys.exit(0)
            except Exception as e:
                print(f"An unexpected error occurred in the main loop: {e}")
                print("Retrying in 10 seconds...")
                time.sleep(10)

    elif args.mode == 'sportsbook':
        output_filename = "sportsbook_matches.json"
        raw_data = fetch_data(mode='sportsbook')
        if raw_data:
            clean_data = structure_match_data(raw_data)
            if clean_data:
                save_data_to_file(clean_data, output_filename)

