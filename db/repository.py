"""
Pet repository for database operations.

This module provides the data access layer for pet persistence,
implementing CRUD operations and business logic for pet management.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.models import PetDB
from models.pet_models import PetState


class PetRepository:
    """
    Repository for pet data access operations.
    
    Provides methods for creating, reading, and updating pet state
    in the database. Handles conversion between ORM models (PetDB)
    and business logic models (PetState).
    """
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session
    
    def get_pet(self, username: str) -> Optional[PetState]:
        """
        Retrieve pet by username.
        
        Args:
            username: GitHub username to look up
        
        Returns:
            PetState if found, None otherwise
        """
        pet_db = self.session.query(PetDB).filter(PetDB.username == username).first()
        
        if pet_db is None:
            return None
        
        # Convert ORM model to Pydantic model
        return PetState.model_validate(pet_db)
    
    def create_pet(self, username: str) -> PetState:
        """
        Create new pet with default values.
        
        Default values:
        - hunger: 50
        - happiness: 50
        - health: 100
        - energy: 100
        - level: 0
        - xp: 0
        - stage: 'egg'
        - last_updated: current timestamp
        
        Args:
            username: GitHub username for the new pet
        
        Returns:
            Newly created PetState
        
        Raises:
            IntegrityError: If pet with username already exists
        """
        current_time = datetime.utcnow()
        
        pet_db = PetDB(
            username=username,
            hunger=50,
            happiness=50,
            health=100,
            energy=100,
            level=0,
            xp=0,
            stage='egg',
            last_updated=current_time,
            created_at=current_time
        )
        
        self.session.add(pet_db)
        self.session.commit()
        self.session.refresh(pet_db)
        
        return PetState.model_validate(pet_db)
    
    def update_pet(self, pet: PetState) -> PetState:
        """
        Update existing pet state.
        
        Updates all mutable fields of the pet in the database.
        The username is used to identify the pet to update.
        
        Args:
            pet: PetState with updated values
        
        Returns:
            Updated PetState from database
        
        Raises:
            ValueError: If pet with username doesn't exist
        """
        pet_db = self.session.query(PetDB).filter(PetDB.username == pet.username).first()
        
        if pet_db is None:
            raise ValueError(f"Pet with username '{pet.username}' not found")
        
        # Update all fields
        pet_db.hunger = pet.hunger
        pet_db.happiness = pet.happiness
        pet_db.health = pet.health
        pet_db.energy = pet.energy
        pet_db.level = pet.level
        pet_db.xp = pet.xp
        pet_db.stage = pet.stage
        pet_db.last_updated = pet.last_updated
        
        self.session.commit()
        self.session.refresh(pet_db)
        
        return PetState.model_validate(pet_db)
    
    def get_or_create_pet(self, username: str) -> PetState:
        """
        Get existing pet or create if doesn't exist.
        
        This is a convenience method that combines get and create operations.
        If the pet exists, it returns the existing pet. If not, it creates
        a new pet with default values.
        
        Args:
            username: GitHub username to look up or create
        
        Returns:
            Existing or newly created PetState
        """
        pet = self.get_pet(username)
        
        if pet is None:
            pet = self.create_pet(username)
        
        return pet
