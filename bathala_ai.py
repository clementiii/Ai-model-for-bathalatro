"""
Main AI Controller for Bathala-like Card Combat Game
Coordinates all AI systems and provides intelligent decision-making for creature opponents
"""

import random
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ai_personality import AIPersonalityConfig, get_personality_for_creature, AIPersonalityType
from hand_strategy import GameContext, PlayerAction


class ActionType(Enum):
    ATTACK = "attack"
    DEFEND = "defend"
    STATUS = "status"


@dataclass
class Enemy:
    """Enemy creature data structure"""
    id: str
    name: str
    max_health: int
    current_health: int
    block: int
    damage: int
    attack_pattern: List[str]
    current_pattern_index: int = 0
    status_effects: List[Dict] = None
    
    def __post_init__(self):
        if self.status_effects is None:
            self.status_effects = []


@dataclass
class AIDecision:
    """AI's decision with complete reasoning and analysis"""
    action: ActionType
    confidence: float = 0.5
    reasoning: str = ""
    estimated_damage: int = 0
    estimated_block: int = 0
    risk_level: float = 0.5
    special_effects: List[str] = None
    
    def __post_init__(self):
        if self.special_effects is None:
            self.special_effects = []


@dataclass
class AIStatistics:
    """Comprehensive AI performance statistics"""
    turns_played: int = 0
    total_damage_dealt: int = 0
    hands_played: int = 0
    average_hand_value: float = 0.0
    personality_type: str = ""
    adaptation_level: float = 0.0
    successful_bluffs: int = 0
    failed_bluffs: int = 0
    special_abilities_used: int = 0
    elemental_combos_played: int = 0


class BathalaAI:
    """Main AI controller for creature opponents"""
    
    def __init__(self, enemy: Enemy, difficulty_level: int = 1):
        self.enemy = enemy
        self.difficulty_level = difficulty_level
        self.personality = get_personality_for_creature(enemy.name)
        self.difficulty_modifier = self._calculate_difficulty_modifier(difficulty_level)
        self.statistics = AIStatistics(personality_type=self.personality.name)
        
        # Combat memory and learning
        self.combat_memory: List[Dict] = []
        self.player_patterns: Dict[str, int] = {}
        
        # Action preferences based on personality
        self.action_preferences = self._calculate_action_preferences()
        
    def make_decision(self, game_context: GameContext) -> AIDecision:
        """Main decision-making method called each AI turn"""
        self.statistics.turns_played += 1
        
        # Choose action based on current situation and personality
        action = self._choose_action(game_context)
        
        # Calculate action effects
        damage, block, effects = self._calculate_action_effects(action, game_context)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(action, game_context)
        
        # Calculate confidence based on situation
        confidence = self._calculate_confidence(action, game_context)
        
        # Create decision
        decision = AIDecision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            estimated_damage=damage,
            estimated_block=block,
            risk_level=self._calculate_risk_level(action, game_context),
            special_effects=effects
        )
        
        # Store decision in combat memory
        self._record_decision(decision, game_context)
        
        return decision
    
    def _calculate_action_preferences(self) -> Dict[ActionType, float]:
        """Calculate action preferences based on personality and creature type"""
        # Base preferences
        preferences = {
            ActionType.ATTACK: 0.4,
            ActionType.DEFEND: 0.3,
            ActionType.STATUS: 0.3
        }
        
        # Adjust based on personality
        if self.personality.name == "Aggressive":
            preferences[ActionType.ATTACK] += 0.3
            preferences[ActionType.DEFEND] -= 0.1
        elif self.personality.name == "Cautious":
            preferences[ActionType.DEFEND] += 0.3
            preferences[ActionType.ATTACK] -= 0.1
        elif self.personality.name == "Calculating":
            preferences[ActionType.STATUS] += 0.2
            preferences[ActionType.ATTACK] -= 0.1
        
        # Adjust based on creature type
        creature_adjustments = {
            "Bakunawa": {ActionType.ATTACK: 0.2, ActionType.STATUS: 0.1},  # Boss - more aggressive
            "Aswang": {ActionType.ATTACK: 0.15, ActionType.DEFEND: -0.1},  # Aggressive creature
            "Kapre": {ActionType.DEFEND: 0.15, ActionType.STATUS: 0.1},   # Defensive earth spirit
            "Manananggal": {ActionType.ATTACK: 0.1, ActionType.STATUS: 0.1}, # Flying terror
        }
        
        if self.enemy.name in creature_adjustments:
            for action, adjustment in creature_adjustments[self.enemy.name].items():
                preferences[action] = max(0.1, preferences[action] + adjustment)
        
        # Normalize to ensure they sum to 1.0
        total = sum(preferences.values())
        for action in preferences:
            preferences[action] /= total
        
        return preferences
    
    def _calculate_difficulty_modifier(self, level: int) -> float:
        """Calculate difficulty modifier based on level (1-10+)"""
        # Level 1: 0.7x (easier)
        # Level 5: 1.0x (normal)
        # Level 10: 1.5x (much harder)
        return max(0.6, min(2.0, 0.6 + (level * 0.09)))
    
    def _choose_action(self, context: GameContext) -> ActionType:
        """Choose the best action based on current situation"""
        # Get current attack pattern action
        pattern_action = self.enemy.attack_pattern[self.enemy.current_pattern_index]
        
        # Convert pattern action to ActionType or use situation-based choice
        if pattern_action == "attack":
            base_action = ActionType.ATTACK
        elif pattern_action in ["defend", "smoke", "block"]:
            base_action = ActionType.DEFEND
        else:
            base_action = ActionType.STATUS  # Special abilities become status actions
        
        # Apply personality and situational modifiers
        action_scores = self.action_preferences.copy()
        
        # Situational adjustments
        ai_health_ratio = context.get_ai_health_ratio()
        player_health_ratio = context.get_player_health_ratio()
        
        # Low health - prefer defense or desperate attacks
        if ai_health_ratio < 0.3:
            if self.personality.name == "Aggressive":
                action_scores[ActionType.ATTACK] += 0.2  # Go all out
            else:
                action_scores[ActionType.DEFEND] += 0.3  # Play defensive
        
        # Player low health - go for the kill
        if player_health_ratio < 0.3:
            action_scores[ActionType.ATTACK] += 0.4
            action_scores[ActionType.DEFEND] -= 0.2
        
        # Early game - more status effects
        if context.turn_number <= 3:
            action_scores[ActionType.STATUS] += 0.2
        
        # Choose action with highest score (with some randomness)
        if random.random() < 0.8:  # 80% choose best, 20% random for unpredictability
            return max(action_scores.keys(), key=lambda x: action_scores[x])
        else:
            # Weight random choice by scores
            actions = list(action_scores.keys())
            weights = list(action_scores.values())
            return random.choices(actions, weights=weights)[0]
    
    def _calculate_action_effects(self, action: ActionType, context: GameContext) -> Tuple[int, int, List[str]]:
        """Calculate damage, block, and special effects for chosen action"""
        damage = 0
        block = 0
        effects = []
        
        # Base values from enemy stats
        base_damage = self.enemy.damage
        
        if action == ActionType.ATTACK:
            damage = int(base_damage * self.difficulty_modifier)
            
            # Creature-specific attack effects
            if self.enemy.name == "Bakunawa":
                effects.append("🐉 Dragon's Fury: Ignores some block")
                damage = int(damage * 1.2)
            elif self.enemy.name == "Aswang":
                effects.append("👹 Shapeshifter Strike: Variable damage")
                damage = int(damage * (0.8 + random.random() * 0.6))  # 80-140% damage
            elif self.enemy.name == "Manananggal":
                effects.append("🦇 Terror Flight: Causes fear")
            
        elif action == ActionType.DEFEND:
            block = int((8 + self.difficulty_level * 2) * self.difficulty_modifier)
            
            # Creature-specific defensive effects
            if self.enemy.name == "Kapre":
                effects.append("🌳 Nature's Shield: Enhanced defense")
                block = int(block * 1.3)
            elif self.enemy.name == "Dwende":
                effects.append("🏔️ Earth Armor: Damage reduction")
                
        elif action == ActionType.STATUS:
            # Get current pattern action for status effects
            pattern_action = self.enemy.attack_pattern[self.enemy.current_pattern_index]
            status_effect = self._get_status_effect_description(pattern_action)
            effects.append(status_effect)
            
            # Some status effects also provide minor benefits
            if pattern_action in ["buff", "power_up"]:
                effects.append("💪 Next attack deals +3 damage")
            elif pattern_action in ["heal", "regenerate"]:
                effects.append("💚 Recovers 5 health")
        
        return damage, block, effects
    
    def _generate_reasoning(self, action: ActionType, context: GameContext) -> str:
        """Generate reasoning for the chosen action"""
        reasoning_parts = []
        
        # Base action reasoning
        if action == ActionType.ATTACK:
            reasoning_parts.append("Launching aggressive assault")
        elif action == ActionType.DEFEND:
            reasoning_parts.append("Taking defensive stance")
        else:
            reasoning_parts.append("Using special ability")
        
        # Situational reasoning
        ai_health_ratio = context.get_ai_health_ratio()
        player_health_ratio = context.get_player_health_ratio()
        
        if ai_health_ratio < 0.3:
            reasoning_parts.append("desperate situation calls for bold action")
        elif player_health_ratio < 0.3:
            reasoning_parts.append("victory is within reach")
        elif context.turn_number <= 2:
            reasoning_parts.append("establishing early game advantage")
        
        # Personality flavor
        personality_flavor = {
            "Aggressive": "with overwhelming force",
            "Cautious": "with careful consideration", 
            "Calculating": "after strategic analysis",
            "Adaptive": "adapting to the situation",
            "Chaotic": "with unpredictable tactics"
        }
        
        if self.personality.name in personality_flavor:
            reasoning_parts.append(personality_flavor[self.personality.name])
        
        # Creature-specific flavor
        creature_flavor = {
            "Tikbalang": "The trickster spirit confuses its foe",
            "Kapre": "The nature spirit draws power from the earth",
            "Manananggal": "The terror takes to the skies",
            "Bakunawa": "The ancient dragon unleashes its might",
            "Aswang": "The shapeshifter reveals its true nature"
        }
        
        if self.enemy.name in creature_flavor:
            reasoning_parts.append(creature_flavor[self.enemy.name])
        
        return "; ".join(reasoning_parts)
    
    def _calculate_confidence(self, action: ActionType, context: GameContext) -> float:
        """Calculate confidence level for the chosen action"""
        base_confidence = 0.7
        
        # Adjust based on health situations
        ai_health_ratio = context.get_ai_health_ratio()
        player_health_ratio = context.get_player_health_ratio()
        
        # More confident when player is low health
        if player_health_ratio < 0.3:
            base_confidence += 0.2
        
        # Less confident when AI is low health
        if ai_health_ratio < 0.3:
            base_confidence -= 0.2
        
        # Action-specific confidence
        if action == ActionType.ATTACK:
            # Aggressive personalities more confident in attacks
            if self.personality.name == "Aggressive":
                base_confidence += 0.1
            # Cautious personalities less confident in attacks when low health
            elif self.personality.name == "Cautious" and ai_health_ratio < 0.5:
                base_confidence -= 0.1
                
        elif action == ActionType.DEFEND:
            # Cautious personalities more confident in defense
            if self.personality.name == "Cautious":
                base_confidence += 0.1
                
        # Difficulty modifier affects confidence
        if self.difficulty_level >= 7:
            base_confidence += 0.1  # High level AI more confident
        elif self.difficulty_level <= 3:
            base_confidence -= 0.1  # Low level AI less confident
        
        return max(0.1, min(1.0, base_confidence))
    
    def _calculate_risk_level(self, action: ActionType, context: GameContext) -> float:
        """Calculate risk level for the chosen action"""
        base_risk = 0.3
        
        ai_health_ratio = context.get_ai_health_ratio()
        
        if action == ActionType.ATTACK:
            base_risk = 0.6  # Attacking is riskier
            # More risky when low health
            if ai_health_ratio < 0.3:
                base_risk += 0.2
        elif action == ActionType.DEFEND:
            base_risk = 0.2  # Defending is safer
        else:  # STATUS
            base_risk = 0.4  # Status effects have medium risk
        
        # Personality adjustments
        if self.personality.name == "Aggressive":
            base_risk += 0.1  # Aggressive AI takes more risks
        elif self.personality.name == "Cautious":
            base_risk -= 0.1  # Cautious AI takes fewer risks
        
        return max(0.1, min(0.9, base_risk))
    
    def _get_status_effect_description(self, ability: str) -> str:
        """Get description of status effects"""
        descriptions = {
            "confuse": "😵 Confuse: Player loses focus",
            "smoke": "💨 Smoke Screen: Reduces player accuracy",
            "mischief": "😈 Mischief: Causes chaos",
            "defend": "🛡️ Defensive Stance: Increased protection",
            "buff": "💪 Power Up: Enhanced strength",
            "command": "👑 Command: Rally allies",
            "invisibility": "👻 Invisibility: Becomes untargetable",
            "deceive": "🎭 Deceive: Creates illusions",
            "flight": "🦅 Flight: Takes to the air",
            "split": "✂️ Split: Divides into copies",
            "shapeshift": "🔄 Shapeshift: Changes form",
            "eclipse": "🌑 Eclipse: Darkens the battlefield",
            "devour": "🦈 Devour: Consumes energy",
            "summon": "👻 Summon: Calls forth allies",
            "heal": "💚 Heal: Restores vitality",
            "poison": "☠️ Poison: Inflicts toxins",
            "stun": "⚡ Stun: Paralyzes target",
        }
        return descriptions.get(ability, f"⚡ {ability.title()}: Special effect activated")
    
    def _update_statistics(self, action: ActionType, damage: int, block: int):
        """Update AI performance statistics"""
        if action == ActionType.ATTACK:
            self.statistics.total_damage_dealt += damage
        
        # Update averages
        if self.statistics.turns_played > 0:
            self.statistics.average_hand_value = self.statistics.total_damage_dealt / self.statistics.turns_played
    

    

    

    

    
    def _record_decision(self, decision: AIDecision, context: GameContext):
        """Record decision in combat memory for analysis"""
        memory_entry = {
            "turn": self.statistics.turns_played,
            "action": decision.action.value,
            "damage": decision.estimated_damage,
            "block": decision.estimated_block,
            "confidence": decision.confidence,
            "risk": decision.risk_level,
            "context": {
                "ai_health_ratio": context.get_ai_health_ratio(),
                "player_health_ratio": context.get_player_health_ratio(),
                "turn_number": context.turn_number
            }
        }
        self.combat_memory.append(memory_entry)
        
        # Keep memory manageable
        if len(self.combat_memory) > 20:
            self.combat_memory.pop(0)
        
        # Update statistics
        self._update_statistics(decision.action, decision.estimated_damage, decision.estimated_block)
    
    def record_player_action(self, action: PlayerAction):
        """Record player action for adaptive learning"""
        # Update player pattern tracking for cards
        for card in action.cards_played:
            element_key = card.element.value
            self.player_patterns[element_key] = self.player_patterns.get(element_key, 0) + 1
        
        # Simple adaptation based on player behavior
        damage_dealt = action.evaluation.total_value if action.evaluation else 0
        
        # Adjust AI behavior based on player aggression
        if damage_dealt > 25:  # High damage play
            # Player is aggressive, AI should be more defensive or counter-aggressive
            self.action_preferences[ActionType.DEFEND] = min(0.6, self.action_preferences[ActionType.DEFEND] + 0.05)
        elif damage_dealt < 10:  # Low damage play
            # Player is passive, AI can be more aggressive
            self.action_preferences[ActionType.ATTACK] = min(0.7, self.action_preferences[ActionType.ATTACK] + 0.05)
        
        # Normalize preferences
        total = sum(self.action_preferences.values())
        for action in self.action_preferences:
            self.action_preferences[action] /= total
        
        # Update adaptation level
        self.statistics.adaptation_level = min(100.0, len(self.player_patterns) * 10)
    

    
    def get_ai_status(self) -> Dict[str, Any]:
        """Get comprehensive AI status and statistics"""
        return {
            "creature": self.enemy.name,
            "personality": self.personality.name,
            "difficulty_level": self.difficulty_level,
            "difficulty_modifier": self.difficulty_modifier,
            "action_preferences": dict(self.action_preferences),
            "statistics": {
                "turns_played": self.statistics.turns_played,
                "total_damage_dealt": self.statistics.total_damage_dealt,
                "average_hand_value": self.statistics.average_hand_value,
                "adaptation_level": self.statistics.adaptation_level,
            },
            "personality_config": {
                "risk_tolerance": self.personality.risk_tolerance,
                "damage_weight": self.personality.damage_weight,
                "elemental_weight": self.personality.elemental_weight,
                "bluff_chance": self.personality.bluff_chance,
                "adaptation_rate": self.personality.adaptation_rate,
            },
            "player_patterns": dict(self.player_patterns),
        }
    
    def simulate_decision(self, context: GameContext) -> AIDecision:
        """Simulate a decision without actually executing it"""
        # Choose action without updating statistics
        action = self._choose_action(context)
        damage, block, effects = self._calculate_action_effects(action, context)
        reasoning = f"[SIMULATION] {self._generate_reasoning(action, context)}"
        confidence = self._calculate_confidence(action, context)
        
        return AIDecision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            estimated_damage=damage,
            estimated_block=block,
            risk_level=self._calculate_risk_level(action, context),
            special_effects=effects
        )
    
    def override_personality(self, new_personality: AIPersonalityConfig):
        """Override AI personality for testing or special scenarios"""
        self.personality = new_personality
        self.statistics.personality_type = new_personality.name
        # Recalculate action preferences with new personality
        self.action_preferences = self._calculate_action_preferences()
    
    def get_current_action_preferences(self) -> Dict[ActionType, float]:
        """Get current action preferences (for debugging/display)"""
        return self.action_preferences.copy()
    
    def advance_attack_pattern(self):
        """Advance to next attack in pattern"""
        self.enemy.current_pattern_index = (self.enemy.current_pattern_index + 1) % len(self.enemy.attack_pattern)


if __name__ == "__main__":
    # Test the Bathala AI system
    print("🐲 Simplified Bathala AI System Test 🐲\n")
    
    # Create test enemy
    test_enemy = Enemy(
        id="test_bakunawa",
        name="Bakunawa",
        max_health=100,
        current_health=100,
        block=0,
        damage=18,
        attack_pattern=["attack", "eclipse", "attack", "devour"]
    )
    
    # Create AI with different difficulty levels
    for difficulty in [1, 5, 10]:
        print(f"🎚️ Testing Difficulty Level {difficulty}")
        ai = BathalaAI(test_enemy, difficulty)
        
        # Create test context
        context = GameContext(
            player_health=40,
            player_max_health=50,
            player_block=3,
            ai_health=test_enemy.current_health,
            ai_max_health=test_enemy.max_health,
            ai_block=test_enemy.block,
            turn_number=3,
            cards_remaining=0  # AI doesn't have cards anymore
        )
        
        # Make decision
        decision = ai.make_decision(context)
        
        print(f"   🎯 Action: {decision.action.value}")
        print(f"   💥 Estimated Damage: {decision.estimated_damage}")
        print(f"   🛡️ Estimated Block: {decision.estimated_block}")
        print(f"   🎲 Confidence: {decision.confidence:.1%}")
        print(f"   🎭 Reasoning: {decision.reasoning}")
        if decision.special_effects:
            print(f"   ✨ Effects: {', '.join(decision.special_effects)}")
        print(f"   ⚠️ Risk Level: {decision.risk_level:.1%}")
        print()
    
    # Test adaptive learning
    print("🧠 Testing Adaptive Learning:")
    adaptive_ai = BathalaAI(test_enemy, 5)
    
    # Import for testing only
    from enhanced_card_system import CardDeck, EnhancedHandEvaluator
    
    # Simulate player actions
    test_deck = CardDeck()
    test_deck.shuffle()
    
    for i in range(3):
        player_cards = test_deck.draw(3)
        player_eval = EnhancedHandEvaluator.evaluate_hand(player_cards)
        
        player_action = PlayerAction(
            cards_played=player_cards,
            evaluation=player_eval,
            turn_number=i + 1,
            game_context=context
        )
        
        adaptive_ai.record_player_action(player_action)
        print(f"   Turn {i+1}: Player played {player_eval.hand_type.value} ({player_eval.total_value} dmg)")
    
    # Show learning progress
    status = adaptive_ai.get_ai_status()
    print(f"\n📊 Learning Progress:")
    print(f"   Adaptation Level: {status['statistics']['adaptation_level']:.1f}%")
    print(f"   Player Patterns: {status['player_patterns']}")
    print(f"   Action Preferences: {status['action_preferences']}")
    
    # Test different actions
    print(f"\n⚔️ Testing Action Patterns:")
    for turn in range(4):
        decision = adaptive_ai.make_decision(context)
        print(f"   Turn {turn+1}: {decision.action.value} - {decision.reasoning}")
        adaptive_ai.advance_attack_pattern()