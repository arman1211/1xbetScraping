import requests
import json

def fetch_pokemon_data(pokemon_name):
    """
    Fetches data for a specific Pokémon from the PokéAPI.
    
    Args:
        pokemon_name (str): The name of the Pokémon to look up.

    Returns:
        dict: The JSON data for the Pokémon, or None if not found.
    """
    # The base URL for the Pokémon endpoint
    base_url = "https://pokeapi.co/api/v2/pokemon/"
    
    # Format the URL to be lowercase as required by the API
    api_url = f"{base_url}{pokemon_name.lower()}"
    
    print(f"🔍 Searching for '{pokemon_name}' at {api_url}...")
    
    try:
        response = requests.get(api_url)
        # This will raise an exception for bad responses (4xx or 5xx)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"❌ Error: Pokémon '{pokemon_name}' not found. Please check the spelling.")
        else:
            print(f"❌ HTTP Error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ A network error occurred: {e}")
        return None

def display_pokemon_info(data):
    """
    Displays a formatted summary of the Pokémon's data.
    """
    if not data:
        return
        
    print("\n" + "="*40)
    print(f" POKÉMON DATA: {data['name'].upper()} ".center(40, "="))
    print("="*40)

    # Basic Info
    print(f"\n✨ Basic Info:")
    print(f"   - National Dex ID: #{data['id']}")
    print(f"   - Height: {data['height'] / 10.0} m")
    print(f"   - Weight: {data['weight'] / 10.0} kg")

    # Types
    types = [t['type']['name'].capitalize() for t in data['types']]
    print(f"\n🍃 Types: {', '.join(types)}")

    # Abilities
    abilities = [a['ability']['name'].replace('-', ' ').title() for a in data['abilities']]
    print(f"\n💪 Abilities: {', '.join(abilities)}")
    
    # Base Stats
    print("\n📊 Base Stats:")
    for stat in data['stats']:
        stat_name = stat['stat']['name'].replace('-', ' ').title()
        base_stat = stat['base_stat']
        # Create a simple bar for visualization
        bar = '█' * (base_stat // 5) 
        print(f"   - {stat_name:<15}: {base_stat:<3} | {bar}")
        
    print("\n" + "="*40 + "\n")


if __name__ == "__main__":
    print("--- PokéAPI Scraper ---")
    
    # Get user input
    pokemon_to_find = input("▶️ Enter the name of a Pokémon (e.g., Pikachu, Charizard): ")

    if not pokemon_to_find:
        print("⚠️ You didn't enter a name. Exiting.")
    else:
        pokemon_data = fetch_pokemon_data(pokemon_to_find)
        
        if pokemon_data:
            # Display the formatted data in the console
            display_pokemon_info(pokemon_data)
            
            # Save the full JSON data to a file
            output_filename = f"{pokemon_to_find.lower()}_data.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(pokemon_data, f, indent=4, ensure_ascii=False)
            
            print(f"💾 Full data saved to '{output_filename}'")
