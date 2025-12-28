#!/usr/bin/env python3
"""
DUPR Rating History Scraper

Scrapes match data from pickleball.com player rating history pages.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Optional
import time
import argparse


class DUPRScraper:
    """Scraper for DUPR rating history from pickleball.com"""
    
    def __init__(self, headless=True):
        self.base_url = "https://pickleball.com"
        self.headless = headless
        self.driver = None
    
    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        if self.driver:
            return
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def __del__(self):
        """Clean up driver on deletion"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def scrape_player_rating_history(self, player_url: str, start_page: int = 1, max_pages: Optional[int] = None) -> pd.DataFrame:
        """
        Scrape all rating history for a player
        
        Args:
            player_url: Full URL to player's rating history page
            start_page: Page number to start scraping from (default: 1)
            max_pages: Maximum number of pages to scrape (None for all pages)
            
        Returns:
            DataFrame with all match data
        """
        self._init_driver()
        
        # Extract player name from URL (e.g., "jessica-wang" -> "Jessica Wang")
        player_slug = player_url.split('/players/')[-1].split('/')[0].split('?')[0]
        player_name = ' '.join(word.capitalize() for word in player_slug.split('-'))
        print(f"Scraping matches for: {player_name}")
        
        all_matches = []
        page = start_page
        pages_scraped = 0
        self._empty_page_count = 0  # Track consecutive empty pages
        
        while True:
            if max_pages and pages_scraped >= max_pages:
                break
                
            # Construct URL with page parameter
            if '?' in player_url:
                base_url = player_url.split('?')[0]
                url = f"{base_url}?current_page={page}"
            else:
                url = f"{player_url}?current_page={page}"
            
            print(f"Scraping page {page}...", end=' ')
            
            try:
                self.driver.get(url)
                
                # Wait for page to load
                wait = WebDriverWait(self.driver, 15)
                time.sleep(4)  # Give JavaScript time to render
                
                # Get the rendered page
                page_source = self.driver.page_source
                
                # Parse matches from rendered HTML
                matches = self._parse_matches_from_html(page_source, player_name)
                
            except Exception as e:
                print(f"Error: {e}")
                break
            
            if not matches:
                print("No matches found on this page")
                # Don't break immediately - the page might be empty but continue to check next pages
                # Only stop after multiple consecutive empty pages
                empty_page_count = getattr(self, '_empty_page_count', 0) + 1
                self._empty_page_count = empty_page_count
                
                if empty_page_count >= 3:
                    print("Found 3 consecutive empty pages, stopping")
                    break
            else:
                # Reset counter when we find matches
                self._empty_page_count = 0
                all_matches.extend(matches)
                print(f"Found {len(matches)} matches")
            
            page += 1
            pages_scraped += 1
            time.sleep(2)  # Be polite to the server
        
        if not all_matches:
            print("\nNo matches found!")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_matches)
        print(f"\nTotal matches scraped: {len(df)}")
        return df
    
    def _parse_matches_from_html(self, html: str, player_name: str) -> List[Dict]:
        """Parse match data from rendered HTML using player name as delimiter
        
        Args:
            html: Rendered HTML from page
            player_name: Name of the player (e.g., "Jessica Wang") to use as match delimiter
        """
        # TODO: Handle edge case where player plays against/with someone of the same name
        soup = BeautifulSoup(html, 'html.parser')
        matches = []
        
        # Find the desktop table view only (to avoid duplicates from mobile view)
        # Look for divs with both 'hidden' and 'md:block' classes
        desktop_sections = soup.find_all('div', class_=lambda x: x and 'hidden' in x and 'md:block' in x)
        
        if not desktop_sections:
            # Fallback to full page if desktop view not found
            text = soup.get_text()
        else:
            # Get text only from the desktop section with a table
            text = ''
            for section in desktop_sections:
                if section.find('table'):
                    text = section.get_text()
                    break
            
            # If no table found, use first desktop section
            if not text:
                text = desktop_sections[0].get_text() if desktop_sections else soup.get_text()
        
        # Date pattern
        date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+,\s+\d{4}'
        
        # Find the "Processed" section to know where matches start (only in mobile view)
        # Desktop table view starts directly with matches
        processed_idx = text.find('Processed')
        if processed_idx == -1:
            # No "Processed" found - might be desktop table view, use full text
            match_text = text
        else:
            # Get text after "Processed"
            match_text = text[processed_idx:]
        
        # Split by player name pattern
        # Pattern can be:
        # - "Jessica WangF | WA, USA" (no age)
        # - "Olivia Wisner26 | F | USA" (with age)
        # Try both patterns
        
        # First try with age: "Name[digits] | [F|M] |"
        split_pattern = None
        is_regex = False
        for gender in ['F', 'M']:
            # Check if pattern exists with or without age
            if f"{player_name}{gender} | " in match_text:
                split_pattern = f"{player_name}{gender} | "
                is_regex = False
                break
            # Also check for age variant: "Name[digits] | F |"
            elif re.search(rf"{re.escape(player_name)}\d+\s*\|\s*{gender}\s*\|", match_text):
                # Use regex split for this pattern
                split_pattern = rf"{re.escape(player_name)}\d+\s*\|\s*{gender}\s*\|"
                is_regex = True
                break
        
        if not split_pattern:
            return []
        
        # Split the text by player occurrences
        if is_regex:
            # Regex pattern - use re.split
            match_chunks = re.split(split_pattern, match_text)[1:]  # Skip first chunk
        else:
            # String pattern - use str.split
            match_chunks = match_text.split(split_pattern)[1:]  # Skip first chunk
        
        print(f"  Found {len(match_chunks)} potential match chunks")
        
        # Parse each match chunk
        for chunk in match_chunks:
            # Extract date from this chunk
            date_match = re.search(date_pattern, chunk)
            match_date = None
            if date_match:
                try:
                    match_date = datetime.strptime(date_match.group(), '%b %d, %Y').strftime('%Y-%m-%d')
                except:
                    pass
            
            # Extract player names from chunk
            # Format: "NameF | Location" or "NameM | Location"
            # Pattern: Name followed by optional age, then F/M marker and pipe
            # The regex captures:
            # - First letter capitalized
            # - Rest lowercase (with hyphens for hyphenated names)
            # - Multi-word names (space + another capitalized word)
            # - Optional age before gender marker: "Name23 | F |"
            # - Gender marker: F or M
            
            # Find all names in the format: "Name[age] | [F|M] |"
            # Need to handle spacing variations and capture the name part only
            all_names = re.findall(
                r'([A-Z][a-z]+(?:[\s-][A-Z][a-z]+)*)\s*(?:\d+\s*\|\s*)?[FM]\s*\|', 
                chunk
            )
            
            # Assign whatever names we found (partner is first, then opponents)
            # Even if we have < 3 names, store what we have
            player_names = all_names[:3] if len(all_names) >= 3 else all_names
            
            # Collect ratings and rating changes
            # Format: before (X.XXX), change (+/-X.XXX or +/-0.XXX), before, change, ...
            # Use pattern to match both ratings (always positive, 1+ digits) and changes (may be negative, 0.XXX or X.XXX)
            # First capture ratings: positive numbers with 3 decimal places
            all_numbers = re.findall(r'(-?\d\.\d{3})', chunk)
            ratings = [float(r) for r in all_numbers]
            
            
            # Determine if player won or lost and extract scores
            # Pattern examples (concatenated HTML):
            # Loss: "014161<01<1416" = 0 games, score appears after SECOND <
            # Win: "10>116" = 1 game won, score appears after >
            # Win 2 games: "20>119116" = 2 games won
            
            won = None
            score_digits = None
            
            # Check for loss pattern first (has two < symbols)
            loss_match = re.search(r'(\d+)<\d+<(\d+)', chunk)
            if loss_match:
                # Loss: games won is 0, scores after second <
                won = False
                score_digits = loss_match.group(2)
            else:
                # Check for win pattern (single > symbol)
                win_match = re.search(r'(\d)>(\d+)', chunk)
                if win_match:
                    games_won = int(win_match.group(1))
                    won = games_won > 0
                    score_digits = win_match.group(2)
            
            # Parse scores greedily from score_digits
            # Games go to 11 or 15, so valid scores are typically 0-15 (or up to 20 for tiebreaks)
            # Parse: take 2 digits if they form 10-20, else take 1 digit
            scores = []
            if score_digits:
                parsed_scores = []
                i = 0
                while i < len(score_digits) and len(parsed_scores) < 6:  # Max 6 scores (3 games)
                    if i + 1 < len(score_digits):
                        two_digit = int(score_digits[i:i+2])
                        # Check if this looks like a valid game score (10-20)
                        if 10 <= two_digit <= 20:
                            parsed_scores.append(str(two_digit))
                            i += 2
                            continue
                    # Take single digit (0-9)
                    parsed_scores.append(score_digits[i])
                    i += 1
                
                # Pad to 6 elements for tuple format
                while len(parsed_scores) < 6:
                    parsed_scores.append('')
                
                scores = [tuple(parsed_scores)]
            
            # Collect rating changes
            changes = [float(c) for c in re.findall(r'(-\d\.\d{3,5})', chunk)]
            
            match_data = {
                'date': match_date,
                'ratings': ratings,
                'scores': scores,
                'changes': changes,
                'player_names': player_names,
                'won': won,
                'raw_chunk': chunk[:300]  # Store more for debugging
            }
            
            if self._is_valid_match(match_data):
                matches.append(match_data)
        
        # Convert raw data to structured format
        structured_matches = []
        for match in matches:
            structured = self._structure_match_data(match, player_name)
            if structured:
                structured_matches.append(structured)
        
        return structured_matches
    
    def _is_valid_match(self, match: Dict) -> bool:
        """Check if match has minimum required data"""
        return (
            len(match.get('ratings', [])) >= 4 and
            len(match.get('scores', [])) >= 1
        )
    
    def _structure_match_data(self, raw_match: Dict, player1_name: str = None) -> Optional[Dict]:
        """Convert raw match data to structured format"""
        ratings = raw_match.get('ratings', [])
        scores = raw_match.get('scores', [])
        changes = raw_match.get('changes', [])
        player_names = raw_match.get('player_names', [])
        won = raw_match.get('won')
        
        # Skip singles matches - we only want doubles
        # Singles matches have only 1 opponent (no partner)
        if len(player_names) < 2:
            return None
        
        if len(ratings) < 4 or not scores:
            return None
        
        # Parse multi-game scores
        # scores is a tuple like ('11', '9', '11', '6', '', '') for 2 games
        # or ('11', '9', '', '', '', '') for 1 game
        score = scores[0]
        
        # For losses, the scores are in opponent's favor order (their score, our score)
        # For wins, scores are in our favor order (our score, opponent's score)
        # We need to check if we need to swap based on won flag
        
        structured = {
            'date': raw_match.get('date'),
        }
        
        # Add player names
        structured['team1_player1_name'] = player1_name  # From URL
        
        # Get other player names from chunk parsing
        # Assign whatever names we found, using None for missing ones
        structured['team1_player2_name'] = player_names[0] if len(player_names) > 0 else None  # Partner
        structured['team2_player1_name'] = player_names[1] if len(player_names) > 1 else None  # Opponent 1  
        structured['team2_player2_name'] = player_names[2] if len(player_names) > 2 else None  # Opponent 2
        
        # Parse game scores
        # Format: game1_team1_score, game1_team2_score, game2_team1_score, game2_team2_score, game3_team1_score, game3_team2_score
        # Scores are parsed in order from HTML: first score, second score
        # For losses like "01<1416": 14 (our score), 16 (their score)
        # For wins like "10>116": 11 (our score), 6 (their score)
        # So actually NO swapping needed - scores are already in our_score, their_score order
        structured['game1_team1_score'] = int(score[0]) if score[0] else None
        structured['game1_team2_score'] = int(score[1]) if score[1] else None
        
        if score[2] and score[3]:  # Game 2 exists
            structured['game2_team1_score'] = int(score[2])
            structured['game2_team2_score'] = int(score[3])
        else:
            structured['game2_team1_score'] = None
            structured['game2_team2_score'] = None
            
        if len(score) > 4 and score[4] and score[5]:  # Game 3 exists
            structured['game3_team1_score'] = int(score[4])
            structured['game3_team2_score'] = int(score[5])
        else:
            structured['game3_team1_score'] = None
            structured['game3_team2_score'] = None
        
        # IMPORTANT: The website shows ratings in this pattern:
        # [before1, change1, after1, before2, change2, after2, before3, change3, after3, before4, change4, after4]
        # Indices: [0,1,2, 3,4,5, 6,7,8, 9,10,11]
        # Pattern: every 3 numbers = (before, change, after) for one player
        
        if len(ratings) >= 12:
            # Team 1 player 1: indices 0,1,2
            structured['team1_player1_rating_before'] = ratings[0]
            structured['team1_player1_rating_change'] = ratings[1]
            structured['team1_player1_rating_after'] = ratings[2]
            
            # Team 1 player 2: indices 3,4,5
            structured['team1_player2_rating_before'] = ratings[3]
            structured['team1_player2_rating_change'] = ratings[4]
            structured['team1_player2_rating_after'] = ratings[5]
            
            # Team 2 player 1: indices 6,7,8
            structured['team2_player1_rating_before'] = ratings[6]
            structured['team2_player1_rating_change'] = ratings[7]
            structured['team2_player1_rating_after'] = ratings[8]
            
            # Team 2 player 2: indices 9,10,11
            structured['team2_player2_rating_before'] = ratings[9]
            structured['team2_player2_rating_change'] = ratings[10]
            structured['team2_player2_rating_after'] = ratings[11]
        elif len(ratings) >= 8:
            # Fewer ratings - likely because some rating changes are 0
            # When change is 0, website shows: [before, before] instead of [before, 0, after]
            # We need to infer the pattern by checking for duplicates
            # Pattern could be: [before1, after1, before2, after2, before3, after3, before4, after4]
            # OR: [before1, change1, after1, before2, change2, after2, ...] with some 0 changes missing
            
            # Try to detect pattern: if ratings[0] == ratings[1], it's likely [before, before] (0 change)
            # Otherwise assume normal [before, change, after] pattern
            
            # For now, assume 8 ratings = [before1, after1, before2, after2, before3, after3, before4, after4]
            # This is the pattern when all changes are 0
            structured['team1_player1_rating_before'] = ratings[0]
            structured['team1_player1_rating_change'] = ratings[1] - ratings[0]
            structured['team1_player1_rating_after'] = ratings[1]
            
            structured['team1_player2_rating_before'] = ratings[2]
            structured['team1_player2_rating_change'] = ratings[3] - ratings[2]
            structured['team1_player2_rating_after'] = ratings[3]
            
            structured['team2_player1_rating_before'] = ratings[4]
            structured['team2_player1_rating_change'] = ratings[5] - ratings[4]
            structured['team2_player1_rating_after'] = ratings[5]
            
            structured['team2_player2_rating_before'] = ratings[6]
            structured['team2_player2_rating_change'] = ratings[7] - ratings[6]
            structured['team2_player2_rating_after'] = ratings[7]
        else:
            # Skip matches with insufficient data
            return None
        
        return structured


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description='Scrape DUPR rating history from pickleball.com')
    parser.add_argument('player_url', help='URL to player rating history page')
    parser.add_argument('--start-page', type=int, default=1, help='Page to start scraping from (default: 1)')
    parser.add_argument('--max-pages', type=int, default=None, help='Maximum number of pages to scrape')
    parser.add_argument('--output', '-o', default='dupr_data.csv', help='Output CSV file name')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window')
    
    args = parser.parse_args()
    
    scraper = DUPRScraper(headless=not args.no_headless)
    
    try:
        df = scraper.scrape_player_rating_history(
            args.player_url, 
            start_page=args.start_page,
            max_pages=args.max_pages
        )
        
        if not df.empty:
            # Save to CSV
            df.to_csv(args.output, index=False)
            print(f"\n✓ Data saved to {args.output}")
            print(f"✓ Columns: {', '.join(df.columns.tolist())}")
            print(f"✓ Shape: {df.shape[0]} matches × {df.shape[1]} fields")
            
            # Show sample
            print("\nSample data:")
            sample_cols = ['date', 'game1_team1_score', 'game1_team2_score']
            if 'team1_player2_name' in df.columns:
                sample_cols.extend(['team1_player2_name', 'team2_player1_name'])
            print(df[sample_cols].head())
        else:
            print("\n✗ No data scraped!")
            return 1
    finally:
        del scraper
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
