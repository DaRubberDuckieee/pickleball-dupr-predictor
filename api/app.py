from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import os

app = Flask(__name__)
CORS(app)

# Load the model
model_path = os.path.join(os.path.dirname(__file__), '..', 'dupr_model.pkl')
with open(model_path, 'rb') as f:
    model = pickle.load(f)

# Feature order matches deep_analysis.py 'All_Features'
FEATURES = ['won', 'rating_diff', 'score_margin', 'total_points', 'partner_diff', 'team_vs_opp', 
            'won_x_rating_diff', 'won_x_score_margin', 'rating_squared', 'surprise', 'opp_spread',
            'player_rating', 'partner_rating', 'opp_avg']

@app.route('/')
def home():
    return jsonify({
        "message": "DUPR Rating Predictor API",
        "model": "Gradient Boosting (R² = 0.86)",
        "endpoint": "/predict"
    })

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        # Extract player ratings
        team1_player1 = float(data['team1_player1'])
        team1_player2 = float(data['team1_player2'])
        team2_player1 = float(data['team2_player1'])
        team2_player2 = float(data['team2_player2'])
        
        # Extract match info
        team1_score = int(data['team1_score'])
        team2_score = int(data['team2_score'])
        
        # Calculate match outcome
        team1_won = 1 if team1_score > team2_score else 0
        team2_won = 1 - team1_won
        score_margin_t1 = team1_score - team2_score
        score_margin_t2 = team2_score - team1_score
        total_points = abs(score_margin_t1)
        
        # Calculate averages
        opp_avg_for_t1 = (team2_player1 + team2_player2) / 2
        opp_avg_for_t2 = (team1_player1 + team1_player2) / 2
        
        # Build feature vectors for each player
        players = []
        
        # Team 1 Player 1
        rating_diff = team1_player1 - opp_avg_for_t1
        partner_diff = team1_player1 - team1_player2
        team_avg = (team1_player1 + team1_player2) / 2
        team_vs_opp = team_avg - opp_avg_for_t1
        opp_spread = abs(team2_player1 - team2_player2)
        won_x_rating_diff = team1_won * rating_diff
        won_x_score_margin = team1_won * score_margin_t1
        rating_squared = team1_player1 ** 2
        expected_outcome = 1 / (1 + 10 ** ((opp_avg_for_t1 - team1_player1) / 4))
        surprise = team1_won - expected_outcome
        
        players.append({
            'name': 'Team 1 Player 1',
            'features': [team1_won, rating_diff, score_margin_t1, total_points, partner_diff, team_vs_opp,
                        won_x_rating_diff, won_x_score_margin, rating_squared, surprise, opp_spread,
                        team1_player1, team1_player2, opp_avg_for_t1]
        })
        
        # Team 1 Player 2
        rating_diff = team1_player2 - opp_avg_for_t1
        partner_diff = team1_player2 - team1_player1
        won_x_rating_diff = team1_won * rating_diff
        rating_squared = team1_player2 ** 2
        expected_outcome = 1 / (1 + 10 ** ((opp_avg_for_t1 - team1_player2) / 4))
        surprise = team1_won - expected_outcome
        
        players.append({
            'name': 'Team 1 Player 2',
            'features': [team1_won, rating_diff, score_margin_t1, total_points, partner_diff, team_vs_opp,
                        won_x_rating_diff, won_x_score_margin, rating_squared, surprise, opp_spread,
                        team1_player2, team1_player1, opp_avg_for_t1]
        })
        
        # Team 2 Player 1
        rating_diff = team2_player1 - opp_avg_for_t2
        partner_diff = team2_player1 - team2_player2
        team_avg = (team2_player1 + team2_player2) / 2
        team_vs_opp = team_avg - opp_avg_for_t2
        opp_spread = abs(team1_player1 - team1_player2)
        won_x_rating_diff = team2_won * rating_diff
        won_x_score_margin = team2_won * score_margin_t2
        rating_squared = team2_player1 ** 2
        expected_outcome = 1 / (1 + 10 ** ((opp_avg_for_t2 - team2_player1) / 4))
        surprise = team2_won - expected_outcome
        
        players.append({
            'name': 'Team 2 Player 1',
            'features': [team2_won, rating_diff, score_margin_t2, total_points, partner_diff, team_vs_opp,
                        won_x_rating_diff, won_x_score_margin, rating_squared, surprise, opp_spread,
                        team2_player1, team2_player2, opp_avg_for_t2]
        })
        
        # Team 2 Player 2
        rating_diff = team2_player2 - opp_avg_for_t2
        partner_diff = team2_player2 - team2_player1
        won_x_rating_diff = team2_won * rating_diff
        rating_squared = team2_player2 ** 2
        expected_outcome = 1 / (1 + 10 ** ((opp_avg_for_t2 - team2_player2) / 4))
        surprise = team2_won - expected_outcome
        
        players.append({
            'name': 'Team 2 Player 2',
            'features': [team2_won, rating_diff, score_margin_t2, total_points, partner_diff, team_vs_opp,
                        won_x_rating_diff, won_x_score_margin, rating_squared, surprise, opp_spread,
                        team2_player2, team2_player1, opp_avg_for_t2]
        })
        
        # Predict for all players
        X = np.array([p['features'] for p in players])
        predictions = model.predict(X)
        
        # Round to 3 decimal places like DUPR
        predictions = np.round(predictions, 3)
        
        return jsonify({
            'team1': {
                'player1': {
                    'rating_before': team1_player1,
                    'rating_change': float(predictions[0]),
                    'rating_after': round(team1_player1 + predictions[0], 3)
                },
                'player2': {
                    'rating_before': team1_player2,
                    'rating_change': float(predictions[1]),
                    'rating_after': round(team1_player2 + predictions[1], 3)
                }
            },
            'team2': {
                'player1': {
                    'rating_before': team2_player1,
                    'rating_change': float(predictions[2]),
                    'rating_after': round(team2_player1 + predictions[2], 3)
                },
                'player2': {
                    'rating_before': team2_player2,
                    'rating_change': float(predictions[3]),
                    'rating_after': round(team2_player2 + predictions[3], 3)
                }
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=8080)
