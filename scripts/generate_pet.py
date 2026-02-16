"""
Generate pet SVG and state file for GitHub Actions (no server or database).

Reads GITHUB_TOKEN from the environment. Loads pet state from a JSON file (or creates
a new pet), fetches GitHub contribution and activity data, updates the pet via the
game engine, then writes the updated state and SVG to files. Used by the GitHub
Action so anyone can have a profile pet without deploying a server.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure repo root is on path when run as script (e.g. PYTHONPATH=.gh-tamagotchi)
if __name__ == "__main__":
    _script_dir = Path(__file__).resolve().parent
    _repo_root = _script_dir.parent
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))

from config.settings import Settings
from models.pet_models import PetState, PetStage
from services.github_service import GitHubService
from services.game_engine import GameEngine
from rendering.svg_renderer import SVGRenderer
from services.github_exceptions import (
    GitHubUserNotFoundError,
    GitHubRateLimitError,
    GitHubServiceError,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_pet_state(path: Path, username: str) -> PetState:
    """Load pet state from JSON file, or create default if file missing."""
    if not path.exists():
        now = datetime.utcnow()
        return PetState(
            username=username,
            hunger=50,
            happiness=50,
            health=100,
            energy=100,
            level=0,
            xp=0,
            stage=PetStage.EGG,
            last_updated=now,
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return PetState.model_validate(data)


def save_pet_state(path: Path, pet: PetState) -> None:
    """Write pet state to JSON file (JSON-serializable form)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        pet.model_dump_json(indent=2),
        encoding="utf-8",
    )


async def generate(
    username: str,
    state_path: Path,
    output_path: Path,
    token: str,
) -> None:
    """Fetch GitHub data, update pet, write state and SVG."""
    settings = Settings(github_token=token)
    game_engine = GameEngine(
        hunger_decay_rate=settings.hunger_decay_rate,
        happiness_decay_rate=settings.happiness_decay_rate,
        energy_decay_rate=settings.energy_decay_rate,
        health_decay_rate=settings.health_decay_rate,
        commit_hunger_boost=settings.commit_hunger_boost,
        commit_happiness_boost=settings.commit_happiness_boost,
        pr_merged_happiness_boost=settings.pr_merged_happiness_boost,
        pr_merged_xp_boost=settings.pr_merged_xp_boost,
        inactive_days_threshold=settings.inactive_days_threshold,
        inactive_happiness_penalty=settings.inactive_happiness_penalty,
        inactive_energy_penalty=settings.inactive_energy_penalty,
    )
    renderer = SVGRenderer()

    pet = load_pet_state(state_path, username)
    current_time = datetime.utcnow()

    async with GitHubService(settings=settings) as github_service:
        await github_service.validate_user_exists(username)
        contribution_data = await github_service.get_contribution_data(username, days=7)
        recent_activity = await github_service.get_recent_activity(username, limit=30)

    pet = game_engine.update_pet(
        pet,
        contribution_data,
        recent_activity,
        current_time,
    )

    save_pet_state(state_path, pet)
    svg = renderer.render_pet(pet)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    logger.info(
        "Pet updated: hunger=%s happiness=%s level=%s stage=%s",
        pet.hunger,
        pet.happiness,
        pet.level,
        pet.stage,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate GitHub Tamagotchi pet SVG and state (for GitHub Actions)."
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("GITHUB_ACTOR") or os.environ.get("GITHUB_REPOSITORY_OWNER", ""),
        help="GitHub username (default: GITHUB_ACTOR or GITHUB_REPOSITORY_OWNER)",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=Path(".pet-state.json"),
        help="Path to JSON state file (default: .pet-state.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("pet.svg"),
        help="Path to write SVG (default: pet.svg)",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        logger.error("GITHUB_TOKEN environment variable is required")
        return 1
    if not args.username:
        logger.error("Set --username or GITHUB_ACTOR / GITHUB_REPOSITORY_OWNER")
        return 1

    try:
        asyncio.run(
            generate(
                username=args.username,
                state_path=args.state_file,
                output_path=args.output,
                token=token,
            )
        )
    except GitHubUserNotFoundError as e:
        logger.error("GitHub user not found: %s", e.username)
        return 1
    except GitHubRateLimitError:
        logger.error("GitHub API rate limit exceeded")
        return 1
    except GitHubServiceError as e:
        logger.error("GitHub API error: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
