# Design Document

## Overview

GitHub Tamagotchi is a FastAPI-based web service that generates dynamic SVG pet widgets driven by GitHub activity. The architecture follows a layered approach with clear separation of concerns: API routing, GitHub data fetching, game logic, persistence, and rendering. The system is designed to be stateless at the request level while maintaining persistent pet state in SQLite (with future PostgreSQL compatibility).

The service operates on a pull-based model: when a user requests their pet widget, the system fetches their GitHub activity, updates pet stats based on time decay and activity boosts, persists the new state, and renders an SVG image.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    User[GitHub User] -->|GET /pet?user=X| API[FastAPI API Layer]
    API --> Cache{Cache Valid?}
    Cache -->|Yes| Render[Rendering Engine]
    Cache -->|No| GitHub[GitHub Data Service]
    GitHub -->|Fetch Activity| GitHubAPI[GitHub GraphQL/REST API]
    GitHubAPI --> GameEngine[Pet Game Engine]
    GameEngine -->|Calculate Stats| Persistence[Persistence Layer]
    Persistence -->|Load/Save| DB[(SQLite Database)]
    Persistence --> Render
    Render -->|SVG| API
    API -->|SVG Image| User
```

### Layer Responsibilities

1. **API Layer** (`api/`)
   - HTTP request handling and routing
   - Query parameter validation
   - Response formatting (SVG, JSON)
   - Error handling and status codes

2. **GitHub Data Service** (`services/github_service.py`)
   - GitHub API authentication
   - Contribution calendar fetching (GraphQL)
   - Recent activity events fetching (REST)
   - Rate limit handling
   - Async HTTP requests

3. **Pet Game Engine** (`services/game_engine.py`)
   - Time decay calculations
   - Activity boost calculations
   - Level and XP management
   - Evolution stage determination
   - Stat capping and validation

4. **Persistence Layer** (`db/`)
   - Database connection management
   - Pet state CRUD operations
   - Schema migrations
   - Transaction handling

5. **Rendering Engine** (`rendering/svg_renderer.py`)
   - SVG template generation
   - Stat bar visualization
   - Pet sprite selection
   - Dynamic text rendering

### Technology Stack

- **Framework**: FastAPI (async support, automatic OpenAPI docs)
- **Database**: SQLite with SQLAlchemy ORM (Postgres-ready schema)
- **HTTP Client**: httpx (async GitHub API calls)
- **Caching**: In-memory dict with TTL (Redis-ready architecture)
- **Configuration**: pydantic-settings for environment variables
- **Deployment**: Docker-ready, compatible with Render/Railway/Fly.io

## Components and Interfaces

### 1. API Layer

**Endpoints:**

```python
# api/routes.py

@app.get("/pet")
async def get_pet_widget(user: str) -> Response:
    """
    Returns SVG image of user's pet.
    
    Query Parameters:
    - user: GitHub username (required)
    
    Returns:
    - SVG image (Content-Type: image/svg+xml)
    - 404 if user not found on GitHub
    - 500 for server errors
    """

@app.get("/stats")
async def get_pet_stats(user: str) -> JSONResponse:
    """
    Returns JSON pet state.
    
    Query Parameters:
    - user: GitHub username (required)
    
    Returns:
    - JSON with pet stats
    - 404 if user not found
    """

@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for deployment platforms."""
```

**Dependencies:**
- PetService (orchestrates all operations)
- Exception handlers for consistent error responses

### 2. GitHub Data Service

**Interface:**

```python
# services/github_service.py

class GitHubService:
    def __init__(self, token: str, http_client: httpx.AsyncClient):
        self.token = token
        self.client = http_client
        self.graphql_url = "https://api.github.com/graphql"
        self.rest_url = "https://api.github.com"
    
    async def get_contribution_data(self, username: str, days: int = 7) -> ContributionData:
        """
        Fetch contribution calendar via GraphQL.
        
        Returns:
        - Total commits in last N days
        - Contribution dates and counts
        """
    
    async def get_recent_activity(self, username: str, limit: int = 30) -> List[ActivityEvent]:
        """
        Fetch recent events via REST API.
        
        Returns:
        - List of events (PushEvent, PullRequestEvent, etc.)
        - Event timestamps and metadata
        """
    
    async def validate_user_exists(self, username: str) -> bool:
        """Check if GitHub user exists."""
```

**Data Models:**

```python
# models/github_models.py

class ContributionData(BaseModel):
    username: str
    total_commits: int
    contribution_days: List[ContributionDay]

class ContributionDay(BaseModel):
    date: date
    count: int

class ActivityEvent(BaseModel):
    type: str  # PushEvent, PullRequestEvent, etc.
    created_at: datetime
    metadata: dict
```

**Caching Strategy:**
- Cache key: `github_data:{username}`
- TTL: 5 minutes (configurable)
- Cache GitHub responses to minimize API calls
- Invalidate on explicit refresh requests

### 3. Pet Game Engine

**Interface:**

```python
# services/game_engine.py

class GameEngine:
    # Stat change rates (per hour)
    HUNGER_DECAY_RATE = 2.0
    HAPPINESS_DECAY_RATE = 3.0
    ENERGY_DECAY_RATE = 1.5
    HEALTH_DECAY_RATE = 0.5
    
    # Activity boost values
    COMMIT_HUNGER_BOOST = 10
    COMMIT_HAPPINESS_BOOST = 5
    PR_MERGED_HAPPINESS_BOOST = 10
    PR_MERGED_XP_BOOST = 20
    
    # Inactivity penalties
    INACTIVE_DAYS_THRESHOLD = 3
    INACTIVE_HAPPINESS_PENALTY = 15
    INACTIVE_ENERGY_PENALTY = 10
    
    def calculate_time_decay(self, pet: PetState, hours_elapsed: float) -> PetState:
        """
        Apply time-based stat decay.
        
        Logic:
        - hunger -= HUNGER_DECAY_RATE * hours_elapsed
        - happiness -= HAPPINESS_DECAY_RATE * hours_elapsed
        - energy -= ENERGY_DECAY_RATE * hours_elapsed
        - health -= HEALTH_DECAY_RATE * hours_elapsed
        - Clamp all stats to [0, 100]
        """
    
    def apply_activity_boosts(
        self, 
        pet: PetState, 
        contribution_data: ContributionData,
        recent_activity: List[ActivityEvent]
    ) -> PetState:
        """
        Apply positive stat changes based on GitHub activity.
        
        Logic:
        - If commits today > 0: hunger +10, happiness +5
        - For each merged PR: happiness +10, xp +20
        - Clamp all stats to [0, 100]
        """
    
    def apply_inactivity_penalties(self, pet: PetState, days_inactive: int) -> PetState:
        """
        Apply penalties for extended inactivity.
        
        Logic:
        - If days_inactive > 3: happiness -15, energy -10
        """
    
    def calculate_level_and_stage(self, pet: PetState) -> PetState:
        """
        Update level based on XP and determine evolution stage.
        
        Logic:
        - Level = XP // 100 (100 XP per level)
        - Stage mapping:
          - 0-2: egg
          - 3-6: baby
          - 7-12: teen
          - 13-20: adult
          - 21+: legendary
        """
    
    def update_pet(
        self,
        pet: PetState,
        contribution_data: ContributionData,
        recent_activity: List[ActivityEvent],
        current_time: datetime
    ) -> PetState:
        """
        Main update method that orchestrates all calculations.
        
        Steps:
        1. Calculate hours elapsed since last_updated
        2. Apply time decay
        3. Apply activity boosts
        4. Apply inactivity penalties if applicable
        5. Calculate level and stage
        6. Update last_updated timestamp
        7. Return updated pet
        """
```

**Evolution Stage Logic:**

| Level Range | Stage     | Description                    |
|-------------|-----------|--------------------------------|
| 0-2         | egg       | Starting stage, minimal sprite |
| 3-6         | baby      | Small, cute appearance         |
| 7-12        | teen      | Medium size, more features     |
| 13-20       | adult     | Full-featured pet              |
| 21+         | legendary | Special effects, premium look  |

### 4. Persistence Layer

**Database Schema:**

```sql
-- db/schema.sql

CREATE TABLE pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    hunger INTEGER NOT NULL DEFAULT 50,
    happiness INTEGER NOT NULL DEFAULT 50,
    health INTEGER NOT NULL DEFAULT 100,
    energy INTEGER NOT NULL DEFAULT 100,
    level INTEGER NOT NULL DEFAULT 0,
    xp INTEGER NOT NULL DEFAULT 0,
    stage TEXT NOT NULL DEFAULT 'egg',
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (hunger >= 0 AND hunger <= 100),
    CHECK (happiness >= 0 AND happiness <= 100),
    CHECK (health >= 0 AND health <= 100),
    CHECK (energy >= 0 AND energy <= 100),
    CHECK (level >= 0),
    CHECK (xp >= 0),
    CHECK (stage IN ('egg', 'baby', 'teen', 'adult', 'legendary'))
);

CREATE INDEX idx_pets_username ON pets(username);
CREATE INDEX idx_pets_last_updated ON pets(last_updated);
```

**ORM Models:**

```python
# models/pet_models.py

from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel, Field

Base = declarative_base()

class PetDB(Base):
    """SQLAlchemy model for database."""
    __tablename__ = "pets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hunger = Column(Integer, nullable=False, default=50)
    happiness = Column(Integer, nullable=False, default=50)
    health = Column(Integer, nullable=False, default=100)
    energy = Column(Integer, nullable=False, default=100)
    level = Column(Integer, nullable=False, default=0)
    xp = Column(Integer, nullable=False, default=0)
    stage = Column(String, nullable=False, default='egg')
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class PetState(BaseModel):
    """Pydantic model for business logic."""
    username: str
    hunger: int = Field(ge=0, le=100, default=50)
    happiness: int = Field(ge=0, le=100, default=50)
    health: int = Field(ge=0, le=100, default=100)
    energy: int = Field(ge=0, le=100, default=100)
    level: int = Field(ge=0, default=0)
    xp: int = Field(ge=0, default=0)
    stage: str = Field(default='egg')
    last_updated: datetime
    
    class Config:
        from_attributes = True
```

**Repository Interface:**

```python
# db/repository.py

class PetRepository:
    def __init__(self, session: Session):
        self.session = session
    
    async def get_pet(self, username: str) -> Optional[PetState]:
        """Retrieve pet by username."""
    
    async def create_pet(self, username: str) -> PetState:
        """Create new pet with default stats."""
    
    async def update_pet(self, pet: PetState) -> PetState:
        """Update existing pet state."""
    
    async def get_or_create_pet(self, username: str) -> PetState:
        """Get existing pet or create if doesn't exist."""
```

### 5. Rendering Engine

**SVG Template Structure:**

```xml
<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="400" height="300" fill="#f0f0f0"/>
  
  <!-- Pet Sprite (stage-dependent) -->
  <g id="pet-sprite">
    <!-- Different shapes/paths for each stage -->
  </g>
  
  <!-- Username -->
  <text x="200" y="30" text-anchor="middle" font-size="20" font-weight="bold">
    {username}'s Pet
  </text>
  
  <!-- Stage Label -->
  <text x="200" y="55" text-anchor="middle" font-size="14" fill="#666">
    Stage: {stage} | Level {level}
  </text>
  
  <!-- Stat Bars -->
  <g id="stats" transform="translate(50, 220)">
    <!-- Hunger Bar -->
    <text x="0" y="0" font-size="12">Hunger:</text>
    <rect x="70" y="-10" width="200" height="15" fill="#ddd" rx="5"/>
    <rect x="70" y="-10" width="{hunger*2}" height="15" fill="#ff6b6b" rx="5"/>
    
    <!-- Happiness Bar -->
    <text x="0" y="25" font-size="12">Happy:</text>
    <rect x="70" y="15" width="200" height="15" fill="#ddd" rx="5"/>
    <rect x="70" y="15" width="{happiness*2}" height="15" fill="#ffd93d" rx="5"/>
    
    <!-- Health Bar -->
    <text x="0" y="50" font-size="12">Health:</text>
    <rect x="70" y="40" width="200" height="15" fill="#ddd" rx="5"/>
    <rect x="70" y="40" width="{health*2}" height="15" fill="#6bcf7f" rx="5"/>
    
    <!-- Energy Bar -->
    <text x="0" y="75" font-size="12">Energy:</text>
    <rect x="70" y="65" width="200" height="15" fill="#ddd" rx="5"/>
    <rect x="70" y="65" width="{energy*2}" height="15" fill="#4d96ff" rx="5"/>
  </g>
  
  <!-- Mood Text -->
  <text x="200" y="280" text-anchor="middle" font-size="12" fill="#888">
    {mood_message}
  </text>
</svg>
```

**Renderer Interface:**

```python
# rendering/svg_renderer.py

class SVGRenderer:
    def render_pet(self, pet: PetState) -> str:
        """
        Generate SVG string from pet state.
        
        Steps:
        1. Select pet sprite based on stage
        2. Calculate stat bar widths
        3. Determine mood message based on stats
        4. Populate SVG template
        5. Return SVG string
        """
    
    def get_pet_sprite(self, stage: str) -> str:
        """Return SVG path/shape for pet based on stage."""
    
    def get_mood_message(self, pet: PetState) -> str:
        """
        Generate mood text based on stats.
        
        Logic:
        - If happiness > 70: "Feeling great!"
        - If happiness < 30: "Needs attention..."
        - If hunger < 30: "Getting hungry!"
        - If energy < 30: "Feeling tired..."
        - Default: "Doing okay"
        """
```

**Pet Sprites (MVP):**

For MVP, use simple geometric shapes:
- **Egg**: Oval shape
- **Baby**: Circle with eyes
- **Teen**: Circle with eyes and mouth
- **Adult**: More detailed shape with features
- **Legendary**: Special effects (glow, stars)

### 6. Service Orchestration

**Main Service:**

```python
# services/pet_service.py

class PetService:
    def __init__(
        self,
        github_service: GitHubService,
        game_engine: GameEngine,
        repository: PetRepository,
        renderer: SVGRenderer,
        cache: CacheService
    ):
        self.github = github_service
        self.engine = game_engine
        self.repo = repository
        self.renderer = renderer
        self.cache = cache
    
    async def get_pet_svg(self, username: str) -> str:
        """
        Main orchestration method for /pet endpoint.
        
        Steps:
        1. Check cache for recent update
        2. If cache miss or expired:
           a. Validate GitHub user exists
           b. Fetch GitHub data
           c. Get or create pet from database
           d. Update pet stats via game engine
           e. Persist updated pet
           f. Update cache
        3. Render SVG from pet state
        4. Return SVG string
        """
    
    async def get_pet_stats(self, username: str) -> PetState:
        """
        Get pet stats as JSON (same logic as get_pet_svg but returns PetState).
        """
    
    def should_update_from_github(self, pet: PetState) -> bool:
        """
        Determine if GitHub data should be fetched.
        
        Logic:
        - If last_updated > 5 minutes ago: True
        - Otherwise: False
        """
```

## Data Models

### Complete Data Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Cache
    participant PetService
    participant GitHub
    participant GameEngine
    participant DB
    participant Renderer
    
    User->>API: GET /pet?user=alice
    API->>PetService: get_pet_svg("alice")
    PetService->>Cache: check("github_data:alice")
    
    alt Cache Hit
        Cache-->>PetService: cached_data
    else Cache Miss
        PetService->>GitHub: get_contribution_data("alice")
        GitHub-->>PetService: contribution_data
        PetService->>GitHub: get_recent_activity("alice")
        GitHub-->>PetService: activity_events
        PetService->>Cache: set("github_data:alice", data, ttl=300)
    end
    
    PetService->>DB: get_or_create_pet("alice")
    DB-->>PetService: pet_state
    
    PetService->>GameEngine: update_pet(pet_state, github_data)
    GameEngine-->>PetService: updated_pet
    
    PetService->>DB: update_pet(updated_pet)
    DB-->>PetService: saved_pet
    
    PetService->>Renderer: render_pet(saved_pet)
    Renderer-->>PetService: svg_string
    
    PetService-->>API: svg_string
    API-->>User: SVG Image
```

## Error Handling

### Error Scenarios and Responses

1. **GitHub User Not Found**
   - Status: 404
   - Response: `{"error": "GitHub user not found"}`

2. **GitHub API Rate Limit**
   - Status: 429
   - Response: `{"error": "Rate limit exceeded, try again later"}`
   - Fallback: Use cached data if available

3. **GitHub API Timeout**
   - Status: 503
   - Response: `{"error": "GitHub service unavailable"}`
   - Fallback: Use last known pet state

4. **Database Error**
   - Status: 500
   - Response: `{"error": "Internal server error"}`
   - Log error details for debugging

5. **Invalid Username Parameter**
   - Status: 400
   - Response: `{"error": "Username parameter required"}`

### Error Handling Strategy

```python
# api/error_handlers.py

@app.exception_handler(GitHubUserNotFoundError)
async def github_user_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "GitHub user not found"}
    )

@app.exception_handler(GitHubRateLimitError)
async def rate_limit_handler(request, exc):
    # Try to serve from cache
    # If no cache, return 429
    pass

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
```

## Testing Strategy

### Unit Tests

1. **Game Engine Tests**
   - Test time decay calculations
   - Test activity boost calculations
   - Test level and stage determination
   - Test stat capping (0-100 bounds)
   - Test inactivity penalties

2. **GitHub Service Tests**
   - Mock GitHub API responses
   - Test contribution data parsing
   - Test activity event parsing
   - Test rate limit handling
   - Test user validation

3. **Repository Tests**
   - Test CRUD operations
   - Test get_or_create logic
   - Test constraint validation
   - Use in-memory SQLite for tests

4. **Renderer Tests**
   - Test SVG generation for each stage
   - Test stat bar calculations
   - Test mood message logic
   - Validate SVG output structure

### Integration Tests

1. **End-to-End Pet Update Flow**
   - Create pet → fetch GitHub data → update stats → render SVG
   - Verify complete data flow

2. **Caching Behavior**
   - Test cache hit/miss scenarios
   - Verify TTL expiration
   - Test cache invalidation

3. **API Endpoint Tests**
   - Test `/pet` endpoint with valid user
   - Test `/stats` endpoint
   - Test error responses
   - Test concurrent requests

### Test Data

```python
# tests/fixtures.py

MOCK_CONTRIBUTION_DATA = ContributionData(
    username="testuser",
    total_commits=15,
    contribution_days=[
        ContributionDay(date=date.today(), count=5),
        ContributionDay(date=date.today() - timedelta(days=1), count=10),
    ]
)

MOCK_ACTIVITY_EVENTS = [
    ActivityEvent(
        type="PushEvent",
        created_at=datetime.utcnow(),
        metadata={"commits": 3}
    ),
    ActivityEvent(
        type="PullRequestEvent",
        created_at=datetime.utcnow() - timedelta(hours=2),
        metadata={"action": "closed", "merged": True}
    )
]

DEFAULT_PET_STATE = PetState(
    username="testuser",
    hunger=50,
    happiness=50,
    health=100,
    energy=100,
    level=0,
    xp=0,
    stage="egg",
    last_updated=datetime.utcnow()
)
```

## Configuration Management

### Environment Variables

```python
# config/settings.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # GitHub API
    github_token: str
    github_graphql_url: str = "https://api.github.com/graphql"
    github_rest_url: str = "https://api.github.com"
    
    # Database
    database_url: str = "sqlite:///./pets.db"
    
    # Caching
    cache_ttl_seconds: int = 300  # 5 minutes
    
    # Game Engine
    hunger_decay_rate: float = 2.0
    happiness_decay_rate: float = 3.0
    energy_decay_rate: float = 1.5
    health_decay_rate: float = 0.5
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### Example `.env` File

```bash
GITHUB_TOKEN=ghp_your_token_here
DATABASE_URL=sqlite:///./pets.db
CACHE_TTL_SECONDS=300
LOG_LEVEL=INFO
```

## Deployment Architecture

### Docker Configuration

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Deployment Platforms

**Render:**
- Use Web Service
- Auto-deploy from GitHub
- Environment variables via dashboard
- Persistent disk for SQLite

**Railway:**
- Connect GitHub repo
- Set environment variables
- Automatic HTTPS
- Volume for database

**Fly.io:**
- Use `fly.toml` configuration
- Persistent volumes for SQLite
- Global edge deployment

### Health Checks

```python
@app.get("/health")
async def health_check():
    """
    Health check endpoint for deployment platforms.
    
    Checks:
    - Database connectivity
    - GitHub API accessibility (optional)
    
    Returns:
    - 200 if healthy
    - 503 if unhealthy
    """
    try:
        # Test database connection
        await repository.health_check()
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )
```

## Performance Considerations

### Optimization Strategies

1. **Async Operations**
   - Use async/await for all I/O operations
   - Parallel GitHub API calls when possible
   - Non-blocking database queries

2. **Caching**
   - Cache GitHub API responses (5-minute TTL)
   - Consider caching rendered SVGs for very active users
   - Implement cache warming for popular users

3. **Database Indexing**
   - Index on `username` for fast lookups
   - Index on `last_updated` for cache invalidation queries

4. **SVG Optimization**
   - Keep SVG size under 10KB
   - Minimize path complexity
   - Avoid external resources

5. **Connection Pooling**
   - Reuse HTTP client connections
   - Database connection pooling via SQLAlchemy

### Performance Targets

- **Response Time**: < 100ms for cached requests, < 500ms for fresh updates
- **Throughput**: Handle 100+ requests/second
- **Database**: < 10ms query time
- **GitHub API**: < 300ms per request

## Security Considerations

1. **GitHub Token Protection**
   - Store in environment variables only
   - Never log or expose in responses
   - Use minimal required scopes

2. **Input Validation**
   - Validate username format
   - Sanitize all user inputs
   - Prevent SQL injection via ORM

3. **Rate Limiting**
   - Implement per-IP rate limiting
   - Respect GitHub API rate limits
   - Graceful degradation on limit exceeded

4. **CORS Configuration**
   - Allow GitHub domains
   - Restrict to necessary origins

5. **Error Messages**
   - Don't expose internal details
   - Generic error messages for users
   - Detailed logging for developers

## Future Enhancements (Post-MVP)

### Phase 2 Features

1. **Enhanced Visuals**
   - Custom pet sprites with animations
   - Theme customization (dark mode, colors)
   - Seasonal variations

2. **Advanced Game Mechanics**
   - Multiple pets per user
   - Pet interactions
   - Achievement system
   - Leaderboards

3. **Performance**
   - Redis caching
   - CDN for SVG delivery
   - Background job for pet updates

### Phase 3 Features

1. **User Accounts**
   - OAuth authentication
   - Pet customization dashboard
   - Premium features

2. **Marketplace**
   - Custom skins
   - Pet accessories
   - Special abilities

3. **Social Features**
   - Pet battles
   - Trading system
   - Community events

## Migration Path to PostgreSQL

When scaling beyond SQLite:

1. **Schema Compatibility**
   - Current schema is PostgreSQL-compatible
   - Use Alembic for migrations

2. **Connection Changes**
   - Update `DATABASE_URL` environment variable
   - Adjust connection pool settings

3. **Query Optimization**
   - Add PostgreSQL-specific indexes
   - Use EXPLAIN ANALYZE for query tuning

4. **Backup Strategy**
   - Implement automated backups
   - Point-in-time recovery

```python
# Example PostgreSQL connection
DATABASE_URL = "postgresql://user:password@localhost:5432/github_tamagotchi"
```
