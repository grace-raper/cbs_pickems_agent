from playwright.sync_api import sync_playwright
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('playwright_debug')

def log_event(message):
    logger.info(message)

def main():
    log_event("Starting Playwright session to inspect page structure")
    with sync_playwright() as p:
        log_event("Launching browser")
        browser = p.chromium.launch(headless=False, slow_mo=200)
        
        log_event("Creating new browser context with saved storage state")
        context = browser.new_context(storage_state="cbs_storage.json")
        
        page = context.new_page()
        
        # Navigate to the CBS Sports Pickem pool URL
        target_url = "https://picks.cbssports.com/football/pickem/pools/my-pool-id===" 
        log_event(f"Navigating to: {target_url}")
        page.goto(target_url)
        
        # Wait for the page to load completely
        page.wait_for_load_state("networkidle")
        
        # Inspect the page structure
        log_event("Inspecting page structure...")
        
        # Check for game modules
        game_modules = page.query_selector_all('.gameModule')
        log_event(f"Found {len(game_modules)} elements with class '.gameModule'")
        
        # Check for alternative game containers
        games = page.query_selector_all('.game')
        log_event(f"Found {len(games)} elements with class '.game'")
        
        # Check for matchup containers
        matchups = page.query_selector_all('.matchup')
        log_event(f"Found {len(matchups)} elements with class '.matchup'")
        
        # Check for team names
        team_names = page.query_selector_all('.teamName')
        log_event(f"Found {len(team_names)} elements with class '.teamName'")
        
        # Check for alternative team name containers
        teams = page.query_selector_all('.team')
        log_event(f"Found {len(teams)} elements with class '.team'")
        
        # Check for game times
        game_times = page.query_selector_all('.gameTime')
        log_event(f"Found {len(game_times)} elements with class '.gameTime'")
        
        # Check for alternative time containers
        times = page.query_selector_all('.time')
        log_event(f"Found {len(times)} elements with class '.time'")
        
        # Check for team records
        records = page.query_selector_all('.record')
        log_event(f"Found {len(records)} elements with class '.record'")
        
        # If we found any game containers, let's examine the first one in detail
        if len(games) > 0:
            log_event("Examining first game element structure:")
            html = games[0].evaluate('el => el.outerHTML')
            log_event(f"HTML structure: {html}")
        elif len(game_modules) > 0:
            log_event("Examining first gameModule element structure:")
            html = game_modules[0].evaluate('el => el.outerHTML')
            log_event(f"HTML structure: {html}")
        elif len(matchups) > 0:
            log_event("Examining first matchup element structure:")
            html = matchups[0].evaluate('el => el.outerHTML')
            log_event(f"HTML structure: {html}")
        
        # Take a screenshot of the page for visual inspection
        page.screenshot(path="page_structure.png")
        log_event("Screenshot saved as 'page_structure.png'")
        
        print("✅ Page structure inspection complete. Check the logs for details.")
        print("   A screenshot has been saved as 'page_structure.png'")
        input("Press ENTER to close the browser...")
        
        log_event("Closing browser")
        browser.close()

if __name__ == "__main__":
    main()
