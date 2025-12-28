#!/usr/bin/env python3
"""
Add temporal features to improve R² to 90%+
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error
import glob

# Load all player data WITH chronological ordering
all_data = []

for csv_file in glob.glob('player_data/*.csv'):
    try:
        df = pd.read_csv(csv_file)
        player_name = csv_file.split('/')[-1].replace('_dupr.csv', '')
        
        # Convert dates and sort chronologically
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values('date')
        
        # Add match sequence number for this player
        df['match_seq'] = range(len(df))
        
        # Calculate days since first match
        if df['date'].notna().any():
            first_date = df[df['date'].notna()]['date'].min()
            df['days_since_start'] = (df['date'] - first_date).dt.days
        else:
            df['days_since_start'] = 0
        
        # Process each player in each match
        for idx, row in df.iterrows():
            for team, player_idx in [('team1', 1), ('team1', 2), ('team2', 1), ('team2', 2)]:
                prefix = f'{team}_player{player_idx}_'
                
                if pd.notna(row[f'{prefix}rating_before']) and pd.notna(row[f'{prefix}rating_change']):
                    # Get opponent and partner info
                    if team == 'team1':
                        opp_avg = (row['team2_player1_rating_before'] + row['team2_player2_rating_before']) / 2
                        partner_idx = 2 if player_idx == 1 else 1
                        partner_rating = row[f'team1_player{partner_idx}_rating_before']
                        opp1, opp2 = row['team2_player1_rating_before'], row['team2_player2_rating_before']
                        score1, score2 = row['game1_team1_score'], row['game1_team2_score']
                    else:
                        opp_avg = (row['team1_player1_rating_before'] + row['team1_player2_rating_before']) / 2
                        partner_idx = 2 if player_idx == 1 else 1
                        partner_rating = row[f'team2_player{partner_idx}_rating_before']
                        opp1, opp2 = row['team1_player1_rating_before'], row['team1_player2_rating_before']
                        score1, score2 = row['game1_team2_score'], row['game1_team1_score']
                    
                    if pd.notna(score1) and pd.notna(score2):
                        all_data.append({
                            'player_name': player_name,
                            'player_rating': row[f'{prefix}rating_before'],
                            'partner_rating': partner_rating,
                            'opp_avg': opp_avg,
                            'opp1_rating': opp1,
                            'opp2_rating': opp2,
                            'won': 1 if score1 > score2 else 0,
                            'score_margin': score1 - score2,
                            'rating_change': row[f'{prefix}rating_change'],
                            # TEMPORAL FEATURES
                            'match_seq': row['match_seq'],
                            'days_since_start': row['days_since_start'],
                        })
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
        continue

df = pd.DataFrame(all_data)
print(f"Total records: {len(df)}")
print()

# Create all features (existing + temporal)
df['rating_diff'] = df['player_rating'] - df['opp_avg']
df['partner_diff'] = df['player_rating'] - df['partner_rating']
df['team_avg'] = (df['player_rating'] + df['partner_rating']) / 2
df['team_vs_opp'] = df['team_avg'] - df['opp_avg']
df['opp_spread'] = abs(df['opp1_rating'] - df['opp2_rating'])
df['won_x_rating_diff'] = df['won'] * df['rating_diff']
df['won_x_score_margin'] = df['won'] * df['score_margin']
df['rating_squared'] = df['player_rating'] ** 2
df['total_points'] = abs(df['score_margin'])
df['expected_outcome'] = 1 / (1 + 10 ** ((df['opp_avg'] - df['player_rating']) / 4))
df['surprise'] = df['won'] - df['expected_outcome']

# TEMPORAL FEATURES
df['is_early_match'] = (df['match_seq'] < 10).astype(int)  # First 10 matches
df['match_experience'] = np.log1p(df['match_seq'])  # Log of matches played
df['days_log'] = np.log1p(df['days_since_start'])  # Log of days
df['matches_per_day'] = df['match_seq'] / (df['days_since_start'] + 1)  # Activity rate

# Calculate rolling stats (last 5 matches for each player)
df = df.sort_values(['player_name', 'match_seq'])
df['recent_win_rate'] = df.groupby('player_name')['won'].transform(lambda x: x.rolling(5, min_periods=1).mean())
df['recent_avg_change'] = df.groupby('player_name')['rating_change'].transform(lambda x: x.rolling(5, min_periods=1).mean().shift(1))
df['rating_volatility'] = df.groupby('player_name')['rating_change'].transform(lambda x: x.rolling(10, min_periods=2).std().shift(1))

# Fill NaN values
df['recent_avg_change'] = df['recent_avg_change'].fillna(0)
df['rating_volatility'] = df['rating_volatility'].fillna(df['rating_volatility'].median())

print("="*80)
print("MODEL WITH TEMPORAL FEATURES")
print("="*80)

# Features without temporal
basic_features = ['won', 'rating_diff', 'score_margin', 'total_points', 'partner_diff', 'team_vs_opp',
                 'won_x_rating_diff', 'won_x_score_margin', 'rating_squared', 'surprise', 'opp_spread',
                 'player_rating', 'partner_rating', 'opp_avg']

# Features WITH temporal
temporal_features = basic_features + ['is_early_match', 'match_experience', 'days_log', 'matches_per_day',
                                      'recent_win_rate', 'recent_avg_change', 'rating_volatility']

y = df['rating_change'].values

# Model WITHOUT temporal
print("\nWithout Temporal Features:")
X_basic = df[basic_features].values
gb_basic = GradientBoostingRegressor(n_estimators=200, max_depth=6, random_state=42, learning_rate=0.05)
gb_basic.fit(X_basic, y)
r2_basic = r2_score(y, gb_basic.predict(X_basic))
mae_basic = mean_absolute_error(y, gb_basic.predict(X_basic))
print(f"  R² = {r2_basic:.4f}, MAE = {mae_basic:.4f}")

# Model WITH temporal
print("\nWith Temporal Features:")
X_temporal = df[temporal_features].values
gb_temporal = GradientBoostingRegressor(n_estimators=200, max_depth=6, random_state=42, learning_rate=0.05)
gb_temporal.fit(X_temporal, y)
r2_temporal = r2_score(y, gb_temporal.predict(X_temporal))
mae_temporal = mean_absolute_error(y, gb_temporal.predict(X_temporal))
print(f"  R² = {r2_temporal:.4f}, MAE = {mae_temporal:.4f}")
print(f"\n  Improvement: R² +{r2_temporal - r2_basic:.4f}, MAE -{mae_basic - mae_temporal:.4f}")

# Feature importances
print("\nTop 10 Feature Importances:")
importances = list(zip(temporal_features, gb_temporal.feature_importances_))
importances.sort(key=lambda x: x[1], reverse=True)
for feat, imp in importances[:10]:
    print(f"  {feat:25s}: {imp:.4f}")

print("\n" + "="*80)
if r2_temporal >= 0.90:
    print(f"🎉 SUCCESS! R² = {r2_temporal:.4f} (≥90%)")
else:
    print(f"R² = {r2_temporal:.4f} ({r2_temporal*100:.1f}%)")
    print(f"To reach 90%+, we need: {0.90 - r2_temporal:.4f} more")
print("="*80)
