#!/usr/bin/env python3
"""
Final comprehensive DUPR algorithm analysis from all 20 players
"""

import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error

def load_all_players():
    """Load data from all players in player_data folder"""
    players_data = []
    player_names = []
    
    for filename in os.listdir('player_data'):
        if filename.endswith('.csv'):
            filepath = f'player_data/{filename}'
            try:
                df = pd.read_csv(filepath)
                # Filter doubles only
                df = df[df['team2_player2_name'].notna()].copy()
                
                if len(df) > 0:
                    # Add computed fields
                    df['team1_won'] = df['game1_team1_score'] > df['game1_team2_score']
                    df['score_margin'] = df['game1_team1_score'] - df['game1_team2_score']
                    df['team1_avg_rating'] = (df['team1_player1_rating_before'] + df['team1_player2_rating_before']) / 2
                    df['team2_avg_rating'] = (df['team2_player1_rating_before'] + df['team2_player2_rating_before']) / 2
                    df['rating_diff'] = df['team1_avg_rating'] - df['team2_avg_rating']
                    
                    players_data.append(df)
                    player_name = df['team1_player1_name'].iloc[0] if len(df) > 0 else filename
                    player_names.append(player_name)
                    print(f"Loaded {player_name}: {len(df)} matches")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    # Combine all data
    combined = pd.concat(players_data, ignore_index=True)
    print(f"\n{'='*80}")
    print(f"Total combined: {len(combined)} matches from {len(player_names)} players")
    print(f"Players: {', '.join(player_names[:10])}...")
    print(f"{'='*80}")
    
    return combined, player_names

def create_analysis_dataframe(df):
    """Create per-player records for analysis"""
    records = []
    
    for idx, row in df.iterrows():
        if pd.isna(row['team1_player1_rating_change']):
            continue
        
        team1_won = row['team1_won']
        score_margin = row['score_margin']
        
        # Calculate total points
        total_team1_points = row['game1_team1_score']
        total_team2_points = row['game1_team2_score']
        
        if pd.notna(row['game2_team1_score']):
            total_team1_points += row['game2_team1_score']
            total_team2_points += row['game2_team2_score']
            
        if pd.notna(row['game3_team1_score']):
            total_team1_points += row['game3_team1_score']
            total_team2_points += row['game3_team2_score']
        
        team1_avg_rating = row['team1_avg_rating']
        team2_avg_rating = row['team2_avg_rating']
        rating_diff = row['rating_diff']
        
        # Add all 4 players' perspectives
        for player_info in [
            ('team1_player1', 1, rating_diff, total_team1_points, total_team2_points),
            ('team1_player2', 1, rating_diff, total_team1_points, total_team2_points),
            ('team2_player1', 2, -rating_diff, total_team2_points, total_team1_points),
            ('team2_player2', 2, -rating_diff, total_team2_points, total_team1_points)
        ]:
            player_prefix, team, rd, pts_for, pts_against = player_info
            
            rating_change = row[f'{player_prefix}_rating_change']
            if pd.isna(rating_change):
                continue
            
            won = team1_won if team == 1 else not team1_won
            sm = score_margin if team == 1 else -score_margin
            
            records.append({
                'player_name': row[f'{player_prefix}_name'],
                'player_rating_before': row[f'{player_prefix}_rating_before'],
                'rating_diff': rd,
                'won': 1 if won else 0,
                'score_margin': sm,
                'total_point_margin': pts_for - pts_against,
                'rating_change': rating_change
            })
    
    return pd.DataFrame(records)

def analyze_combined_data(df):
    """Run comprehensive analysis"""
    
    print(f"\n{'='*80}")
    print("FINAL COMPREHENSIVE DUPR ALGORITHM ANALYSIS")
    print(f"{'='*80}")
    print(f"\nDataset: {len(df)} player-match records")
    print(f"Wins: {df['won'].sum()}, Losses: {len(df) - df['won'].sum()}")
    print(f"\nRating change range: [{df['rating_change'].min():.3f}, {df['rating_change'].max():.3f}]")
    print(f"Mean rating change: {df['rating_change'].mean():.3f}")
    print(f"Median rating change: {df['rating_change'].median():.3f}")
    
    # Wins vs Losses
    wins = df[df['won'] == 1]
    losses = df[df['won'] == 0]
    
    print(f"\n{'='*80}")
    print("WINS vs LOSSES (OVERALL)")
    print(f"{'='*80}")
    print(f"Wins - Mean change: {wins['rating_change'].mean():.3f}, Median: {wins['rating_change'].median():.3f}")
    print(f"Losses - Mean change: {losses['rating_change'].mean():.3f}, Median: {losses['rating_change'].median():.3f}")
    
    # BY RATING LEVEL (Corrected analysis)
    print(f"\n{'='*80}")
    print("WINS vs LOSSES BY RATING LEVEL")
    print(f"{'='*80}")
    
    df['rating_bucket'] = pd.cut(df['player_rating_before'], 
                                   bins=[0, 3.0, 3.5, 4.0, 4.5, 10],
                                   labels=['<3.0', '3.0-3.5', '3.5-4.0', '4.0-4.5', '4.5+'])
    
    for bucket in ['<3.0', '3.0-3.5', '3.5-4.0', '4.0-4.5', '4.5+']:
        subset = df[df['rating_bucket'] == bucket]
        if len(subset) > 0:
            wins_subset = subset[subset['won'] == 1]
            losses_subset = subset[subset['won'] == 0]
            
            print(f"\n{bucket}: {len(subset)} records")
            if len(wins_subset) > 0:
                print(f"  Wins (n={len(wins_subset)}): mean={wins_subset['rating_change'].mean():+.3f}, median={wins_subset['rating_change'].median():+.3f}")
            if len(losses_subset) > 0:
                print(f"  Losses (n={len(losses_subset)}): mean={losses_subset['rating_change'].mean():+.3f}, median={losses_subset['rating_change'].median():+.3f}")
            if len(wins_subset) > 0 and len(losses_subset) > 0:
                diff = wins_subset['rating_change'].mean() - losses_subset['rating_change'].mean()
                if diff > 0:
                    print(f"  → Wins are {diff:+.3f} BETTER")
                else:
                    print(f"  → Wins are {diff:.3f} WORSE")
    
    # Zero changes
    zero_changes = df[df['rating_change'] == 0]
    print(f"\n{'='*80}")
    print("ZERO RATING CHANGES")
    print(f"{'='*80}")
    print(f"Total: {len(zero_changes)} ({len(zero_changes)/len(df)*100:.1f}%)")
    print(f"  In wins: {len(zero_changes[zero_changes['won']==1])} ({len(zero_changes[zero_changes['won']==1])/len(wins)*100:.1f}% of wins)")
    print(f"  In losses: {len(zero_changes[zero_changes['won']==0])} ({len(zero_changes[zero_changes['won']==0])/len(losses)*100:.1f}% of losses)")
    
    # Correlations
    print(f"\n{'='*80}")
    print("CORRELATIONS WITH RATING CHANGE")
    print(f"{'='*80}")
    features = ['player_rating_before', 'rating_diff', 'score_margin', 'total_point_margin']
    correlations = df[features + ['rating_change']].corr()['rating_change'].drop('rating_change')
    for feat in features:
        print(f"  {feat:30s}: {correlations[feat]:7.3f}")
    
    # Linear regression
    print(f"\n{'='*80}")
    print("LINEAR REGRESSION MODEL")
    print(f"{'='*80}")
    
    feature_cols = ['won', 'rating_diff', 'score_margin', 'total_point_margin']
    X = df[feature_cols]
    y = df['rating_change']
    
    model = LinearRegression()
    model.fit(X, y)
    predictions = model.predict(X)
    
    r2 = r2_score(y, predictions)
    mae = mean_absolute_error(y, predictions)
    
    print(f"\nR² Score: {r2:.4f}")
    print(f"Mean Absolute Error: {mae:.4f}")
    print("\nCoefficients:")
    for feat, coef in zip(feature_cols, model.coef_):
        print(f"  {feat:30s}: {coef:10.4f}")
    print(f"  {'Intercept':30s}: {model.intercept_:10.4f}")
    
    print("\nEstimated formula:")
    print(f"  rating_change = {model.intercept_:.3f}")
    for feat, coef in zip(feature_cols, model.coef_):
        sign = "+" if coef >= 0 else ""
        print(f"                  {sign}{coef:.3f} × {feat}")
    
    # ELO-style analysis
    print(f"\n{'='*80}")
    print("ELO-STYLE K-FACTOR ANALYSIS")
    print(f"{'='*80}")
    
    df['expected_win_prob'] = 1 / (1 + 10**(-df['rating_diff'] / 400))
    df['result_surprise'] = df['won'] - df['expected_win_prob']
    
    nonzero = df[df['rating_change'] != 0].copy()
    nonzero['k_factor'] = nonzero['rating_change'] / nonzero['result_surprise']
    
    print(f"\nImplied K-factor statistics (non-zero changes):")
    print(f"  Mean K: {nonzero['k_factor'].mean():.3f}")
    print(f"  Median K: {nonzero['k_factor'].median():.3f}")
    print(f"  Std K: {nonzero['k_factor'].std():.3f}")
    
    # K by rating level
    print(f"\nK-factor by player rating level:")
    nonzero['rating_bucket'] = pd.cut(nonzero['player_rating_before'], 
                                       bins=[0, 3.0, 3.5, 4.0, 4.5, 10], 
                                       labels=['<3.0', '3.0-3.5', '3.5-4.0', '4.0-4.5', '4.5+'])
    
    for bucket in ['<3.0', '3.0-3.5', '3.5-4.0', '4.0-4.5', '4.5+']:
        subset = nonzero[nonzero['rating_bucket'] == bucket]
        if len(subset) > 0:
            print(f"  {bucket}: K = {subset['k_factor'].mean():.3f} (n={len(subset)})")
    
    # Pattern analysis
    print(f"\n{'='*80}")
    print("RATING CHANGE PATTERNS BY OPPONENT STRENGTH")
    print(f"{'='*80}")
    
    for condition, label in [(df['rating_diff'] > 0.3, 'Favored (>0.3)'),
                              (abs(df['rating_diff']) <= 0.3, 'Even (±0.3)'),
                              (df['rating_diff'] < -0.3, 'Underdog (<-0.3)')]:
        subset = df[condition]
        if len(subset) > 0:
            wins_subset = subset[subset['won'] == 1]
            losses_subset = subset[subset['won'] == 0]
            print(f"\n{label} ({len(subset)} records):")
            if len(wins_subset) > 0:
                print(f"  Wins: avg change = {wins_subset['rating_change'].mean():+.3f} (n={len(wins_subset)})")
            if len(losses_subset) > 0:
                print(f"  Losses: avg change = {losses_subset['rating_change'].mean():+.3f} (n={len(losses_subset)})")
    
    return model, df

def main():
    df_raw, player_names = load_all_players()
    df_analysis = create_analysis_dataframe(df_raw)
    
    print(f"\nAnalysis dataframe: {len(df_analysis)} player-match records")
    
    model, df = analyze_combined_data(df_analysis)
    
    print("\n" + "="*80)
    print("Analysis complete!")
    print(f"Data from {len(player_names)} players analyzed")
    print("="*80)
    
    return model, df, df_raw

if __name__ == "__main__":
    model, analysis_df, raw_df = main()
