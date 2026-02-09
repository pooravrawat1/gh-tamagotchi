# Requirements Document

## Introduction

GitHub Tamagotchi is a web service that generates dynamic SVG pet widgets based on a user's GitHub activity. The service provides an embeddable image URL for GitHub profile READMEs, where a virtual pet's stats and evolution are driven by the user's coding activity. The system must be stateless at the request level, fast, cache-aware, and production-ready.

## Glossary

- **Pet Widget**: An SVG image representing a virtual pet with visual stats and appearance
- **GitHub Tamagotchi Service**: The FastAPI-based web service that generates pet widgets
- **Pet State**: The persistent data model containing username, stats (hunger, happiness, health, energy), level, stage, and last update timestamp
- **Game Engine**: The component responsible for calculating stat updates, decay, and evolution logic
- **GitHub Data Service**: The component that fetches user activity from GitHub APIs
- **Rendering Engine**: The component that generates SVG output from pet state
- **Persistence Layer**: SQLite database storing pet state with future Postgres compatibility
- **Activity Boost**: Positive stat changes triggered by GitHub events (commits, PRs, etc.)
- **Time Decay**: Negative stat changes based on elapsed time since last update
- **Evolution Stage**: Pet appearance tier (egg, baby, teen, adult, legendary) based on level

## Requirements

### Requirement 1

**User Story:** As a GitHub user, I want to embed a dynamic pet widget in my README, so that my profile displays a virtual pet that reflects my coding activity

#### Acceptance Criteria

1. WHEN a user requests `/pet?user=USERNAME`, THE GitHub Tamagotchi Service SHALL return an SVG image within 100 milliseconds
2. THE GitHub Tamagotchi Service SHALL generate the SVG image containing the pet sprite, username, stage label, stat bars, and mood text
3. THE GitHub Tamagotchi Service SHALL support embedding via standard markdown image syntax in GitHub READMEs
4. THE Rendering Engine SHALL generate lightweight SVG output without external asset dependencies
5. THE GitHub Tamagotchi Service SHALL handle multiple concurrent requests without state conflicts

### Requirement 2

**User Story:** As a GitHub user, I want my pet's stats to increase when I'm active on GitHub, so that my coding efforts are rewarded

#### Acceptance Criteria

1. WHEN the GitHub Data Service detects commits for the current day, THE Game Engine SHALL increase hunger by 10 points and happiness by 5 points
2. WHEN the GitHub Data Service detects a merged pull request, THE Game Engine SHALL increase happiness by 10 points and level experience by 20 points
3. THE Game Engine SHALL cap all stat values at a maximum of 100 points
4. THE Game Engine SHALL calculate Activity Boosts based on GitHub events retrieved from the GitHub GraphQL API or REST API
5. THE Game Engine SHALL apply all applicable Activity Boosts during a single update cycle

### Requirement 3

**User Story:** As a GitHub user, I want my pet's stats to decrease when I'm inactive, so that the pet feels alive and requires attention

#### Acceptance Criteria

1. WHILE time since last update is greater than zero, THE Game Engine SHALL decrease hunger based on elapsed time
2. WHILE the user has no GitHub activity, THE Game Engine SHALL decrease happiness at a faster rate than hunger
3. WHEN the user has been inactive for more than 3 days, THE Game Engine SHALL decrease happiness by 15 points and energy by 10 points
4. THE Game Engine SHALL calculate Time Decay based on the difference between current timestamp and last_updated timestamp
5. THE Game Engine SHALL prevent stat values from falling below 0 points

### Requirement 4

**User Story:** As a GitHub user, I want my pet to evolve through different stages, so that I can see visual progression as I level up

#### Acceptance Criteria

1. WHEN the pet level is between 0 and 2, THE Game Engine SHALL set the evolution stage to "egg"
2. WHEN the pet level is between 3 and 6, THE Game Engine SHALL set the evolution stage to "baby"
3. WHEN the pet level is between 7 and 12, THE Game Engine SHALL set the evolution stage to "teen"
4. WHEN the pet level is between 13 and 20, THE Game Engine SHALL set the evolution stage to "adult"
5. WHEN the pet level is greater than 20, THE Game Engine SHALL set the evolution stage to "legendary"
6. THE Rendering Engine SHALL display different visual representations for each evolution stage

### Requirement 5

**User Story:** As a GitHub user, I want the service to cache my GitHub data, so that the widget loads quickly and respects API rate limits

#### Acceptance Criteria

1. WHEN the time since last GitHub sync is less than a configured threshold, THE GitHub Data Service SHALL return cached pet stats without fetching from GitHub APIs
2. WHEN the time since last GitHub sync exceeds the configured threshold, THE GitHub Data Service SHALL fetch fresh data from GitHub APIs
3. THE GitHub Data Service SHALL store the timestamp of the last GitHub sync in the Persistence Layer
4. THE GitHub Tamagotchi Service SHALL use in-memory caching with architecture ready for Redis integration
5. THE GitHub Data Service SHALL use asynchronous HTTP requests via httpx or aiohttp for GitHub API calls

### Requirement 6

**User Story:** As a developer, I want the service to persist pet state in a database, so that pets maintain their stats across requests

#### Acceptance Criteria

1. THE Persistence Layer SHALL store username, hunger, happiness, health, energy, level, stage, and last_updated timestamp for each pet
2. THE Persistence Layer SHALL use SQLite as the database engine for the MVP
3. THE Persistence Layer SHALL implement a database schema that allows future migration to PostgreSQL
4. WHEN a pet state is updated, THE Persistence Layer SHALL persist the changes with the current timestamp
5. WHEN a pet does not exist for a given username, THE Persistence Layer SHALL create a new pet with default initial values

### Requirement 7

**User Story:** As a developer, I want the codebase to be modular and production-ready, so that the service is maintainable and extensible

#### Acceptance Criteria

1. THE GitHub Tamagotchi Service SHALL separate concerns into distinct layers: API, GitHub Data Service, Game Engine, Persistence Layer, and Rendering Engine
2. THE GitHub Tamagotchi Service SHALL use environment variables for configuration including GitHub tokens
3. THE GitHub Tamagotchi Service SHALL include Python type hints throughout the codebase
4. THE GitHub Tamagotchi Service SHALL avoid hardcoded credentials and blocking API calls
5. THE GitHub Tamagotchi Service SHALL implement a project structure with separate directories for api, services, models, db, rendering, and utils

### Requirement 8

**User Story:** As a developer, I want to deploy the service to a cloud platform, so that users can access the pet widget via a public URL

#### Acceptance Criteria

1. THE GitHub Tamagotchi Service SHALL be deployable to Render, Railway, or Fly.io platforms
2. THE GitHub Tamagotchi Service SHALL include necessary configuration files for deployment
3. THE GitHub Tamagotchi Service SHALL handle environment-specific configuration via environment variables
4. THE GitHub Tamagotchi Service SHALL serve the `/pet` endpoint at the root domain path
5. THE GitHub Tamagotchi Service SHALL return appropriate HTTP status codes and error messages for invalid requests

### Requirement 9

**User Story:** As a GitHub user, I want to view my pet's stats as JSON, so that I can integrate the data with other tools

#### Acceptance Criteria

1. WHEN a user requests `/stats?user=USERNAME`, THE GitHub Tamagotchi Service SHALL return a JSON response containing all pet state fields
2. THE GitHub Tamagotchi Service SHALL include username, hunger, happiness, health, energy, level, stage, and last_updated in the JSON response
3. THE GitHub Tamagotchi Service SHALL return the JSON response with appropriate content-type headers
4. THE GitHub Tamagotchi Service SHALL apply the same caching and update logic for `/stats` as for `/pet`
5. THE GitHub Tamagotchi Service SHALL return a 404 status code when the requested username does not exist

### Requirement 10

**User Story:** As a developer, I want the GitHub API integration to be secure and configurable, so that the service can authenticate properly without exposing credentials

#### Acceptance Criteria

1. THE GitHub Data Service SHALL accept GitHub API tokens via environment variables
2. THE GitHub Data Service SHALL use the GitHub GraphQL API for fetching contribution calendar data
3. THE GitHub Data Service SHALL use the GitHub REST API for fetching recent activity events
4. THE GitHub Data Service SHALL handle GitHub API rate limit errors gracefully
5. THE GitHub Data Service SHALL not expose GitHub tokens in logs, error messages, or API responses
