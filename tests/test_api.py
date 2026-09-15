"""
Tests for API route wiring.
"""

from datetime import datetime

from fastapi.testclient import TestClient

from api.dependencies import get_pet_service_dependency
from api.main import app
from models.github_models import GitHubProfileSnapshot
from models.pet_models import PetProfile, PetState


class StubPetService:
    async def get_pet_svg(self, username):
        return f"<svg><text>{username}</text></svg>"

    async def get_pet_stats(self, username):
        return PetState(
            username=username,
            hunger=50,
            happiness=60,
            health=100,
            energy=90,
            level=0,
            xp=0,
            stage="egg",
            last_updated=datetime(2026, 5, 6, 12, 0, 0),
        )

    async def get_pet_profile(self, username):
        return PetProfile(
            pet=await self.get_pet_stats(username),
            github=GitHubProfileSnapshot(
                username=username,
                account_created_at=datetime(2020, 1, 1),
                recent_commits=25,
                recent_total_contributions=40,
                lifetime_contributions=200,
                fetched_at=datetime(2026, 5, 6, 12, 0, 0),
            ),
        )


async def override_pet_service():
    return StubPetService()


def test_pet_endpoint_uses_dependency_and_returns_svg():
    app.dependency_overrides[get_pet_service_dependency] = override_pet_service
    client = TestClient(app)
    try:
        response = client.get("/pet?user=octocat")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml; charset=utf-8"
    assert "<text>octocat</text>" in response.text


def test_stats_endpoint_uses_dependency_and_returns_json():
    app.dependency_overrides[get_pet_service_dependency] = override_pet_service
    client = TestClient(app)
    try:
        response = client.get("/stats?user=octocat")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["username"] == "octocat"
    assert response.json()["happiness"] == 60


def test_clean_pet_image_url_uses_same_service():
    app.dependency_overrides[get_pet_service_dependency] = override_pet_service
    client = TestClient(app)
    try:
        response = client.get("/pet/octocat.svg")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml; charset=utf-8"
    assert "<text>octocat</text>" in response.text


def test_profile_endpoint_returns_pet_and_github_snapshot():
    app.dependency_overrides[get_pet_service_dependency] = override_pet_service
    client = TestClient(app)
    try:
        response = client.get("/profile/octocat")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["pet"]["username"] == "octocat"
    assert response.json()["github"]["recent_commits"] == 25
    assert "recent_private_contributions" not in response.json()["github"]


def test_empty_user_returns_400():
    app.dependency_overrides[get_pet_service_dependency] = override_pet_service
    client = TestClient(app)
    try:
        response = client.get("/pet?user=")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
