import requests
import json
import time
import sys
import logging
import argparse
from datetime import datetime
import pytz


def setup_logging(log_file):
    """Sets up logging to both console and a file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )


def load_config():
    """Loads settings from config.json."""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("❌ CRITICAL: config.json not found. Please create it.")
        sys.exit()
    except json.JSONDecodeError:
        logging.error("❌ CRITICAL: config.json is not a valid JSON file.")
        sys.exit()


def parse_live_score(score_obj):
    """Parses the complex 'SC' object into a simple, readable format."""
    # This function remains the same as before...
    if not score_obj:
        return None
    live_score = {
        "status": score_obj.get("SLS", "Not available"),
        "current_period": score_obj.get("CPS"),
        "team1_score": "N/A",
        "team2_score": "N/A",
    }
    for score_part in score_obj.get("S", []):
        if score_part.get("Key") == "Team1Scores":
            live_score["team1_score"] = score_part.get("Value")
        elif score_part.get("Key") == "Team2Scores":
            live_score["team2_score"] = score_part.get("Value")
    if score_obj.get("SS") and score_obj.get("PS"):
        current_game_score = score_obj.get("SS", {})
        live_score["team1_score"] = (
            f"Sets: {score_obj.get('FS', {}).get('S1', 0)}, Games: {score_obj.get('PS', [{}])[0].get('Value', {}).get('S1', 0)}, Points: {current_game_score.get('S1', 0)}"
        )
        live_score["team2_score"] = (
            f"Sets: {score_obj.get('FS', {}).get('S2', 0)}, Games: {score_obj.get('PS', [{}])[0].get('Value', {}).get('S2', 0)}, Points: {current_game_score.get('S2', 0)}"
        )
    return live_score


def calculate_win_probability_from_odds(odds_data):
    """Calculates implied winning percentages from odds."""
    # This function remains the same as before...
    if not odds_data:
        return None
    try:
        p1 = (
            1 / float(odds_data.get("team1_win", 0))
            if odds_data.get("team1_win")
            else 0
        )
        p_draw = 1 / float(odds_data.get("draw", 0)) if odds_data.get("draw") else 0
        p2 = (
            1 / float(odds_data.get("team2_win", 0))
            if odds_data.get("team2_win")
            else 0
        )
        total_probability = p1 + p_draw + p2
        if total_probability == 0:
            return None
        return {
            "team1_percent": round((p1 / total_probability) * 100, 2),
            "draw_percent": (
                round((p_draw / total_probability) * 100, 2) if p_draw > 0 else None
            ),
            "team2_percent": round((p2 / total_probability) * 100, 2),
        }
    except (ValueError, ZeroDivisionError):
        return None


# --- Main Execution ---
if __name__ == "__main__":
    config = load_config()
    setup_logging(config["log_file"])

    # --- 1. Set up Command-Line Argument Parsing ---
    parser = argparse.ArgumentParser(description="Fetch live sports data.")
    parser.add_argument(
        "--sports", type=int, help="Optional: A specific sport ID to filter by."
    )
    args = parser.parse_args()

    logging.info("🚀 Starting the robust live data updater script.")

    tz = pytz.timezone(config["target_timezone"])

    while True:
        try:
            if args.sports:
                params = {
                    "sports": args.sports,
                    "count": 50,
                    "lng": "en",
                    "mode": 4,
                    "country": 19,
                }
                logging.info(f"Fetching live data for Sport ID: {args.sports}...")

            else:
                params = {"count": 50, "lng": "en", "mode": 4, "country": 19}
                logging.info("Fetching live data for all sports...")

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            response = requests.get(config["api_url"], params=params, headers=headers)
            response.raise_for_status()
            live_games = response.json().get("Value", [])

            if not live_games:
                logging.warning("No live games found at the moment.")
            else:
                logging.info(f"Found {len(live_games)} live games. Processing...")

            # --- 3. The rest of the processing logic is the same ---
            formatted_games = []
            for game in live_games:
                odds = {}
                for event in game.get("E", []):
                    if event.get("G") == 1:
                        if event.get("T") == 1:
                            odds["team1_win"] = event.get("C")
                        elif event.get("T") == 2:
                            odds["draw"] = event.get("C")
                        elif event.get("T") == 3:
                            odds["team2_win"] = event.get("C")

                win_prob_raw = game.get("WP")
                win_probability = None
                if win_prob_raw:
                    win_probability = {
                        "team1_percent": win_prob_raw.get("P1", 0) * 100,
                        "team2_percent": win_prob_raw.get("P2", 0) * 100,
                        "draw_percent": (
                            win_prob_raw.get("PX", 0) * 100
                            if "PX" in win_prob_raw
                            else None
                        ),
                    }
                else:
                    win_probability = calculate_win_probability_from_odds(odds)

                formatted_game = {
                    "game_id": game.get("I"),
                    "sport": game.get("SN"),
                    "league": game.get("L"),
                    "team1": game.get("O1"),
                    "team2": game.get("O2"),
                    "live_score": parse_live_score(game.get("SC")),
                    "odds": odds or None,
                    "win_probability": win_probability,
                }
                formatted_games.append(formatted_game)

            output_data = {
                "updated_at": datetime.now(tz).isoformat(),
                "data": formatted_games,
            }

            with open(config["database_file"], "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=4, ensure_ascii=False)

            logging.info(f"Successfully updated '{config['database_file']}'.")

        except KeyboardInterrupt:
            logging.info("🛑 Script stopped by user.")
            break
        except requests.exceptions.HTTPError as e:
            logging.error(
                f"HTTP Error: {e.response.status_code}. Url: {e.request.url} The API might be temporarily down or blocking."
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}", exc_info=True)

        logging.info(f"Waiting for {config['poll_interval_seconds']} seconds...")
        time.sleep(config["poll_interval_seconds"])
