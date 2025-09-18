import requests
import json
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict
from enum import Enum

# --- Configuration ---
EXTERNAL_API_URL = "https://8unx689.com/api/v3/user/line/list"
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'Referer': 'https://8unx689.com/',
}

# --- Pydantic Models for Data Validation ---

class LiveDetails(BaseModel):
    """Defines the structure for live match statistics."""
    status: Optional[str] = None
    current_score: Optional[str] = None
    current_period: Optional[str] = None
    match_time_minutes: Optional[int] = None
    period_scores: Optional[Dict] = None

class Odds(BaseModel):
    """Defines the structure for betting odds."""
    team1_win: Optional[float] = None
    draw: Optional[float] = None
    team2_win: Optional[float] = None

class Match(BaseModel):
    """The main model defining the final, clean structure for each match."""
    match_id: int
    match_type: str
    sport_name: str
    region: str
    league_name: str
    team1: Optional[str] = None
    team2: Optional[str] = None
    start_time_utc: Optional[datetime] = None
    live_details: Optional[LiveDetails] = None
    main_odds: Optional[Odds] = None
    livestream_url: Optional[str] = None

# --- Enums for API Documentation Dropdowns ---

class MatchMode(str, Enum):
    """Selectable modes for the type of matches to fetch."""
    live = "live"
    sportsbook = "sportsbook"

class SportChoice(str, Enum):
    """Enumeration for selectable sports by their API ID."""
    football = "football"
    cricket = "cricket"
    ice_hockey = "ice_hockey"
    padel_tennis = "padel_tennis"

# --- NEW: Mapping from user-friendly name to API ID ---
SPORT_ID_MAP = {
    "football": 1,
    "cricket": 45,
    "ice_hockey": 5,
    "padel_tennis": 211,
}


# --- FastAPI Application ---

app = FastAPI(
    title="Eternity Labs Real-time Sports API",
    description="An API that scrapes, processes, and serves live and pre-match sports data in real-time.",
    version="1.3.0"
)

# --- Scraper and Data Processing Logic ---

def fetch_external_data(mode: str, sport_id: Optional[int] = None) -> Optional[dict]:
    """Fetches raw match data from the external API with optional sport filtering."""
    type_param = '2' if mode == 'live' else '1'
    params = {'t[]': type_param, 'ss': 'all', 'l': '50', 'ltr': '0'}
    
    # Add the sport ID to the parameters if one is provided
    if sport_id:
        params['lc[]'] = sport_id
    
    try:
        response = requests.get(EXTERNAL_API_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not fetch data from external API: {e}")

def structure_match_data(raw_data: dict) -> List[Match]:
    """Parses raw JSON and validates it against Pydantic models."""
    if not raw_data or 'lines_hierarchy' not in raw_data:
        return []

    validated_matches = []
    for sport_group in raw_data.get('lines_hierarchy', []):
        match_type = sport_group.get("line_type_title", "UNKNOWN")
        
        for sport in sport_group.get('line_category_dto_collection', []):
            for region in sport.get('line_supercategory_dto_collection', []):
                for league in region.get('line_subcategory_dto_collection', []):
                    for line in league.get('line_dto_collection', []):
                        match_info = line.get('match', {})
                        if not match_info.get('id'): continue

                        live_stats = match_info.get('stat', {})
                        main_odds_data = {}
                        for outcome in line.get('outcomes', []):
                            if outcome.get('group_alias') == '1x2' and outcome.get('odd'):
                                alias = outcome.get('alias')
                                if alias == '1': main_odds_data['team1_win'] = outcome.get('odd')
                                elif alias == 'x': main_odds_data['draw'] = outcome.get('odd')
                                elif alias == '2': main_odds_data['team2_win'] = outcome.get('odd')
                        
                        livestream_url = next((w.get('url') for w in match_info.get('widgets', []) if w.get('name') == 'LiveStreamWidget'), None)
                        
                        try:
                            match_model = Match(
                                match_id=match_info['id'],
                                match_type=match_type,
                                sport_name=sport.get('title'),
                                region=region.get('title'),
                                league_name=league.get('title'),
                                team1=match_info.get('team1', {}).get('title'),
                                team2=match_info.get('team2', {}).get('title'),
                                start_time_utc=datetime.fromtimestamp(match_info['begin_at'], tz=timezone.utc) if 'begin_at' in match_info else None,
                                live_details=LiveDetails(**live_stats) if match_type == "LIVE" else None,
                                main_odds=Odds(**main_odds_data) if main_odds_data else None,
                                livestream_url=livestream_url
                            )
                            validated_matches.append(match_model)
                        except ValidationError as e:
                            print(f"Validation Error for match ID {match_info.get('id')}: {e.errors()[0]['msg']}")
                        except Exception as e:
                            print(f"Processing Error for match ID {match_info.get('id')}: {e}")

    return validated_matches

# --- API Endpoints ---

@app.get("/", tags=["Root"])
async def read_root():
    """Welcome endpoint for the API."""
    return {"message": "Welcome to the Sports Data API. Use /docs for documentation."}

@app.get("/matches/", response_model=List[Match], tags=["Matches"])
async def get_matches(mode: MatchMode, sport: Optional[SportChoice] = None):
    """
    Fetches, processes, and returns a list of matches in real-time.
    
    - **mode**: Choose whether to fetch `live` or `sportsbook` matches.
    - **sport**: (Optional) Filter the results by a specific sport.
    """
    # Convert the user-friendly sport name back to the required integer ID
    sport_id_value = None
    if sport:
        sport_id_value = SPORT_ID_MAP[sport.value]
    
    raw_data = fetch_external_data(mode.value, sport_id_value)
    
    structured_data = structure_match_data(raw_data)
    
    if not structured_data:
        raise HTTPException(status_code=404, detail=f"No matches found for the selected criteria.")
        
    return structured_data

