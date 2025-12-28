# Quick Start Guide

## Setup (One-time)

```bash
# Navigate to project directory
cd "/Users/jess/Documents/Coding Projects/Pickleball-DUPR-Reverse-Rating"

# Activate virtual environment
source venv/bin/activate

# Verify installation
python dupr_scraper.py --help
```

## Scrape Data

### Quick scrape (2-5 pages)
```bash
python dupr_scraper.py "https://pickleball.com/players/jessica-wang/rating-history" --max-pages 5
```

### Comprehensive scrape (all pages)
```bash
python dupr_scraper.py "https://pickleball.com/players/jessica-wang/rating-history"
```

### Custom output
```bash
python dupr_scraper.py "https://pickleball.com/players/jessica-wang/rating-history" \
  --max-pages 10 \
  --output my_data.csv
```

## Analyze Data

Once you have CSV data, you can analyze it with pandas:

```python
import pandas as pd

# Load data
df = pd.read_csv('dupr_data.csv')

# Show summary
print(f"Total matches: {len(df)}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")

# Calculate average rating changes
print(f"Avg team1 player1 change: {df['team1_player1_change'].mean():.4f}")
print(f"Avg team2 player1 change: {df['team2_player1_change'].mean():.4f}")

# Show matches with biggest upsets (lower rated team won)
df['rating_diff'] = df['team1_avg_before'] - df['team2_avg_before']
upsets = df[df['rating_diff'] < -0.5].sort_values('rating_diff')
print("\nBiggest upsets:")
print(upsets[['date', 'winner_score', 'loser_score', 'rating_diff']])
```

## Next Steps

1. **Collect more data**: Scrape multiple players' histories
2. **Analyze patterns**: Look for relationships between rating differentials and rating changes
3. **Build model**: Use scikit-learn to predict rating changes
4. **Create web UI**: Build Flask app for predictions

## Deactivate Environment

When done:
```bash
deactivate
```
