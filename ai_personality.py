"""
AI Personality System for Bathala-like Card Combat Game
Defines distinct AI behaviors for different creature types based on Filipino mythology
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any


class AIPersonalityType(Enum):
    CAUTIOUS = "cautious"        # Defensive, prefers safe plays
    AGGRESSIVE = "aggressive"     # High risk/reward, goes for big damage
    CALCULATING = "calculating"   # Mathematical optimal plays
    ELEMENTAL = "elemental"      # Focuses on elemental synergies
    CHAOTIC = "chaotic"          # Unpredictable, high variance
    ADAPTIVE = "adaptive"        # Learns from player behavior


class Element(Enum):
    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"
    AIR = "air"
    NEUTRAL = "neutral"


@dataclass
class AIPersonalityConfig:
    """Configuration for AI personality behavior"""
    name: str
    description: str
    
    # Risk tolerance (0-1)
    risk_tolerance: float
    
    # How much AI values different aspects (0-1)
    damage_weight: float
    block_weight: float
    hand_type_weight: float
    elemental_weight: float
    
    # Decision modifiers
    min_hand_threshold: int  # Won't play hands below this value
    preferred_elements: List[Element]
    
    # Bluffing and unpredictability
    bluff_chance: float
    randomness_weight: float
    
    # Learning parameters
    adaptation_rate: float
    memory_length: int


# AI Personality Configurations
AI_PERSONALITIES: Dict[AIPersonalityType, AIPersonalityConfig] = {
    AIPersonalityType.CAUTIOUS: AIPersonalityConfig(
        name="Cautious",
        description="Defensive creature that prioritizes survival over big damage",
        risk_tolerance=0.2,
        damage_weight=0.4,
        block_weight=0.8,
        hand_type_weight=0.7,
        elemental_weight=0.5,
        min_hand_threshold=15,
        preferred_elements=[Element.EARTH, Element.WATER],
        bluff_chance=0.1,
        randomness_weight=0.1,
        adaptation_rate=0.2,
        memory_length=10,
    ),
    
    AIPersonalityType.AGGRESSIVE: AIPersonalityConfig(
        name="Aggressive",
        description="High-damage creature that takes big risks for big rewards",
        risk_tolerance=0.9,
        damage_weight=1.0,
        block_weight=0.2,
        hand_type_weight=0.9,
        elemental_weight=0.7,
        min_hand_threshold=8,
        preferred_elements=[Element.FIRE, Element.AIR],
        bluff_chance=0.4,
        randomness_weight=0.3,
        adaptation_rate=0.3,
        memory_length=8,
    ),
    
    AIPersonalityType.CALCULATING: AIPersonalityConfig(
        name="Calculating",
        description="Mathematical creature that makes optimal decisions",
        risk_tolerance=0.5,
        damage_weight=0.7,
        block_weight=0.6,
        hand_type_weight=0.8,
        elemental_weight=0.6,
        min_hand_threshold=12,
        preferred_elements=[Element.NEUTRAL],
        bluff_chance=0.15,
        randomness_weight=0.05,
        adaptation_rate=0.1,
        memory_length=15,
    ),
    
    AIPersonalityType.ELEMENTAL: AIPersonalityConfig(
        name="Elemental",
        description="Element-focused creature that prioritizes synergies",
        risk_tolerance=0.6,
        damage_weight=0.6,
        block_weight=0.4,
        hand_type_weight=0.5,
        elemental_weight=1.0,
        min_hand_threshold=10,
        preferred_elements=[Element.FIRE, Element.WATER, Element.EARTH, Element.AIR],
        bluff_chance=0.2,
        randomness_weight=0.2,
        adaptation_rate=0.25,
        memory_length=12,
    ),
    
    AIPersonalityType.CHAOTIC: AIPersonalityConfig(
        name="Chaotic",
        description="Unpredictable creature with wild and varied strategies",
        risk_tolerance=0.8,
        damage_weight=0.7,
        block_weight=0.3,
        hand_type_weight=0.6,
        elemental_weight=0.8,
        min_hand_threshold=5,
        preferred_elements=[Element.FIRE, Element.AIR],
        bluff_chance=0.5,
        randomness_weight=0.6,
        adaptation_rate=0.4,
        memory_length=5,
    ),
    
    AIPersonalityType.ADAPTIVE: AIPersonalityConfig(
        name="Adaptive",
        description="Intelligent creature that learns and counters player behavior",
        risk_tolerance=0.5,
        damage_weight=0.6,
        block_weight=0.5,
        hand_type_weight=0.7,
        elemental_weight=0.6,
        min_hand_threshold=10,
        preferred_elements=[Element.NEUTRAL],
        bluff_chance=0.25,
        randomness_weight=0.15,
        adaptation_rate=0.5,
        memory_length=20,
    ),
}


# Maps creature types to their AI personalities
CREATURE_PERSONALITIES: Dict[str, AIPersonalityType] = {
    # Common enemies - simpler AI
    "Tikbalang": AIPersonalityType.CHAOTIC,
    "Dwende": AIPersonalityType.CAUTIOUS,
    "Kapre": AIPersonalityType.ELEMENTAL,
    "Sigbin": AIPersonalityType.AGGRESSIVE,
    "Tiyanak": AIPersonalityType.CAUTIOUS,
    
    # Elite enemies - more sophisticated AI
    "Manananggal": AIPersonalityType.ADAPTIVE,
    "Aswang": AIPersonalityType.AGGRESSIVE,
    "Duwende Chief": AIPersonalityType.CALCULATING,
    
    # Boss enemies - most advanced AI
    "Bakunawa": AIPersonalityType.ADAPTIVE,
    
    # Generic enemies
    "Forest Goblin": AIPersonalityType.CAUTIOUS,
    "Fire Elemental": AIPersonalityType.ELEMENTAL,
    "Shadow Beast": AIPersonalityType.AGGRESSIVE,
    "Ancient Dragon": AIPersonalityType.ADAPTIVE,
}


def get_personality_for_creature(creature_name: str) -> AIPersonalityConfig:
    """Get AI personality configuration for a specific creature"""
    personality_type = CREATURE_PERSONALITIES.get(creature_name, AIPersonalityType.CALCULATING)
    return AI_PERSONALITIES[personality_type]


def get_all_personality_types() -> List[AIPersonalityType]:
    """Get list of all available personality types"""
    return list(AIPersonalityType)


def get_personality_by_type(personality_type: AIPersonalityType) -> AIPersonalityConfig:
    """Get personality configuration by type"""
    return AI_PERSONALITIES[personality_type]


def create_custom_personality(
    name: str,
    description: str,
    risk_tolerance: float = 0.5,
    damage_weight: float = 0.6,
    block_weight: float = 0.4,
    **kwargs
) -> AIPersonalityConfig:
    """Create a custom AI personality configuration"""
    
    defaults = {
        "hand_type_weight": 0.7,
        "elemental_weight": 0.5,
        "min_hand_threshold": 10,
        "preferred_elements": [Element.NEUTRAL],
        "bluff_chance": 0.2,
        "randomness_weight": 0.2,
        "adaptation_rate": 0.3,
        "memory_length": 12,
    }
    
    # Override defaults with provided kwargs
    config_args = {
        "name": name,
        "description": description,
        "risk_tolerance": risk_tolerance,
        "damage_weight": damage_weight,
        "block_weight": block_weight,
        **defaults,
        **kwargs
    }
    
    return AIPersonalityConfig(**config_args)


class PersonalityAnalyzer:
    """Utility class for analyzing and comparing AI personalities"""
    
    @staticmethod
    def get_personality_strength(personality: AIPersonalityConfig) -> Dict[str, float]:
        """Analyze personality strengths and weaknesses"""
        return {
            "offense": (personality.damage_weight + personality.hand_type_weight) / 2,
            "defense": personality.block_weight,
            "strategy": (personality.elemental_weight + (1 - personality.randomness_weight)) / 2,
            "adaptability": personality.adaptation_rate,
            "unpredictability": personality.randomness_weight,
            "aggression": personality.risk_tolerance,
        }
    
    @staticmethod
    def recommend_counter_strategy(enemy_personality: AIPersonalityConfig) -> str:
        """Recommend strategy to counter specific AI personality"""
        strengths = PersonalityAnalyzer.get_personality_strength(enemy_personality)
        
        if strengths["aggression"] > 0.7:
            return "Play defensively, let aggressive AI overextend and punish mistakes"
        elif strengths["defense"] > 0.7:
            return "Build up powerful hands, overwhelming defensive play with burst damage"
        elif strengths["unpredictability"] > 0.5:
            return "Stay flexible, adapt to chaotic plays, focus on consistent value"
        elif strengths["adaptability"] > 0.4:
            return "Vary your strategy, avoid predictable patterns, use mixed tactics"
        else:
            return "Balanced approach, focus on optimal play and hand evaluation"
    
    @staticmethod
    def personality_matchup(p1: AIPersonalityConfig, p2: AIPersonalityConfig) -> str:
        """Analyze how two personalities would fare against each other"""
        s1 = PersonalityAnalyzer.get_personality_strength(p1)
        s2 = PersonalityAnalyzer.get_personality_strength(p2)
        
        if s1["aggression"] > s2["defense"] + 0.3:
            return f"{p1.name} likely wins through aggressive pressure"
        elif s2["defense"] > s1["offense"] + 0.3:
            return f"{p2.name} likely wins through defensive play"
        elif abs(s1["adaptability"] - s2["adaptability"]) > 0.3:
            higher_adapt = p1 if s1["adaptability"] > s2["adaptability"] else p2
            return f"{higher_adapt.name} likely wins through adaptation"
        else:
            return "Close matchup, outcome depends on card draws and execution"


if __name__ == "__main__":
    # Test the personality system
    print("🎭 AI Personality System Test 🎭\n")
    
    # Test creature personality mapping
    test_creatures = ["Tikbalang", "Bakunawa", "Kapre", "Unknown Creature"]
    
    for creature in test_creatures:
        personality = get_personality_for_creature(creature)
        print(f"🐲 {creature}: {personality.name}")
        print(f"   {personality.description}")
        print(f"   Risk Tolerance: {personality.risk_tolerance:.1f}")
        print(f"   Preferred Elements: {[e.value for e in personality.preferred_elements]}")
        print()
    
    # Test personality analysis
    print("📊 Personality Analysis:")
    tikbalang_personality = get_personality_for_creature("Tikbalang")
    bakunawa_personality = get_personality_for_creature("Bakunawa")
    
    print(f"\n{tikbalang_personality.name} vs {bakunawa_personality.name}:")
    matchup = PersonalityAnalyzer.personality_matchup(tikbalang_personality, bakunawa_personality)
    print(f"Prediction: {matchup}")
    
    counter_strategy = PersonalityAnalyzer.recommend_counter_strategy(bakunawa_personality)
    print(f"Counter Strategy vs {bakunawa_personality.name}: {counter_strategy}")
    
    # Test custom personality creation
    print(f"\n🛠️ Custom Personality Test:")
    custom = create_custom_personality(
        "Berserker",
        "Goes all-out with maximum aggression",
        risk_tolerance=1.0,
        damage_weight=1.0,
        block_weight=0.1,
        randomness_weight=0.8
    )
    print(f"Custom: {custom.name} - {custom.description}")
    print(f"Risk: {custom.risk_tolerance}, Damage: {custom.damage_weight}, Chaos: {custom.randomness_weight}")