#!/usr/bin/env python3
"""
predict_winners.py - Predicts NFL game winners based on expert picks and user preferences

This script analyzes matchup data from a JSON file and generates predictions for NFL games.
It uses a combination of expert consensus and user team preferences to make predictions.

Usage:
    python predict_winners.py [path_to_matchups_json]

If no path is provided, it will use the current week's matchups.json file.
"""

import json
import os
import sys
import re
import logging
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# User's favorite teams (in order of preference)
FAVORITE_TEAMS = [
    "SEAHAWKS",  # Always pick the Seahawks
    "LIONS",     # Advantage when spread is reasonable
    "FALCONS",   # Advantage when spread is reasonable
    "RAIDERS",   # Advantage when spread is reasonable
    "RAVENS",    # Advantage when spread is reasonable
    "VIKINGS"    # Advantage when spread is reasonable
]

# Define what constitutes a "reasonable" spread (in points)
REASONABLE_SPREAD = 5.5  # 5.5 points or less is considered reasonable

# Define what constitutes strong expert consensus
STRONG_EXPERT_CONSENSUS = 0.75  # 75% or more experts agree

def log_event(message):
    """Log an event with timestamp"""
    logging.info(message)

def get_default_matchups_path():
    """Get the default path for the current week's matchups.json file"""
    # Default to the most recent matchups.json file
    # First check if there's a matchups.json in the current directory
    if os.path.exists("matchups.json"):
        return "matchups.json"
    
    # Otherwise, look for the most recent season/week folder
    try:
        # Get all directories that look like YYYY-YYYY (season folders)
        season_dirs = [d for d in os.listdir() if re.match(r'\d{4}-\d{4}', d) and os.path.isdir(d)]
        if not season_dirs:
            return "matchups.json"  # Fall back to default if no season folders found
        
        # Get the most recent season
        latest_season = sorted(season_dirs)[-1]
        
        # Get all week folders in that season
        week_dirs = [d for d in os.listdir(latest_season) 
                    if d.startswith("week-") and os.path.isdir(os.path.join(latest_season, d))]
        if not week_dirs:
            return "matchups.json"  # Fall back to default if no week folders found
        
        # Get the most recent week
        # Sort by week number (extract number from "week-X")
        latest_week = sorted(week_dirs, key=lambda w: int(w.split("-")[1]))[-1]
        
        # Return the path to the matchups.json file
        return os.path.join(latest_season, latest_week, "matchups.json")
    except Exception as e:
        log_event(f"Error finding default matchups path: {str(e)}")
        return "matchups.json"  # Fall back to default

def parse_expert_picks(matchup):
    """
    Parse expert picks from a matchup and return:
    - The team with the most expert picks
    - The percentage of experts picking that team
    """
    if "expert_picks" not in matchup or "team_picks" not in matchup["expert_picks"]:
        return None, 0.0
    
    team_picks = matchup["expert_picks"]["team_picks"]
    
    # Extract team names and pick counts
    teams_and_picks = {}
    for team, picks_str in team_picks.items():
        # Extract the number from strings like "7 Picks"
        picks_count = int(re.search(r'(\d+)', picks_str).group(1))
        teams_and_picks[team] = picks_count
    
    if not teams_and_picks:
        return None, 0.0
    
    # Find the team with the most picks
    most_picked_team = max(teams_and_picks.items(), key=lambda x: x[1])
    team_name = most_picked_team[0]
    pick_count = most_picked_team[1]
    
    # Calculate the percentage of experts picking this team
    total_picks = sum(teams_and_picks.values())
    percentage = pick_count / total_picks if total_picks > 0 else 0.0
    
    return team_name, percentage

def parse_spread(matchup):
    """
    Parse the spread from a matchup and return:
    - The team favored by the spread
    - The spread value (absolute)
    """
    if "odds" not in matchup or "current_odds" not in matchup["odds"]:
        return None, 0.0
    
    # Get the away and home team spreads
    away_spread_str = matchup["odds"]["current_odds"]["away"]["spread"]
    home_spread_str = matchup["odds"]["current_odds"]["home"]["spread"]
    
    # Parse the spread values
    away_spread = float(away_spread_str) if away_spread_str and away_spread_str[0] != 'o' and away_spread_str[0] != 'u' else 0.0
    home_spread = float(home_spread_str) if home_spread_str and home_spread_str[0] != 'o' and home_spread_str[0] != 'u' else 0.0
    
    # Determine which team is favored
    if away_spread < 0:  # Away team is favored
        return matchup["away_team"], abs(away_spread)
    elif home_spread < 0:  # Home team is favored
        return matchup["home_team"], abs(home_spread)
    else:  # No clear favorite or pick'em
        return None, 0.0

def predict_winner(matchup):
    """
    Predict the winner of a matchup based on expert picks and user preferences.
    
    Algorithm:
    1. Always pick the Seahawks (user's team)
    2. For favorite teams, pick them if the spread is reasonable (<= 5.5 points)
    3. If expert consensus is strong (>75%), go with the experts
    4. Otherwise, go with the team favored by the spread
    5. If no clear favorite, go with the home team
    """
    away_team = matchup["away_team"]
    home_team = matchup["home_team"]
    
    log_event(f"Analyzing matchup: {away_team} @ {home_team}")
    
    # Rule 1: Always pick the Seahawks
    if away_team == "SEAHAWKS":
        log_event(f"✅ Picking {away_team} (User's favorite team)")
        return away_team
    elif home_team == "SEAHAWKS":
        log_event(f"✅ Picking {home_team} (User's favorite team)")
        return home_team
    
    # Get expert consensus
    expert_pick, expert_percentage = parse_expert_picks(matchup)
    log_event(f"Expert consensus: {expert_percentage:.1%} for {expert_pick if expert_pick else 'None'}")
    
    # Get spread information
    spread_favorite, spread_value = parse_spread(matchup)
    log_event(f"Spread favorite: {spread_favorite if spread_favorite else 'None'} by {spread_value} points")
    
    # Rule 2: Favorite teams with reasonable spread (PRIORITIZED OVER EXPERT CONSENSUS)
    for team in FAVORITE_TEAMS:
        if away_team == team:
            # If away team is a favorite and either favored by spread or underdog by reasonable amount
            if not spread_favorite or spread_favorite == away_team or spread_value <= REASONABLE_SPREAD:
                log_event(f"✅ Picking {away_team} (User's preferred team with reasonable spread)")
                return away_team
        elif home_team == team:
            # If home team is a favorite and either favored by spread or underdog by reasonable amount
            if not spread_favorite or spread_favorite == home_team or spread_value <= REASONABLE_SPREAD:
                log_event(f"✅ Picking {home_team} (User's preferred team with reasonable spread)")
                return home_team
    
    # Rule 3: Strong expert consensus (>75%) - NOW LOWER PRIORITY THAN FAVORITE TEAMS
    if expert_pick and expert_percentage >= STRONG_EXPERT_CONSENSUS:
        log_event(f"✅ Picking {expert_pick} (Strong expert consensus: {expert_percentage:.1%})")
        return expert_pick
    
    # Rule 4: Go with the spread favorite
    if spread_favorite:
        log_event(f"✅ Picking {spread_favorite} (Favored by {spread_value} points)")
        return spread_favorite
    
    # Rule 5: Default to home team
    log_event(f"✅ Picking {home_team} (Home field advantage)")
    return home_team

# Removed sorting function as we want to keep matchups in original order

def predict_winners(matchups_path):
    """
    Predict winners for all matchups in the given JSON file
    and save predictions to a my_picks.json file in the same directory
    """
    try:
        # Load matchups from JSON file
        with open(matchups_path, 'r') as f:
            data = json.load(f)
        
        matchups = data.get("matchups", [])
        if not matchups:
            log_event("No matchups found in the JSON file")
            return False
        
        log_event(f"Loaded {len(matchups)} matchups from {matchups_path}")
        
        # Keep matchups in original order (no sorting)
        
        # Predict winners for each matchup
        predictions = []
        for i, matchup in enumerate(matchups):
            log_event(f"\nProcessing matchup {i+1} of {len(matchups)}")
            winner = predict_winner(matchup)
            predictions.append(winner)
            log_event(f"Prediction for {matchup['away_team']} @ {matchup['home_team']}: {winner}")
        
        # Save predictions to my_picks.json in the same directory as the input file
        output_dir = os.path.dirname(matchups_path)
        output_path = os.path.join(output_dir, "my_picks.json")
        
        with open(output_path, 'w') as f:
            json.dump(predictions, f)
        
        log_event(f"Saved {len(predictions)} predictions to {output_path}")
        print(f"\n✅ Predictions saved to {output_path}")
        
        # Print the predictions
        print("\nPredicted Winners:")
        print("=================")
        for i, (matchup, pick) in enumerate(zip(matchups, predictions)):
            away = matchup["away_team"]
            home = matchup["home_team"]
            game_time = matchup.get("game_time", "Time unknown")
            print(f"{i+1}. {away} @ {home} ({game_time}): {pick}")
        
        return True
    
    except Exception as e:
        log_event(f"Error predicting winners: {str(e)}")
        import traceback
        log_event(traceback.format_exc())
        return False

def main():
    """Main function to run the script"""
    parser = argparse.ArgumentParser(description='Predict NFL game winners based on expert picks and user preferences')
    parser.add_argument('matchups_path', nargs='?', default=None, help='Path to the matchups.json file')
    args = parser.parse_args()
    
    # If no path is provided, use the default path
    if not args.matchups_path:
        args.matchups_path = get_default_matchups_path()
        log_event(f"No path provided, using default path: {args.matchups_path}")
    
    # Check if the file exists
    if not os.path.exists(args.matchups_path):
        log_event(f"Error: File not found: {args.matchups_path}")
        print(f"Error: File not found: {args.matchups_path}")
        return False
    
    # Predict winners
    return predict_winners(args.matchups_path)

if __name__ == "__main__":
    main()
