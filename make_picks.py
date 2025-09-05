from playwright.sync_api import sync_playwright
import logging
import time
import json
import os
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('playwright_debug')

def log_event(message):
    logger.info(message)

def load_picks_from_file(filename):
    """Load picks from a JSON file"""
    try:
        with open(filename, 'r') as f:
            picks_data = json.load(f)
            return picks_data
    except Exception as e:
        log_event(f"Error loading picks from file: {str(e)}")
        return None

def make_picks(page, picks_list):
    """Make picks based on the provided list"""
    log_event("Starting to make picks")
    
    # Wait for the page to load and matchups to appear
    try:
        # Wait for content to load
        page.wait_for_selector('div.MuiBox-root div.MuiStack-root[data-cy]', timeout=60000)
        log_event("Content has appeared")
        
        # Give extra time for everything to render
        time.sleep(2)
        
        # Get all matchup containers
        matchup_containers = page.query_selector_all('div.MuiBox-root div.MuiStack-root[data-cy]')
        log_event(f"Found {len(matchup_containers)} potential matchup containers")
        
        picks_made = 0
        
        # Process each matchup
        for i, container in enumerate(matchup_containers):
            try:
                # Extract game info to identify the matchup
                away_team_element = container.query_selector('div.MuiStack-root.left-side h3.MuiTypography-h3')
                home_team_element = container.query_selector('div.MuiStack-root.right-side h3.MuiTypography-h3')
                
                if not away_team_element or not home_team_element:
                    log_event(f"Skipping matchup {i+1} - Could not find team names")
                    continue
                
                away_team = away_team_element.inner_text().strip()
                home_team = home_team_element.inner_text().strip()
                
                # Check if we have a pick for this matchup
                pick_for_matchup = None
                for pick in picks_list:
                    if pick == away_team:
                        pick_for_matchup = "away"
                        break
                    elif pick == home_team:
                        pick_for_matchup = "home"
                        break
                
                if not pick_for_matchup:
                    log_event(f"No pick found for matchup: {away_team} @ {home_team}")
                    continue
                
                # Check if a pick is already made
                away_selected = container.query_selector('div.MuiStack-root.left-side.item-selected') is not None
                home_selected = container.query_selector('div.MuiStack-root.right-side.item-selected') is not None
                
                # If the desired pick is already selected, skip
                if (pick_for_matchup == "away" and away_selected) or (pick_for_matchup == "home" and home_selected):
                    log_event(f"Pick already made for {away_team} @ {home_team}")
                    continue
                
                # Make the pick by clicking on the team
                if pick_for_matchup == "away":
                    # Click on away team
                    away_team_container = container.query_selector('div.MuiStack-root.left-side')
                    if away_team_container:
                        log_event(f"Clicking on {away_team}")
                        away_team_container.click()
                        picks_made += 1
                        # Wait a bit to avoid overwhelming the page
                        time.sleep(0.5)
                else:
                    # Click on home team
                    home_team_container = container.query_selector('div.MuiStack-root.right-side')
                    if home_team_container:
                        log_event(f"Clicking on {home_team}")
                        home_team_container.click()
                        picks_made += 1
                        # Wait a bit to avoid overwhelming the page
                        time.sleep(0.5)
                
            except Exception as e:
                log_event(f"Error making pick for matchup {i+1}: {str(e)}")
        
        log_event(f"Made {picks_made} picks successfully")
        return picks_made
        
    except Exception as e:
        log_event(f"Error during pick making: {str(e)}")
        return 0

def main():
    """Main function to run the script"""
    log_event("Starting script")
    
    # Check if picks file is provided
    if len(sys.argv) < 2:
        print("Usage: python make_picks.py <picks_file.json>")
        print("Example picks file format: [\"EAGLES\", \"CHIEFS\", \"BUCCANEERS\"]")
        return
    
    picks_file = sys.argv[1]
    
    # Load picks from file
    picks_data = load_picks_from_file(picks_file)
    if not picks_data:
        print(f"Could not load picks from {picks_file}")
        return
    
    # Ensure picks_data is a list
    if not isinstance(picks_data, list):
        print(f"Picks data must be a list of team names. Found: {type(picks_data)}")
        return
    
    log_event(f"Loaded {len(picks_data)} picks from {picks_file}")
    print(f"Loaded picks: {', '.join(picks_data)}")
    
    with sync_playwright() as p:
        log_event("Launching browser")
        browser = p.chromium.launch(headless=False, slow_mo=200)
        
        log_event("Creating context with saved storage state")
        context = browser.new_context(storage_state="cbs_storage.json")
        
        # Add event listeners for debugging
        context.on("request", lambda request: log_event(f"Request: {request.method} {request.url}"))
        context.on("response", lambda response: log_event(f"Response: {response.status} {response.url}"))
        
        page = context.new_page()
        
        # Navigate to the CBS Sports Pickem pool page
        log_event("Navigating to CBS Sports Pickem pool page")
        page.goto("https://picks.cbssports.com/football/pickem/pools/my-pool-id===")
        
        # Make picks
        picks_made = make_picks(page, picks_data)
        
        if picks_made > 0:
            print(f"\n✅ Successfully made {picks_made} picks")
            
            # Wait for user confirmation before closing
            input("\nPress ENTER to close the browser...")
        else:
            print("\n❌ No picks were made. Check the logs for details.")
        
        # Close the browser
        log_event("Closing browser")
        browser.close()

if __name__ == "__main__":
    main()
