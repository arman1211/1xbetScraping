import requests
import json
from datetime import datetime

# FotMob URL for fetching matches by date
# The date format required is YYYYMMDD
API_URL = "https://www.fotmob.com/api/data/matches"


def get_matches_by_date(date_str):
    """
    Fetches all football matches for a specific date from the FotMob API.

    Args:
        date_str (str): The date in 'YYYY-MM-DD' format.

    Returns:
        dict: A dictionary containing the match data, or None if an error occurs.
    """
    try:
        # Validate and format the date string to YYYYMMDD
        dt_object = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt_object.strftime("%Y%m%d")

        # Construct the parameters for the API request
        params = {"date": formatted_date, "timezone": "Asia/Dhaka", "ccode3": "BGD"}

        print(
            f"Fetching data from: https://www.fotmob.com/api/data/matches?date={formatted_date}"
        )

        # Add a comprehensive set of headers to mimic a real browser request
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": f"https://www.fotmob.com/?date={formatted_date}",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }

        # Make the GET request to the API with headers and params
        response = requests.get(API_URL, headers=headers, params=params)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        return data

    except ValueError:
        print("Error: Invalid date format. Please use 'YYYY-MM-DD'.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
        return None
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the response.")
        return None


def save_to_json(data, filename="matches.json"):
    """
    Saves the fetched match data to a JSON file.

    Args:
        data (dict): The match data to save.
        filename (str): The name of the file to save the data to.
    """
    if data:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Successfully saved data to {filename}")
        except IOError as e:
            print(f"Error saving file: {e}")


def main():
    """
    Main function to run the scraper.
    """
    print("Football Match Scraper")
    print("=" * 25)

    # Get date input from the user
    date_input = input(
        "Enter the date for which you want to fetch matches (YYYY-MM-DD): "
    )

    # Fetch the match data
    matches_data = get_matches_by_date(date_input)

    if matches_data:
        # Save the data to a file
        filename = f"matches_{date_input.replace('-', '')}.json"
        save_to_json(matches_data, filename)

        # Optionally, print a summary of leagues found
        if "leagues" in matches_data:
            print("\n--- Summary ---")
            print(
                f"Found {len(matches_data.get('leagues', []))} leagues with matches on this date."
            )
            for league in matches_data.get("leagues", []):
                print(
                    f"- {league.get('name', 'Unnamed League')} ({len(league.get('matches', []))} matches)"
                )
    else:
        print("Could not retrieve match data.")


if __name__ == "__main__":
    main()
