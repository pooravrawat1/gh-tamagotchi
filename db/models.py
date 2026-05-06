"""
SQLAlchemy ORM models for database persistence.

This module defines the database schema for pet state storage.
The schema is designed to be compatible with both SQLite and PostgreSQL.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, CheckConstraint, Index
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class PetDB(Base):
    """
    SQLAlchemy ORM model for pet persistence.
    
    This model represents the pets table with all necessary constraints
    and indexes for efficient querying and data integrity.
    
    Attributes:
        id: Primary key, auto-incrementing
        username: GitHub username (unique, indexed)
        hunger: Hunger stat (0-100)
        happiness: Happiness stat (0-100)
        health: Health stat (0-100)
        energy: Energy stat (0-100)
        level: Pet level (non-negative)
        xp: Experience points (non-negative)
        stage: Evolution stage (egg, baby, teen, adult, legendary)
        last_commit_reward_date: Last date the daily commit reward was applied
        last_updated: Timestamp of last update (indexed)
        created_at: Timestamp of pet creation
    """
    __tablename__ = "pets"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core fields
    username = Column(String, unique=True, nullable=False, index=True)
    
    # Stats (0-100 range)
    hunger = Column(Integer, nullable=False, default=50)
    happiness = Column(Integer, nullable=False, default=50)
    health = Column(Integer, nullable=False, default=100)
    energy = Column(Integer, nullable=False, default=100)
    
    # Progression
    level = Column(Integer, nullable=False, default=0)
    xp = Column(Integer, nullable=False, default=0)
    stage = Column(String, nullable=False, default='egg')
    
    # Timestamps
    last_commit_reward_date = Column(Date, nullable=True)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Check constraints for data integrity
    __table_args__ = (
        CheckConstraint('hunger >= 0 AND hunger <= 100', name='check_hunger_range'),
        CheckConstraint('happiness >= 0 AND happiness <= 100', name='check_happiness_range'),
        CheckConstraint('health >= 0 AND health <= 100', name='check_health_range'),
        CheckConstraint('energy >= 0 AND energy <= 100', name='check_energy_range'),
        CheckConstraint('level >= 0', name='check_level_non_negative'),
        CheckConstraint('xp >= 0', name='check_xp_non_negative'),
        CheckConstraint(
            "stage IN ('egg', 'baby', 'teen', 'adult', 'legendary')",
            name='check_stage_valid'
        ),
        # Indexes are defined via Column(index=True) above, but we can add composite indexes here if needed
    )
    
    def __repr__(self):
        return (
            f"<PetDB(username='{self.username}', stage='{self.stage}', "
            f"level={self.level}, last_updated='{self.last_updated}')>"
        )
