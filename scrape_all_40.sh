#!/bin/bash

cd "/Users/jess/Documents/Coding Projects/Pickleball-DUPR-Reverse-Rating"

players=(
  # Original 20
  "jessica-wang"
  "olivia-wisner"
  "michelle-fat"
  "clayton-truex"
  "jonathan-li"
  "wilbert-lam"
  "annelise-nguyen"
  "jordan-huntley"
  "terrence-drinkwater"
  "sam-young"
  "addison-wright"
  "allie-sinex"
  "ben-haun"
  "daniel-colon"
  "ella-cosma"
  "grace-bascue"
  "kristin-deverin"
  "megan-chow"
  "steven-ip"
  "takato-watanabe"
  # New 20
  "aanik-lohani"
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
  "alexa-schull"
  "alexander-coury"
  "alexander-crum"
  "alexander-huizar"
)

count=0
for player in "${players[@]}"; do
  count=$((count + 1))
  echo "===================="
  echo "[$count/40] Scraping: $player"
  echo "===================="
  
  python3 dupr_scraper.py "https://pickleball.com/players/$player/rating-history" 2>&1 | grep -E "Total matches"
  
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
echo "Total players: $(ls player_data/*.csv 2>/dev/null | wc -l | tr -d ' ')"
echo "===================="
