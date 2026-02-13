# GitHub Tamagotchi

A web service that generates dynamic SVG pet widgets based on GitHub activity. Embed a virtual pet in your GitHub profile README that evolves and responds to your coding activity.

## Features

- **Dynamic Pet Widget**: SVG-based pet that changes appearance based on your GitHub activity
- **Real-time Stats**: Hunger, happiness, health, and energy stats that decay over time
- **Activity Rewards**: Commits and pull requests boost your pet's stats
- **Evolution System**: Pet evolves through 5 stages (egg → baby → teen → adult → legendary)
- **Embeddable**: Works with standard markdown image syntax in GitHub READMEs
- **Fast & Cached**: Responses under 100ms with intelligent caching

## Quick Start

### Prerequisites

- Python 3.11+
- GitHub Personal Access Token (for API access)

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/github-tamagotchi.git
cd github-tamagotchi
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

5. Edit `.env` and add your GitHub token:
```bash
GITHUB_TOKEN=ghp_your_github_token_here
```

6. Run the application:
```bash
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`

### Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=term-missing
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | Yes | - | GitHub Personal Access Token for API authentication |
| `GITHUB_GRAPHQL_URL` | No | `https://api.github.com/graphql` | GitHub GraphQL API endpoint |
| `GITHUB_REST_URL` | No | `https://api.github.com` | GitHub REST API endpoint |
| `DATABASE_URL` | No | `sqlite:///./pets.db` | Database connection URL |
| `CACHE_TTL_SECONDS` | No | `300` | Cache time-to-live in seconds (5 minutes) |
| `HOST` | No | `0.0.0.0` | Server host address |
| `PORT` | No | `8000` | Server port |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Game Engine Configuration (Optional)

These variables control pet stat decay and activity boosts:

```bash
# Decay rates (per hour)
HUNGER_DECAY_RATE=2.0
HAPPINESS_DECAY_RATE=3.0
ENERGY_DECAY_RATE=1.5
HEALTH_DECAY_RATE=0.5

# Activity boosts
COMMIT_HUNGER_BOOST=10
COMMIT_HAPPINESS_BOOST=5
PR_MERGED_HAPPINESS_BOOST=10
PR_MERGED_XP_BOOST=20

# Inactivity penalties
INACTIVE_DAYS_THRESHOLD=3
INACTIVE_HAPPINESS_PENALTY=15
INACTIVE_ENERGY_PENALTY=10
```

## API Endpoints

### GET /pet

Returns an SVG image of your pet widget.

**Query Parameters:**
- `user` (required): GitHub username

**Example:**
```bash
curl "http://localhost:8000/pet?user=octocat"
```

**Response:**
- Content-Type: `image/svg+xml`
- Status: 200 (success), 404 (user not found), 500 (error)

**Embed in GitHub README:**
```markdown
![My GitHub Pet](http://your-domain.com/pet?user=yourusername)
```

### GET /stats

Returns JSON data of your pet's current stats.

**Query Parameters:**
- `user` (required): GitHub username

**Example:**
```bash
curl "http://localhost:8000/stats?user=octocat"
```

**Response:**
```json
{
  "username": "octocat",
  "hunger": 45,
  "happiness": 72,
  "health": 95,
  "energy": 68,
  "level": 5,
  "xp": 520,
  "stage": "teen",
  "last_updated": "2024-02-13T10:30:45.123456"
}
```

### GET /health

Health check endpoint for deployment monitoring.

**Example:**
```bash
curl "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy"
}
```

## Deployment

### Docker

Build the Docker image:
```bash
docker build -t github-tamagotchi .
```

Run the container:
```bash
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=your_token_here \
  -e DATABASE_URL=sqlite:///./pets.db \
  github-tamagotchi
```

### Render

1. Push your code to GitHub
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repository
4. Set environment variables in the Render dashboard:
   - `GITHUB_TOKEN`: Your GitHub Personal Access Token
   - `DATABASE_URL`: Leave as default for SQLite, or use PostgreSQL
5. Deploy

### Railway

1. Push your code to GitHub
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub repository
4. Add environment variables:
   - `GITHUB_TOKEN`: Your GitHub Personal Access Token
5. Deploy

### Fly.io

1. Install the Fly CLI: https://fly.io/docs/getting-started/installing-flyctl/
2. Create a new app:
```bash
flyctl launch
```

3. Set secrets:
```bash
flyctl secrets set GITHUB_TOKEN=your_token_here
```

4. Deploy:
```bash
flyctl deploy
```

## Testing the Deployment

Once deployed, test the endpoints:

```bash
# Test with your GitHub username
curl "https://your-domain.com/pet?user=yourusername" -o pet.svg

# View stats as JSON
curl "https://your-domain.com/stats?user=yourusername"

# Check health
curl "https://your-domain.com/health"
```

## Project Structure

```
github-tamagotchi/
├── api/                    # FastAPI application and routes
│   ├── main.py            # Application entry point
│   ├── routes.py          # API endpoints
│   ├── dependencies.py    # Dependency injection
│   └── error_handlers.py  # Error handling
├── services/              # Business logic
│   ├── pet_service.py     # Pet orchestration
│   ├── game_engine.py     # Game mechanics
│   └── github_service.py  # GitHub API integration
├── db/                    # Database layer
│   ├── database.py        # Database setup
│   ├── models.py          # SQLAlchemy models
│   └── repository.py      # Data access
├── models/                # Pydantic models
│   ├── pet_models.py      # Pet state models
│   └── github_models.py   # GitHub data models
├── rendering/             # SVG rendering
│   └── svg_renderer.py    # Pet widget generation
├── utils/                 # Utilities
│   └── cache.py           # Caching service
├── config/                # Configuration
│   └── settings.py        # Environment settings
├── tests/                 # Test suite
├── Dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## CI/CD

The project uses GitHub Actions for continuous integration. On every push and pull request, the following checks run:

- Unit tests (pytest)
- Security checks (bandit, safety)

## Troubleshooting

### GitHub Token Issues

- Ensure your token has at least `public_repo` scope
- Check that the token is not expired
- Verify the token is correctly set in your `.env` file

### Database Errors

- For SQLite: Ensure the directory where `pets.db` is created has write permissions
- For PostgreSQL: Verify the connection string is correct and the database is accessible

### Rate Limiting

- GitHub API has rate limits (60 requests/hour for unauthenticated, 5000 for authenticated)
- The service caches responses for 5 minutes to minimize API calls
- If rate limited, wait for the cache to expire or upgrade your GitHub token

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
