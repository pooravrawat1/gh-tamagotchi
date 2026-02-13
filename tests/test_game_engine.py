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
