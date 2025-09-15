import requests
import json
import time

# --- Configuration ---
# The file with your 300 sports and their IDs
INPUT_SPORTS_FILE = "sports_all_languages.json"
# The new file where all the leagues will be saved
OUTPUT_LEAGUES_FILE = "all_leagues.json"
# The delay between each API call in seconds to avoid getting blocked
DELAY_BETWEEN_REQUESTS = 1.5

# --- API Details ---
api_url = "https://1xbet.com/LineFeed/GetChamps"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
}

# --- Main Script ---
try:
    with open(INPUT_SPORTS_FILE, "r", encoding="utf-8") as f:
        sports_list = json.load(f)
except FileNotFoundError:
    print(
        f"❌ Error: Input file '{INPUT_SPORTS_FILE}' not found. Please make sure it's in the same directory."
    )
    exit()

# This dictionary will store all the final data
# The key will be the sport ID, the value will be the list of its leagues
all_leagues_data = {}
total_sports = len(sports_list)

print(
    f"🚀 Starting to fetch leagues for {total_sports} sports. This will take a while..."
)

# Loop through each sport from your file
for index, sport in enumerate(sports_list):
    sport_id = sport.get("sports_id")
    sport_name = sport.get("name_eng", "Unknown Sport")

    # Print progress
    print(
        f"({index + 1}/{total_sports}) Fetching leagues for: {sport_name} (ID: {sport_id})..."
    )

    params = {"sportId": sport_id, "lng": "en", "country": 19, "partner": 1, "tz": 6}

    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()
        # The list of leagues is in the 'Value' key
        leagues = data.get("Value", [])

        if leagues:
            # Store the found leagues using the sport_id as the key
            all_leagues_data[sport_id] = leagues
            print(f"  ✅ Found {len(leagues)} leagues.")
        else:
            print(f"  🟡 No leagues found for {sport_name}.")
            all_leagues_data[sport_id] = []  # Store an empty list

    except requests.exceptions.HTTPError as e:
        print(f"  ❌ HTTP Error for sport ID {sport_id}: {e.response.status_code}")
    except Exception as e:
        print(f"  ❌ An unexpected error occurred for sport ID {sport_id}: {e}")

    # --- CRUCIAL: Wait before the next request ---
    print(f"  💤 Waiting for {DELAY_BETWEEN_REQUESTS} seconds...")
    time.sleep(DELAY_BETWEEN_REQUESTS)

# After the loop is finished, save everything to one file
print(f"\n💾 Saving all collected leagues to '{OUTPUT_LEAGUES_FILE}'...")
with open(OUTPUT_LEAGUES_FILE, "w", encoding="utf-8") as f:
    json.dump(all_leagues_data, f, indent=4, ensure_ascii=False)

print("🎉 All done! Your file with all the leagues is ready.")
