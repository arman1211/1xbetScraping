import requests
import json
from datetime import datetime
import pytz
import time
import os

# --- Configuration ---
API_URL = "https://1xbet.com/LiveFeed/BestGamesExtVZip"
OUTPUT_DB_FILE = "live_sports_database.json"
POLL_INTERVAL_SECONDS = 15 # Time to wait between updates
TARGET_TIMEZONE = 'America/New_York'

# API parameters - Fetches top live games across ALL sports
params = {
    'count': 50,
    'lng': 'en',
    'mode': 4,
    'country': 19
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def calculate_win_probability_from_odds(odds_data):
    """
    Calculates implied winning percentages from odds.
    Handles both 2-way (e.g., Tennis) and 3-way (e.g., Football) markets.
    """
    if not odds_data:
        return None

    try:
        p1 = 1 / float(odds_data.get('team1_win', 0)) if odds_data.get('team1_win') else 0
        p_draw = 1 / float(odds_data.get('draw', 0)) if odds_data.get('draw') else 0
        p2 = 1 / float(odds_data.get('team2_win', 0)) if odds_data.get('team2_win') else 0

        total_probability = p1 + p_draw + p2
        if total_probability == 0:
            return None

        return {
            "team1_percent": round((p1 / total_probability) * 100, 2),
            "draw_percent": round((p_draw / total_probability) * 100, 2) if p_draw > 0 else None,
            "team2_percent": round((p2 / total_probability) * 100, 2)
        }
    except (ValueError, ZeroDivisionError):
        return None


def parse_live_score(score_obj):
    """
    Parses the complex 'SC' object into a simple, readable format.
    Handles different structures for different sports (e.g., Cricket vs. Tennis).
    """
    if not score_obj:
        return None

    # --- Standard Score Parsing (Football, Cricket, etc.) ---
    live_score = {
        "status": score_obj.get("SLS", "Not available"),
        "current_period": score_obj.get("CPS"),
        "team1_score": "N/A",
        "team2_score": "N/A"
    }
    for score_part in score_obj.get("S", []):
        if score_part.get("Key") == "Team1Scores":
            live_score["team1_score"] = score_part.get("Value")
        elif score_part.get("Key") == "Team2Scores":
            live_score["team2_score"] = score_part.get("Value")

    # --- Tennis Score Parsing ---
    if score_obj.get("SS") and score_obj.get("PS"):
        current_game_score = score_obj.get("SS", {})
        live_score["team1_score"] = f"Sets: {score_obj.get('FS', {}).get('S1', 0)}, Games: {score_obj.get('PS', [{}])[0].get('Value', {}).get('S1', 0)}, Points: {current_game_score.get('S1', 0)}"
        live_score["team2_score"] = f"Sets: {score_obj.get('FS', {}).get('S2', 0)}, Games: {score_obj.get('PS', [{}])[0].get('Value', {}).get('S2', 0)}, Points: {current_game_score.get('S2', 0)}"

    return live_score

# --- Main Polling Loop ---
if __name__ == "__main__":
    print("🚀 Starting the live data updater script.")
    print(f"   - Will update '{OUTPUT_DB_FILE}' with odds and probabilities every {POLL_INTERVAL_SECONDS} seconds.")
    print("   - Press Ctrl+C to stop the script.")

    tz = pytz.timezone(TARGET_TIMEZONE) # <-- MOVED THIS LINE HERE

    while True:
        try:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching live data...")
            response = requests.get(API_URL, params=params, headers=headers)
            response.raise_for_status()
            live_games = response.json().get('Value', [])

            if not live_games:
                print("   - No live games found at the moment.")
                # Create the structured object even when there's no data
                output_data = {
                    "updated_at": datetime.now(tz).isoformat(),
                    "data": []
                }
                with open(OUTPUT_DB_FILE, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)
                
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            print(f"   - Found {len(live_games)} live games. Processing...")
            
            formatted_games = []
            # tz = pytz.timezone(TARGET_TIMEZONE) <-- REMOVED FROM HERE
            for game in live_games:
                # --- Odds Parsing ---
                odds = {}
                for event in game.get('E', []):
                    if event.get('G') == 1: # Market Group 1 is the main result
                        if event.get('T') == 1: odds['team1_win'] = event.get('C')
                        elif event.get('T') == 2: odds['draw'] = event.get('C')
                        elif event.get('T') == 3: odds['team2_win'] = event.get('C')
                
                # --- Win Probability Logic ---
                win_prob_raw = game.get('WP')
                win_probability = None
                if win_prob_raw:
                    win_probability = {
                        "team1_percent": win_prob_raw.get('P1', 0) * 100,
                        "team2_percent": win_prob_raw.get('P2', 0) * 100,
                        "draw_percent": win_prob_raw.get('PX', 0) * 100 if 'PX' in win_prob_raw else None
                    }
                else:
                    # If WP object is missing, calculate from odds
                    win_probability = calculate_win_probability_from_odds(odds)

                # --- Assemble Final Object ---
                formatted_game = {
                    "game_id": game.get('I'),
                    "sport": game.get('SN'),
                    "league": game.get('L'),
                    "team1": game.get('O1'),
                    "team2": game.get('O2'),
                    "live_score": parse_live_score(game.get('SC')),
                    "odds": odds or None,
                    "win_probability": win_probability
                }
                formatted_games.append(formatted_game)
            
            # Create the final object with the timestamp and data
            output_data = {
                "updated_at": datetime.now(tz).isoformat(),
                "data": formatted_games
            }

            # Update the local JSON database
            with open(OUTPUT_DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4, ensure_ascii=False)
            
            print(f"   - Successfully updated '{OUTPUT_DB_FILE}'.")
            
            # Wait for the next interval
            print(f"   - Waiting for {POLL_INTERVAL_SECONDS} seconds...")
            time.sleep(POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\n🛑 Script stopped by user.")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            print(f"   - Retrying in {POLL_INTERVAL_SECONDS} seconds...")
            time.sleep(POLL_INTERVAL_SECONDS)



