
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
    log_event("Starting Playwright session")
    with sync_playwright() as p:
        log_event("Launching browser")
        browser = p.chromium.launch(headless=False, slow_mo=200)
        
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
        target_url = "https://picks.cbssports.com/football/pickem/pools/my-pool-id===" 
        log_event(f"Navigating to: {target_url}")
        page.goto(target_url)

        print("👉 Please log in manually in the opened browser window.")
        print("   Watch the terminal for detailed debug logs of all Playwright actions.")
        input("Press ENTER here once you are logged in successfully...")

        log_event("Saving login state to cbs_storage.json")
        context.storage_state(path="cbs_storage.json")
        print("✅ Login state saved to cbs_storage.json")

        log_event("Closing browser")
        browser.close()

if __name__ == "__main__":
    main()
