
from playwright.sync_api import sync_playwright
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('playwright_debug')

def log_event(message):
    logger.info(message)

def verify_login(page):
    """
    Verify that the login was successful by checking for specific elements on the page.
    Returns True if login is verified, False otherwise.
    """
    try:
        # Wait a bit for the page to fully render
        page.wait_for_timeout(2000)
        
        # Take a screenshot for verification
        log_event("Taking screenshot for verification")
        page.screenshot(path="login_verification.png")
        
        # First, check if we're on the login page with Sign Up/Log In buttons
        log_event("Checking if we're on a login page")
        
        # Check for the invite-row which appears on the login page
        invite_row = page.query_selector('div.invite-row')
        if invite_row:
            log_event("ERROR: Found invite-row element - this is the login page")
            return False
            
        # Look for navigation tabs (Picks, Standings, Players)
        log_event("Checking for navigation tabs")
        tabs_exist = (
            page.query_selector('a[role="tab"]:has-text("Picks")') is not None or
            page.query_selector('div[role="tablist"] a:has-text("Picks")') is not None
        )
        
        if not tabs_exist:
            log_event("ERROR: Navigation tabs not found - login may have failed")
            return False
        
        # Check for user name in the header (indicates logged in state)
        log_event("Checking for user name in header")
        user_element = page.query_selector('span.MuiTypography-noWrap:has-text("Grace Raper")')
        if user_element:
            log_event("SUCCESS: Found user name in header - definitely logged in")
        else:
            log_event("WARNING: Could not find user name in header, but navigation tabs exist")
            # Continue anyway as we found navigation tabs
            
        log_event("Login verification successful")
        return True
        
    except Exception as e:
        log_event(f"ERROR during login verification: {str(e)}")
        return False

def main():
    log_event("Starting Playwright session to check saved login state")
    with sync_playwright() as p:
        log_event("Launching browser")
        browser = p.chromium.launch(headless=False, slow_mo=200)
        
        log_event("Creating new browser context with saved storage state")
        context = browser.new_context(storage_state="cbs_storage.json")
        
        # Create a new page without verbose network event listeners
        page = context.new_page()
        
        # # Only log console errors which might be important
        # page.on("console", lambda msg: log_event(f"Console {msg.type}: {msg.text}") if msg.type == "error" else None)
        
        # Navigate to the CBS Sports Pickem pool URL from environment variables
        target_url = os.getenv("CBS_POOL_URL")
        if not target_url:
            log_event("ERROR: CBS_POOL_URL environment variable not found")
            print("❌ Error: CBS_POOL_URL not found in .env file")
            print("   Please make sure you have set CBS_POOL_URL in your .env file")
            return
            
        log_event(f"Navigating to: {target_url}")
        page.goto(target_url)
        
        # Use a fixed timeout instead of networkidle to avoid issues with dynamic ads
        log_event("Waiting 5 seconds for page to load...")
        page.wait_for_timeout(5000)  # 5 seconds
        
        # Verify login by checking for specific elements
        login_verified = verify_login(page)
        
        if login_verified:
            print("✅ Successfully verified CBS login state - you are properly logged in!")
            print("   Watch the terminal for detailed debug logs of all Playwright actions.")
        else:
            print("❌ Login verification failed - your session may have expired.")
            print("   Please run 'python login.py' to create a new session.")
        
        input("Press ENTER to close...")
        
        log_event("Closing browser")
        browser.close()

if __name__ == "__main__":
    main()
