import requests
import json
import time

# 1. Define the languages and their corresponding key in the final JSON
languages_to_fetch = {
    "en": "name_eng",
    "bn": "name_bangla",
    "fr": "name_france",
    "es": "name_spanish",
    "hi": "name_hindi",
}

# Base URL, the language code will be added in the loop
base_url = "https://tepowue7.xyz/service-api/RestCore/api/external/v1/Web/SportInfo?ref=1&gr=70&fcountry=19&lng="
output_filename = "sports_all_languages.json"

# This dictionary will store the merged data.
# We use the original sport ID from the API as the key to ensure we match the correct sport.
consolidated_sports = {}

print("🚀 Starting the multi-language sport scraper...")

try:
    # 2. Loop through each language to fetch its data
    for lang_code, field_name in languages_to_fetch.items():
        api_url = base_url + lang_code
        print(f"Fetching data for language: '{lang_code}'...")

        response = requests.get(api_url)
        response.raise_for_status()  # Check for request errors
        sports_data = response.json()

        # 3. Process each sport in the current language's data
        for sport in sports_data:
            sport_id = sport.get("id")
            sport_name = sport.get("name")

            if not sport_id:
                continue  # Skip if a sport has no ID

            # If we haven't seen this sport ID before, create a new entry for it
            if sport_id not in consolidated_sports:
                consolidated_sports[sport_id] = {"sports_id": sport_id}

            # Add the translated name under the correct key (e.g., "name_bangla")
            consolidated_sports[sport_id][field_name] = sport_name

        # A small delay to be polite to the server
        time.sleep(1)

    # 4. Convert the dictionary of sports into a simple list for the final JSON array
    final_data_list = list(consolidated_sports.values())

    # 5. Save the final list to a single JSON file
    with open(output_filename, "w", encoding="utf-8") as json_file:
        json.dump(final_data_list, json_file, indent=4, ensure_ascii=False)

    print(
        f"\n✅ Success! All language data has been consolidated into '{output_filename}'"
    )
    print(f"Total unique sports found: {len(final_data_list)}")


except requests.exceptions.RequestException as e:
    print(f"❌ An error occurred during an API request: {e}")
except json.JSONDecodeError:
    print("❌ Failed to decode JSON from a response.")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")
