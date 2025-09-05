from playwright.sync_api import sync_playwright
import logging
import json

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
    log_event("Starting Playwright session to inspect HTML structure")
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
        
        # Take a screenshot of the page for visual inspection
        page.screenshot(path="page_structure.png")
        log_event("Screenshot saved as 'page_structure.png'")
        
        # Get the HTML content of the page
        html_content = page.content()
        
        # Save the HTML content to a file for inspection
        with open("page_content.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        log_event("HTML content saved to 'page_content.html'")
        
        # Try to find elements that might contain game information
        print("\nSearching for potential game containers...")
        
        # Look for elements with common game-related terms in their attributes
        selectors = [
            "div[class*='game']",
            "div[class*='match']",
            "div[class*='contest']",
            "div[class*='event']",
            "div[class*='fixture']",
            "div[id*='game']",
            "div[id*='match']",
            "section[class*='game']",
            "section[class*='match']",
            "li[class*='game']",
            "li[class*='match']"
        ]
        
        for selector in selectors:
            elements = page.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} elements matching '{selector}'")
                if len(elements) > 0:
                    # Print the HTML of the first element
                    html = elements[0].evaluate('el => el.outerHTML')
                    print(f"Sample HTML: {html[:200]}...\n")
        
        # Execute JavaScript to get all elements with their classes
        elements_info = page.evaluate('''() => {
            const allElements = document.querySelectorAll('*');
            const result = [];
            
            for (const el of allElements) {
                if (el.className && typeof el.className === 'string' && 
                    (el.className.includes('game') || 
                     el.className.includes('match') || 
                     el.className.includes('team') || 
                     el.className.includes('contest') ||
                     el.className.includes('event'))) {
                    result.push({
                        tagName: el.tagName.toLowerCase(),
                        className: el.className,
                        id: el.id || null,
                        text: el.textContent.trim().substring(0, 50)
                    });
                }
            }
            
            return result;
        }''')
        
        # Print elements with game-related classes
        if elements_info:
            print("\nElements with game-related classes:")
            for info in elements_info[:20]:  # Limit to first 20 to avoid overwhelming output
                print(f"{info['tagName']} - class: {info['className']} - id: {info['id']} - text: {info['text']}")
        
        print("\n✅ Page structure inspection complete.")
        print("   HTML content saved to 'page_content.html'")
        print("   Screenshot saved as 'page_structure.png'")
        input("Press ENTER to close the browser...")
        
        log_event("Closing browser")
        browser.close()

if __name__ == "__main__":
    main()
