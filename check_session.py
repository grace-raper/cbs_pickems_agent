
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
    log_event("Starting Playwright session to check saved login state")
    with sync_playwright() as p:
        log_event("Launching browser")
        browser = p.chromium.launch(headless=False, slow_mo=200)
        
        log_event("Creating new browser context with saved storage state")
        context = browser.new_context(storage_state="cbs_storage.json")
        
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
        
        print("✅ Browser opened with saved CBS login state (if still valid).")
        print("   Watch the terminal for detailed debug logs of all Playwright actions.")
        input("Press ENTER to close...")
        
        log_event("Closing browser")
        browser.close()

if __name__ == "__main__":
    main()
