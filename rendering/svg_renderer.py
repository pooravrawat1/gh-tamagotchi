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

    # System monospace stack keeps the SVG self-contained for README embedding.
    FONT_FAMILY = '"Courier New", Courier, monospace'

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
        
        # Get pet sprite and mood message
        pet_sprite = self.get_pet_sprite(pet.stage)
        mood_message = self.get_mood_message(pet)
        
        # Build SVG
        svg = f'''<svg width="{self.WIDTH}" height="{self.HEIGHT}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="{self.WIDTH}" height="{self.HEIGHT}" fill="{self.COLOR_BACKGROUND}"/>
  
  <!-- Pet Sprite -->
  <g id="pet-sprite" transform="translate(200, 120)">
    {pet_sprite}
  </g>
  
  <!-- Username -->
  <text x="200" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="{self.COLOR_TEXT_PRIMARY}" font-family='{self.FONT_FAMILY}'>
    {self._escape_xml(pet.username)}'s Pet
  </text>
  
  <!-- Stage and Level Label -->
  <text x="200" y="55" text-anchor="middle" font-size="14" fill="{self.COLOR_TEXT_SECONDARY}" font-family='{self.FONT_FAMILY}'>
    Stage: {pet.stage.value if hasattr(pet.stage, 'value') else pet.stage} | Level {pet.level}
  </text>
  
  <!-- Mood Text (below sprite, above bars) -->
  <text x="200" y="205" text-anchor="middle" font-size="12" fill="{self.COLOR_TEXT_TERTIARY}" font-family='{self.FONT_FAMILY}'>
    {self._escape_xml(mood_message)}
  </text>
  
  <!-- Stat Bars -->
  <g id="stats" transform="translate(50, 220)">
    <!-- Hunger Bar -->
    <text x="0" y="0" font-size="12" fill="{self.COLOR_TEXT_PRIMARY}" font-family='{self.FONT_FAMILY}'>Hunger:</text>
    <rect x="{self.STAT_BAR_X}" y="-10" width="{self.STAT_BAR_WIDTH}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_BAR_BG}" rx="5"/>
    <rect x="{self.STAT_BAR_X}" y="-10" width="{hunger_width}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_HUNGER}" rx="5"/>
    <text x="{self.STAT_BAR_X + self.STAT_BAR_WIDTH + 10}" y="0" font-size="11" fill="{self.COLOR_TEXT_SECONDARY}" font-family='{self.FONT_FAMILY}'>{pet.hunger}</text>
    
    <!-- Happiness Bar -->
    <text x="0" y="{self.STAT_BAR_SPACING}" font-size="12" fill="{self.COLOR_TEXT_PRIMARY}" font-family='{self.FONT_FAMILY}'>Happy:</text>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING - 10}" width="{self.STAT_BAR_WIDTH}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_BAR_BG}" rx="5"/>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING - 10}" width="{happiness_width}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_HAPPINESS}" rx="5"/>
    <text x="{self.STAT_BAR_X + self.STAT_BAR_WIDTH + 10}" y="{self.STAT_BAR_SPACING}" font-size="11" fill="{self.COLOR_TEXT_SECONDARY}" font-family='{self.FONT_FAMILY}'>{pet.happiness}</text>
    
    <!-- Health Bar -->
    <text x="0" y="{self.STAT_BAR_SPACING * 2}" font-size="12" fill="{self.COLOR_TEXT_PRIMARY}" font-family='{self.FONT_FAMILY}'>Health:</text>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING * 2 - 10}" width="{self.STAT_BAR_WIDTH}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_BAR_BG}" rx="5"/>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING * 2 - 10}" width="{health_width}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_HEALTH}" rx="5"/>
    <text x="{self.STAT_BAR_X + self.STAT_BAR_WIDTH + 10}" y="{self.STAT_BAR_SPACING * 2}" font-size="11" fill="{self.COLOR_TEXT_SECONDARY}" font-family='{self.FONT_FAMILY}'>{pet.health}</text>
    
    <!-- Energy Bar -->
    <text x="0" y="{self.STAT_BAR_SPACING * 3}" font-size="12" fill="{self.COLOR_TEXT_PRIMARY}" font-family='{self.FONT_FAMILY}'>Energy:</text>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING * 3 - 10}" width="{self.STAT_BAR_WIDTH}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_BAR_BG}" rx="5"/>
    <rect x="{self.STAT_BAR_X}" y="{self.STAT_BAR_SPACING * 3 - 10}" width="{energy_width}" height="{self.STAT_BAR_HEIGHT}" fill="{self.COLOR_ENERGY}" rx="5"/>
    <text x="{self.STAT_BAR_X + self.STAT_BAR_WIDTH + 10}" y="{self.STAT_BAR_SPACING * 3}" font-size="11" fill="{self.COLOR_TEXT_SECONDARY}" font-family='{self.FONT_FAMILY}'>{pet.energy}</text>
  </g>
</svg>'''
        
        return svg
    
    def get_pet_sprite(self, stage: str) -> str:
        """
        Generate pet sprite based on evolution stage.
        
        Creates simple geometric sprites for each stage:
        - egg: oval shape
        - baby: circle with eyes
        - teen: circle with eyes and mouth
        - adult: detailed shape with features
        - legendary: shape with special effects
        
        Args:
            stage: The evolution stage of the pet (egg, baby, teen, adult, legendary)
            
        Returns:
            SVG markup for the pet sprite
        """
        # Normalize stage string (handle both string and enum values)
        stage_str = stage.value if hasattr(stage, 'value') else str(stage).lower()
        
        if stage_str == 'egg':
            # Oval shape for egg
            return '''
    <ellipse cx="0" cy="0" rx="35" ry="50" fill="#e8e8e8" stroke="#999" stroke-width="2"/>
    <ellipse cx="0" cy="0" rx="30" ry="45" fill="#f5f5f5" opacity="0.6"/>
    <ellipse cx="-10" cy="-15" rx="8" ry="12" fill="#fff" opacity="0.8"/>
'''
        
        elif stage_str == 'baby':
            # Circle with eyes
            return '''
    <circle cx="0" cy="0" r="45" fill="#ffd1dc" stroke="#ff69b4" stroke-width="2"/>
    <circle cx="0" cy="0" r="40" fill="#ffe4e9" opacity="0.7"/>
    <!-- Eyes -->
    <circle cx="-15" cy="-5" r="6" fill="#333"/>
    <circle cx="15" cy="-5" r="6" fill="#333"/>
    <circle cx="-13" cy="-7" r="2" fill="#fff"/>
    <circle cx="17" cy="-7" r="2" fill="#fff"/>
    <!-- Blush -->
    <circle cx="-25" cy="8" r="5" fill="#ffb6c1" opacity="0.6"/>
    <circle cx="25" cy="8" r="5" fill="#ffb6c1" opacity="0.6"/>
'''
        
        elif stage_str == 'teen':
            # Circle with eyes and mouth
            return '''
    <circle cx="0" cy="0" r="48" fill="#87ceeb" stroke="#4682b4" stroke-width="2"/>
    <circle cx="0" cy="0" r="43" fill="#b0e0e6" opacity="0.7"/>
    <!-- Eyes -->
    <ellipse cx="-15" cy="-8" rx="7" ry="9" fill="#333"/>
    <ellipse cx="15" cy="-8" rx="7" ry="9" fill="#333"/>
    <circle cx="-13" cy="-10" r="3" fill="#fff"/>
    <circle cx="17" cy="-10" r="3" fill="#fff"/>
    <!-- Mouth -->
    <path d="M -15 10 Q 0 20 15 10" stroke="#333" stroke-width="2" fill="none" stroke-linecap="round"/>
    <!-- Cheeks -->
    <circle cx="-28" cy="5" r="6" fill="#ff9999" opacity="0.5"/>
    <circle cx="28" cy="5" r="6" fill="#ff9999" opacity="0.5"/>
'''
        
        elif stage_str == 'adult':
            # Detailed shape with features
            return '''
    <!-- Body -->
    <ellipse cx="0" cy="5" rx="50" ry="55" fill="#9370db" stroke="#6a5acd" stroke-width="2"/>
    <ellipse cx="0" cy="5" rx="45" ry="50" fill="#b19cd9" opacity="0.6"/>
    <!-- Head -->
    <circle cx="0" cy="-20" r="35" fill="#9370db" stroke="#6a5acd" stroke-width="2"/>
    <circle cx="0" cy="-20" r="30" fill="#b19cd9" opacity="0.6"/>
    <!-- Eyes -->
    <ellipse cx="-12" cy="-25" rx="8" ry="10" fill="#fff" stroke="#333" stroke-width="1"/>
    <ellipse cx="12" cy="-25" rx="8" ry="10" fill="#fff" stroke="#333" stroke-width="1"/>
    <circle cx="-12" cy="-23" r="5" fill="#333"/>
    <circle cx="12" cy="-23" r="5" fill="#333"/>
    <circle cx="-10" cy="-25" r="2" fill="#fff"/>
    <circle cx="14" cy="-25" r="2" fill="#fff"/>
    <!-- Mouth -->
    <path d="M -12 -10 Q 0 -5 12 -10" stroke="#333" stroke-width="2" fill="none" stroke-linecap="round"/>
    <!-- Arms -->
    <ellipse cx="-45" cy="10" rx="12" ry="25" fill="#9370db" stroke="#6a5acd" stroke-width="2"/>
    <ellipse cx="45" cy="10" rx="12" ry="25" fill="#9370db" stroke="#6a5acd" stroke-width="2"/>
'''
        
        elif stage_str == 'legendary':
            # Shape with special effects (glow, stars)
            return '''
    <!-- Glow effect -->
    <circle cx="0" cy="0" r="70" fill="#ffd700" opacity="0.2"/>
    <circle cx="0" cy="0" r="60" fill="#ffd700" opacity="0.3"/>
    <!-- Body -->
    <ellipse cx="0" cy="5" rx="50" ry="55" fill="#ff6347" stroke="#ff4500" stroke-width="2"/>
    <ellipse cx="0" cy="5" rx="45" ry="50" fill="#ff7f50" opacity="0.7"/>
    <!-- Head -->
    <circle cx="0" cy="-20" r="35" fill="#ff6347" stroke="#ff4500" stroke-width="2"/>
    <circle cx="0" cy="-20" r="30" fill="#ff7f50" opacity="0.7"/>
    <!-- Eyes with sparkle -->
    <ellipse cx="-12" cy="-25" rx="8" ry="10" fill="#fff" stroke="#333" stroke-width="1"/>
    <ellipse cx="12" cy="-25" rx="8" ry="10" fill="#fff" stroke="#333" stroke-width="1"/>
    <circle cx="-12" cy="-23" r="5" fill="#ffd700"/>
    <circle cx="12" cy="-23" r="5" fill="#ffd700"/>
    <circle cx="-10" cy="-25" r="2" fill="#fff"/>
    <circle cx="14" cy="-25" r="2" fill="#fff"/>
    <!-- Smile -->
    <path d="M -15 -8 Q 0 -2 15 -8" stroke="#333" stroke-width="2" fill="none" stroke-linecap="round"/>
    <!-- Crown -->
    <path d="M -20 -50 L -15 -40 L -10 -48 L 0 -38 L 10 -48 L 15 -40 L 20 -50 L 20 -52 L -20 -52 Z" fill="#ffd700" stroke="#ffaa00" stroke-width="1"/>
    <!-- Stars -->
    <path d="M -55 -30 L -52 -25 L -47 -25 L -51 -21 L -49 -16 L -55 -20 L -61 -16 L -59 -21 L -63 -25 L -58 -25 Z" fill="#ffd700" opacity="0.8"/>
    <path d="M 55 -10 L 58 -5 L 63 -5 L 59 -1 L 61 4 L 55 0 L 49 4 L 51 -1 L 47 -5 L 52 -5 Z" fill="#ffd700" opacity="0.8"/>
    <path d="M 0 -65 L 2 -61 L 6 -61 L 3 -58 L 4 -54 L 0 -57 L -4 -54 L -3 -58 L -6 -61 L -2 -61 Z" fill="#ffd700" opacity="0.9"/>
    <!-- Arms -->
    <ellipse cx="-45" cy="10" rx="12" ry="25" fill="#ff6347" stroke="#ff4500" stroke-width="2"/>
    <ellipse cx="45" cy="10" rx="12" ry="25" fill="#ff6347" stroke="#ff4500" stroke-width="2"/>
'''
        
        else:
            # Default fallback (egg)
            return '''
    <ellipse cx="0" cy="0" rx="35" ry="50" fill="#e8e8e8" stroke="#999" stroke-width="2"/>
    <ellipse cx="0" cy="0" rx="30" ry="45" fill="#f5f5f5" opacity="0.6"/>
'''
    
    def get_mood_message(self, pet: PetState) -> str:
        """
        Generate mood message based on pet stats.
        
        Analyzes pet stats to determine the most relevant mood message.
        Priority is given to critical stats (low values) over positive stats.
        
        Args:
            pet: The pet state
            
        Returns:
            Mood message string based on stat thresholds
        """
        # Check for critical conditions first (low stats)
        if pet.hunger < 30:
            return "Getting hungry!"
        if pet.energy < 30:
            return "Feeling tired..."
        if pet.health < 30:
            return "Not feeling well..."
        if pet.happiness < 30:
            return "Needs attention..."
        
        # Check for positive conditions (high stats)
        if pet.happiness > 70:
            return "Feeling great!"
        if pet.energy > 70 and pet.health > 70:
            return "Full of energy!"
        if pet.hunger > 70:
            return "Well fed and happy!"
        
        # Default neutral message
        return "Doing okay"
    
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
