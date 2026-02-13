"""
Game engine for GitHub Tamagotchi pet stats and evolution logic.
"""
from datetime import date
from typing import List
from models.pet_models import PetState
from models.github_models import ContributionData, ActivityEvent


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
    
    def calculate_time_decay(self, pet: PetState, hours_elapsed: float) -> PetState:
        """
        Apply time-based stat decay to the pet.
        
        Stats decay at different rates per hour:
        - Hunger decreases by HUNGER_DECAY_RATE per hour
        - Happiness decreases by HAPPINESS_DECAY_RATE per hour
        - Energy decreases by ENERGY_DECAY_RATE per hour
        - Health decreases by HEALTH_DECAY_RATE per hour
        
        All stats are clamped to [0, 100] after decay.
        
        Args:
            pet: Current pet state
            hours_elapsed: Number of hours since last update
            
        Returns:
            Updated pet state with decayed stats
        """
        # Calculate new stat values after decay
        new_hunger = pet.hunger - (self.HUNGER_DECAY_RATE * hours_elapsed)
        new_happiness = pet.happiness - (self.HAPPINESS_DECAY_RATE * hours_elapsed)
        new_energy = pet.energy - (self.ENERGY_DECAY_RATE * hours_elapsed)
        new_health = pet.health - (self.HEALTH_DECAY_RATE * hours_elapsed)
        
        # Clamp all stats to valid range [0, 100]
        return pet.model_copy(update={
            'hunger': self.clamp_stat(new_hunger),
            'happiness': self.clamp_stat(new_happiness),
            'energy': self.clamp_stat(new_energy),
            'health': self.clamp_stat(new_health)
        })
    
    def apply_activity_boosts(
        self,
        pet: PetState,
        contribution_data: ContributionData,
        recent_activity: List[ActivityEvent]
    ) -> PetState:
        """
        Apply positive stat changes based on GitHub activity.
        
        Boosts are applied for:
        - Commits today: hunger +10, happiness +5
        - Merged PRs: happiness +10, xp +20 (per merged PR)
        
        All stats are clamped to [0, 100] after boosts.
        
        Args:
            pet: Current pet state
            contribution_data: GitHub contribution data
            recent_activity: List of recent GitHub activity events
            
        Returns:
            Updated pet state with activity boosts applied
        """
        # Start with current stat values
        new_hunger = pet.hunger
        new_happiness = pet.happiness
        new_xp = pet.xp
        
        # Check for commits today
        today = date.today()
        commits_today = 0
        
        for day in contribution_data.contribution_days:
            if day.date == today:
                commits_today = day.count
                break
        
        # Apply commit boosts if there are commits today
        if commits_today > 0:
            new_hunger += self.COMMIT_HUNGER_BOOST
            new_happiness += self.COMMIT_HAPPINESS_BOOST
        
        # Check for merged PRs in recent activity
        merged_pr_count = 0
        
        for event in recent_activity:
            if event.type == "PullRequestEvent":
                # Check if the PR was merged
                if event.metadata.get("action") == "closed" and event.metadata.get("merged"):
                    merged_pr_count += 1
        
        # Apply merged PR boosts
        if merged_pr_count > 0:
            new_happiness += self.PR_MERGED_HAPPINESS_BOOST * merged_pr_count
            new_xp += self.PR_MERGED_XP_BOOST * merged_pr_count
        
        # Clamp stats to valid range [0, 100]
        # Note: XP is not clamped as it can grow indefinitely
        return pet.model_copy(update={
            'hunger': self.clamp_stat(new_hunger),
            'happiness': self.clamp_stat(new_happiness),
            'xp': new_xp
        })
    
    def apply_inactivity_penalties(self, pet: PetState, days_inactive: int) -> PetState:
        """
        Apply penalties for extended inactivity.
        
        If the user has been inactive for more than INACTIVE_DAYS_THRESHOLD (3 days),
        penalties are applied:
        - Happiness decreases by INACTIVE_HAPPINESS_PENALTY (15 points)
        - Energy decreases by INACTIVE_ENERGY_PENALTY (10 points)
        
        All stats are clamped to [0, 100] after penalties.
        
        Args:
            pet: Current pet state
            days_inactive: Number of days since last GitHub activity
            
        Returns:
            Updated pet state with inactivity penalties applied
        """
        # Only apply penalties if inactive for more than threshold
        if days_inactive <= self.INACTIVE_DAYS_THRESHOLD:
            return pet
        
        # Calculate new stat values after penalties
        new_happiness = pet.happiness - self.INACTIVE_HAPPINESS_PENALTY
        new_energy = pet.energy - self.INACTIVE_ENERGY_PENALTY
        
        # Clamp stats to valid range [0, 100]
        return pet.model_copy(update={
            'happiness': self.clamp_stat(new_happiness),
            'energy': self.clamp_stat(new_energy)
        })
    
    def calculate_level_and_stage(self, pet: PetState) -> PetState:
        """
        Calculate level from XP and determine evolution stage.
        
        Level is calculated as XP // 100 (100 XP per level).
        
        Evolution stages are mapped based on level:
        - Level 0-2: egg
        - Level 3-6: baby
        - Level 7-12: teen
        - Level 13-20: adult
        - Level 21+: legendary
        
        Args:
            pet: Current pet state
            
        Returns:
            Updated pet state with level and stage fields updated
        """
        # Calculate level from XP (100 XP per level)
        new_level = pet.xp // 100
        
        # Determine evolution stage based on level
        if new_level <= 2:
            new_stage = "egg"
        elif new_level <= 6:
            new_stage = "baby"
        elif new_level <= 12:
            new_stage = "teen"
        elif new_level <= 20:
            new_stage = "adult"
        else:  # level 21+
            new_stage = "legendary"
        
        # Update pet's level and stage
        return pet.model_copy(update={
            'level': new_level,
            'stage': new_stage
        })
