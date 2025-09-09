#!/usr/bin/env python3
"""
CBS Pickem Local Workflow Script

This script runs the entire CBS Pickem workflow locally:
1. Checks if authentication cookies are valid
2. Reads matchups from CBS
3. Generates predictions
4. Submits picks to CBS
5. Generates social preview images
6. Commits and pushes changes to GitHub

If authentication fails, it sends a macOS notification with instructions
for reauthentication.
"""

import os
import sys
import subprocess
import traceback
import json
import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cbs_pickem_workflow.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
COOKIE_FILE = "cbs_storage.json"
REAUTH_INSTRUCTIONS = "REAUTH_INSTRUCTIONS.md"

def send_notification(title, message, subtitle=None, open_file=None):
    """Send a macOS notification with optional file opening action."""
    try:
        script_parts = [
            'display notification',
            f'"{message}"',
            'with title',
            f'"{title}"'
        ]
        
        if subtitle:
            script_parts.extend(['subtitle', f'"{subtitle}"'])
            
        osascript_cmd = ["osascript", "-e", " ".join(script_parts)]
        subprocess.run(osascript_cmd, check=True)
        
        # If a file path is provided, open it
        if open_file and os.path.exists(open_file):
            subprocess.run(["open", open_file], check=True)
            
        logger.info(f"Notification sent: {title} - {message}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

def check_cookie_validity():
    """Check if the cookie file exists and is valid."""
    if not os.path.exists(COOKIE_FILE):
        logger.error(f"Cookie file {COOKIE_FILE} not found")
        return False
    
    # Check if the file is not empty
    if os.path.getsize(COOKIE_FILE) == 0:
        logger.error(f"Cookie file {COOKIE_FILE} is empty")
        return False
    
    # Try to parse the JSON
    try:
        with open(COOKIE_FILE, 'r') as f:
            cookie_data = json.load(f)
        
        # Basic validation - check if it has cookies
        if not cookie_data.get('cookies'):
            logger.error("Cookie file doesn't contain 'cookies' field")
            return False
            
        # Check if any cookies exist
        if len(cookie_data.get('cookies', [])) == 0:
            logger.error("No cookies found in cookie file")
            return False
            
        logger.info("Cookie file exists and appears valid")
        return True
    except json.JSONDecodeError:
        logger.error(f"Cookie file {COOKIE_FILE} is not valid JSON")
        return False
    except Exception as e:
        logger.error(f"Error checking cookie validity: {e}")
        return False

def run_command(command, description):
    """Run a command and log its output."""
    logger.info(f"Running {description}...")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"{description} completed successfully")
        logger.debug(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"{description} failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        return False

def get_current_season_week():
    """Get the current season/week folder by finding the most recent one."""
    try:
        # Find all season folders (format: YYYY-YYYY)
        season_folders = [f for f in os.listdir() if os.path.isdir(f) and f.startswith("20")]
        
        if not season_folders:
            logger.error("No season folders found")
            return None
            
        # Get the latest season folder
        latest_season = max(season_folders)
        
        # Find all week folders in the latest season
        week_folders = [f for f in os.listdir(latest_season) if os.path.isdir(os.path.join(latest_season, f))]
        
        if not week_folders:
            logger.error(f"No week folders found in {latest_season}")
            return None
            
        # Get the latest week folder
        latest_week = max(week_folders)
        
        season_week_path = os.path.join(latest_season, latest_week)
        logger.info(f"Current season/week folder: {season_week_path}")
        return season_week_path
    except Exception as e:
        logger.error(f"Error determining current season/week: {e}")
        return None

def commit_and_push_changes(season_week_path):
    """Commit and push changes to GitHub."""
    try:
        # Check if there are any changes to commit
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if not status_result.stdout.strip():
            logger.info("No changes to commit")
            return True
            
        # Add the files
        matchups_path = os.path.join(season_week_path, "matchups.json")
        picks_path = os.path.join(season_week_path, "my_picks.json")
        preview1_path = os.path.join(season_week_path, "my_picks_1.png")
        preview2_path = os.path.join(season_week_path, "my_picks_2.png")
        
        files_to_add = []
        for file_path in [matchups_path, picks_path, preview1_path, preview2_path]:
            if os.path.exists(file_path):
                files_to_add.append(file_path)
        
        if not files_to_add:
            logger.warning("No files to commit")
            return True
            
        # Add files
        add_result = subprocess.run(
            ["git", "add"] + files_to_add,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Commit changes
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        commit_result = subprocess.run(
            ["git", "commit", "-m", f"Auto-update picks for {season_week_path} on {current_date}"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Push changes
        push_result = subprocess.run(
            ["git", "push"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("Successfully committed and pushed changes")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error in commit_and_push_changes: {e}")
        return False

def main():
    """Main workflow function."""
    try:
        logger.info("Starting CBS Pickem workflow")
        
        # Step 1: Check if cookie file is valid
        if not check_cookie_validity():
            logger.error("Authentication cookies are invalid or missing")
            send_notification(
                "CBS Pickem Authentication Failed",
                "Please run the login script to reauthenticate",
                "Cookie file is invalid or missing",
                REAUTH_INSTRUCTIONS
            )
            return 1
            
        # Step 2: Read matchups
        if not run_command(["python", "read_matchups.py"], "Read matchups"):
            send_notification(
                "CBS Pickem Workflow Failed",
                "Failed to read matchups from CBS",
                "Authentication may have expired",
                REAUTH_INSTRUCTIONS
            )
            return 1
            
        # Get the current season/week folder
        season_week_path = get_current_season_week()
        if not season_week_path:
            send_notification(
                "CBS Pickem Workflow Failed",
                "Could not determine current season/week folder",
                "Check the logs for more information"
            )
            return 1
            
        # Step 3: Predict winners
        matchups_file = os.path.join(season_week_path, "matchups.json")
        if not run_command(["python", "predict_winners.py", matchups_file], "Predict winners"):
            send_notification(
                "CBS Pickem Workflow Failed",
                "Failed to predict winners",
                "Check the logs for more information"
            )
            return 1
            
        # Step 4: Make picks
        picks_file = os.path.join(season_week_path, "my_picks.json")
        if not run_command(["python", "make_picks.py", picks_file], "Make picks"):
            send_notification(
                "CBS Pickem Workflow Failed",
                "Failed to submit picks to CBS",
                "Authentication may have expired",
                REAUTH_INSTRUCTIONS
            )
            return 1
            
        # Step 5: Generate social previews
        if not run_command(["python", "generate_social_previews.py", season_week_path], "Generate social previews"):
            send_notification(
                "CBS Pickem Workflow Warning",
                "Failed to generate social preview images",
                "Picks were submitted successfully, but preview generation failed"
            )
            # Continue with the workflow even if preview generation fails
            
        # Step 6: Commit and push changes
        if not commit_and_push_changes(season_week_path):
            send_notification(
                "CBS Pickem Workflow Warning",
                "Failed to commit and push changes to GitHub",
                "Picks were submitted successfully, but GitHub update failed"
            )
            # Continue with the workflow even if GitHub push fails
            
        # Success notification
        send_notification(
            "CBS Pickem Workflow Completed",
            f"Successfully submitted picks for {season_week_path}",
            "All steps completed successfully"
        )
        
        logger.info("Workflow completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Workflow failed with exception: {e}")
        logger.error(traceback.format_exc())
        
        send_notification(
            "CBS Pickem Workflow Failed",
            f"Unexpected error: {str(e)}",
            "Check the logs for more information"
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())
