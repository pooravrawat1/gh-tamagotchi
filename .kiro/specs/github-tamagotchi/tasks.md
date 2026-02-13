# Implementation Plan

- [x] 1. Set up project structure and dependencies





  - Create directory structure: api/, services/, models/, db/, rendering/, utils/, config/, tests/
  - Create requirements.txt with FastAPI, SQLAlchemy, httpx, pydantic-settings, uvicorn
  - Create .env.example file with required environment variables
  - Create main application entry point at api/main.py
  - _Requirements: 7.5, 8.2_

- [x] 2. Implement configuration management





  - Create config/settings.py with pydantic BaseSettings class
  - Define all environment variables (GitHub token, database URL, cache TTL, game engine rates)
  - Implement settings validation and loading from .env file
  - _Requirements: 7.2, 10.1_

- [ ] 3. Create data models and database schema
  - [x] 3.1 Define Pydantic models for business logic





    - Create models/pet_models.py with PetState class
    - Create models/github_models.py with ContributionData, ContributionDay, ActivityEvent classes
    - Add field validation and constraints (0-100 for stats, stage enum)
    - _Requirements: 6.1, 7.3_
  
  - [x] 3.2 Define SQLAlchemy ORM models




    - Create db/models.py with PetDB class
    - Define table schema with all columns, constraints, and indexes
    - Add check constraints for stat ranges and stage values
    - _Requirements: 6.1, 6.3_
  
  - [x] 3.3 Implement database initialization





    - Create db/database.py with engine and session management
    - Implement create_tables() function for schema creation
    - Add database connection lifecycle management
    - _Requirements: 6.2, 6.3_

- [x] 4. Implement persistence layer
  - [x] 4.1 Create pet repository





    - Create db/repository.py with PetRepository class
    - Implement get_pet(username) method
    - Implement create_pet(username) method with default values
    - Implement update_pet(pet) method
    - Implement get_or_create_pet(username) method
    - _Requirements: 6.1, 6.4_
  
  - [ ]* 4.2 Write repository tests
    - Create tests/test_repository.py
    - Test CRUD operations with in-memory SQLite
    - Test get_or_create logic
    - Test constraint validation
    - _Requirements: 6.1, 6.4_

- [ ] 5. Implement GitHub data service
  - [x] 5.1 Create GitHub API client





    - Create services/github_service.py with GitHubService class
    - Implement async HTTP client initialization with authentication headers
    - Implement validate_user_exists(username) method using REST API
    - _Requirements: 5.2, 10.1, 10.2, 10.5_
  
  - [x] 5.2 Implement contribution data fetching





    - Implement get_contribution_data(username, days) method using GraphQL API
    - Create GraphQL query for contribution calendar
    - Parse GraphQL response into ContributionData model
    - _Requirements: 5.2, 10.2_
  
  - [x] 5.3 Implement activity event fetching




    - Implement get_recent_activity(username, limit) method using REST API
    - Fetch events from /users/{username}/events endpoint
    - Parse events into ActivityEvent models
    - Filter for relevant event types (PushEvent, PullRequestEvent)
    - _Requirements: 5.2, 10.3_
  
  - [ ] 5.4 Add error handling for GitHub API
    - Handle rate limit errors (403 with rate limit message)
    - Handle user not found errors (404)
    - Handle timeout errors
    - Implement retry logic for transient failures
    - _Requirements: 10.4_
  
  - [ ]* 5.5 Write GitHub service tests
    - Create tests/test_github_service.py
    - Mock GitHub API responses using httpx mock
    - Test contribution data parsing
    - Test activity event parsing
    - Test error handling scenarios
    - _Requirements: 10.2, 10.3_

- [ ] 6. Implement pet game engine
  - [ ] 6.1 Create game engine core
    - Create services/game_engine.py with GameEngine class
    - Define stat decay rates and activity boost constants
    - Implement helper method to clamp stats to [0, 100] range
    - _Requirements: 2.3, 3.5_
  
  - [ ] 6.2 Implement time decay calculations
    - Implement calculate_time_decay(pet, hours_elapsed) method
    - Apply decay rates to hunger, happiness, energy, health
    - Calculate hours elapsed from last_updated timestamp
    - Clamp all stats after decay
    - _Requirements: 3.1, 3.2, 3.4_
  
  - [ ] 6.3 Implement activity boost calculations
    - Implement apply_activity_boosts(pet, contribution_data, recent_activity) method
    - Check for commits today and apply hunger/happiness boosts
    - Check for merged PRs and apply happiness/XP boosts
    - Clamp all stats after boosts
    - _Requirements: 2.1, 2.2, 2.4, 2.5_
  
  - [ ] 6.4 Implement inactivity penalties
    - Implement apply_inactivity_penalties(pet, days_inactive) method
    - Calculate days since last activity from contribution data
    - Apply penalties if inactive > 3 days
    - _Requirements: 3.3_
  
  - [ ] 6.5 Implement level and evolution logic
    - Implement calculate_level_and_stage(pet) method
    - Calculate level from XP (100 XP per level)
    - Map level to evolution stage (egg, baby, teen, adult, legendary)
    - Update pet's level and stage fields
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 6.6 Implement main update orchestration
    - Implement update_pet(pet, contribution_data, recent_activity, current_time) method
    - Call calculate_time_decay
    - Call apply_activity_boosts
    - Call apply_inactivity_penalties
    - Call calculate_level_and_stage
    - Update last_updated timestamp
    - Return updated pet
    - _Requirements: 2.5, 3.4, 3.5_
  
  - [ ]* 6.7 Write game engine tests
    - Create tests/test_game_engine.py
    - Test time decay with various elapsed times
    - Test activity boosts with different GitHub data
    - Test inactivity penalties
    - Test level and stage calculations
    - Test stat capping at boundaries
    - _Requirements: 2.3, 3.5, 4.6_

- [ ] 7. Implement caching service
  - Create utils/cache.py with CacheService class
  - Implement in-memory cache with TTL using dict and timestamps
  - Implement get(key), set(key, value, ttl), and invalidate(key) methods
  - Add cache key generation helper for GitHub data
  - _Requirements: 5.1, 5.2, 5.4_

- [ ] 8. Implement SVG rendering engine
  - [ ] 8.1 Create SVG renderer core
    - Create rendering/svg_renderer.py with SVGRenderer class
    - Define SVG template structure with placeholders
    - Implement render_pet(pet) method that returns SVG string
    - _Requirements: 1.2, 1.4_
  
  - [ ] 8.2 Implement pet sprite generation
    - Implement get_pet_sprite(stage) method
    - Create simple geometric sprites for each stage (egg: oval, baby: circle with eyes, teen: circle with eyes and mouth, adult: detailed shape, legendary: shape with effects)
    - Return SVG path/shape elements as strings
    - _Requirements: 4.6_
  
  - [ ] 8.3 Implement stat bar rendering
    - Create stat bar SVG elements with background and filled portions
    - Calculate bar widths based on stat values (0-100 maps to 0-200px)
    - Apply color coding (hunger: red, happiness: yellow, health: green, energy: blue)
    - _Requirements: 1.2_
  
  - [ ] 8.4 Implement mood message generation
    - Implement get_mood_message(pet) method
    - Generate message based on stat thresholds (happiness > 70: "Feeling great!", happiness < 30: "Needs attention...", etc.)
    - Return appropriate mood text
    - _Requirements: 1.2_
  
  - [ ] 8.5 Assemble complete SVG
    - Populate SVG template with username, stage, level
    - Insert pet sprite
    - Insert stat bars
    - Insert mood message
    - Return complete SVG string
    - _Requirements: 1.2, 1.4_
  
  - [ ]* 8.6 Write renderer tests
    - Create tests/test_svg_renderer.py
    - Test SVG generation for each evolution stage
    - Test stat bar width calculations
    - Test mood message logic
    - Validate SVG output is well-formed XML
    - _Requirements: 1.2, 1.4_

- [ ] 9. Implement pet service orchestration
  - [ ] 9.1 Create pet service
    - Create services/pet_service.py with PetService class
    - Initialize with dependencies (GitHubService, GameEngine, PetRepository, SVGRenderer, CacheService)
    - _Requirements: 7.1_
  
  - [ ] 9.2 Implement cache check logic
    - Implement should_update_from_github(pet) method
    - Check if last_updated is older than cache TTL (5 minutes)
    - Return boolean indicating if GitHub fetch is needed
    - _Requirements: 5.1, 5.3_
  
  - [ ] 9.3 Implement main pet SVG generation
    - Implement get_pet_svg(username) method
    - Check cache for GitHub data
    - If cache miss: validate user exists, fetch contribution data, fetch recent activity, update cache
    - Get or create pet from repository
    - Update pet stats via game engine
    - Persist updated pet to database
    - Render SVG from pet state
    - Return SVG string
    - _Requirements: 1.1, 1.5, 5.1, 5.2, 5.3, 6.5_
  
  - [ ] 9.4 Implement pet stats JSON generation
    - Implement get_pet_stats(username) method
    - Use same logic as get_pet_svg but return PetState instead of SVG
    - _Requirements: 9.2, 9.4_
  
  - [ ]* 9.5 Write pet service integration tests
    - Create tests/test_pet_service.py
    - Test complete flow from GitHub fetch to SVG generation
    - Test cache hit and miss scenarios
    - Test error handling paths
    - _Requirements: 1.5, 5.1_

- [ ] 10. Implement API layer
  - [ ] 10.1 Create FastAPI application
    - Create api/main.py with FastAPI app instance
    - Configure CORS middleware
    - Set up dependency injection for services
    - Initialize database on startup
    - _Requirements: 7.1, 8.1_
  
  - [ ] 10.2 Implement /pet endpoint
    - Create api/routes.py with pet router
    - Implement GET /pet endpoint with user query parameter
    - Validate username parameter is provided
    - Call PetService.get_pet_svg(username)
    - Return Response with SVG content and image/svg+xml content-type
    - _Requirements: 1.1, 1.3, 8.4_
  
  - [ ] 10.3 Implement /stats endpoint
    - Implement GET /stats endpoint with user query parameter
    - Validate username parameter is provided
    - Call PetService.get_pet_stats(username)
    - Return JSONResponse with pet state
    - _Requirements: 9.1, 9.2, 9.3, 9.5_
  
  - [ ] 10.4 Implement /health endpoint
    - Implement GET /health endpoint
    - Check database connectivity
    - Return 200 with {"status": "healthy"} if healthy
    - Return 503 with error details if unhealthy
    - _Requirements: 8.1_
  
  - [ ] 10.5 Implement error handlers
    - Create api/error_handlers.py
    - Add exception handler for GitHub user not found (404)
    - Add exception handler for GitHub rate limit (429)
    - Add exception handler for GitHub timeout (503)
    - Add exception handler for invalid parameters (400)
    - Add general exception handler (500)
    - Register all handlers with FastAPI app
    - _Requirements: 8.5_
  
  - [ ]* 10.6 Write API endpoint tests
    - Create tests/test_api.py
    - Test /pet endpoint with valid username
    - Test /stats endpoint with valid username
    - Test error responses (404, 400, 500)
    - Test concurrent requests
    - Use TestClient from FastAPI
    - _Requirements: 1.1, 1.5, 8.5, 9.5_

- [ ] 11. Create deployment configuration
  - [ ] 11.1 Create Docker configuration
    - Create Dockerfile with Python 3.11 base image
    - Copy requirements and install dependencies
    - Copy application code
    - Expose port 8000
    - Set CMD to run uvicorn
    - _Requirements: 8.1, 8.2_
  
  - [ ] 11.2 Create deployment files
    - Create .dockerignore file
    - Create README.md with setup and deployment instructions
    - Document environment variables needed
    - Add example curl commands for testing endpoints
    - _Requirements: 8.2, 8.3_
  
  - [ ] 11.3 Create example environment file
    - Create .env.example with all required variables
    - Add comments explaining each variable
    - Include placeholder values
    - _Requirements: 7.2, 8.3_

- [ ] 12. Integration and final wiring
  - [ ] 12.1 Wire up dependency injection
    - Create api/dependencies.py
    - Implement factory functions for all services
    - Set up database session dependency
    - Configure httpx AsyncClient as dependency
    - _Requirements: 7.1_
  
  - [ ] 12.2 Initialize application on startup
    - Add startup event handler to create database tables
    - Initialize cache service
    - Validate GitHub token is configured
    - Log application startup information
    - _Requirements: 6.3, 8.1_
  
  - [ ] 12.3 Add logging configuration
    - Create utils/logging.py with logging setup
    - Configure log levels from environment
    - Add structured logging for key operations
    - Ensure no sensitive data (tokens) in logs
    - _Requirements: 7.3, 10.5_
  
  - [ ]* 12.4 Run end-to-end manual testing
    - Start application locally
    - Test /pet endpoint with real GitHub username
    - Test /stats endpoint
    - Verify SVG renders correctly in browser
    - Test with non-existent username
    - Verify database persistence across requests
    - _Requirements: 1.1, 1.3, 1.5_
