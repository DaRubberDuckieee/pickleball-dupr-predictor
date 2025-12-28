# DUPR Algorithm Reverse Engineering - 6-Player Analysis (Findings #3)

## Dataset Overview
- **Total Matches Analyzed**: 401 matches
- **Players**: Jessica Wang (58), Olivia Wisner (129), Michelle Fat (19), Clayton Truex (38), Jonathan Li (122), Wilbert Lam (35)
- **Player-Match Records**: 1,604 (4 players per match)
- **Date Range**: Jul 2025 - Dec 2025
- **Win Rate**: 50% (802 wins, 802 losses - perfectly balanced)

## Key Discovery: Zero Rating Changes (STABILIZED)

**12.7% of all records (203/1604) resulted in ZERO rating change**

### Characteristics:
- **In Wins**: 105 records (13.1% of wins)
- **In Losses**: 98 records (12.2% of losses)
- **Pattern**: Nearly equal distribution (win vs loss)

**FINDING**: Zero-change rate has stabilized at ~13% with larger dataset (24% → 15% → 13%)

## Algorithm Structure

### Linear Regression Model (R² = 0.0926)
```
rating_change = -0.833 
                -0.052 × won 
                -0.516 × rating_diff 
                +0.018 × score_margin 
                -0.011 × total_point_margin
```

**CRITICAL**: Won coefficient is **NEGATIVE** (-0.052)!
- However, this is NOT a universal win penalty
- It's driven by mid-tier players (3.0-4.0) who often play as favorites
- See rating-level breakdown below for details

### Estimated ELO Formula
```
rating_change = K × (actual_result - expected_result)

where:
- expected_result = 1 / (1 + 10^((opponent_avg - your_team_avg) / 400))
- K varies by rating level (see below)
```

## K-Factor Analysis (REFINED WITH 1604 RECORDS)

### Average K-Factors (Non-Zero Changes):
- **Mean K**: -0.449 (median: +0.020)
- **Std K**: 7.074 (high variance but improving)

### K-Factor by Rating Level (FINAL PATTERN):
| Rating Level | K-Factor | Sample Size | Change from #2 |
|-------------|----------|-------------|----------------|
| **< 3.0** | **-1.605** | 350 | Was -2.590 |
| **3.0-3.5** | **+0.526** | 150 | Was +0.226 |
| **3.5-4.0** | **+0.479** | 290 | Was +0.254 |
| **4.0-4.5** | **-0.532** | 434 | Was -0.056 |
| **4.5+** | **-0.322** | 173 | Was -3.494 |

**MAJOR REVISION**: The U-curve is now an **inverted W-shape**!
- **<3.0**: Negative K (-1.6) - compression
- **3.0-4.0**: Positive K (+0.5) - normal growth zone
- **4.0-4.5**: Negative K (-0.5) - compression returns
- **4.5+**: Negative K (-0.3) - moderate compression

**INSIGHT**: DUPR has TWO compression zones (low and mid-high), with 3.0-4.0 as the sweet spot.

## Rating Change Patterns (VALIDATED WITH LARGE SAMPLE)

### By Match Outcome (Overall):
- **Wins**: Mean change = **-1.050** (median: 0.000)
- **Losses**: Mean change = **-0.669** (median: -0.141)

**Note**: Overall wins appear worse, but this is misleading! See rating-level breakdown:

### By Match Outcome AND Rating Level:

| Rating Level | Wins Mean | Losses Mean | Difference | Winner? |
|--------------|-----------|-------------|------------|---------|
| **<3.0** | -2.816 | -2.873 | **+0.057** | ✓ Wins better |
| **3.0-3.5** | -3.338 | -3.322 | **-0.017** | ✗ Wins slightly worse |
| **3.5-4.0** | -3.328 | -3.041 | **-0.288** | ✗ Wins worse |
| **4.0-4.5** | -3.265 | -3.453 | **+0.188** | ✓ Wins better |
| **4.5+** | -3.654 | -4.353 | **+0.699** | ✓ Wins much better |

**CRITICAL FINDING**: 
- **Mid-tier players (3.0-4.0)**: Wins are WORSE than losses (driven by playing as favorites)
- **High-tier players (4.0+)**: Wins are BETTER than losses (normal ELO behavior)
- **The negative win coefficient (-0.052) is NOT a universal penalty**
- It's caused by mid-tier players frequently playing down and getting penalized as favorites

### By Opponent Strength (HIGHLY VALIDATED):

#### When Favored (>0.3 rating advantage) - 700 records:
- **Win**: Average change = **-1.835** (n=434)
- **Loss**: Average change = **-2.017** (n=266)
- **Pattern**: MASSIVE negative changes regardless of outcome

#### Even Match (±0.3 rating difference) - 204 records:
- **Win**: Average change = **-0.490** (n=102)
- **Loss**: Average change = **-0.558** (n=102)
- **Pattern**: Moderate negative changes

#### When Underdog (<-0.3 rating disadvantage) - 700 records:
- **Win**: Average change = **+0.015** (n=266)
- **Loss**: Average change = **+0.131** (n=434)
- **Pattern**: Small positive changes even in losses!

## Correlations with Rating Change (STRONGEST YET)

| Feature | Correlation |
|---------|-------------|
| Player rating (before) | **-0.806** (extremely strong!) |
| Rating difference | -0.304 |
| Score margin | -0.076 (near zero) |
| Total point margin | -0.078 (near zero) |

**KEY INSIGHT**: Rating correlation increased from -0.775 → **-0.806** 
- This is the DOMINANT factor by far
- Your current rating predicts 65% of variance (R² = 0.65 from simple linear)

## Separate Models: Wins vs Losses

### WINS Model (R² = 0.0879, MAE = 2.61):
```
change = -0.944 - 0.488 × rating_diff + 0.048 × score_margin - 0.034 × total_point_margin
```

### LOSSES Model (R² = 0.0916, MAE = 2.87):
```
change = -0.891 - 0.543 × rating_diff - 0.013 × score_margin + 0.012 × total_point_margin
```

**FINDING**: Both models show similar R² (~0.09), both are weak. Rating changes are dominated by player_rating_before, not match details.

## Major Insights (6-Player Validation)

1. **Win Effect Varies by Rating Level** (CORRECTED)
   - Won coefficient: -0.052 (negative in aggregate)
   - **BUT**: This is NOT a universal win penalty
   - **Mid-tier (3.0-4.0)**: Wins worse than losses (-0.29 to -0.02 difference)
   - **High-tier (4.0+)**: Wins better than losses (+0.19 to +0.70 difference)
   - Negative coefficient driven by mid-tier playing down frequently

2. **Rating Dominates Everything**
   - Correlation: **-0.806** (strongest we've measured)
   - Current rating explains changes better than any match factor
   - The algorithm is player-centric, not outcome-centric

3. **Inverted W K-Factor Curve**
   - Two compression zones: <3.0 and 4.0-4.5
   - Growth zone: 3.0-4.0 (positive K)
   - High ratings (4.5+) less compressed than mid-high (4.0-4.5)

4. **Playing Favored is Disastrous**
   - Win as favorite: -1.835
   - Lose as favorite: -2.017
   - Average: **-1.90 regardless of outcome**

5. **Score Margin is Cosmetic**
   - Correlation: -0.076 (essentially zero)
   - 11-0 win = 11-9 win in DUPR's eyes
   - Only win/loss matters

## Comparison to Previous Findings

### Findings #1 → #2 → #3:
| Metric | #1 (1 player) | #2 (3 players) | #3 (6 players) | Trend |
|--------|---------------|----------------|----------------|--------|
| **Records** | 232 | 824 | **1,604** | ↑ 7x |
| **Zero-change rate** | 24.1% | 15.2% | **12.7%** | ↓ Stabilizing |
| **Rating correlation** | -0.684 | -0.775 | **-0.806** | ↓ Strengthening |
| **R² score** | 0.108 | 0.086 | **0.093** | → Stable low |
| **Mean change** | -0.617 | -0.715 | **-0.860** | ↓ More negative |
| **Win coefficient** | +0.005 | +0.006 | **-0.052** | ↓ NOW NEGATIVE! |

### What Changed in #3:

1. **Won Coefficient Went Negative** (MAJOR - BUT MISLEADING)
   - #1: +0.005
   - #2: +0.006  
   - #3: **-0.052**
   - **Initial Conclusion**: Winning is penalized
   - **CORRECTED**: Not a universal penalty - it's rating-level specific:
     - Mid-tier (3.0-4.0): Wins worse due to playing as favorites
     - High-tier (4.0+): Wins better (normal ELO)
     - Aggregate coefficient is negative due to mid-tier sample size

2. **K-Factor Pattern Refined** (MAJOR)
   - #2: Simple U-shape (<3.0 negative, 3.0-4.0 positive, 4.5+ very negative)
   - #3: **Inverted W** (<3.0 neg, 3.0-4.0 pos, 4.0-4.5 neg, 4.5+ less neg)
   - **Conclusion**: 4.0-4.5 is a second compression zone

3. **Rating Correlation Stronger** (HIGH)
   - Increased from -0.775 → **-0.806**
   - Now explains 65% of variance alone
   - **Conclusion**: Rating is overwhelmingly dominant

4. **Zero-Change Rate Stabilized** (MODERATE)
   - 24% → 15% → **13%**
   - Jessica's 24% was an outlier
   - **Conclusion**: True rate is ~13% (1 in 8 matches)

5. **Favored Penalty Confirmed** (HIGH)
   - #2: -1.645 win, -1.633 loss
   - #3: **-1.835 win, -2.017 loss** (even worse!)
   - **Conclusion**: Validated and magnitude increased

### What Stayed the Same:

- ✓ ELO-based core (400-point scale)
- ✓ Score margin irrelevant (~0 correlation)
- ✓ Underdog bonus (~+0.1 to +0.15)
- ✓ Systematic deflation (negative mean)
- ✓ Low R² (~0.09) - complex non-linear system

## Algorithm Components (FINAL HYPOTHESIS)

Based on 1,604 records from 6 players:

1. **ELO-style expected outcome** ✓✓✓
   - Uses team average ratings
   - 400-point scale
   - Standard formula

2. **Inverted W K-factor curve** ✓✓✓
   - <3.0: K = -1.6 (compression)
   - 3.0-4.0: K = +0.5 (growth zone)
   - 4.0-4.5: K = -0.5 (compression)
   - 4.5+: K = -0.3 (moderate compression)

3. **Favorite penalty (NOT universal win penalty)** ✓✓✓
   - Aggregate win coefficient: -0.052 (misleading)
   - Reality: Mid-tier players (3.0-4.0) penalized for playing down
   - High-tier players (4.0+): Wins are better than losses (+0.19 to +0.70)
   - "Win penalty" is actually "favorite penalty" in disguise

4. **Rating-dominant system** ✓✓✓
   - Correlation: -0.806
   - Current rating is THE predictor
   - Match outcome barely matters

5. **Threshold system** ✓✓
   - 12.7% zero-change rate
   - Applied equally to wins/losses
   - Filters low-confidence matches

6. **Score margin ignored** ✓✓✓
   - Correlation: -0.076
   - Only win/loss counted
   - Blowouts = close games

## Practical Implications

### To Increase Your Rating:
1. **Play as underdog** (+0.13 avg even in losses)
2. **Avoid playing as favorite** (-1.9 avg regardless of outcome)
3. **Target 3.0-4.0 range** (positive K-factors)
4. **Don't worry about score** (margins don't matter)

### Rating Zones:
- **<3.0**: Rating compressed down (K = -1.6)
- **3.0-4.0**: Sweet spot for growth (K = +0.5)
- **4.0-4.5**: Compression returns (K = -0.5)
- **4.5+**: Moderate compression (K = -0.3)

### Why Your Rating Drops Despite Winning:
1. **If mid-tier (3.0-4.0)**: You're favored in most matches → penalty (-1.9 avg)
2. **If high-tier (4.0+)**: Wins are better than losses, but:
   - Playing as favorite still penalizes you (-1.8 to -2.0)
   - High rating triggers compression (negative K for 4.0-4.5)
3. Overall deflation system (mean change = -0.86 across all matches)

## Summary

With 6 players' data (1,604 records), DUPR's algorithm is:

- ✓ **ELO core** (400-point scale)
- ✓ **Inverted W K-factors** (two compression zones)
- ✓ **Favorite-penalizing** (not universal win penalty)
- ✓ **Rating-dominant** (correlation: -0.806)
- ✓ **Score-blind** (correlation: -0.076)
- ✓ **Threshold-based** (13% zero changes)
- ✓ **Deflation-driven** (mean: -0.86)
- ✗ **NOT pure ELO**

**The algorithm prioritizes rating distribution management over match performance reflection.**

DUPR is designed to:
1. Keep players in 3.0-4.0 range (positive K)
2. Compress extremes (<3.0, 4.0-4.5, 4.5+)
3. Prevent inflation (win penalty + deflation)
4. Discourage playing weak opponents (favorite penalty)
5. Ignore score margins (win/loss only)

**Bottom line**: Your current rating matters ~10x more than whether you win or lose.
