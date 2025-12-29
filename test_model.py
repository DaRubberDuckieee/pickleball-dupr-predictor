"""
Unit tests for DUPR rating prediction model
Tests real cases from the dataset to ensure model sanity
"""
import requests
import json

API_URL = "http://localhost:8080/predict"  # Change to production URL when deployed

# Test cases from real DUPR data
TEST_CASES = [
    {
        "name": "Balanced teams, blowout win",
        "input": {
            "team1_player1": 5.088,
            "team1_player2": 5.353,
            "team2_player1": 5.148,
            "team2_player2": 5.297,
            "team1_score": 15,
            "team2_score": 1
        },
        "expected": {
            "team1_p1_change": 0.038,
            "team1_p2_change": 0.030,
            "team2_p1_change": -0.093,
            "team2_p2_change": -0.175
        }
    },
    {
        "name": "Upset win (weaker beats stronger)",
        "input": {
            "team1_player1": 5.086,
            "team1_player2": 5.133,
            "team2_player1": 5.712,
            "team2_player2": 5.380,
            "team1_score": 15,
            "team2_score": 13
        },
        "expected": {
            "team1_p1_change": 0.023,
            "team1_p2_change": 0.038,
            "team2_p1_change": -0.016,
            "team2_p2_change": -0.027
        }
    },
    {
        "name": "Expected win (stronger wins but close)",
        "input": {
            "team1_player1": 5.099,
            "team1_player2": 5.155,
            "team2_player1": 4.702,
            "team2_player2": 4.834,
            "team1_score": 15,
            "team2_score": 13
        },
        "expected": {
            "team1_p1_change": -0.013,
            "team1_p2_change": -0.022,
            "team2_p1_change": 0.009,
            "team2_p2_change": 0.015
        }
    },
    {
        "name": "High rated players",
        "input": {
            "team1_player1": 5.110,
            "team1_player2": 5.171,
            "team2_player1": 4.829,
            "team2_player2": 5.026,
            "team1_score": 8,
            "team2_score": 15
        },
        "expected": {
            "team1_p1_change": -0.026,
            "team1_p2_change": -0.042,
            "team2_p1_change": 0.016,
            "team2_p2_change": 0.055
        }
    },
    {
        "name": "Low rated players (zero changes)",
        "input": {
            "team1_player1": 3.360,
            "team1_player2": 3.285,
            "team2_player1": 3.424,
            "team2_player2": 4.002,
            "team1_score": 8,
            "team2_score": 11
        },
        "expected": {
            "team1_p1_change": 0.000,
            "team1_p2_change": 0.000,
            "team2_p1_change": 0.000,
            "team2_p2_change": 0.000
        }
    },
    {
        "name": "Very close game",
        "input": {
            "team1_player1": 5.086,
            "team1_player2": 5.133,
            "team2_player1": 5.712,
            "team2_player2": 5.380,
            "team1_score": 15,
            "team2_score": 13
        },
        "expected": {
            "team1_p1_change": 0.023,
            "team1_p2_change": 0.038,
            "team2_p1_change": -0.016,
            "team2_p2_change": -0.027
        }
    },
    {
        "name": "Large skill gap (zero changes)",
        "input": {
            "team1_player1": 4.962,
            "team1_player2": 5.260,
            "team2_player1": 3.926,
            "team2_player2": 3.928,
            "team1_score": 11,
            "team2_score": 3
        },
        "expected": {
            "team1_p1_change": 0.000,
            "team1_p2_change": 0.000,
            "team2_p1_change": 0.000,
            "team2_p2_change": 0.000
        }
    },
    {
        "name": "Mixed ratings",
        "input": {
            "team1_player1": 4.391,
            "team1_player2": 5.774,
            "team2_player1": 4.882,
            "team2_player2": 4.795,
            "team1_score": 15,
            "team2_score": 11
        },
        "expected": {
            "team1_p1_change": 0.003,
            "team1_p2_change": 0.008,
            "team2_p1_change": -0.006,
            "team2_p2_change": -0.018
        }
    }
]


def test_model_predictions(api_url=API_URL, tolerance=0.10):
    """
    Test model predictions against real DUPR data
    
    Args:
        api_url: URL of the prediction API
        tolerance: Acceptable error margin (default 0.10 points)
    """
    print("=" * 80)
    print("DUPR MODEL SANITY TESTS")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 60)
        
        try:
            # Make API request
            response = requests.post(api_url, json=test['input'])
            response.raise_for_status()
            result = response.json()
            
            # Extract predictions
            pred = {
                "team1_p1_change": result['team1']['player1']['rating_change'],
                "team1_p2_change": result['team1']['player2']['rating_change'],
                "team2_p1_change": result['team2']['player1']['rating_change'],
                "team2_p2_change": result['team2']['player2']['rating_change']
            }
            
            # Check each prediction
            all_close = True
            for key in test['expected'].keys():
                expected = test['expected'][key]
                predicted = pred[key]
                error = abs(predicted - expected)
                
                status = "✓" if error <= tolerance else "✗"
                print(f"  {status} {key:20s}: Expected {expected:+.3f}, Got {predicted:+.3f} (error: {error:.3f})")
                
                if error > tolerance:
                    all_close = False
            
            if all_close:
                passed += 1
                print("  PASSED ✓")
            else:
                failed += 1
                print("  FAILED ✗ (errors exceed tolerance)")
                
        except Exception as e:
            failed += 1
            print(f"  ERROR: {str(e)}")
            print("  FAILED ✗")
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed}/{len(TEST_CASES)} passed, {failed}/{len(TEST_CASES)} failed")
    print("=" * 80)
    
    return passed, failed


if __name__ == "__main__":
    import sys
    
    # Allow custom API URL from command line
    api_url = sys.argv[1] if len(sys.argv) > 1 else API_URL
    
    passed, failed = test_model_predictions(api_url)
    
    # Exit with non-zero code if any tests failed
    sys.exit(1 if failed > 0 else 0)
