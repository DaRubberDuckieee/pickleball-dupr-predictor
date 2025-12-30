"""
Train 4 different model variants for comparison
"""
import pandas as pd
import glob
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error
import pickle

# Load data and normalize by removing per-match deflation
all_data = []
match_deflations = []  # Track per-match total change

for csv_file in glob.glob('player_data/*.csv'):
    try:
        df_csv = pd.read_csv(csv_file)
        
        for _, row in df_csv.iterrows():
            score1 = row['game1_team1_score']
            score2 = row['game1_team2_score']
            if not pd.notna(score1) or not pd.notna(score2):
                continue
            
            # Calculate match-level deflation (total of all 4 rating changes)
            match_total_change = (
                row['team1_player1_rating_change'] + 
                row['team1_player2_rating_change'] + 
                row['team2_player1_rating_change'] + 
                row['team2_player2_rating_change']
            )
            per_player_adjustment = match_total_change / 4
            match_deflations.append(per_player_adjustment)
            
            won_t1 = 1 if score1 > score2 else 0
            score_margin_t1 = score1 - score2
            
            # Team 1 players - subtract match deflation
            for player_col, partner_col in [('team1_player1', 'team1_player2'), ('team1_player2', 'team1_player1')]:
                if pd.notna(row[f'{player_col}_rating_before']) and pd.notna(row[f'{player_col}_rating_change']):
                    opp_avg = (row['team2_player1_rating_before'] + row['team2_player2_rating_before']) / 2
                    partner_rating = row[f'{partner_col}_rating_before']
                    
                    all_data.append({
                        'player_rating': row[f'{player_col}_rating_before'],
                        'partner_rating': partner_rating,
                        'opp_avg': opp_avg,
                        'opp1_rating': row['team2_player1_rating_before'],
                        'opp2_rating': row['team2_player2_rating_before'],
                        'won': won_t1,
                        'score_margin': score_margin_t1,
                        'total_points': abs(score_margin_t1),
                        'rating_change': row[f'{player_col}_rating_change'] - per_player_adjustment,
                    })
            
            # Team 2 players - subtract match deflation
            score_margin_t2 = score2 - score1
            won_t2 = 1 - won_t1
            
            for player_col, partner_col in [('team2_player1', 'team2_player2'), ('team2_player2', 'team2_player1')]:
                if pd.notna(row[f'{player_col}_rating_before']) and pd.notna(row[f'{player_col}_rating_change']):
                    opp_avg = (row['team1_player1_rating_before'] + row['team1_player2_rating_before']) / 2
                    partner_rating = row[f'{partner_col}_rating_before']
                    
                    all_data.append({
                        'player_rating': row[f'{player_col}_rating_before'],
                        'partner_rating': partner_rating,
                        'opp_avg': opp_avg,
                        'opp1_rating': row['team1_player1_rating_before'],
                        'opp2_rating': row['team1_player2_rating_before'],
                        'won': won_t2,
                        'score_margin': score_margin_t2,
                        'total_points': abs(score_margin_t2),
                        'rating_change': row[f'{player_col}_rating_change'] - per_player_adjustment,
                    })
    except Exception as e:
        continue

# Calculate mean per-player deflation to add back at prediction time
mean_deflation = np.mean(match_deflations)
print(f"Mean per-player deflation: {mean_deflation:.4f}")

df = pd.DataFrame(all_data)

# Create features
df['rating_diff'] = df['player_rating'] - df['opp_avg']
df['partner_diff'] = df['player_rating'] - df['partner_rating']
df['team_avg'] = (df['player_rating'] + df['partner_rating']) / 2
df['team_vs_opp'] = df['team_avg'] - df['opp_avg']
df['opp_spread'] = abs(df['opp1_rating'] - df['opp2_rating'])
df['won_x_rating_diff'] = df['won'] * df['rating_diff']
df['won_x_score_margin'] = df['won'] * df['score_margin']
df['rating_squared'] = df['player_rating'] ** 2
df['expected_outcome'] = 1 / (1 + 10 ** ((df['opp_avg'] - df['player_rating']) / 4))
df['surprise'] = df['won'] - df['expected_outcome']

features = ['won', 'rating_diff', 'score_margin', 'total_points', 'partner_diff', 'team_vs_opp', 
            'won_x_rating_diff', 'won_x_score_margin', 'rating_squared', 'surprise', 'opp_spread',
            'player_rating', 'partner_rating', 'opp_avg']

X = df[features].values
y = df['rating_change'].values

print("Training 4 model variants...")
print("="*80)

# MODEL 1: Simple Ridge Regression (most conservative)
print("\nMODEL 1: Ridge Regression (Conservative)")
model1 = Ridge(alpha=1.0)
model1.fit(X, y)
pred1 = model1.predict(X)
print(f"R² = {r2_score(y, pred1):.4f}, MAE = {mean_absolute_error(y, pred1):.4f}")

with open('models/model1_ridge.pkl', 'wb') as f:
    pickle.dump((model1, features, mean_deflation), f)

# MODEL 2: Gradient Boosting - Very Conservative
print("\nMODEL 2: Gradient Boosting (Very Conservative)")
model2 = GradientBoostingRegressor(n_estimators=50, max_depth=2, learning_rate=0.01, random_state=42)
model2.fit(X, y)
pred2 = model2.predict(X)
print(f"R² = {r2_score(y, pred2):.4f}, MAE = {mean_absolute_error(y, pred2):.4f}")

with open('models/model2_gb_conservative.pkl', 'wb') as f:
    pickle.dump((model2, features, mean_deflation), f)

# MODEL 3: Gradient Boosting - Balanced
print("\nMODEL 3: Gradient Boosting (Balanced)")
model3 = GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, min_samples_leaf=10, random_state=42)
model3.fit(X, y)
pred3 = model3.predict(X)
print(f"R² = {r2_score(y, pred3):.4f}, MAE = {mean_absolute_error(y, pred3):.4f}")

with open('models/model3_gb_balanced.pkl', 'wb') as f:
    pickle.dump((model3, features, mean_deflation), f)

# MODEL 4: Gradient Boosting - Aggressive (high accuracy)
print("\nMODEL 4: Gradient Boosting (Aggressive - High Accuracy)")
model4 = GradientBoostingRegressor(n_estimators=150, max_depth=5, learning_rate=0.1, random_state=42)
model4.fit(X, y)
pred4 = model4.predict(X)
print(f"R² = {r2_score(y, pred4):.4f}, MAE = {mean_absolute_error(y, pred4):.4f}")

with open('models/model4_gb_aggressive.pkl', 'wb') as f:
    pickle.dump((model4, features, mean_deflation), f)

print("\n" + "="*80)
print("All models saved to models/ directory")
print("\nUse compare_models.py to test them on specific scenarios")
