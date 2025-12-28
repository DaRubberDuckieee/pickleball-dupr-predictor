#!/bin/bash

cd "/Users/jess/Documents/Coding Projects/Pickleball-DUPR-Reverse-Rating"

players=(
  "aaron-huie"
  "aaron-keller"
  "aaron-nakamura-weiser"
  "aaron-parker"
  "abhaydeep-singh"
  "abhishek-bhargava"
  "abla-mannarino"
  "abraham-reyes"
  "adam-baldwin"
  "adam-braddock"
  "adrian-cosma"
  "adrian-davila"
  "aidan-schenk"
  "aimy-tan"
  "akhil-mehta"
  "akiko-westerhout"
  "akshatha-vijendra"
  "alex-neumann"
  "alex-watanabe"
  "alvin-wang"
)

for player in "${players[@]}"; do
  echo "===================="
  echo "Scraping: $player"
  echo "===================="
  
  python3 dupr_scraper.py "https://pickleball.com/players/$player/rating-history"
  
  if [ -f dupr_data.csv ]; then
    mv dupr_data.csv "player_data/${player}_dupr.csv"
    echo "✓ Saved to player_data/${player}_dupr.csv"
  else
    echo "✗ Failed to scrape $player"
  fi
  
  sleep 2
done

echo ""
echo "===================="
echo "Batch scraping complete!"
echo "===================="
