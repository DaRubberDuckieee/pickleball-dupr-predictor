# Pickleball DUPR Reverse Rating Tool

A tool to scrape DUPR (Dynamic Universal Pickleball Rating) match data from pickleball.com and reverse engineer the rating algorithm.

## Project Status

✅ **Phase 1: Web Scraper & Data Collection** - COMPLETE  
⏳ Phase 2: Algorithm Reverse Engineering - TODO  
⏳ Phase 3: Web UI for Predictions - TODO  

## Installation

1. Create and activate virtual environment:
```bash
cd Pickleball-DUPR-Reverse-Rating
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
```

2. Install dependencies:
```bash
pip install selenium beautifulsoup4 pandas
```

3. Make sure you have Chrome/Chromium installed (required for Selenium)

## Usage

### Scraping Player Data

The main scraper script is `dupr_scraper.py`. It can be run from the command line:

**Basic usage:**
```bash
python dupr_scraper.py "https://pickleball.com/players/jessica-wang/rating-history"
```

**Options:**
```bash
python dupr_scraper.py <player_url> [options]

Options:
  --start-page INT    Page to start scraping from (default: 1)
  --max-pages INT     Maximum number of pages to scrape
  --output FILE       Output CSV file name (default: dupr_data.csv)
  --no-headless       Show browser window while scraping
```

**Examples:**
```bash
# Scrape first 5 pages
python dupr_scraper.py "https://pickleball.com/players/jessica-wang/rating-history" --max-pages 5

# Start from page 2, scrape 10 pages
python dupr_scraper.py "https://pickleball.com/players/jessica-wang/rating-history" --start-page 2 --max-pages 10

# Custom output file
python dupr_scraper.py "https://pickleball.com/players/jessica-wang/rating-history" --output my_data.csv

# Show browser (useful for debugging)
python dupr_scraper.py "https://pickleball.com/players/jessica-wang/rating-history" --no-headless
```

### Output Data Format

The scraper outputs a CSV file with the following key fields:

**Match Information:**
- `date`: Match date (YYYY-MM-DD)
- `team1_score`: Team 1's score
- `team2_score`: Team 2's score

**Individual Player Ratings (Team 1):**
- `team1_player1_rating_before`: Team 1 Player 1's DUPR before match
- `team1_player1_rating_after`: Team 1 Player 1's DUPR after match
- `team1_player1_rating_change`: Change in DUPR for Team 1 Player 1
- `team1_player2_rating_before`: Team 1 Player 2's DUPR before match
- `team1_player2_rating_after`: Team 1 Player 2's DUPR after match
- `team1_player2_rating_change`: Change in DUPR for Team 1 Player 2

**Individual Player Ratings (Team 2):**
- `team2_player1_rating_before`: Team 2 Player 1's DUPR before match
- `team2_player1_rating_after`: Team 2 Player 1's DUPR after match
- `team2_player1_rating_change`: Change in DUPR for Team 2 Player 1
- `team2_player2_rating_before`: Team 2 Player 2's DUPR before match
- `team2_player2_rating_after`: Team 2 Player 2's DUPR after match
- `team2_player2_rating_change`: Change in DUPR for Team 2 Player 2

**Team Averages:**
- `team1_avg_rating_before`: Average DUPR of Team 1 before match
- `team1_avg_rating_after`: Average DUPR of Team 1 after match
- `team2_avg_rating_before`: Average DUPR of Team 2 before match
- `team2_avg_rating_after`: Average DUPR of Team 2 after match
- `rating_differential`: Difference between team averages (team1 - team2)

**Additional Fields:**
- `observed_change_0` through `observed_change_3`: Raw rating changes as observed on the page (may not perfectly align with calculated changes due to parsing)

## Current Limitations

1. **Parser Accuracy**: The scraper uses pattern matching on rendered HTML. In some cases, ratings may not align perfectly with players due to variations in page structure.

2. **Rate Limiting**: The scraper includes delays between page requests (2 seconds) to be respectful to the server. Scraping many pages will take time.

3. **Match Details**: Currently captures ratings and scores, but not player names. This is a known limitation that may be addressed in future versions.

4. **JavaScript Dependency**: Requires Selenium with Chrome/Chromium since the site uses client-side rendering.

## Next Steps

### Phase 2: Algorithm Reverse Engineering
- Collect larger dataset (100+ matches)
- Analyze rating changes vs match outcomes
- Test hypotheses (Elo-based, Glicko-based, custom formula)
- Build predictive model

### Phase 3: Web UI
- Flask/FastAPI backend
- Simple HTML interface
- Input: your DUPR, partner DUPR, opponent DUPRs, hypothetical score
- Output: Predicted DUPR change

## Troubleshooting

**"ChromeDriver" error:**
- Make sure Chrome is installed
- Selenium should auto-download ChromeDriver, but you can manually install it if needed

**No matches found:**
- Check the URL is correct
- Try with `--no-headless` to see what's being rendered
- The site may have changed structure

**SSL warnings:**
- The urllib3 warnings can be safely ignored; they don't affect functionality

## License

This is a personal project for educational purposes.
