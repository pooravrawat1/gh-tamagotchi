"""
Tests for PetService orchestration and cache behavior.
"""

import asyncio
import pytest
from datetime import date, datetime, timedelta

from models.github_models import ContributionData, ContributionDay, GitHubProfileSnapshot
from models.pet_models import PetState
from services.game_engine import GameEngine
from services.pet_service import PetService
from utils.cache import CacheService


class StubSettings:
    cache_ttl_seconds = 300


class StubGitHubService:
    def __init__(self):
        self.validations = 0
        self.contribution_fetches = 0
        self.activity_fetches = 0

    async def validate_user_exists(self, username):
        self.validations += 1
        return True

    async def get_contribution_data(self, username, days=7):
        self.contribution_fetches += 1
        return ContributionData(
            username=username,
            total_commits=1,
            contribution_days=[
                ContributionDay(date=date.today(), count=1)
            ],
            commit_days=[
                ContributionDay(date=date.today(), count=1)
            ],
        )

    async def get_recent_activity(self, username, limit=30):
        self.activity_fetches += 1
        return []


class StubRepository:
    def __init__(self, initial_pet=None):
        self.pet = initial_pet
        self.created = 0
        self.updated = 0

    def get_pet(self, username):
        return self.pet

    def create_pet(self, username):
        self.created += 1
        self.pet = PetState(
            username=username,
            hunger=50,
            happiness=50,
            health=100,
            energy=100,
            level=0,
            xp=0,
            stage="egg",
            last_updated=datetime.utcnow(),
        )
        return self.pet

    def update_pet(self, pet):
        self.updated += 1
        self.pet = pet
        return pet


class StubRenderer:
    def render_pet(self, pet, profile=None):
        return f"svg:{pet.username}:{pet.hunger}:{pet.happiness}"


class SnapshotGitHubService:
    def __init__(self):
        self.snapshot_fetches = 0

    async def get_profile_snapshot(self, username):
        self.snapshot_fetches += 1
        today = date.today()
        return GitHubProfileSnapshot(
            username=username,
            display_name="The Octocat",
            account_created_at=datetime(2021, 1, 1),
            followers=10,
            public_repos=5,
            total_stars=25,
            languages=["Python", "TypeScript"],
            recent_commits=24,
            recent_pull_requests=8,
            recent_reviews=12,
            recent_issues=4,
            recent_active_days=2,
            recent_total_contributions=48,
            contribution_days=[
                ContributionDay(date=today, count=12),
                ContributionDay(date=today - timedelta(days=1), count=8),
            ],
            lifetime_contributions=2500,
            fetched_at=datetime.utcnow(),
        )


@pytest.mark.asyncio
async def test_fresh_existing_pet_renders_without_github_calls():
    pet = PetState(
        username="octocat",
        hunger=42,
        happiness=70,
        health=100,
        energy=90,
        level=0,
        xp=0,
        stage="egg",
        last_updated=datetime.utcnow(),
    )
    github = StubGitHubService()
    repository = StubRepository(initial_pet=pet)
    service = PetService(
        github_service=github,
        game_engine=GameEngine(),
        repository=repository,
        renderer=StubRenderer(),
        cache=CacheService(),
        settings=StubSettings(),
    )

    svg = await service.get_pet_svg("octocat")

    assert svg == "svg:octocat:42:70"
    assert github.validations == 0
    assert github.contribution_fetches == 0
    assert github.activity_fetches == 0
    assert repository.created == 0
    assert repository.updated == 0


@pytest.mark.asyncio
async def test_new_pet_validates_and_syncs_immediately():
    github = StubGitHubService()
    repository = StubRepository()
    service = PetService(
        github_service=github,
        game_engine=GameEngine(),
        repository=repository,
        renderer=StubRenderer(),
        cache=CacheService(),
        settings=StubSettings(),
    )

    svg = await service.get_pet_svg("octocat")

    assert svg == "svg:octocat:60:55"
    assert github.validations == 1
    assert github.contribution_fetches == 1
    assert github.activity_fetches == 1
    assert repository.created == 1
    assert repository.updated == 1


@pytest.mark.asyncio
async def test_stale_pet_refresh_uses_cached_validation_and_github_data():
    pet = PetState(
        username="octocat",
        hunger=50,
        happiness=50,
        health=100,
        energy=100,
        level=0,
        xp=0,
        stage="egg",
        last_updated=datetime.utcnow() - timedelta(minutes=10),
    )
    github = StubGitHubService()
    repository = StubRepository(initial_pet=pet)
    service = PetService(
        github_service=github,
        game_engine=GameEngine(),
        repository=repository,
        renderer=StubRenderer(),
        cache=CacheService(),
        settings=StubSettings(),
    )

    await service.get_pet_svg("octocat")
    repository.pet = repository.pet.model_copy(
        update={"last_updated": datetime.utcnow() - timedelta(minutes=10)}
    )
    await service.get_pet_stats("octocat")

    assert github.validations == 1
    assert github.contribution_fetches == 1
    assert github.activity_fetches == 1
    assert repository.updated == 2


@pytest.mark.asyncio
async def test_profile_snapshot_drives_pet_and_is_reused_for_svg_and_profile():
    github = SnapshotGitHubService()
    repository = StubRepository()
    service = PetService(
        github_service=github,
        game_engine=GameEngine(),
        repository=repository,
        renderer=StubRenderer(),
        cache=CacheService(),
        settings=StubSettings(),
    )

    svg = await service.get_pet_svg("octocat")
    profile = await service.get_pet_profile("octocat")

    assert svg.startswith("svg:octocat:100:")
    assert github.snapshot_fetches == 1
    assert profile.github.recent_reviews == 12
    assert profile.pet.xp > 500
    assert repository.updated == 1


@pytest.mark.asyncio
async def test_cache_single_flight_loads_a_profile_once():
    cache = CacheService()
    calls = 0

    async def loader():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)
        return {"fresh": True}

    values = await asyncio.gather(*[
        cache.get_or_set_async("profile:octocat", loader, ttl=60)
        for _ in range(5)
    ])

    assert calls == 1
    assert values == [{"fresh": True}] * 5
