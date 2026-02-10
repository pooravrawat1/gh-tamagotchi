"""
Pet data models for business logic.

This module defines the Pydantic models used throughout the application
for representing pet state and validation.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class PetStage(str, Enum):
    """Evolution stages for the pet."""
    EGG = "egg"
    BABY = "baby"
    TEEN = "teen"
    ADULT = "adult"
    LEGENDARY = "legendary"


class PetState(BaseModel):
    """
    Pydantic model for pet state used in business logic.
    
    All stats are constrained to [0, 100] range.
    Level and XP must be non-negative.
    """
    username: str
    hunger: int = Field(ge=0, le=100, default=50, description="Hunger level (0-100)")
    happiness: int = Field(ge=0, le=100, default=50, description="Happiness level (0-100)")
    health: int = Field(ge=0, le=100, default=100, description="Health level (0-100)")
    energy: int = Field(ge=0, le=100, default=100, description="Energy level (0-100)")
    level: int = Field(ge=0, default=0, description="Pet level")
    xp: int = Field(ge=0, default=0, description="Experience points")
    stage: PetStage = Field(default=PetStage.EGG, description="Evolution stage")
    last_updated: datetime = Field(description="Last update timestamp")
    
    class Config:
        from_attributes = True
        use_enum_values = True
