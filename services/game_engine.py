"""
Game engine for GitHub Tamagotchi pet stats and evolution logic.
"""
from datetime import datetime, timezone
from typing import List, Optional
from models.pet_models import PetState
from models.github_models import ContributionData, ActivityEvent


class GameEngine:
    """
    Game engine responsible for calculating pet stat updates, decay, and evolution.
    """
    
    def __init__(
        self,
        hunger_decay_rate: float = 2.0,
        happiness_decay_rate: float = 3.0,
        energy_decay_rate: float = 1.5,
        health_decay_rate: float = 0.5,
        commit_hunger_boost: int = 10,
        commit_happiness_boost: int = 5,
        pr_merged_happiness_boost: int = 10,
        pr_merged_xp_boost: int = 20,
        inactive_days_threshold: int = 3,
        inactive_happiness_penalty: int = 15,
        inactive_energy_penalty: int = 10
    ):
        """
        Initialize the game engine with configurable parameters.
        
        Args:
            hunger_decay_rate: Hunger decay rate per hour
            happiness_decay_rate: Happiness decay rate per hour
            energy_decay_rate: Energy decay rate per hour
            health_decay_rate: Health decay rate per hour
            commit_hunger_boost: Hunger boost for commits today
            commit_happiness_boost: Happiness boost for commits today
            pr_merged_happiness_boost: Happiness boost for merged PRs
            pr_merged_xp_boost: XP boost for merged PRs
            inactive_days_threshold: Days of inactivity before penalties apply
            inactive_happiness_penalty: Happiness penalty for inactivity
            inactive_energy_penalty: Energy penalty for inactivity
        """
        # Stat decay rates (per hour)
        self.HUNGER_DECAY_RATE = hunger_decay_rate
        self.HAPPINESS_DECAY_RATE = happiness_decay_rate
        self.ENERGY_DECAY_RATE = energy_decay_rate
        self.HEALTH_DECAY_RATE = health_decay_rate
        
        # Activity boost values
        self.COMMIT_HUNGER_BOOST = commit_hunger_boost
        self.COMMIT_HAPPINESS_BOOST = commit_happiness_boost
        self.PR_MERGED_HAPPINESS_BOOST = pr_merged_happiness_boost
        self.PR_MERGED_XP_BOOST = pr_merged_xp_boost
        
        # Inactivity penalties
        self.INACTIVE_DAYS_THRESHOLD = inactive_days_threshold
        self.INACTIVE_HAPPINESS_PENALTY = inactive_happiness_penalty
        self.INACTIVE_ENERGY_PENALTY = inactive_energy_penalty
    
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

    @staticmethod
    def _as_naive_utc(value: datetime) -> datetime:
        """Normalize aware datetimes from GitHub to naive UTC for comparison."""
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    
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
        recent_activity: List[ActivityEvent],
        current_time: Optional[datetime] = None,
        reward_since: Optional[datetime] = None
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
        
        # Check for GitHub-counted commit contributions today. This avoids
        # depending on the shallow REST events feed for commit rewards.
        today = (current_time or datetime.utcnow()).date()
        reward_since = (
            self._as_naive_utc(reward_since)
            if reward_since is not None
            else None
        )
        commits_today = 0

        for day in contribution_data.commit_days:
            if day.date == today:
                commits_today = day.count
                break

        # Apply commit boosts if there are commits today
        last_commit_reward_date = pet.last_commit_reward_date
        commit_bonus_already_awarded = (
            last_commit_reward_date is not None
            and last_commit_reward_date >= today
        )
        updated_fields = {}
        if commits_today > 0 and not commit_bonus_already_awarded:
            new_hunger += self.COMMIT_HUNGER_BOOST
            new_happiness += self.COMMIT_HAPPINESS_BOOST
            updated_fields["last_commit_reward_date"] = today
        
        # Check for merged PRs in recent activity
        merged_pr_count = 0
        
        for event in recent_activity:
            if event.type == "PullRequestEvent":
                event_time = self._as_naive_utc(event.created_at)
                if reward_since is not None and event_time <= reward_since:
                    continue

                # Check if the PR was merged
                if event.metadata.get("action") == "closed" and event.metadata.get("merged"):
                    merged_pr_count += 1
        
        # Apply merged PR boosts
        if merged_pr_count > 0:
            new_happiness += self.PR_MERGED_HAPPINESS_BOOST * merged_pr_count
            new_xp += self.PR_MERGED_XP_BOOST * merged_pr_count
        
        # Clamp stats to valid range [0, 100]
        # Note: XP is not clamped as it can grow indefinitely
        updated_fields.update({
            'hunger': self.clamp_stat(new_hunger),
            'happiness': self.clamp_stat(new_happiness),
            'xp': new_xp
        })
        return pet.model_copy(update=updated_fields)
    
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
    
    def update_pet(
        self,
        pet: PetState,
        contribution_data: ContributionData,
        recent_activity: List[ActivityEvent],
        current_time: datetime,
        initial_sync: bool = False
    ) -> PetState:
        """
        Main orchestration method that updates pet state based on time and activity.
        
        This method coordinates all pet stat updates by:
        1. Calculating time elapsed since last update
        2. Applying time-based stat decay
        3. Applying activity boosts from GitHub data
        4. Applying inactivity penalties if applicable
        5. Calculating level and evolution stage
        6. Updating the last_updated timestamp
        
        Args:
            pet: Current pet state
            contribution_data: GitHub contribution data
            recent_activity: List of recent GitHub activity events
            current_time: Current timestamp for the update
            
        Returns:
            Updated pet state with all calculations applied
        """
        last_updated = self._as_naive_utc(pet.last_updated)
        current_time = self._as_naive_utc(current_time)

        # Calculate hours elapsed since last update
        time_delta = current_time - last_updated
        hours_elapsed = time_delta.total_seconds() / 3600.0
        
        # Apply time decay based on elapsed time
        pet = self.calculate_time_decay(pet, hours_elapsed)
        
        # Apply activity boosts from GitHub data
        reward_since = None if initial_sync else last_updated
        pet = self.apply_activity_boosts(
            pet,
            contribution_data,
            recent_activity,
            current_time=current_time,
            reward_since=reward_since
        )
        
        # Calculate days since last activity for inactivity penalties
        days_inactive = self._calculate_days_inactive(contribution_data, current_time)
        
        # Apply inactivity penalties if applicable
        pet = self.apply_inactivity_penalties(pet, days_inactive)
        
        # Calculate level and evolution stage based on XP
        pet = self.calculate_level_and_stage(pet)
        
        # Update the last_updated timestamp
        pet = pet.model_copy(update={'last_updated': current_time})
        
        return pet
    
    def _calculate_days_inactive(
        self,
        contribution_data: ContributionData,
        current_time: datetime
    ) -> int:
        """
        Calculate the number of days since the last GitHub activity.
        
        Args:
            contribution_data: GitHub contribution data
            current_time: Current timestamp
            
        Returns:
            Number of days since last activity (0 if active today)
        """
        if not contribution_data.contribution_days:
            # No contribution data available, assume inactive
            return 999  # Large number to trigger penalties
        
        # Find the most recent day with contributions
        today = current_time.date()
        
        # Check if there are contributions today
        for day in contribution_data.contribution_days:
            if day.date == today and day.count > 0:
                return 0
        
        # Find the most recent day with contributions
        most_recent_activity = None
        for day in contribution_data.contribution_days:
            if day.count > 0:
                if most_recent_activity is None or day.date > most_recent_activity:
                    most_recent_activity = day.date
        
        # If no activity found in the contribution data, return large number
        if most_recent_activity is None:
            return 999
        
        # Calculate days between most recent activity and today
        days_inactive = (today - most_recent_activity).days
        
        return days_inactive
