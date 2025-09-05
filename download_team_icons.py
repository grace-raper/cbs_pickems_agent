#!/usr/bin/env python3
import os
import json
import requests
import re
from collections import defaultdict

# Base URL for CBS team icons
BASE_URL = "https://sports.cbsimg.net/fly/images/nfl/logos/team/"

# Directory to save the icons
ICONS_DIR = "team_icons"

# List of team icon IDs from the user's input
TEAM_ICON_IDS = [
    "404", "405", "406", "407", "408", "409", "410", "411", "412", "413", "414", 
    "415", "416", "417", "418", "419", "420", "421", "422", "423", "424", "425", 
    "426", "427", "428", "429", "430", "431", "432", "433", "434", "435", "436",
    "437", "438", "439", "440", "441", "247415"
]

# Known team names mapping (based on the get_team_name_from_code function in read_matchups.py)
TEAM_NAMES = {
    '410': 'BENGALS',
    '434': 'BROWNS',
    '417': 'CHIEFS',
    '428': 'CHARGERS',
    '407': 'BILLS',
    '409': 'BEARS',
    '413': 'COWBOYS',
    '414': 'EAGLES',
    '415': 'FALCONS',
    '416': 'GIANTS',
    '418': 'COLTS',
    '419': 'JAGUARS',
    '420': 'DOLPHINS',
    '421': 'VIKINGS',
    '422': 'PATRIOTS',
    '423': 'SAINTS',
    '424': 'RAIDERS',
    '425': 'JETS',
    '426': 'PANTHERS',
    '427': 'COMMANDERS',
    '429': 'STEELERS',
    '430': 'RAMS',
    '431': 'RAVENS',
    '432': 'SEAHAWKS',
    '433': 'BUCCANEERS',
    '435': 'TITANS',
    '436': 'BRONCOS',
    '437': 'PACKERS',
    '438': 'LIONS',
    '439': 'CARDINALS',
    '440': 'TEXANS',
    '441': '49ERS',
    '404': 'TEAM-404',
    '405': 'TEAM-405',
    '406': 'TEAM-406',
    '408': 'TEAM-408',
    '412': 'TEAM-412',
    '247415': 'TEAM-247415'
}

def download_icon(icon_id):
    """Download a team icon by its ID"""
    url = f"{BASE_URL}{icon_id}.svg"
    output_path = os.path.join(ICONS_DIR, f"{icon_id}.svg")
    
    try:
        print(f"Downloading {url}...")
        response = requests.get(url)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Successfully downloaded {icon_id}.svg")
            return True
        else:
            print(f"❌ Failed to download {icon_id}.svg - Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error downloading {icon_id}.svg: {str(e)}")
        return False

def create_mapping_json():
    """Create a JSON mapping of team IDs to team names and filenames"""
    mapping = {}
    
    # Check which icons were successfully downloaded
    for icon_id in TEAM_ICON_IDS:
        icon_path = os.path.join(ICONS_DIR, f"{icon_id}.svg")
        if os.path.exists(icon_path):
            team_name = TEAM_NAMES.get(icon_id, f"TEAM-{icon_id}")
            mapping[icon_id] = {
                "team_name": team_name,
                "filename": f"{icon_id}.svg",
                "path": icon_path,
                "url": f"{BASE_URL}{icon_id}.svg"
            }
    
    # Create a reverse mapping (team name to icon ID)
    team_name_to_id = {}
    for icon_id, data in mapping.items():
        team_name_to_id[data["team_name"]] = icon_id
    
    # Create the final mapping object
    final_mapping = {
        "id_to_team": mapping,
        "team_to_id": team_name_to_id
    }
    
    # Save the mapping to a JSON file
    with open('team_icons_mapping.json', 'w') as f:
        json.dump(final_mapping, f, indent=2)
    
    print(f"✅ Created team_icons_mapping.json with {len(mapping)} team mappings")
    return final_mapping

def analyze_matchups_json():
    """Analyze the matchups.json file to find any missing team mappings"""
    try:
        with open('matchups.json', 'r') as f:
            matchups_data = json.load(f)
        
        # Collect all team names and team codes that appear in the file
        team_names = set()
        team_codes = set()
        
        # Function to extract team codes from the data
        def extract_team_codes(data, path=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    new_path = f"{path}.{key}" if path else key
                    if key == "pick_team" and isinstance(value, str):
                        team_names.add(value)
                    if isinstance(value, str) and value.startswith("TEAM-"):
                        code = value.replace("TEAM-", "")
                        team_codes.add(code)
                        print(f"Found unmapped team code: {code} at {new_path}")
                    extract_team_codes(value, new_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    extract_team_codes(item, f"{path}[{i}]")
        
        extract_team_codes(matchups_data)
        
        print(f"\nFound {len(team_names)} team names and {len(team_codes)} unmapped team codes")
        if team_codes:
            print("Unmapped team codes:", team_codes)
        
        return team_codes
    except Exception as e:
        print(f"Error analyzing matchups.json: {str(e)}")
        return set()

def main():
    """Main function to download icons and create mapping"""
    # Create the icons directory if it doesn't exist
    os.makedirs(ICONS_DIR, exist_ok=True)
    
    # Download all team icons
    successful_downloads = 0
    for icon_id in TEAM_ICON_IDS:
        if download_icon(icon_id):
            successful_downloads += 1
    
    print(f"\nDownloaded {successful_downloads} out of {len(TEAM_ICON_IDS)} team icons")
    
    # Create the mapping JSON
    mapping = create_mapping_json()
    
    # Analyze matchups.json for any missing mappings
    missing_codes = analyze_matchups_json()
    
    # Print summary
    print("\n=== Summary ===")
    print(f"- Downloaded {successful_downloads} team icons to {ICONS_DIR}/")
    print(f"- Created mapping with {len(mapping['id_to_team'])} teams")
    print(f"- Found {len(missing_codes)} unmapped team codes in matchups.json")
    
    if missing_codes:
        print("\nTo fix unmapped team codes, add these to the TEAM_NAMES dictionary:")
        for code in missing_codes:
            print(f"    '{code}': 'TEAM_NAME_HERE',")

if __name__ == "__main__":
    main()
