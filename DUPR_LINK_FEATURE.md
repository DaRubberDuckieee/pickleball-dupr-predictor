# DUPR Link Scraper Feature

## Overview
This feature allows users to input pickleball.com player profile URLs instead of manually entering DUPR ratings. The system will attempt to extract the DUPR rating from the player's profile.

## How It Works

### Frontend Changes
- All four player rating input fields now accept either:
  - A numeric DUPR rating (e.g., `4.267`)
  - A pickleball.com player URL (e.g., `https://pickleball.com/players/jessica-wang`)

- Input validation:
  - Validates pickleball.com URL format
  - Validates DUPR rating range (0-8)
  - Shows inline error messages for invalid inputs

### Backend API
New endpoint: `POST /scrape_dupr`

**Request:**
```json
{
  "url": "https://pickleball.com/players/jessica-wang"
}
```

**Success Response (if rating is accessible):**
```json
{
  "dupr_rating": 4.267,
  "dupr_id": "N7Z7G7",
  "player_slug": "jessica-wang"
}
```

**Error Response (rating requires authentication):**
```json
{
  "error": "DUPR ratings on pickleball.com require authentication. Player DUPR ID is N7Z7G7. Please manually enter the DUPR rating from your pickleball.com account.",
  "player_slug": "jessica-wang",
  "dupr_id": "N7Z7G7",
  "url": "https://pickleball.com/players/jessica-wang"
}
```

## Limitations

### DUPR Ratings Require Authentication
Currently, DUPR ratings on pickleball.com are hidden behind authentication. This means:
- The scraper can extract the player's DUPR ID
- The actual rating value is not publicly accessible
- Users must manually enter the rating after looking it up

### Why This Happens
1. Pickleball.com requires users to log in to view DUPR ratings
2. DUPR does not provide a public API for accessing player ratings
3. Player privacy and data protection

## Future Improvements

### Potential Solutions
1. **Browser Automation with Authentication**: Use Playwright/Selenium with user credentials to access authenticated pages (requires user to provide login)
2. **DUPR Public API**: Wait for DUPR to release a public API
3. **Chrome Extension**: Create a browser extension that can access authenticated pages
4. **Manual Entry**: Current solution - provide helpful error messages to guide users

## Testing Locally

1. Start the Flask server:
```bash
python3 api/app.py
```

2. Open `index.html` in a browser

3. Test with URLs:
   - `https://pickleball.com/players/jessica-wang`
   - Or any other pickleball.com player URL

4. The system will:
   - Validate the URL format
   - Attempt to scrape the DUPR rating
   - Show an error message with the DUPR ID if authentication is required
   - Allow user to manually enter the rating

## Dependencies

New dependencies added to `requirements.txt`:
- `requests==2.31.0` - For HTTP requests
- `beautifulsoup4==4.12.3` - For HTML parsing

## Code Structure

### Frontend (`index.html`)
- `isPickleballURL()` - Checks if input is a URL
- `validateURL()` - Validates URL format
- `fetchDUPRFromURL()` - Calls backend API to scrape DUPR
- `processInput()` - Handles both URL and numeric input
- Error handling with inline messages

### Backend (`api/app.py`)
- `/scrape_dupr` endpoint - Main scraping endpoint
- `fetch_dupr_rating_from_api()` - Attempts to fetch from DUPR APIs
- BeautifulSoup for HTML parsing
- Regex for extracting player slugs and DUPR IDs

## Example Usage

### Entering URLs
```
Your Rating: https://pickleball.com/players/jessica-wang
Partner's Rating: https://pickleball.com/players/john-doe
Opponent 1: 3.729
Opponent 2: https://pickleball.com/players/jane-smith
```

### Mixed Input
Users can mix URLs and numeric ratings in the same form.

## Error Messages

The system provides clear, actionable error messages:
- "Invalid pickleball.com URL format"
- "DUPR rating must be between 0 and 8"
- "This field is required"
- "DUPR ratings on pickleball.com require authentication. Player DUPR ID is N7Z7G7..."
