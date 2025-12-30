#!/usr/bin/env python3
"""
Batch scraper with timeout handling and partial saves
"""
import subprocess
import signal
import time
from pathlib import Path

def scrape_with_timeout(url, output_file, timeout=180):
    """
    Scrape a player with timeout, saving partial results
    Returns: (success, matches_scraped, message)
    """
    player_name = url.split('/players/')[1].split('/')[0]
    
    # Start scraping process
    proc = subprocess.Popen(
        ['python3', 'dupr_scraper.py', url, '-o', output_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        
        if proc.returncode == 0:
            # Success - extract match count from output
            for line in stdout.split('\n'):
                if 'Total matches scraped:' in line:
                    count = int(line.split(':')[1].strip())
                    return (True, count, 'Success')
            return (True, 0, 'Success (0 matches)')
        else:
            # Failed but might have partial data
            if Path(output_file).exists():
                # Check if CSV has data
                try:
                    import pandas as pd
                    df = pd.read_csv(output_file)
                    if len(df) > 0:
                        return (False, len(df), f'Partial ({len(df)} matches saved)')
                except:
                    pass
            return (False, 0, f'Failed (exit {proc.returncode})')
            
    except subprocess.TimeoutExpired:
        # Timeout - kill process but check for partial data
        proc.send_signal(signal.SIGTERM)
        time.sleep(2)
        proc.kill()
        
        # Check if any data was saved
        if Path(output_file).exists():
            try:
                import pandas as pd
                df = pd.read_csv(output_file)
                if len(df) > 0:
                    return (False, len(df), f'Timeout ({len(df)} matches saved)')
            except:
                pass
        
        return (False, 0, 'Timeout (no data)')


def main():
    # Get failed URLs from last run
    failed_urls = [
        'https://pickleball.com/players/linda-lang/rating-history',
        'https://pickleball.com/players/charlie-cannon/rating-history',
        'https://pickleball.com/players/justine-mangkornkeo/rating-history',
        'https://pickleball.com/players/luke-williams/rating-history',
        'https://pickleball.com/players/dena-quigley/rating-history',
        'https://pickleball.com/players/patricia-cayo/rating-history',
        'https://pickleball.com/players/amber-chong/rating-history',
        'https://pickleball.com/players/thomas-yu/rating-history',
        'https://pickleball.com/players/liam-meyer/rating-history',
        'https://pickleball.com/players/colby-bishop/rating-history',
        'https://pickleball.com/players/amanda-crain/rating-history',
        'https://pickleball.com/players/annelise-nguyen/rating-history',
        'https://pickleball.com/players/laura-pelton/rating-history',
        'https://pickleball.com/players/rob-evans/rating-history',
        'https://pickleball.com/players/madeline-welch/rating-history',
        'https://pickleball.com/players/michael-maldazys/rating-history',
        'https://pickleball.com/players/nicholas-button/rating-history',
        'https://pickleball.com/players/angie-cosma/rating-history',
        'https://pickleball.com/players/olivia-wisner/rating-history',
        'https://pickleball.com/players/aly-caliri/rating-history',
    ]
    
    print(f'Scraping {len(failed_urls)} players with 180s timeout...\n')
    
    success_count = 0
    partial_count = 0
    fail_count = 0
    total_matches = 0
    
    for i, url in enumerate(failed_urls, 1):
        player_name = url.split('/players/')[1].split('/')[0]
        output_file = f'player_data/{player_name}_dupr.csv'
        
        print(f'[{i}/{len(failed_urls)}] {player_name}...', end=' ', flush=True)
        
        success, matches, msg = scrape_with_timeout(url, output_file, timeout=180)
        
        print(msg)
        
        if success:
            success_count += 1
        elif matches > 0:
            partial_count += 1
        else:
            fail_count += 1
        
        total_matches += matches
        
        time.sleep(1)  # Be polite
    
    print(f'\n=== Summary ===')
    print(f'Success: {success_count}')
    print(f'Partial: {partial_count}')
    print(f'Failed: {fail_count}')
    print(f'Total matches: {total_matches:,}')


if __name__ == '__main__':
    main()
