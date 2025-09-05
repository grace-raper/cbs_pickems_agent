from playwright.sync_api import sync_playwright
import logging
import re
from datetime import datetime
import time
import json
import os
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('playwright_debug')

def log_event(message):
    logger.info(message)

def extract_odds_data(page):
    """Extract odds data from the matchup analysis popup"""
    try:
        log_event("Extracting odds data")
        odds_data = {}
        
        # Wait for odds section to appear
        page.wait_for_selector('div.MuiStack-root.latest-odds', timeout=5000)
        
        # Extract spread, money, and total odds
        try:
            # Get team names from the odds section
            team_elements = page.query_selector_all('div.MuiStack-root.latest-odds div.MuiStack-root div.MuiStack-root p.MuiTypography-body1')
            if len(team_elements) >= 2:
                away_team_odds = team_elements[0].inner_text().strip()
                home_team_odds = team_elements[1].inner_text().strip()
                odds_data['away_team_odds'] = away_team_odds
                odds_data['home_team_odds'] = home_team_odds
        except Exception as e:
            log_event(f"Error extracting team names from odds: {str(e)}")
        
        # Extract current odds
        try:
            odds_boxes = page.query_selector_all('div.MuiStack-root.latest-odds div.MuiBox-root.mui-style-1wwjoop')
            
            if len(odds_boxes) >= 6:  # We expect 6 boxes for spread, money, total (away and home)
                # Away team odds
                away_spread = odds_boxes[0].query_selector('p.MuiTypography-body1')
                away_spread_odds = odds_boxes[0].query_selector('p.MuiTypography-body1 + p.MuiTypography-body1')
                
                away_money = odds_boxes[1].query_selector('p.MuiTypography-body1')
                
                away_total = odds_boxes[2].query_selector('p.MuiTypography-body1')
                away_total_odds = odds_boxes[2].query_selector('p.MuiTypography-body1 + p.MuiTypography-body1')
                
                # Home team odds
                home_spread = odds_boxes[3].query_selector('p.MuiTypography-body1')
                home_spread_odds = odds_boxes[3].query_selector('p.MuiTypography-body1 + p.MuiTypography-body1')
                
                home_money = odds_boxes[4].query_selector('p.MuiTypography-body1')
                
                home_total = odds_boxes[5].query_selector('p.MuiTypography-body1')
                home_total_odds = odds_boxes[5].query_selector('p.MuiTypography-body1 + p.MuiTypography-body1')
                
                odds_data['current_odds'] = {
                    'away': {
                        'spread': away_spread.inner_text().strip() if away_spread else '',
                        'spread_odds': away_spread_odds.inner_text().strip() if away_spread_odds else '',
                        'money': away_money.inner_text().strip() if away_money else '',
                        'total': away_total.inner_text().strip() if away_total else '',
                        'total_odds': away_total_odds.inner_text().strip() if away_total_odds else ''
                    },
                    'home': {
                        'spread': home_spread.inner_text().strip() if home_spread else '',
                        'spread_odds': home_spread_odds.inner_text().strip() if home_spread_odds else '',
                        'money': home_money.inner_text().strip() if home_money else '',
                        'total': home_total.inner_text().strip() if home_total else '',
                        'total_odds': home_total_odds.inner_text().strip() if home_total_odds else ''
                    }
                }
        except Exception as e:
            log_event(f"Error extracting current odds: {str(e)}")
        
        # Extract opening odds
        try:
            opening_odds_element = page.query_selector('div.MuiStack-root.table-footer div.MuiStack-root')
            if opening_odds_element:
                opening_odds_texts = opening_odds_element.query_selector_all('p.MuiTypography-body1')
                if len(opening_odds_texts) >= 3:
                    # Skip the first element which is just the label "Opening"
                    opening_spread = opening_odds_texts[1].inner_text().strip()
                    opening_total = opening_odds_texts[2].inner_text().strip()
                    
                    odds_data['opening_odds'] = {
                        'spread': opening_spread,
                        'total': opening_total
                    }
        except Exception as e:
            log_event(f"Error extracting opening odds: {str(e)}")
            
        return odds_data
    except Exception as e:
        log_event(f"Error extracting odds data: {str(e)}")
        return {}

def extract_expert_picks(page):
    """Extract expert picks data from the matchup analysis popup"""
    try:
        log_event("Extracting expert picks data")
        expert_data = {}
        
        # Wait for expert picks section to appear
        page.wait_for_selector('div.MuiStack-root h3.MuiTypography-h3:text("Expert Picks")', timeout=5000)
        
        # Extract team pick counts
        try:
            team_picks = page.query_selector_all('div.MuiStack-root h3:text("Expert Picks") + div.MuiStack-root > div.MuiStack-root')
            
            if len(team_picks) >= 2:
                # First team
                team1_img = team_picks[0].query_selector('div.MuiAvatar-root img')
                team1_picks = team_picks[0].query_selector('p.MuiTypography-body1')
                
                # Second team
                team2_img = team_picks[1].query_selector('div.MuiAvatar-root img')
                team2_picks = team_picks[1].query_selector('p.MuiTypography-body1')
                
                if team1_img and team1_picks and team2_img and team2_picks:
                    # Extract team names from image URLs
                    team1_src = team1_img.get_attribute('src')
                    team2_src = team2_img.get_attribute('src')
                    
                    team1_name = extract_team_name_from_url(team1_src)
                    team2_name = extract_team_name_from_url(team2_src)
                    
                    team1_pick_count = team1_picks.inner_text().strip()
                    team2_pick_count = team2_picks.inner_text().strip()
                    
                    expert_data['team_picks'] = {
                        team1_name: team1_pick_count,
                        team2_name: team2_pick_count
                    }
        except Exception as e:
            log_event(f"Error extracting team pick counts: {str(e)}")
        
        # Extract individual expert picks
        try:
            expert_elements = page.query_selector_all('div.MuiTabs-list div.MuiStack-root[id^="expert-"]')
            experts = []
            
            for expert_element in expert_elements:
                expert_name = expert_element.query_selector('h6.MuiTypography-subtitle1')
                expert_role = expert_element.query_selector('span.MuiTypography-misc')
                expert_record = expert_element.query_selector('span.MuiTypography-menu')
                expert_pick_img = expert_element.query_selector('div.MuiStack-root div.MuiAvatar-root img')
                expert_pick_text = expert_element.query_selector('div.MuiStack-root span.MuiTypography-misc')
                
                if expert_name and expert_pick_img:
                    expert_info = {
                        'name': expert_name.inner_text().strip(),
                        'role': expert_role.inner_text().strip() if expert_role else '',
                        'record': expert_record.inner_text().strip() if expert_record else '',
                        'pick': expert_pick_text.inner_text().strip() if expert_pick_text else '',
                        'pick_team': extract_team_name_from_url(expert_pick_img.get_attribute('src'))
                    }
                    experts.append(expert_info)
            
            expert_data['experts'] = experts
        except Exception as e:
            log_event(f"Error extracting individual expert picks: {str(e)}")
            
        return expert_data
    except Exception as e:
        log_event(f"Error extracting expert picks data: {str(e)}")
        return {}

def extract_matchup_stats(page):
    """Extract offense/defense matchup stats from the matchup analysis popup"""
    try:
        log_event("Extracting matchup stats data")
        stats_data = {}
        
        # Wait for matchup section to appear
        page.wait_for_selector('div.MuiStack-root h3.MuiTypography-h3:text("Matchup")', timeout=5000)
        
        # Extract team names from matchup section
        try:
            team_sections = page.query_selector_all('div.MuiStack-root.mui-style-1i67s9, div.MuiStack-root.mui-style-1sqwbr3')
            
            if len(team_sections) >= 4:  # We expect 4 sections (2 for offense matchup, 2 for defense matchup)
                team1_img = team_sections[0].query_selector('div.MuiAvatar-root img')
                team2_img = team_sections[1].query_selector('div.MuiAvatar-root img')
                
                if team1_img and team2_img:
                    team1_name = extract_team_name_from_url(team1_img.get_attribute('src'))
                    team2_name = extract_team_name_from_url(team2_img.get_attribute('src'))
                    
                    stats_data['teams'] = {
                        'team1': team1_name,
                        'team2': team2_name
                    }
        except Exception as e:
            log_event(f"Error extracting team names from matchup stats: {str(e)}")
        
        # Extract offense vs defense stats
        try:
            # First matchup section (team1 offense vs team2 defense)
            offense_defense_sections = page.query_selector_all('div.MuiStack-root.mui-style-10p98jm')
            
            if len(offense_defense_sections) >= 2:
                # Process first section: team1 offense vs team2 defense
                team1_offense_stats = extract_stats_from_section(offense_defense_sections[0])
                
                # Process second section: team1 defense vs team2 offense
                team2_offense_stats = extract_stats_from_section(offense_defense_sections[1])
                
                stats_data['offense_defense_stats'] = {
                    'team1_offense_vs_team2_defense': team1_offense_stats,
                    'team2_offense_vs_team1_defense': team2_offense_stats
                }
        except Exception as e:
            log_event(f"Error extracting offense/defense stats: {str(e)}")
            
        return stats_data
    except Exception as e:
        log_event(f"Error extracting matchup stats data: {str(e)}")
        return {}

def extract_stats_from_section(section):
    """Helper function to extract stats from a matchup section"""
    stats = {}
    try:
        stat_rows = section.query_selector_all('div.MuiStack-root.mui-style-13na5pa')
        
        for row in stat_rows:
            # Get the stat name (e.g., "Total Yds", "Passing Yds", etc.)
            stat_name_element = row.query_selector('p.MuiTypography-body1')
            if not stat_name_element:
                continue
                
            stat_name = stat_name_element.inner_text().strip()
            
            # Get team1 rank and value
            team1_element = row.query_selector('div.MuiStack-root:first-child')
            team1_rank_elem = team1_element.query_selector('*:first-child') if team1_element else None
            team1_rank = team1_rank_elem.inner_text().strip() if team1_rank_elem else ''
            team1_value_elem = team1_element.query_selector('p.MuiTypography-body2') if team1_element else None
            team1_value = team1_value_elem.inner_text().strip() if team1_value_elem else ''
            
            # Get team2 rank and value
            team2_element = row.query_selector('div.MuiStack-root:last-child')
            team2_rank_elem = team2_element.query_selector('*:first-child') if team2_element else None
            team2_rank = team2_rank_elem.inner_text().strip() if team2_rank_elem else ''
            team2_value_elem = team2_element.query_selector('p.MuiTypography-body2') if team2_element else None
            team2_value = team2_value_elem.inner_text().strip() if team2_value_elem else ''
            
            stats[stat_name] = {
                'team1': {
                    'rank': team1_rank,
                    'value': team1_value
                },
                'team2': {
                    'rank': team2_rank,
                    'value': team2_value
                }
            }
    except Exception as e:
        log_event(f"Error extracting stats from section: {str(e)}")
    
    return stats

def extract_team_name_from_url(url):
    """Extract team name from image URL"""
    if not url:
        return ""
    
    try:
        # URLs are like: https://sports.cbsimg.net/fly/images/nfl/logos/team/417.svg
        # We'll map the team code to a name in a separate function
        match = re.search(r'team/([^.]+)', url)
        if match:
            team_code = match.group(1)
            return get_team_name_from_code(team_code)
        return ""
    except Exception:
        return ""

def get_team_name_from_code(code):
    """Map team code to team name"""
    # This is a simplified mapping - you might want to expand this
    team_codes = {
        '405': 'FALCONS',
        '431': 'BUCCANEERS',



    #     '410': 'BENGALS',
    #     '434': 'BROWNS',
    #     '417': 'CHIEFS',
    #     '428': 'CHARGERS',
    #     '407': 'BILLS',
    #     '409': 'BEARS',
    #     '413': 'COWBOYS',
    #     '414': 'EAGLES',
    #     '415': 'FALCONS',
    #     '416': 'GIANTS',
    #     '418': 'COLTS',
    #     '419': 'JAGUARS',
    #     '420': 'DOLPHINS',
    #     '421': 'VIKINGS',
    #     '422': 'PATRIOTS',
    #     '423': 'SAINTS',
    #     '424': 'RAIDERS',
    #     '425': 'JETS',
    #     '426': 'PANTHERS',
    #     '427': 'COMMANDERS',
    #     '429': 'STEELERS',
    #     '430': 'RAMS',
    #     '431': 'RAVENS',
    #     '432': 'SEAHAWKS',
    #     '433': 'BUCCANEERS',
    #     '435': 'TITANS',
    #     '436': 'BRONCOS',
    #     '437': 'PACKERS',
    #     '438': 'LIONS',
    #     '439': 'CARDINALS',
    #     '440': 'TEXANS',
    #     '441': '49ERS',
    #     '408': 'TEAM_NAME_HERE',
    #     '412': 'TEAM_NAME_HERE',
    #     '406': 'TEAM_NAME_HERE',
    #     '404': 'TEAM_NAME_HERE',
    #     '405': 'TEAM_NAME_HERE',
    #     '247415': 'TEAM_NAME_HERE',
    # }
    return team_codes.get(code, f"TEAM-{code}")

def extract_matchups(page):
    """Extract all matchups from the page with detailed analysis"""
    log_event("Extracting matchups from the page")
    
    # Wait for the page to load and matchups to appear
    # Using the MuiBox-root selector that contains matchups
    try:
        # Wait for content to load
        page.wait_for_selector('div.MuiBox-root div.MuiStack-root[data-cy]', timeout=60000)
        
        # Give a little extra time for everything to render
        time.sleep(2)
        
        # Get all matchup containers
        matchup_containers = page.query_selector_all('div.MuiBox-root div.MuiStack-root[data-cy]')
        log_event(f"Found {len(matchup_containers)} potential matchup containers")
        
        matchups = []
        
        for i, container in enumerate(matchup_containers):
            try:
                log_event(f"Processing matchup {i+1} of {len(matchup_containers)}")
                
                # Extract game time (Thu @ 5:20 PM)
                game_time_element = container.query_selector('h6.MuiTypography-subtitle2')
                game_time = game_time_element.inner_text().strip() if game_time_element else "Time not found"
                
                # Extract network (NBC, CBS, etc.)
                network_element = container.query_selector('div.MuiBox-root h6.MuiTypography-subtitle2:nth-child(3)')
                network = network_element.inner_text().strip() if network_element else ""
                
                # Extract away team (left side)
                away_team_element = container.query_selector('div.MuiStack-root.left-side h3.MuiTypography-h3')
                away_team = away_team_element.inner_text().strip() if away_team_element else "Team not found"
                
                # Extract away team record
                away_record_element = container.query_selector('div.MuiStack-root.left-side span.MuiTypography-misc')
                away_record = away_record_element.inner_text().strip() if away_record_element else "Record not found"
                
                # Extract home team (right side)
                home_team_element = container.query_selector('div.MuiStack-root.right-side h3.MuiTypography-h3')
                home_team = home_team_element.inner_text().strip() if home_team_element else "Team not found"
                
                # Extract home team record
                home_record_element = container.query_selector('div.MuiStack-root.right-side span.MuiTypography-misc')
                home_record = home_record_element.inner_text().strip() if home_record_element else "Record not found"
                
                # Check if either team is selected (has the item-selected class)
                away_selected = container.query_selector('div.MuiStack-root.left-side.item-selected') is not None
                home_selected = container.query_selector('div.MuiStack-root.right-side.item-selected') is not None
                
                # Determine which team was picked (if any)
                picked_team = None
                if away_selected:
                    picked_team = away_team
                    log_event(f"User picked: {away_team}")
                elif home_selected:
                    picked_team = home_team
                    log_event(f"User picked: {home_team}")
                
                # Create the basic matchup data
                matchup_data = {
                    'game_time': game_time,
                    'network': network,
                    'away_team': away_team,
                    'away_record': away_record,
                    'home_team': home_team,
                    'home_record': home_record,
                    'picked_team': picked_team
                }
                
                # Now click on the Matchup Analysis button to get additional data
                try:
                    # Find and click the Matchup Analysis button
                    analysis_button = container.query_selector('button[data-cy="matchup-analysis"]')
                    if analysis_button:
                        log_event(f"Clicking Matchup Analysis button for {away_team} @ {home_team}")
                        analysis_button.click()
                        
                        # Wait for the popup to appear
                        page.wait_for_selector('div.MuiStack-root.latest-odds, div.MuiStack-root h3:text("Expert Picks"), div.MuiStack-root h3:text("Matchup")', timeout=5000)
                        
                        # Give a little time for everything to load
                        time.sleep(1)
                        
                        # Extract odds data
                        odds_data = extract_odds_data(page)
                        if odds_data:
                            matchup_data['odds'] = odds_data
                            log_event("Added odds data to matchup")
                        
                        # Extract expert picks
                        expert_data = extract_expert_picks(page)
                        if expert_data:
                            matchup_data['expert_picks'] = expert_data
                            log_event("Added expert picks data to matchup")
                        
                        # Extract matchup stats
                        stats_data = extract_matchup_stats(page)
                        if stats_data:
                            matchup_data['matchup_stats'] = stats_data
                            log_event("Added matchup stats data to matchup")
                        
                        # Close the popup by clicking the X button
                        close_button = page.query_selector('svg.MuiSvgIcon-root[viewBox="0 0 24 24"] path[d^="M18.3 5.7"]')
                        if close_button:
                            log_event("Closing matchup analysis popup")
                            close_button.click()
                            time.sleep(0.5)  # Give time for popup to close
                        else:
                            log_event("Could not find close button for popup")
                    else:
                        log_event(f"Could not find Matchup Analysis button for {away_team} @ {home_team}")
                except Exception as e:
                    log_event(f"Error processing matchup analysis: {str(e)}")
                    log_event(traceback.format_exc())
                
                # Only add if we have valid team names
                if away_team != "Team not found" and home_team != "Team not found":
                    matchups.append(matchup_data)
                    
                    # Log the extraction with pick information
                    pick_info = f" - Picked: {picked_team}" if picked_team else ""
                    log_event(f"Extracted matchup: {away_team} ({away_record}) @ {home_team} ({home_record}) - {game_time} on {network}{pick_info}")
            except Exception as e:
                log_event(f"Error extracting matchup details: {str(e)}")
                log_event(traceback.format_exc())
        
        return matchups
    except Exception as e:
        log_event(f"Error during matchup extraction: {str(e)}")
        log_event(traceback.format_exc())
        return []

def save_matchups_to_json(matchups, filename="matchups.json"):
    """Save matchups to a JSON file"""
    try:
        # Create the output directory if it doesn't exist
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Add timestamp to the data
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "matchups": matchups
        }
        
        # Write to JSON file
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
            
        log_event(f"Successfully saved {len(matchups)} matchups to {filename}")
        return True
    except Exception as e:
        log_event(f"Error saving matchups to JSON: {str(e)}")
        return False

def print_matchups(matchups):
    """Print matchups in the requested format"""
    print("\n" + "="*50)
    print("WEEKLY MATCHUPS")
    print("="*50)
    
    for matchup in matchups:
        # Print game time and network if available
        game_info = matchup['game_time']
        if matchup.get('network'):
            game_info += f" on {matchup['network']}"
        
        print(f"\n{game_info}\n")
        
        # Print away team info
        print(f"{matchup['away_record']}")
        print(f"{matchup['away_team']}")
        
        # Print home team info
        print(f"\n{matchup['home_record']}")
        print(f"{matchup['home_team']}")
        
        # Print user's pick if available
        if matchup.get('picked_team'):
            print(f"\n🏈 Your pick: {matchup['picked_team']} 🏈")
        
        print("\n" + "-"*30)
    
    if not matchups:
        print("\nNo matchups found. Please check if you're logged in and the page has loaded correctly.")
    
    print("\n")

def main():
    """Main function to run the script"""
    log_event("Starting script")
    
    # Define output JSON file path
    output_file = "matchups.json"
    
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
        
        # Wait for the page to load - use a more reliable strategy
        log_event("Waiting for page to load")
        try:
            # Wait for a specific element that indicates content has loaded
            log_event("Waiting for content to appear")
            page.wait_for_selector('div.MuiBox-root div.MuiStack-root[data-cy]', timeout=60000)
            log_event("Content has appeared")
            
            # Give extra time for dynamic content to load
            log_event("Waiting additional time for dynamic content")
            time.sleep(5)
            
            # Extract matchups
            matchups = extract_matchups(page)
            
            # Print matchups to console
            print_matchups(matchups)
            
            # Save matchups to JSON file
            if matchups:
                if save_matchups_to_json(matchups, output_file):
                    print(f"\n✅ Matchups saved to {output_file}")
                else:
                    print(f"\n❌ Failed to save matchups to {output_file}")
            
        except Exception as e:
            log_event(f"Error during page loading or extraction: {str(e)}")
            print(f"\nError: {str(e)}\n")
            
            # Take a screenshot to help debug
            try:
                page.screenshot(path="page_error.png")
                log_event("Saved screenshot to page_error.png")
                print("Screenshot saved to page_error.png for debugging")
            except Exception as screenshot_error:
                log_event(f"Failed to take screenshot: {str(screenshot_error)}")
        
        # Close the browser
        log_event("Closing browser")
        browser.close()

if __name__ == "__main__":
    main()
