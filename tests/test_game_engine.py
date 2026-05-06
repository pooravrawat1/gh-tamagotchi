"""
Tests for the game engine time decay calculations.
"""
from datetime import datetime, timedelta
from services.game_engine import GameEngine
from models.pet_models import PetState, PetStage


def test_calculate_time_decay_basic():
    """Test basic time decay calculation."""
    engine = GameEngine()
    
    # Create a pet with known stats
    pet = PetState(
        username="testuser",
        hunger=50,
        happiness=60,
        health=100,
        energy=80,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    
    # Apply 1 hour of decay
    updated_pet = engine.calculate_time_decay(pet, hours_elapsed=1.0)
    
    # Verify decay rates applied correctly
    # hunger: 50 - (2.0 * 1) = 48
    assert updated_pet.hunger == 48
    # happiness: 60 - (3.0 * 1) = 57
    assert updated_pet.happiness == 57
    # energy: 80 - (1.5 * 1) = 78.5 -> 78
    assert updated_pet.energy == 78
    # health: 100 - (0.5 * 1) = 99.5 -> 99
    assert updated_pet.health == 99


def test_calculate_time_decay_clamping_at_zero():
    """Test that stats are clamped at 0 when decay would make them negative."""
    engine = GameEngine()
    
    # Create a pet with low stats
    pet = PetState(
        username="testuser",
        hunger=5,
        happiness=10,
        health=2,
        energy=3,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    
    # Apply 10 hours of decay (should bring all stats to 0)
    updated_pet = engine.calculate_time_decay(pet, hours_elapsed=10.0)
    
    # All stats should be clamped at 0
    assert updated_pet.hunger == 0
    assert updated_pet.happiness == 0
    assert updated_pet.energy == 0
    assert updated_pet.health == 0


def test_calculate_time_decay_multiple_hours():
    """Test time decay over multiple hours."""
    engine = GameEngine()
    
    pet = PetState(
        username="testuser",
        hunger=100,
        happiness=100,
        health=100,
        energy=100,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    
    # Apply 5 hours of decay
    updated_pet = engine.calculate_time_decay(pet, hours_elapsed=5.0)
    
    # hunger: 100 - (2.0 * 5) = 90
    assert updated_pet.hunger == 90
    # happiness: 100 - (3.0 * 5) = 85
    assert updated_pet.happiness == 85
    # energy: 100 - (1.5 * 5) = 92.5 -> 92
    assert updated_pet.energy == 92
    # health: 100 - (0.5 * 5) = 97.5 -> 97
    assert updated_pet.health == 97


def test_calculate_time_decay_zero_hours():
    """Test that no decay occurs when hours_elapsed is 0."""
    engine = GameEngine()
    
    pet = PetState(
        username="testuser",
        hunger=50,
        happiness=60,
        health=100,
        energy=80,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    
    # Apply 0 hours of decay
    updated_pet = engine.calculate_time_decay(pet, hours_elapsed=0.0)
    
    # Stats should remain unchanged
    assert updated_pet.hunger == 50
    assert updated_pet.happiness == 60
    assert updated_pet.energy == 80
    assert updated_pet.health == 100


def test_apply_activity_boosts_commits_today():
    """Test activity boosts when there are commit contributions today."""
    from datetime import date
    from models.github_models import ContributionData, ContributionDay
    
    engine = GameEngine()
    
    pet = PetState(
        username="testuser",
        hunger=40,
        happiness=50,
        health=100,
        energy=80,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    
    contribution_data = ContributionData(
        username="testuser",
        total_commits=0,
        contribution_days=[],
        commit_days=[
            ContributionDay(date=date.today(), count=5)
        ]
    )
    
    updated_pet = engine.apply_activity_boosts(
        pet,
        contribution_data,
        []
    )
    
    # Verify boosts applied
    # hunger: 40 + 10 = 50
    assert updated_pet.hunger == 50
    # happiness: 50 + 5 = 55
    assert updated_pet.happiness == 55
    # xp should remain unchanged
    assert updated_pet.xp == 0


def test_contribution_calendar_without_commit_day_does_not_grant_commit_boost():
    """Test generic contribution calendar activity does not count as commits."""
    from datetime import date
    from models.github_models import ContributionData, ContributionDay

    engine = GameEngine()
    pet = PetState(
        username="testuser",
        hunger=40,
        happiness=50,
        health=100,
        energy=80,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    contribution_data = ContributionData(
        username="testuser",
        total_commits=5,
        contribution_days=[
            ContributionDay(date=date.today(), count=5)
        ]
    )

    updated_pet = engine.apply_activity_boosts(pet, contribution_data, [])

    assert updated_pet.hunger == 40
    assert updated_pet.happiness == 50
    assert updated_pet.xp == 0


def test_apply_activity_boosts_merged_pr():
    """Test activity boosts when there are merged PRs."""
    from datetime import date
    from models.github_models import ContributionData, ActivityEvent
    
    engine = GameEngine()
    
    pet = PetState(
        username="testuser",
        hunger=40,
        happiness=50,
        health=100,
        energy=80,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    
    # Create contribution data with no commits today
    contribution_data = ContributionData(
        username="testuser",
        total_commits=0,
        contribution_days=[]
    )
    
    # Create activity with a merged PR
    recent_activity = [
        ActivityEvent(
            type="PullRequestEvent",
            created_at=datetime.utcnow(),
            metadata={"action": "closed", "merged": True}
        )
    ]
    
    # Apply activity boosts
    updated_pet = engine.apply_activity_boosts(pet, contribution_data, recent_activity)
    
    # Verify boosts applied
    # hunger should remain unchanged
    assert updated_pet.hunger == 40
    # happiness: 50 + 10 = 60
    assert updated_pet.happiness == 60
    # xp: 0 + 20 = 20
    assert updated_pet.xp == 20


def test_apply_activity_boosts_commits_and_merged_pr():
    """Test activity boosts when there are commit contributions and merged PRs."""
    from datetime import date
    from models.github_models import ContributionData, ContributionDay, ActivityEvent
    
    engine = GameEngine()
    
    pet = PetState(
        username="testuser",
        hunger=40,
        happiness=50,
        health=100,
        energy=80,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    
    contribution_data = ContributionData(
        username="testuser",
        total_commits=0,
        contribution_days=[],
        commit_days=[
            ContributionDay(date=date.today(), count=5)
        ]
    )
    
    recent_activity = [
        ActivityEvent(
            type="PullRequestEvent",
            created_at=datetime.utcnow(),
            metadata={"action": "closed", "merged": True}
        )
    ]
    
    # Apply activity boosts
    updated_pet = engine.apply_activity_boosts(pet, contribution_data, recent_activity)
    
    # Verify boosts applied
    # hunger: 40 + 10 = 50
    assert updated_pet.hunger == 50
    # happiness: 50 + 5 (commits) + 10 (PR) = 65
    assert updated_pet.happiness == 65
    # xp: 0 + 20 = 20
    assert updated_pet.xp == 20


def test_apply_activity_boosts_multiple_merged_prs():
    """Test activity boosts with multiple merged PRs."""
    from datetime import date
    from models.github_models import ContributionData, ActivityEvent
    
    engine = GameEngine()
    
    pet = PetState(
        username="testuser",
        hunger=40,
        happiness=50,
        health=100,
        energy=80,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    
    # Create contribution data with no commits today
    contribution_data = ContributionData(
        username="testuser",
        total_commits=0,
        contribution_days=[]
    )
    
    # Create activity with multiple merged PRs
    recent_activity = [
        ActivityEvent(
            type="PullRequestEvent",
            created_at=datetime.utcnow(),
            metadata={"action": "closed", "merged": True}
        ),
        ActivityEvent(
            type="PullRequestEvent",
            created_at=datetime.utcnow() - timedelta(hours=1),
            metadata={"action": "closed", "merged": True}
        )
    ]
    
    # Apply activity boosts
    updated_pet = engine.apply_activity_boosts(pet, contribution_data, recent_activity)
    
    # Verify boosts applied
    # hunger should remain unchanged
    assert updated_pet.hunger == 40
    # happiness: 50 + (10 * 2) = 70
    assert updated_pet.happiness == 70
    # xp: 0 + (20 * 2) = 40
    assert updated_pet.xp == 40


def test_apply_activity_boosts_clamping_at_100():
    """Test that stats are clamped at 100 when boosts would exceed maximum."""
    from datetime import date
    from models.github_models import ContributionData, ContributionDay
    
    engine = GameEngine()
    
    pet = PetState(
        username="testuser",
        hunger=95,
        happiness=98,
        health=100,
        energy=80,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    
    contribution_data = ContributionData(
        username="testuser",
        total_commits=0,
        contribution_days=[],
        commit_days=[
            ContributionDay(date=date.today(), count=5)
        ]
    )
    
    updated_pet = engine.apply_activity_boosts(
        pet,
        contribution_data,
        []
    )
    
    # Verify stats are clamped at 100
    # hunger: 95 + 10 = 105 -> clamped to 100
    assert updated_pet.hunger == 100
    # happiness: 98 + 5 = 103 -> clamped to 100
    assert updated_pet.happiness == 100


def test_apply_activity_boosts_no_activity():
    """Test that no boosts are applied when there's no activity."""
    from models.github_models import ContributionData
    
    engine = GameEngine()
    
    pet = PetState(
        username="testuser",
        hunger=40,
        happiness=50,
        health=100,
        energy=80,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    
    # Create contribution data with no commits today
    contribution_data = ContributionData(
        username="testuser",
        total_commits=0,
        contribution_days=[]
    )
    
    # Apply activity boosts with no recent activity
    updated_pet = engine.apply_activity_boosts(pet, contribution_data, [])
    
    # Verify no changes
    assert updated_pet.hunger == 40
    assert updated_pet.happiness == 50
    assert updated_pet.xp == 0


def test_apply_activity_boosts_pr_not_merged():
    """Test that no boosts are applied for PRs that are not merged."""
    from models.github_models import ContributionData, ActivityEvent
    
    engine = GameEngine()
    
    pet = PetState(
        username="testuser",
        hunger=40,
        happiness=50,
        health=100,
        energy=80,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=datetime.utcnow()
    )
    
    # Create contribution data with no commits today
    contribution_data = ContributionData(
        username="testuser",
        total_commits=0,
        contribution_days=[]
    )
    
    # Create activity with a non-merged PR
    recent_activity = [
        ActivityEvent(
            type="PullRequestEvent",
            created_at=datetime.utcnow(),
            metadata={"action": "opened", "merged": False}
        )
    ]
    
    # Apply activity boosts
    updated_pet = engine.apply_activity_boosts(pet, contribution_data, recent_activity)
    
    # Verify no boosts applied
    assert updated_pet.hunger == 40
    assert updated_pet.happiness == 50
    assert updated_pet.xp == 0


def test_update_pet_does_not_reward_same_activity_twice():
    """Test repeated syncs do not grant XP/commit boosts for old activity."""
    from models.github_models import ContributionData, ContributionDay, ActivityEvent

    engine = GameEngine()
    first_sync_time = datetime(2026, 5, 6, 12, 0, 0)
    second_sync_time = first_sync_time + timedelta(minutes=10)

    pet = PetState(
        username="testuser",
        hunger=50,
        happiness=50,
        health=100,
        energy=100,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=first_sync_time - timedelta(days=1)
    )
    contribution_data = ContributionData(
        username="testuser",
        total_commits=1,
        contribution_days=[
            ContributionDay(date=first_sync_time.date(), count=1)
        ],
        commit_days=[
            ContributionDay(date=first_sync_time.date(), count=3)
        ]
    )
    recent_activity = [
        ActivityEvent(
            type="PullRequestEvent",
            created_at=first_sync_time - timedelta(minutes=1),
            metadata={"action": "closed", "merged": True}
        )
    ]

    first_update = engine.update_pet(
        pet,
        contribution_data,
        recent_activity,
        first_sync_time
    )
    second_update = engine.update_pet(
        first_update,
        contribution_data,
        recent_activity,
        second_sync_time
    )

    assert first_update.xp == 20
    assert second_update.xp == 20
    assert second_update.happiness < first_update.happiness
    assert second_update.hunger < first_update.hunger


def test_initial_sync_rewards_existing_recent_activity():
    """Test an initial sync can reward today's commits and current recent PRs."""
    from models.github_models import ContributionData, ContributionDay, ActivityEvent

    engine = GameEngine()
    current_time = datetime(2026, 5, 6, 12, 0, 0)
    pet = PetState(
        username="testuser",
        hunger=50,
        happiness=50,
        health=100,
        energy=100,
        level=0,
        xp=0,
        stage=PetStage.EGG,
        last_updated=current_time
    )
    contribution_data = ContributionData(
        username="testuser",
        total_commits=1,
        contribution_days=[
            ContributionDay(date=current_time.date(), count=1)
        ],
        commit_days=[
            ContributionDay(date=current_time.date(), count=3)
        ]
    )
    recent_activity = [
        ActivityEvent(
            type="PullRequestEvent",
            created_at=current_time - timedelta(hours=1),
            metadata={"action": "closed", "merged": True}
        )
    ]

    updated_pet = engine.update_pet(
        pet,
        contribution_data,
        recent_activity,
        current_time,
        initial_sync=True
    )

    assert updated_pet.hunger == 60
    assert updated_pet.happiness == 65
    assert updated_pet.xp == 20


def test_activity_reward_cutoff_handles_timezone_aware_events():
    """Test aware GitHub timestamps compare cleanly with naive UTC state."""
    from datetime import timezone
    from models.github_models import ContributionData, ActivityEvent

    engine = GameEngine()
    sync_time = datetime(2026, 5, 6, 12, 0, 0)
    pet = PetState(
        username="testuser",
        hunger=50,
        happiness=50,
        health=100,
        energy=100,
        level=0,
        xp=20,
        stage=PetStage.EGG,
        last_updated=sync_time
    )
    contribution_data = ContributionData(
        username="testuser",
        total_commits=0,
        contribution_days=[]
    )
    recent_activity = [
        ActivityEvent(
            type="PullRequestEvent",
            created_at=sync_time.replace(tzinfo=timezone.utc),
            metadata={"action": "closed", "merged": True}
        )
    ]

    updated_pet = engine.update_pet(
        pet,
        contribution_data,
        recent_activity,
        sync_time + timedelta(minutes=10)
    )

    assert updated_pet.xp == 20
