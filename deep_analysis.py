#!/usr/bin/env python3
"""
Deep analysis to improve R² from 0.12 to 0.90+
We need to find what factors DUPR is actually using
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score, mean_absolute_error
import os
import glob

# Load all player data
all_data = []
player_data_dir = 'player_data'

for csv_file in glob.glob(f'{player_data_dir}/*.csv'):
    try:
        df = pd.read_csv(csv_file)
        player_name = os.path.basename(csv_file).replace('_dupr.csv', '').replace('-', ' ').title()
        
        # Process each match - create 4 records (one per player)
        for _, row in df.iterrows():
            # Team 1 Player 1
            if pd.notna(row['team1_player1_rating_before']) and pd.notna(row['team1_player1_rating_change']):
                # Calculate opponent average
                opp_avg = (row['team2_player1_rating_before'] + row['team2_player2_rating_before']) / 2
                partner_rating = row['team1_player2_rating_before']
                
                # Determine win/loss
                score1 = row['game1_team1_score']
                score2 = row['game1_team2_score']
                if pd.notna(score1) and pd.notna(score2):
                    won = 1 if score1 > score2 else 0
                    score_margin = score1 - score2
                else:
                    continue
                
                all_data.append({
                    'player_rating': row['team1_player1_rating_before'],
                    'partner_rating': partner_rating,
                    'opp_avg': opp_avg,
                    'opp1_rating': row['team2_player1_rating_before'],
                    'opp2_rating': row['team2_player2_rating_before'],
                    'won': won,
                    'score_margin': score_margin,
                    'total_points': abs(score_margin),
                    'rating_change': row['team1_player1_rating_change'],
                })
            
            # Team 1 Player 2
            if pd.notna(row['team1_player2_rating_before']) and pd.notna(row['team1_player2_rating_change']):
                opp_avg = (row['team2_player1_rating_before'] + row['team2_player2_rating_before']) / 2
                partner_rating = row['team1_player1_rating_before']
                
                score1 = row['game1_team1_score']
                score2 = row['game1_team2_score']
                if pd.notna(score1) and pd.notna(score2):
                    won = 1 if score1 > score2 else 0
                    score_margin = score1 - score2
                else:
                    continue
                
                all_data.append({
                    'player_rating': row['team1_player2_rating_before'],
                    'partner_rating': partner_rating,
                    'opp_avg': opp_avg,
                    'opp1_rating': row['team2_player1_rating_before'],
                    'opp2_rating': row['team2_player2_rating_before'],
                    'won': won,
                    'score_margin': score_margin,
                    'total_points': abs(score_margin),
                    'rating_change': row['team1_player2_rating_change'],
                })
            
            # Team 2 Player 1
            if pd.notna(row['team2_player1_rating_before']) and pd.notna(row['team2_player1_rating_change']):
                opp_avg = (row['team1_player1_rating_before'] + row['team1_player2_rating_before']) / 2
                partner_rating = row['team2_player2_rating_before']
                
                score1 = row['game1_team2_score']
                score2 = row['game1_team1_score']
                if pd.notna(score1) and pd.notna(score2):
                    won = 1 if score1 > score2 else 0
                    score_margin = score1 - score2
                else:
                    continue
                
                all_data.append({
                    'player_rating': row['team2_player1_rating_before'],
                    'partner_rating': partner_rating,
                    'opp_avg': opp_avg,
                    'opp1_rating': row['team1_player1_rating_before'],
                    'opp2_rating': row['team1_player2_rating_before'],
                    'won': won,
                    'score_margin': score_margin,
                    'total_points': abs(score_margin),
                    'rating_change': row['team2_player1_rating_change'],
                })
            
            # Team 2 Player 2
            if pd.notna(row['team2_player2_rating_before']) and pd.notna(row['team2_player2_rating_change']):
                opp_avg = (row['team1_player1_rating_before'] + row['team1_player2_rating_before']) / 2
                partner_rating = row['team2_player1_rating_before']
                
                score1 = row['game1_team2_score']
                score2 = row['game1_team1_score']
                if pd.notna(score1) and pd.notna(score2):
                    won = 1 if score1 > score2 else 0
                    score_margin = score1 - score2
                else:
                    continue
                
                all_data.append({
                    'player_rating': row['team2_player2_rating_before'],
                    'partner_rating': partner_rating,
                    'opp_avg': opp_avg,
                    'opp1_rating': row['team1_player1_rating_before'],
                    'opp2_rating': row['team1_player2_rating_before'],
                    'won': won,
                    'score_margin': score_margin,
                    'total_points': abs(score_margin),
                    'rating_change': row['team2_player2_rating_change'],
                })
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
        continue

# Create DataFrame
df = pd.DataFrame(all_data)
print(f"Total records: {len(df)}")
print(f"Rating change stats: mean={df['rating_change'].mean():.3f}, median={df['rating_change'].median():.3f}")
print(f"Zero changes: {(df['rating_change'] == 0).sum()} ({(df['rating_change'] == 0).sum() / len(df) * 100:.1f}%)")
print()

# Create additional features
df['rating_diff'] = df['player_rating'] - df['opp_avg']
df['partner_diff'] = df['player_rating'] - df['partner_rating']
df['team_avg'] = (df['player_rating'] + df['partner_rating']) / 2
df['team_vs_opp'] = df['team_avg'] - df['opp_avg']
df['opp_spread'] = abs(df['opp1_rating'] - df['opp2_rating'])

# Interaction terms
df['won_x_rating_diff'] = df['won'] * df['rating_diff']
df['won_x_score_margin'] = df['won'] * df['score_margin']
df['rating_squared'] = df['player_rating'] ** 2
df['rating_cubed'] = df['player_rating'] ** 3

# Expected outcome (ELO formula)
df['expected_outcome'] = 1 / (1 + 10 ** ((df['opp_avg'] - df['player_rating']) / 4))
df['surprise'] = df['won'] - df['expected_outcome']

print("="*80)
print("MODEL COMPARISON")
print("="*80)

# Prepare features
feature_sets = {
    'Basic': ['won', 'rating_diff', 'score_margin', 'total_points'],
    'With_Partner': ['won', 'rating_diff', 'score_margin', 'total_points', 'partner_diff', 'team_vs_opp'],
    'With_Interactions': ['won', 'rating_diff', 'score_margin', 'total_points', 'won_x_rating_diff', 'won_x_score_margin'],
    'With_NonLinear': ['won', 'rating_diff', 'score_margin', 'player_rating', 'rating_squared', 'opp_avg', 'partner_rating'],
    'With_ELO': ['surprise', 'score_margin', 'player_rating', 'opp_avg', 'partner_rating', 'opp_spread'],
    'All_Features': ['won', 'rating_diff', 'score_margin', 'total_points', 'partner_diff', 'team_vs_opp', 
                     'won_x_rating_diff', 'won_x_score_margin', 'rating_squared', 'surprise', 'opp_spread',
                     'player_rating', 'partner_rating', 'opp_avg'],
}

y = df['rating_change'].values

for name, features in feature_sets.items():
    X = df[features].values
    
    # Linear Regression
    lr = LinearRegression()
    lr.fit(X, y)
    y_pred = lr.predict(X)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    print(f"\n{name} - Linear Regression:")
    print(f"  R² = {r2:.4f}, MAE = {mae:.4f}")
    
    # Print coefficients
    if name == 'All_Features':
        print("  Coefficients:")
        for feat, coef in zip(features, lr.coef_):
            print(f"    {feat:20s}: {coef:8.4f}")
        print(f"    {'Intercept':20s}: {lr.intercept_:8.4f}")

# Try Random Forest
print("\n" + "="*80)
print("RANDOM FOREST (Non-linear model)")
print("="*80)

X_all = df[feature_sets['All_Features']].values
rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X_all, y)
y_pred_rf = rf.predict(X_all)
r2_rf = r2_score(y, y_pred_rf)
mae_rf = mean_absolute_error(y, y_pred_rf)

print(f"R² = {r2_rf:.4f}, MAE = {mae_rf:.4f}")
print("\nFeature Importances:")
for feat, imp in sorted(zip(feature_sets['All_Features'], rf.feature_importances_), key=lambda x: x[1], reverse=True):
    print(f"  {feat:20s}: {imp:.4f}")

# Try Gradient Boosting
print("\n" + "="*80)
print("GRADIENT BOOSTING")
print("="*80)

gb = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
gb.fit(X_all, y)
y_pred_gb = gb.predict(X_all)
r2_gb = r2_score(y, y_pred_gb)
mae_gb = mean_absolute_error(y, y_pred_gb)

print(f"R² = {r2_gb:.4f}, MAE = {mae_gb:.4f}")

# Analyze residuals
print("\n" + "="*80)
print("RESIDUAL ANALYSIS")
print("="*80)

residuals = y - y_pred_gb
df['residual'] = residuals
df['abs_residual'] = abs(residuals)

print(f"Mean residual: {residuals.mean():.4f}")
print(f"Median abs residual: {np.median(abs(residuals)):.4f}")
print(f"90th percentile error: {np.percentile(abs(residuals), 90):.4f}")

# Find patterns in large errors
large_errors = df[df['abs_residual'] > 0.5].copy()
print(f"\nLarge errors (>0.5): {len(large_errors)} ({len(large_errors)/len(df)*100:.1f}%)")
if len(large_errors) > 0:
    print(f"  Mean rating: {large_errors['player_rating'].mean():.3f}")
    print(f"  Win rate: {large_errors['won'].mean():.3f}")
    print(f"  Mean rating_diff: {large_errors['rating_diff'].mean():.3f}")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print(f"Best model: Gradient Boosting with R² = {r2_gb:.4f}")
print(f"This suggests the true algorithm is NON-LINEAR")
print(f"To reach 90%+ R², we likely need:")
print("  1. Match recency/chronology information")
print("  2. Player-specific factors (rating volatility, confidence)")
print("  3. Tournament/event context")
print("  4. More sophisticated non-linear interactions")
