"""
Tests for the PetRepository class.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.models import Base, PetDB
from db.repository import PetRepository
from models.pet_models import PetState


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def repository(db_session):
    """Create a PetRepository instance with test database."""
    return PetRepository(db_session)


def test_create_pet(repository):
    """Test creating a new pet with default values."""
    pet = repository.create_pet("testuser")
    
    assert pet.username == "testuser"
    assert pet.hunger == 50
    assert pet.happiness == 50
    assert pet.health == 100
    assert pet.energy == 100
    assert pet.level == 0
    assert pet.xp == 0
    assert pet.stage == "egg"
    assert isinstance(pet.last_updated, datetime)


def test_get_pet_exists(repository):
    """Test retrieving an existing pet."""
    repository.create_pet("testuser")
    pet = repository.get_pet("testuser")
    
    assert pet is not None
    assert pet.username == "testuser"


def test_get_pet_not_exists(repository):
    """Test retrieving a non-existent pet returns None."""
    pet = repository.get_pet("nonexistent")
    assert pet is None


def test_update_pet(repository):
    """Test updating pet stats."""
    pet = repository.create_pet("testuser")
    
    # Modify pet stats
    pet.hunger = 75
    pet.happiness = 80
    pet.level = 5
    pet.xp = 500
    pet.stage = "baby"
    
    updated_pet = repository.update_pet(pet)
    
    assert updated_pet.hunger == 75
    assert updated_pet.happiness == 80
    assert updated_pet.level == 5
    assert updated_pet.xp == 500
    assert updated_pet.stage == "baby"


def test_update_pet_not_exists(repository):
    """Test updating a non-existent pet raises ValueError."""
    pet = PetState(
        username="nonexistent",
        hunger=50,
        happiness=50,
        health=100,
        energy=100,
        level=0,
        xp=0,
        stage="egg",
        last_updated=datetime.utcnow()
    )
    
    with pytest.raises(ValueError, match="Pet with username 'nonexistent' not found"):
        repository.update_pet(pet)


def test_get_or_create_pet_creates(repository):
    """Test get_or_create creates pet when it doesn't exist."""
    pet = repository.get_or_create_pet("newuser")
    
    assert pet.username == "newuser"
    assert pet.hunger == 50


def test_get_or_create_pet_gets(repository):
    """Test get_or_create returns existing pet."""
    # Create pet first
    original_pet = repository.create_pet("existinguser")
    
    # Modify it
    original_pet.hunger = 30
    repository.update_pet(original_pet)
    
    # get_or_create should return the existing pet
    pet = repository.get_or_create_pet("existinguser")
    
    assert pet.username == "existinguser"
    assert pet.hunger == 30  # Should have the modified value


def test_create_duplicate_pet_raises_error(repository):
    """Test creating a pet with duplicate username raises IntegrityError."""
    from sqlalchemy.exc import IntegrityError
    
    repository.create_pet("testuser")
    
    with pytest.raises(IntegrityError):
        repository.create_pet("testuser")


def test_repository_can_use_session_factory():
    """Test repository opens per-operation sessions from a factory."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    repository = PetRepository(session_factory=SessionLocal)

    pet = repository.create_pet("factoryuser")
    pet.hunger = 25
    repository.update_pet(pet)

    fetched_pet = repository.get_pet("factoryuser")

    assert fetched_pet is not None
    assert fetched_pet.hunger == 25
