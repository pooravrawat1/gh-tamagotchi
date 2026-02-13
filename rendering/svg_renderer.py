"""
SVG rendering engine for pet widgets.

This module generates dynamic SVG images representing pet state,
including pet sprites, stat bars, and mood messages.
"""

from models.pet_models import PetState


class SVGRenderer:
    """
    Renders pet state as SVG images.
    
    The renderer generates lightweight, self-contained SVG images
    suitable for embedding in GitHub READMEs and web pages.
    """
    
    # SVG dimensions
    WIDTH = 400
    HEIGHT = 300
    
    # Stat bar configuration
    STAT_BAR_WIDTH = 200
    STAT_BAR_HEIGHT = 15
    STAT_BAR_X = 70
    STAT_BAR_SPACING = 25
    
    # Colors
    COLOR_BACKGROUND = "#f0f0f0"
    COLOR_HUNGER = "#ff6b6b"
    COLOR_HAPPINESS = "#ffd93d"
    COLOR_HEALTH = "#6bcf7f"
    COLOR_ENERGY = "#4d96ff"
    COLOR_BAR_BG = "#ddd"
    COLOR_TEXT_PRIMARY = "#333"
    COLOR_TEXT_SECONDARY = "#666"
    COLOR_TEXT_TERTIARY = "#888"
    
    def render_pet(self, pet: PetState) -> str:
        """
        Generate SVG string from pet state.
        
        Args:
            pet: The pet state to render
            
        Returns:
            Complete SVG markup as a string
            
        The SVG includes:
        - Background
        - Pet sprite (stage-dependent)
        - Username and stage/level labels
        - Four stat bars (hunger, happiness, health, energy)
        - Mood message
        """
        # Calculate stat bar widths (0-100 maps to 0-STAT_BAR_WIDTH)
        hunger_width = (pet.hunger / 100) * self.STAT_BAR_WIDTH
        happiness_width = (pet.happiness / 100) * self.STAT_BAR_WIDTH
        health_width = (pet.health / 100) * self.STAT_BAR_WIDTH
        energy_width = (pet.energy / 100) * self.STAT_BAR_WIDTH
        
        # Get pet sprite and mood message (to be implemented in subtasks)
        pet_sprite = self._get_pet_sprite_placeholder(pet.stage)
        mood_message = self._get_mood_message_placeholder(pet)
        
        # Build SVG
        svg = f'''<svg width="{self.WIDTH}" height="{self.HEIGHT}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="{self.WIDTH}" height="{self.HEIGHT}" fill="{self.COLOR_BACKGROUND}"/>
  
  <!-- Pet Sprite -->
  <g id="pet-sprite" transform="translate(200, 120)">
    {pet_sprite}
  </g>
  
  <!-- Username -->
  <text x="200" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="{self.COLOR_TEXT_PRIMARY}" font-family="Arial, sans-serif">
    {self._escape_xml(pet.username)}'s Pet
  </text>
  
  <!-- Stage and Level Label -->
  <text x="200" y="55" text-anchor="middle" font-size="14" fill="{self.COLOR_TEXT_SECONDARY}" font-family="Arial, sans-serif">
    Stage: {pet.stage.value if hasattr(pet.stage, 'value') else pet.stage} | Level {pet.level}
  </text>
  
  <!-- Stat Bars -->
  <g id="stats" transform="translate(50, 220)">
    <!-- Hunger Bar -->
    <text x="0" y="0" font-size="12" fill="{self.COLOR_TEXT_PRIMARY}" font-family="Arial, sans-serif">Hunger:</text>
    <rect x="{self.STAT_BAR_X}" y="-10" width="{self.STAT_BAR_WIDTH}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_BAR_BG}" rx="5"/>
    <rect x="{self.STAT_BAR_X}" y="-10" width="{hunger_width}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_HUNGER}" rx="5"/>
    <text x="{self.STAT_BAR_X + self.STAT_BAR_WIDTH + 10}" y="0" font-size="11" fill="{self.COLOR_TEXT_SECONDARY}" font-family="Arial, sans-serif">{pet.hunger}</text>
    
    <!-- Happiness Bar -->
    <text x="0" y="{self.STAT_BAR_SPACING}" font-size="12" fill="{self.COLOR_TEXT_PRIMARY}" font-family="Arial, sans-serif">Happy:</text>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING - 10}" width="{self.STAT_BAR_WIDTH}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_BAR_BG}" rx="5"/>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING - 10}" width="{happiness_width}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_HAPPINESS}" rx="5"/>
    <text x="{self.STAT_BAR_X + self.STAT_BAR_WIDTH + 10}" y="{self.STAT_BAR_SPACING}" font-size="11" fill="{self.COLOR_TEXT_SECONDARY}" font-family="Arial, sans-serif">{pet.happiness}</text>
    
    <!-- Health Bar -->
    <text x="0" y="{self.STAT_BAR_SPACING * 2}" font-size="12" fill="{self.COLOR_TEXT_PRIMARY}" font-family="Arial, sans-serif">Health:</text>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING * 2 - 10}" width="{self.STAT_BAR_WIDTH}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_BAR_BG}" rx="5"/>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING * 2 - 10}" width="{health_width}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_HEALTH}" rx="5"/>
    <text x="{self.STAT_BAR_X + self.STAT_BAR_WIDTH + 10}" y="{self.STAT_BAR_SPACING * 2}" font-size="11" fill="{self.COLOR_TEXT_SECONDARY}" font-family="Arial, sans-serif">{pet.health}</text>
    
    <!-- Energy Bar -->
    <text x="0" y="{self.STAT_BAR_SPACING * 3}" font-size="12" fill="{self.COLOR_TEXT_PRIMARY}" font-family="Arial, sans-serif">Energy:</text>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING * 3 - 10}" width="{self.STAT_BAR_WIDTH}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_BAR_BG}" rx="5"/>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING * 3 - 10}" width="{energy_width}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_ENERGY}" rx="5"/>
    <text x="{self.STAT_BAR_X + self.STAT_BAR_WIDTH + 10}" y="{self.STAT_BAR_SPACING * 3}" font-size="11" fill="{self.COLOR_TEXT_SECONDARY}" font-family="Arial, sans-serif">{pet.energy}</text>
  </g>
  
  <!-- Mood Text -->
  <text x="200" y="285" text-anchor="middle" font-size="12" fill="{self.COLOR_TEXT_TERTIARY}" font-family="Arial, sans-serif">
    {self._escape_xml(mood_message)}
  </text>
</svg>'''
        
        return svg
    
    def _get_pet_sprite_placeholder(self, stage: str) -> str:
        """
        Placeholder for pet sprite generation.
        
        This will be implemented in task 8.2.
        For now, returns a simple circle as a placeholder.
        
        Args:
            stage: The evolution stage of the pet
            
        Returns:
            SVG markup for the pet sprite
        """
        # Simple placeholder circle
        return '<circle cx="0" cy="0" r="40" fill="#999" opacity="0.3"/>'
    
    def _get_mood_message_placeholder(self, pet: PetState) -> str:
        """
        Placeholder for mood message generation.
        
        This will be implemented in task 8.4.
        For now, returns a generic message.
        
        Args:
            pet: The pet state
            
        Returns:
            Mood message string
        """
        return "Your virtual pet"
    
    def _escape_xml(self, text: str) -> str:
        """
        Escape special XML characters in text.
        
        Args:
            text: Text to escape
            
        Returns:
            XML-safe text
        """
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))
