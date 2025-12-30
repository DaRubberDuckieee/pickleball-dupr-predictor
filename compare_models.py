"""
Compare predictions from all 4 model variants on test scenarios
"""
import pickle
import numpy as np

def predict_scenario(model, features, team1_p1, team1_p2, team2_p1, team2_p2, score1, score2):
    """Predict rating changes for a given scenario"""
    won_t1 = 1 if score1 > score2 else 0
    score_margin = score1 - score2
    total_points = abs(score_margin)
    
    opp_avg = (team2_p1 + team2_p2) / 2
    partner_rating = team1_p2
    
    # Build features
    rating_diff = team1_p1 - opp_avg
    partner_diff = team1_p1 - partner_rating
    team_avg = (team1_p1 + partner_rating) / 2
    team_vs_opp = team_avg - opp_avg
    opp_spread = abs(team2_p1 - team2_p2)
    won_x_rating_diff = won_t1 * rating_diff
    won_x_score_margin = won_t1 * score_margin
    rating_squared = team1_p1 ** 2
    expected_outcome = 1 / (1 + 10 ** ((opp_avg - team1_p1) / 4))
    surprise = won_t1 - expected_outcome
    
    X = [[won_t1, rating_diff, score_margin, total_points, partner_diff, team_vs_opp,
          won_x_rating_diff, won_x_score_margin, rating_squared, surprise, opp_spread,
          team1_p1, partner_rating, opp_avg]]
    
    return model.predict(X)[0]

# Load all models
models = {}
for i in range(1, 5):
    model_files = {
        1: 'models/model1_ridge.pkl',
        2: 'models/model2_gb_conservative.pkl',
        3: 'models/model3_gb_balanced.pkl',
        4: 'models/model4_gb_aggressive.pkl'
    }
    with open(model_files[i], 'rb') as f:
        model, features, _ = pickle.load(f)
        models[i] = model

# Test scenarios
scenarios = [
    {
        'name': "4.0 vs 4.0, score 11-9 (YOUR TEST CASE)",
        'team1_p1': 4.0, 'team1_p2': 4.0,
        'team2_p1': 4.0, 'team2_p2': 4.0,
        'score1': 11, 'score2': 9,
        'expected': "~0 for all (balanced match)"
    },
    {
        'name': "4.5 vs 3.5, score 11-3 (Expected win, blowout)",
        'team1_p1': 4.5, 'team1_p2': 4.5,
        'team2_p1': 3.5, 'team2_p2': 3.5,
        'score1': 11, 'score2': 3,
        'expected': "Small positive for winners, small negative for losers"
    },
    {
        'name': "3.5 vs 4.5, score 11-9 (UPSET!)",
        'team1_p1': 3.5, 'team1_p2': 3.5,
        'team2_p1': 4.5, 'team2_p2': 4.5,
        'score1': 11, 'score2': 9,
        'expected': "Large positive for winners, large negative for losers"
    },
    {
        'name': "5.0 vs 5.0, score 11-7",
        'team1_p1': 5.0, 'team1_p2': 5.0,
        'team2_p1': 5.0, 'team2_p2': 5.0,
        'score1': 11, 'score2': 7,
        'expected': "Small changes (balanced teams)"
    }
]

print("MODEL COMPARISON ON TEST SCENARIOS")
print("="*90)

for scenario in scenarios:
    print(f"\n{scenario['name']}")
    print(f"Expected: {scenario['expected']}")
    print("-"*90)
    print(f"{'Model':<30} {'Winner 1':<12} {'Winner 2':<12} {'Loser 1':<12} {'Loser 2':<12}")
    print("-"*90)
    
    for i in range(1, 5):
        model_names = {
            1: "Model 1: Ridge (Conservative)",
            2: "Model 2: GB Very Conservative",
            3: "Model 3: GB Balanced",
            4: "Model 4: GB Aggressive"
        }
        
        # Predict for all 4 players
        w1 = predict_scenario(models[i], None, scenario['team1_p1'], scenario['team1_p2'], 
                               scenario['team2_p1'], scenario['team2_p2'], 
                               scenario['score1'], scenario['score2'])
        w2 = predict_scenario(models[i], None, scenario['team1_p2'], scenario['team1_p1'], 
                               scenario['team2_p1'], scenario['team2_p2'], 
                               scenario['score1'], scenario['score2'])
        l1 = predict_scenario(models[i], None, scenario['team2_p1'], scenario['team2_p2'], 
                               scenario['team1_p1'], scenario['team1_p2'], 
                               scenario['score2'], scenario['score1'])
        l2 = predict_scenario(models[i], None, scenario['team2_p2'], scenario['team2_p1'], 
                               scenario['team1_p1'], scenario['team1_p2'], 
                               scenario['score2'], scenario['score1'])
        
        print(f"{model_names[i]:<30} {w1:+.3f}       {w2:+.3f}       {l1:+.3f}       {l2:+.3f}")

print("\n" + "="*90)
print("\nWhich model looks most accurate to you?")
print("Tell me the number (1-4) and I'll use that model for the website!")
