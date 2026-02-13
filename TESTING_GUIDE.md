# End-to-End Manual Testing Guide

## Prerequisites

1. **GitHub Personal Access Token**
   - Create one at: https://github.com/settings/tokens
   - Required scopes: `public_repo`, `read:user`
   - Update the `GITHUB_TOKEN` in `.env` file with your token

2. **Python Environment**
   - Python 3.11+
   - Dependencies installed: `pip install -r requirements.txt`

## Testing Steps

### Step 1: Start the Application

Run the following command in your terminal:

```bash
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 2: Test Root Endpoint

Open your browser or use curl to test the root endpoint:

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "service": "GitHub Tamagotchi",
  "version": "1.0.0",
  "endpoints": {
    "pet": "/pet?user=USERNAME",
    "stats": "/stats?user=USERNAME",
    "health": "/health"
  }
}
```

### Step 3: Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy"
}
```

### Step 4: Test /pet Endpoint with Real GitHub Username

Replace `octocat` with a real GitHub username (e.g., your own username or a well-known user):

```bash
curl http://localhost:8000/pet?user=octocat
```

Expected response:
- HTTP 200 status code
- Content-Type: `image/svg+xml`
- SVG image content containing:
  - Pet sprite (based on evolution stage)
  - Username label
  - Stage and level information
  - Stat bars (hunger, happiness, health, energy)
  - Mood message

**Browser Test:**
Open in your browser: `http://localhost:8000/pet?user=octocat`

You should see an SVG image rendered directly in the browser.

### Step 5: Test /stats Endpoint with Real GitHub Username

```bash
curl http://localhost:8000/stats?user=octocat
```

Expected response (JSON):
```json
{
  "username": "octocat",
  "hunger": 50,
  "happiness": 65,
  "health": 100,
  "energy": 85,
  "level": 2,
  "xp": 150,
  "stage": "baby",
  "last_updated": "2024-02-13T10:30:45.123456"
}
```

### Step 6: Test with Non-Existent Username

```bash
curl http://localhost:8000/pet?user=nonexistent_user_12345_xyz
```

Expected response:
- HTTP 404 status code
- Error message: `{"error": "GitHub user not found"}`

### Step 7: Test Database Persistence Across Requests

1. Make a request to `/stats?user=testuser`:
   ```bash
   curl http://localhost:8000/stats?user=testuser
   ```
   Note the `last_updated` timestamp and stat values.

2. Wait a few seconds.

3. Make another request to the same user:
   ```bash
   curl http://localhost:8000/stats?user=testuser
   ```
   
   Verify:
   - The pet data is retrieved from the database
   - The `last_updated` timestamp is the same (within cache TTL)
   - Stats remain consistent

4. Wait 5+ minutes (cache TTL expires) and make another request:
   ```bash
   curl http://localhost:8000/stats?user=testuser
   ```
   
   Verify:
   - The `last_updated` timestamp is updated
   - Stats may have changed due to time decay and new GitHub activity

### Step 8: Test SVG Rendering in Browser

1. Open your browser and navigate to:
   ```
   http://localhost:8000/pet?user=octocat
   ```

2. Verify the SVG renders correctly:
   - Pet sprite is visible
   - Username is displayed
   - Stage and level are shown
   - Stat bars are visible with appropriate colors:
     - Hunger: Red
     - Happiness: Yellow
     - Health: Green
     - Energy: Blue
   - Mood message is displayed

### Step 9: Test Concurrent Requests

Open multiple browser tabs or use curl in parallel:

```bash
# Terminal 1
curl http://localhost:8000/pet?user=user1

# Terminal 2
curl http://localhost:8000/pet?user=user2

# Terminal 3
curl http://localhost:8000/stats?user=user1
```

Verify:
- All requests complete successfully
- No state conflicts between requests
- Each user's pet data is independent

### Step 10: Test Error Handling

#### Missing Username Parameter
```bash
curl http://localhost:8000/pet
```

Expected response:
- HTTP 422 status code
- Error message about missing query parameter

#### Invalid Request
```bash
curl http://localhost:8000/pet?user=
```

Expected response:
- HTTP 400 or 422 status code
- Appropriate error message

## Verification Checklist

- [ ] Application starts without errors
- [ ] Root endpoint returns correct information
- [ ] Health endpoint returns healthy status
- [ ] /pet endpoint returns SVG for valid GitHub user
- [ ] /stats endpoint returns JSON for valid GitHub user
- [ ] SVG renders correctly in browser
- [ ] Non-existent username returns 404 error
- [ ] Database persists pet data across requests
- [ ] Cache works (same data returned within TTL)
- [ ] Concurrent requests work without conflicts
- [ ] Error handling works for invalid requests

## Troubleshooting

### Application Won't Start
- Check that port 8000 is not in use: `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (Mac/Linux)
- Verify Python 3.11+ is installed: `python --version`
- Check that all dependencies are installed: `pip install -r requirements.txt`

### GitHub API Errors
- Verify GitHub token is valid and has correct scopes
- Check GitHub API rate limits: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit`
- Ensure the GitHub username exists

### Database Errors
- Delete `pets.db` to reset the database: `rm pets.db`
- Check database file permissions

### SVG Not Rendering
- Check browser console for errors
- Verify the response Content-Type is `image/svg+xml`
- Try opening the SVG in a different browser

## Performance Notes

- First request for a user may take 300-500ms (GitHub API call)
- Subsequent requests within 5 minutes should be < 100ms (cached)
- SVG generation is typically < 50ms
- Database queries are typically < 10ms

</content>
</invoke>