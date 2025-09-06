
from playwright.sync_api import sync_playwright
import logging
import os
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
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

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Login to CBS Sports Pickem')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--manual', action='store_true', help='Manual login mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    
    # Debug: Print all environment variables if debug flag is set
    if args.debug:
        log_event("Environment variables loaded by dotenv:")
        for key, value in os.environ.items():
            if key.startswith('CBS_'):
                log_event(f"{key}: {value[:3]}{'*' * (len(value) - 3) if len(value) > 3 else ''}")
    
    # Get credentials from environment variables
    username = os.environ.get('CBS_USERNAME')
    password = os.environ.get('CBS_PASSWORD')
    pool_url = os.environ.get('CBS_POOL_URL')
    
    # Debug: Print credential status
    log_event(f"Username loaded: {'Yes' if username else 'No'}")
    log_event(f"Password loaded: {'Yes' if password else 'No'}")
    log_event(f"Pool URL loaded: {'Yes' if pool_url else 'No'}")
    
    # Check if we're in manual mode or missing credentials
    manual_login = args.manual or not (username and password)
    
    log_event("Starting Playwright session")
    with sync_playwright() as p:
        log_event("Launching browser")
        browser = p.chromium.launch(headless=args.headless, slow_mo=200)
        
        log_event("Creating new browser context")
        context = browser.new_context()
        
        # Add event listeners for various Playwright events
        page = context.new_page()
        
        # Add event listeners for navigation events
        page.on("framenavigated", lambda frame: log_event(f"Navigated to: {frame.url}"))
        page.on("request", lambda request: log_event(f"Request: {request.method} {request.url}"))
        page.on("response", lambda response: log_event(f"Response: {response.status} {response.url}"))
        page.on("console", lambda msg: log_event(f"Console {msg.type}: {msg.text}"))
        
        # Navigate to the CBS Sports Pickem pool URL
        log_event(f"Navigating to: {pool_url}")
        page.goto(pool_url)
        
        if manual_login:
            # Manual login mode
            print("👉 Please log in manually in the opened browser window.")
            print("   Watch the terminal for detailed debug logs of all Playwright actions.")
            input("Press ENTER here once you are logged in successfully...")
        else:
            # Automatic login using environment variables
            log_event("Attempting automatic login with provided credentials")
            try:
                # Wait for and click the Log In link
                log_event("Looking for Log In link")
                page.wait_for_selector('a[href*="cbssports.com/login"]', timeout=30000)
                log_in_link = page.query_selector('a[href*="cbssports.com/login"]')
                if log_in_link:
                    log_event("Found Log In link, clicking it")
                    log_in_link.click()
                    log_event("Clicked Log In link")
                else:
                    log_event("Could not find Log In link")
                    raise Exception("Log In link not found")
                
                # Wait for login form and fill credentials
                log_event("Waiting for login form")
                page.wait_for_selector('input[name="email"]', timeout=30000)
                
                log_event("Filling email")
                email_input = page.query_selector('input[name="email"]')
                email_input.fill(username)
                
                log_event("Filling password")
                password_input = page.query_selector('input[name="password"]')
                password_input.fill(password)
                
                # Click Continue button
                log_event("Clicking Continue button")
                continue_button = page.query_selector('button[data-testid="submit-button"]')
                if continue_button:
                    continue_button.click()
                    log_event("Clicked Continue button")
                else:
                    log_event("Could not find Continue button")
                    raise Exception("Continue button not found")
                
                # Wait for successful login
                log_event("Waiting for successful login")
                page.wait_for_selector('div.MuiBox-root div.MuiStack-root[data-cy]', timeout=60000)
                log_event("Login successful")
            except Exception as e:
                log_event(f"Error during automatic login: {str(e)}")
                print("\n❌ Automatic login encountered an issue. This might be due to a CAPTCHA or verification step.")
                print("Please complete any verification steps and log in manually if needed.")
                print("The script has already filled in your username and password from the .env file.")
                input("Press ENTER here once you are logged in successfully...")

        log_event("Saving login state to cbs_storage.json")
        context.storage_state(path="cbs_storage.json")
        print("✅ Login state saved to cbs_storage.json")

        log_event("Closing browser")
        browser.close()

if __name__ == "__main__":
    main()
