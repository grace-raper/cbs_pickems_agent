#!/usr/bin/env python3
"""
generate_social_previews.py - Generate social preview images of NFL picks

This script generates two PNG images of NFL picks for social media sharing.
It takes a folder path containing matchups.json and my_picks.json, and generates
two PNG images with the picks split in half, using team icons from the team_icons folder.

Usage:
    python generate_social_previews.py [path_to_folder]

If no path is provided, it will use the current week's folder.
"""

import os
import json
import argparse
import logging
import re
import base64
from datetime import datetime
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Team code to name mapping
TEAM_CODE_TO_NAME = {
    '404': 'CARDINALS',
    '405': 'FALCONS',
    '406': 'RAVENS',
    '407': 'BILLS',
    '408': 'PANTHERS',
    '409': 'BEARS',
    '410': 'BENGALS',
    '411': 'COWBOYS',
    '412': 'BRONCOS',
    '413': 'LIONS',
    '414': 'PACKERS',
    '415': 'COLTS',
    '416': 'JAGUARS',
    '417': 'CHIEFS',
    '418': 'DOLPHINS',
    '419': 'VIKINGS',
    '420': 'PATRIOTS',
    '421': 'SAINTS',
    '422': 'GIANTS',
    '423': 'JETS',
    '424': 'RAIDERS',
    '425': 'EAGLES',
    '426': 'STEELERS',
    '427': 'RAMS',
    '428': 'CHARGERS',
    '429': '49ERS',
    '430': 'SEAHAWKS',
    '431': 'BUCCANEERS',
    '432': 'TITANS',
    '433': 'COMMANDERS',
    '434': 'BROWNS',
    '247415': 'TEXANS',
}

# Team name to code mapping
TEAM_NAME_TO_CODE = {v: k for k, v in TEAM_CODE_TO_NAME.items()}

# Team colors mapping
TEAM_COLORS = {
    'CARDINALS': 'bg-red-700',
    'FALCONS': 'bg-red-600',
    'RAVENS': 'bg-purple-900',
    'BILLS': 'bg-blue-700',
    'PANTHERS': 'bg-blue-800',
    'BEARS': 'bg-blue-900',
    'BENGALS': 'bg-orange-600',
    'COWBOYS': 'bg-blue-800',
    'BRONCOS': 'bg-orange-700',
    'LIONS': 'bg-blue-500',
    'PACKERS': 'bg-green-700',
    'COLTS': 'bg-blue-600',
    'JAGUARS': 'bg-teal-800',
    'CHIEFS': 'bg-red-600',
    'DOLPHINS': 'bg-teal-500',
    'VIKINGS': 'bg-purple-900',
    'PATRIOTS': 'bg-blue-900',
    'SAINTS': 'bg-yellow-700',
    'GIANTS': 'bg-blue-800',
    'JETS': 'bg-green-800',
    'RAIDERS': 'bg-black',
    'EAGLES': 'bg-teal-800',
    'STEELERS': 'bg-yellow-500',
    'RAMS': 'bg-blue-700',
    'CHARGERS': 'bg-blue-600',
    '49ERS': 'bg-red-700',
    'SEAHAWKS': 'bg-blue-800',
    'BUCCANEERS': 'bg-red-800',
    'TITANS': 'bg-blue-800',
    'COMMANDERS': 'bg-red-800',
    'BROWNS': 'bg-orange-700',
    'TEXANS': 'bg-red-800',
}

# Helper function to convert Tailwind color classes to CSS color values
def getColorFromClass(colorClass, opacity=0.5):
    """Convert Tailwind color classes to CSS color values"""
    colorMap = {
        'bg-purple-900': f"rgba(88, 28, 135, {opacity})",
        'bg-red-600': f"rgba(220, 38, 38, {opacity})",
        'bg-red-700': f"rgba(185, 28, 28, {opacity})",
        'bg-red-800': f"rgba(153, 27, 27, {opacity})",
        'bg-green-700': f"rgba(21, 128, 61, {opacity})",
        'bg-green-800': f"rgba(22, 101, 52, {opacity})",
        'bg-blue-400': f"rgba(96, 165, 250, {opacity})",
        'bg-blue-500': f"rgba(59, 130, 246, {opacity})",
        'bg-blue-600': f"rgba(37, 99, 235, {opacity})",
        'bg-blue-700': f"rgba(29, 78, 216, {opacity})",
        'bg-blue-800': f"rgba(30, 64, 175, {opacity})",
        'bg-blue-900': f"rgba(30, 58, 138, {opacity})",
        'bg-yellow-500': f"rgba(234, 179, 8, {opacity})",
        'bg-yellow-700': f"rgba(161, 98, 7, {opacity})",
        'bg-orange-500': f"rgba(249, 115, 22, {opacity})",
        'bg-orange-600': f"rgba(234, 88, 12, {opacity})",
        'bg-orange-700': f"rgba(194, 65, 12, {opacity})",
        'bg-teal-500': f"rgba(20, 184, 166, {opacity})",
        'bg-teal-600': f"rgba(13, 148, 136, {opacity})",
        'bg-teal-800': f"rgba(17, 94, 89, {opacity})",
        'bg-black': f"rgba(0, 0, 0, {opacity})"
    }
    return colorMap.get(colorClass, f"rgba(107, 114, 128, {opacity})")  # Default to gray if color not found

def log_event(message):
    """Log an event with timestamp"""
    logging.info(message)

def get_default_matchups_path():
    """Get the default path for the current week's matchups.json file"""
    try:
        # Get all directories that look like YYYY-YYYY (season folders)
        season_dirs = [d for d in os.listdir() if re.match(r'\d{4}-\d{4}', d) and os.path.isdir(d)]
        if not season_dirs:
            return None  # No season folders found
        
        # Get the most recent season
        latest_season = sorted(season_dirs)[-1]
        
        # Get all week folders in that season
        week_dirs = [d for d in os.listdir(latest_season) 
                    if d.startswith("week-") and os.path.isdir(os.path.join(latest_season, d))]
        if not week_dirs:
            return None  # No week folders found
        
        # Get the most recent week
        # Sort by week number (extract number from "week-X")
        latest_week = sorted(week_dirs, key=lambda w: int(w.split("-")[1]))[-1]
        
        # Return the path to the folder
        return os.path.join(latest_season, latest_week)
    except Exception as e:
        log_event(f"Error finding default matchups path: {str(e)}")
        return None

def load_data(folder_path):
    """Load matchups and picks data from the specified folder"""
    try:
        # Load matchups data
        matchups_path = os.path.join(folder_path, "matchups.json")
        with open(matchups_path, 'r') as f:
            matchups_data = json.load(f)
        
        # Load picks data
        picks_path = os.path.join(folder_path, "my_picks.json")
        with open(picks_path, 'r') as f:
            picks_data = json.load(f)
        
        log_event(f"Loaded data from {folder_path}")
        return matchups_data, picks_data
    except Exception as e:
        log_event(f"Error loading data: {str(e)}")
        import traceback
        log_event(traceback.format_exc())
        return None, None

def get_team_svg_base64(team_name):
    """Get the team SVG as a base64 encoded string"""
    try:
        team_code = TEAM_NAME_TO_CODE.get(team_name)
        if not team_code:
            log_event(f"No team code found for {team_name}")
            return None
        
        svg_path = os.path.join("team_icons", f"{team_code}.svg")
        if not os.path.exists(svg_path):
            log_event(f"No SVG file found at {svg_path}")
            return None
        
        with open(svg_path, 'rb') as f:
            svg_data = f.read()
        
        # Special handling for Saints and Commanders logos
        if team_name == "SAINTS" or team_name == "COMMANDERS":
            # Create a simple text-based logo as fallback
            first_letter = team_name[0]
            svg_data = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text x="50" y="50" font-family="Arial" font-size="50" text-anchor="middle" dominant-baseline="central" fill="white">{first_letter}</text></svg>'.encode('utf-8')
        else:
            # Convert SVG to white if it exists
            try:
                svg_text = svg_data.decode('utf-8')
                # Add fill="white" to the SVG to ensure it's white on the colored background
                if '<svg' in svg_text and 'fill="white"' not in svg_text:
                    svg_text = svg_text.replace('<svg', '<svg fill="white"')
                    svg_data = svg_text.encode('utf-8')
            except:
                pass
        
        base64_data = base64.b64encode(svg_data).decode('utf-8')
        return f"data:image/svg+xml;base64,{base64_data}"
    except Exception as e:
        log_event(f"Error getting team SVG: {str(e)}")
        return None

def prepare_game_data(matchups_data, picks_data):
    """Prepare game data for rendering"""
    games = []
    matchups = matchups_data.get("matchups", [])
    
    for i, (matchup, pick) in enumerate(zip(matchups, picks_data)):
        away_team = matchup.get("away_team")
        home_team = matchup.get("home_team")
        game_time = matchup.get("game_time", "Time not found")
        
        # Extract date and time
        date_match = re.search(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)', game_time)
        time_match = re.search(r'(\d+:\d+ [AP]M)', game_time)
        
        date = date_match.group(0) if date_match else ""
        time = time_match.group(1) if time_match else ""
        
        # Get spread from odds if available
        spread = ""
        if "odds" in matchup and "current_odds" in matchup["odds"]:
            away_spread = matchup["odds"]["current_odds"]["away"]["spread"]
            home_spread = matchup["odds"]["current_odds"]["home"]["spread"]
            
            if away_spread and away_spread[0] != 'o' and away_spread[0] != 'u':
                spread = f"{away_team} {away_spread}"
            elif home_spread and home_spread[0] != 'o' and home_spread[0] != 'u':
                spread = f"{home_team} {home_spread}"
        
        # Determine which team was picked
        is_away_picked = pick == away_team
        is_home_picked = pick == home_team
        
        # Get team logos
        away_logo = get_team_svg_base64(away_team)
        home_logo = get_team_svg_base64(home_team)
        
        # Get team colors
        away_color = TEAM_COLORS.get(away_team, "bg-gray-800")
        home_color = TEAM_COLORS.get(home_team, "bg-gray-800")
        
        games.append({
            "awayTeam": {
                "name": away_team,
                "fullName": away_team,
                "record": matchup.get("away_record", "0-0"),
                "logo": away_logo,
                "color": away_color
            },
            "homeTeam": {
                "name": home_team,
                "fullName": home_team,
                "record": matchup.get("home_record", "0-0"),
                "logo": home_logo,
                "color": home_color
            },
            "date": date,
            "time": time,
            "spread": spread,
            "pick": "away" if is_away_picked else "home" if is_home_picked else None,
            "upset": False  # We don't have upset data
        })
    
    return games

def generate_html(games, title, week_number, year):
    """Generate HTML for the social preview"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NFL Picks</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{
                display: flex;
                justify-content: center;
                align-items: center;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #0a1f44; /* Navy background */
            }}
            .container {{
                width: 768px;
                height: 1280px;
                background-color: #0a1f44; /* Navy background */
                display: flex;
                justify-content: center;
                align-content: center;
            }}
            .content-container {{
                width: 640px;
                margin: 40px 0 0 0;
                box-sizing: border-box;
            }}
            .team-logo {{
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }}
            .team-logo img {{
                width: 100%;
                height: 100%;
                object-fit: contain;
            }}
            .game-card {{
                border-radius: 12px;
                overflow: hidden;
                margin-bottom: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                background-color: #f3f4f6;
            }}
            .game-header {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                align-items: center;
                padding: 8px 12px;
                background-color: #e5e7eb;
                border-bottom: 1px solid #d1d5db;
            }}
            .game-date {{
                text-align: left;
            }}
            .game-time {{
                text-align: center;
                font-weight: 500;
            }}
            .game-spread {{
                text-align: right;
            }}
            .matchup-row {{
                display: flex;
                align-items: center;
                padding: 10px;
            }}
            .team-vs {{
                display: flex;
                flex-direction: column;
                align-items: center;
                margin: 0 8px;
            }}
            .team-container {{
                display: flex;
                justify-content: space-between;
                padding: 10px;
            }}
            .team-box {{
                display: flex;
                align-items: center;
                padding: 8px;
                border-radius: 8px;
                width: 48%;
            }}
            .team-info {{
                margin-left: 16px;
                margin-right: 16px;
                flex-grow: 1;
                overflow: hidden;
            }}
            .team-name {{
                font-weight: bold;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .team-record {{
                font-size: 0.75rem;
                color: #6b7280;
            }}
            .vs-text {{
                font-size: 0.875rem;
                color: #6b7280;
                margin: 0 8px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="content-container">
                <!-- Header -->
                <div class="bg-gray-200 text-gray-800 text-center py-6 rounded-lg shadow-lg mb-6 border-b-4 border-yellow-500">
                    <h1 class="text-3xl font-bold">2025-26</h1>
                    <h2 class="text-4xl font-extrabold tracking-tight">
                        {title}
                    </h2>
                </div>
                
                <!-- Games Container -->
                <div class="games-container">
    """
    
    for i, game in enumerate(games):
        away_team = game["awayTeam"]
        home_team = game["homeTeam"]
        
        # Get color values for team backgrounds
        away_color = getColorFromClass(away_team['color'], 0.2)
        home_color = getColorFromClass(home_team['color'], 0.2)
        
        # Border for picked team
        away_border = f"border: 3px solid {getColorFromClass(away_team['color'], 1.0)};" if game["pick"] == "away" else ""
        home_border = f"border: 3px solid {getColorFromClass(home_team['color'], 1.0)};" if game["pick"] == "home" else ""
        
        html += f"""
                    <div class="game-card">
                        <!-- Game Date & Time -->
                        <div class="game-header">
                            <div class="game-date text-gray-700 text-sm">{game["date"]}</div>
                            <div class="game-time text-gray-700 text-sm">{game["time"]}</div>
                            <div class="game-spread font-medium text-gray-700 text-sm">{game["spread"]}</div>
                        </div>
                        
                        <!-- Teams in a row -->
                        <div class="team-container">
                            <!-- Away Team -->
                            <div class="team-box" 
                                 style="background: {game['pick'] == 'away' and away_color or 'transparent'}; 
                                        {game['pick'] == 'away' and away_border or ''}">
                                <div class="team-logo">
                                    {away_team['logo'] and f'<img src="{away_team["logo"]}" alt="{away_team["name"]}" />' or away_team["name"]}
                                </div>
                                <div class="team-info">
                                    <div class="team-name text-gray-900">
                                        {away_team["fullName"]}
                                    </div>
                                    <div class="team-record">
                                        {away_team["record"]}
                                    </div>
                                </div>
                            </div>
                            
                            <!-- VS -->
                            <div class="vs-text">@</div>
                            
                            <!-- Home Team - Right aligned -->
                            <div class="team-box" 
                                 style="background: {game['pick'] == 'home' and home_color or 'transparent'}; 
                                        {game['pick'] == 'home' and home_border or ''}">
                                <div class="team-info" style="text-align: right;">
                                    <div class="team-name text-gray-900">
                                        {home_team["fullName"]}
                                    </div>
                                    <div class="team-record">
                                        {home_team["record"]}
                                    </div>
                                </div>
                                <div class="team-logo">
                                    {home_team['logo'] and f'<img src="{home_team["logo"]}" alt="{home_team["name"]}" />' or home_team["name"]}
                                </div>
                            </div>
                        </div>
                    </div>
        """
    
    html += """
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_social_previews(folder_path):
    """Generate social preview images of NFL picks"""
    try:
        # Load data
        matchups_data, picks_data = load_data(folder_path)
        if not matchups_data or not picks_data:
            log_event("Failed to load data")
            return False
        
        # Extract week and year information
        timestamp = matchups_data.get("timestamp", "")
        year = datetime.now().year
        
        # Try to extract week number from folder path
        week_match = re.search(r'week-(\d+)', folder_path)
        week_number = int(week_match.group(1)) if week_match else 0
        
        # Prepare game data
        games = prepare_game_data(matchups_data, picks_data)
        
        # Split games into two halves
        half_length = len(games) // 2
        first_half = games[:half_length]
        second_half = games[half_length:]
        
        # Generate HTML for each half
        first_half_html = generate_html(first_half, f"WEEK {week_number} PICKS (1/2)", week_number, year)
        second_half_html = generate_html(second_half, f"WEEK {week_number} PICKS (2/2)", week_number, year)
        
        # Generate screenshots using Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 720, "height": 1280})
            
            # Generate first half screenshot
            log_event("Generating first half screenshot")
            page.set_content(first_half_html)
            page.screenshot(path=os.path.join(folder_path, "my_picks_1.png"))
            
            # Generate second half screenshot
            log_event("Generating second half screenshot")
            page.set_content(second_half_html)
            page.screenshot(path=os.path.join(folder_path, "my_picks_2.png"))
            
            browser.close()
        
        log_event(f"Successfully generated social preview images in {folder_path}")
        return True
    
    except Exception as e:
        log_event(f"Error generating social previews: {str(e)}")
        import traceback
        log_event(traceback.format_exc())
        return False

def main():
    """Main function to run the script"""
    parser = argparse.ArgumentParser(description='Generate social preview images of NFL picks')
    parser.add_argument('folder_path', nargs='?', default=None, help='Path to the folder containing matchups.json and my_picks.json')
    args = parser.parse_args()
    
    # If no path is provided, use the default path
    if not args.folder_path:
        args.folder_path = get_default_matchups_path()
        if not args.folder_path:
            log_event("No folder path provided and could not determine default path")
            print("Error: No folder path provided and could not determine default path")
            return False
        log_event(f"No path provided, using default path: {args.folder_path}")
    
    # Check if the folder exists
    if not os.path.exists(args.folder_path):
        log_event(f"Error: Folder not found: {args.folder_path}")
        print(f"Error: Folder not found: {args.folder_path}")
        return False
    
    # Check if the required files exist
    matchups_path = os.path.join(args.folder_path, "matchups.json")
    picks_path = os.path.join(args.folder_path, "my_picks.json")
    
    if not os.path.exists(matchups_path):
        log_event(f"Error: matchups.json not found in {args.folder_path}")
        print(f"Error: matchups.json not found in {args.folder_path}")
        return False
    
    if not os.path.exists(picks_path):
        log_event(f"Error: my_picks.json not found in {args.folder_path}")
        print(f"Error: my_picks.json not found in {args.folder_path}")
        return False
    
    # Generate social previews
    success = generate_social_previews(args.folder_path)
    
    if success:
        print(f"\n✅ Social preview images generated in {args.folder_path}")
        print(f"   - my_picks_1.png")
        print(f"   - my_picks_2.png")
    else:
        print("\n❌ Failed to generate social preview images")
    
    return success

if __name__ == "__main__":
    main()
