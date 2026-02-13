"""
Game engine for GitHub Tamagotchi pet stats and evolution logic.
"""
from models.pet_models import PetState


class GameEngine:
    """
    Game engine responsible for calculating pet stat updates, decay, and evolution.
    """
    
    # Stat decay rates (per hour)
    HUNGER_DECAY_RATE = 2.0
    HAPPINESS_DECAY_RATE = 3.0
    ENERGY_DECAY_RATE = 1.5
    HEALTH_DECAY_RATE = 0.5
    
    # Activity boost values
    COMMIT_HUNGER_BOOST = 10
    COMMIT_HAPPINESS_BOOST = 5
    PR_MERGED_HAPPINESS_BOOST = 10
    PR_MERGED_XP_BOOST = 20
    
    # Inactivity penalties
    INACTIVE_DAYS_THRESHOLD = 3
    INACTIVE_HAPPINESS_PENALTY = 15
    INACTIVE_ENERGY_PENALTY = 10
    
    @staticmethod
    def clamp_stat(value: float, min_value: int = 0, max_value: int = 100) -> int:
        """
        Clamp a stat value to the range [min_value, max_value].
        
        Args:
            value: The stat value to clamp
            min_value: Minimum allowed value (default: 0)
            max_value: Maximum allowed value (default: 100)
            
        Returns:
            Clamped integer value within [min_value, max_value]
        """
        return int(max(min_value, min(max_value, value)))
