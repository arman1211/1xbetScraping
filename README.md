1xBet Sports Data Scraping Project
This project contains a collection of Python scripts designed to scrape sports, leagues, and live match data from the unofficial 1xBet API. The scripts are organized to fetch different types of data and save them into structured JSON files for analysis or use in other applications.

🚀 Getting Started
Follow these steps to set up and run the project on your local machine.

1. Set Up and Activate the Virtual Environment
   It is highly recommended to run this project in a Python virtual environment to manage dependencies and avoid conflicts.

Create the environment (if you haven't already):

python -m venv venv

Activate the environment:

On Windows:

.\venv\Scripts\activate

On macOS / Linux:

source venv/bin/activate

2. Install Dependencies
   Once the virtual environment is active, install the necessary Python libraries from the requirements.txt file.

pip install -r requirements.txt

🌐 API Endpoints & Parameters
This project interacts with several unofficial API endpoints from 1xbet.com.

1. Sport Info API
   URL: https://1xbet.com/service-api/RestCore/api/external/v1/Web/SportInfo

Used in: sports_name.py

Purpose: Fetches a list of all available sports and their names, translated by language.

Key Parameters:

lng: The language code (e.g., en, bn, es).

gr: Group ID (constant 70).

fcountry: Country ID (set to 19).

2. Leagues API
   URL: https://1xbet.com/LineFeed/GetChamps

Used in: all_leagues.py

Purpose: Fetches all leagues (championships) for a given sport ID.

Key Parameters:

sportId: The numerical ID of the sport.

lng: The language code (e.g., en).

country: Country ID (set to 19).

partner: Partner ID (set to 1).

tz: Timezone offset (set to 6).

3. Games API
   URL 1 (All Matches): https://1xbet.com/LineFeed/Get1x2_VZip

URL 2 (Top Games): https://1xbet.com/LineFeed/GetTopGamesStatZip

Used in: dynamic_match_scraper.py, collect_games.py, live_updater.py.

Purpose: Fetches lists of matches, including teams, start times, odds, and other metadata.

Key Parameters:

sports: The numerical ID of the sport.

count: The maximum number of matches to return.

lng: The language code.

mode: Data mode (set to 4).

country: Country ID (set to 19).

getEmpty: Boolean to include matches without available odds.

📜 How to Use the Scripts
The scripts are designed to be run in a specific order to build the necessary data files.

1. sports_name.py
   This is the first script you should run. It fetches the names of all sports in multiple languages and creates the sports_all_languages.json file, which is required by other scripts.

Usage:

python sports_name.py

2. all_leagues.py
   After generating the sports file, run this script to fetch all available leagues for every sport. It uses sports_all_languages.json as input and saves the complete league data to all_leagues.json.

Usage:

python all_leagues.py

3. collect_games.py
   This script fetches a pre-selected list of top upcoming games across various sports. It processes the raw data to make it more usable by converting timestamps to the America/New_York timezone, calculating winning percentages from odds, and parsing extra details. The output is saved to top_games_formatted.json.

Usage:

python collect_games.py

4. dynamic_match_scraper.py
   Use this script when you need all upcoming matches for a single, specific sport. It will prompt you to enter a Sport ID.

Usage:

python dynamic_match_scraper.py

Example: When prompted, enter 1 to fetch all football matches. The output will be saved to football_matches.json.

5. live_updater.py
   This is a continuous script designed to be left running to poll for live game data at regular intervals. It uses config.json for its settings (API URL, polling interval, output file).

Usage:

To fetch all live sports:

python live_updater.py

To fetch live games for a specific sport (e.g., Football, ID 1):

python live_updater.py --sports 1

The script logs its actions to live_updater.log and continuously updates the live_sports_database.json file.
