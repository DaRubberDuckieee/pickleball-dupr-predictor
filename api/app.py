from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import os
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Lazy-load models only when needed (so scraping endpoint works without scikit-learn)
models = None

def load_models():
    global models
    if models is not None:
        return models
    loaded = {}
    for model_num in [1, 3]:
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', f'model{model_num}_{"ridge" if model_num == 1 else "gb_balanced"}.pkl')
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
            if isinstance(data, tuple) and len(data) == 3:
                loaded[model_num] = {'model': data[0], 'features': data[1], 'deflation': data[2]}
            else:
                loaded[model_num] = {'model': data, 'features': None, 'deflation': 0.0}
    models = loaded
    return models

# Feature order matches deep_analysis.py 'All_Features'
FEATURES = ['won', 'rating_diff', 'score_margin', 'total_points', 'partner_diff', 'team_vs_opp', 
            'won_x_rating_diff', 'won_x_score_margin', 'rating_squared', 'surprise', 'opp_spread',
            'player_rating', 'partner_rating', 'opp_avg']

@app.route('/')
def home():
    return jsonify({
        "message": "DUPR Rating Predictor API",
        "model": "Gradient Boosting (R² = 0.86)",
        "endpoints": {
            "/predict": "Predict DUPR rating changes",
            "/scrape_dupr": "Scrape DUPR rating from pickleball.com URL"
        }
    })

@app.route('/scrape_dupr', methods=['POST'])
def scrape_dupr():
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate URL format
        if 'pickleball.com/players/' not in url:
            return jsonify({'error': 'Invalid pickleball.com player URL'}), 400
        
        # Extract player slug
        match = re.search(r'pickleball\.com/players/([\w-]+)', url)
        if not match:
            return jsonify({'error': 'Could not extract player name from URL'}), 400
        
        player_slug = match.group(1)
        
        # Use rating-history URL where ratings are publicly visible
        rating_history_url = f'https://pickleball.com/players/{player_slug}/rating-history'
        
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(rating_history_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to fetch player page (status {response.status_code})'}), 400
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract DUPR rating from the rating history page
        page_text = response.text
        
        # Extract player name from slug
        name_parts = player_slug.replace('-', ' ').title()
        
        # Try to extract from JSON data first (most reliable)
        # Pattern 1: Look for currentDuprDoublesRating in JSON data
        json_rating_match = re.search(r'"currentDuprDoublesRating":\s*([\d\.]+)', page_text)
        if json_rating_match:
            dupr_rating = float(json_rating_match.group(1))
            return jsonify({
                'dupr_rating': round(dupr_rating, 3),
                'player_name': name_parts,
                'player_slug': player_slug,
                'source': 'json_data'
            })
        
        # Pattern 2: Look for player name followed by rating in match history
        # Format: "Clayton Truex 34 | M | Kirkland, WA, USA 4.919"
        name_rating_match = re.search(rf'{re.escape(name_parts)}[^\d]+\d+\s*\|[^\d]+(\d+\.\d{{3}})', page_text, re.IGNORECASE)
        if name_rating_match:
            dupr_rating = float(name_rating_match.group(1))
            return jsonify({
                'dupr_rating': dupr_rating,
                'player_name': name_parts,
                'player_slug': player_slug,
                'source': 'rating_history'
            })
        
        # Pattern 3: Generic pattern - player name followed by a 3-decimal rating
        generic_match = re.search(rf'{re.escape(name_parts)}[^\d]+(\d+\.\d{{3}})', page_text, re.IGNORECASE)
        if generic_match:
            dupr_rating = float(generic_match.group(1))
            return jsonify({
                'dupr_rating': dupr_rating,
                'player_name': name_parts,
                'player_slug': player_slug,
                'source': 'rating_history'
            })
        
        # If we couldn't extract the rating, return an error
        return jsonify({
            'error': f'Could not find DUPR rating for player {player_slug}. The player may not have any match history.',
            'player_slug': player_slug
        }), 404
        
    except requests.Timeout:
        return jsonify({'error': 'Request timed out while fetching player page'}), 500
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

def fetch_dupr_rating_from_api(dupr_id):
    """Attempt to fetch DUPR rating from DUPR's API or website"""
    # Try mydupr.com API endpoints
    api_urls = [
        f'https://api.dupr.gg/player/{dupr_id}',
        f'https://mydupr.com/api/player/{dupr_id}',
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    for api_url in api_urls:
        try:
            response = requests.get(api_url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Try to extract doubles rating
                if 'doubles' in data:
                    return float(data['doubles'])
                if 'rating' in data and 'doubles' in data['rating']:
                    return float(data['rating']['doubles'])
        except:
            continue
    
    return None

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        # Get model selection (default to 1)
        model_num = int(data.get('model', 1))
        models_dict = load_models()
        if model_num not in models_dict:
            model_num = 1
        
        model_data = models_dict[model_num]
        model = model_data['model']
        deflation = model_data['deflation']
        
        # Extract player ratings
        team1_player1 = float(data['team1_player1'])
        team1_player2 = float(data['team1_player2'])
        team2_player1 = float(data['team2_player1'])
        team2_player2 = float(data['team2_player2'])
        
        # Extract match info
        team1_score = int(data['team1_score'])
        team2_score = int(data['team2_score'])
        
        # Validate scores
        if team1_score == team2_score:
            return jsonify({'error': 'Tie games are not valid in pickleball. One team must win.'}), 400
        if team1_score < 0 or team2_score < 0:
            return jsonify({'error': 'Scores must be non-negative.'}), 400
        
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
        
        # Add back DUPR's deflation constant
        predictions = predictions + deflation
        
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
