"""
AI Manager for Bathala-like Card Combat Game
Main integration interface that coordinates AI with game systems
"""

import time
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from enhanced_card_system import Card, EnhancedHandEvaluator, Element
from ai_personality import AIPersonalityConfig, get_personality_for_creature, AIPersonalityType
from hand_strategy import GameContext, PlayerAction
from bathala_ai import BathalaAI, Enemy, AIDecision, ActionType, AIStatistics


@dataclass
class AIConfig:
    """Configuration for AI system"""
    difficulty_level: int = 1
    enable_adaptation: bool = True
    debug_mode: bool = False
    ai_card_count: int = 8
    auto_adjust_difficulty: bool = False
    personality_override: Optional[AIPersonalityType] = None


@dataclass  
class AITurnResult:
    """Complete result of an AI turn with all effects"""
    decision: AIDecision
    cards_played: List[Card]
    damage_dealt: int
    block_gained: int
    special_effects: List[str]
    ai_status: str
    debug_info: Optional[Dict] = None
    
    def get_summary(self) -> str:
        """Get human-readable summary of the turn"""
        if self.decision.action == ActionType.PLAY_HAND:
            cards_str = " ".join(str(card) for card in self.cards_played)
            return f"Played {cards_str} for {self.damage_dealt} damage"
        elif self.decision.action == ActionType.SPECIAL_ABILITY:
            return f"Used special ability: {', '.join(self.special_effects)}"
        else:
            return "Passed turn"


class CombatPhase(Enum):
    PLAYER_TURN = "player_turn"
    AI_TURN = "ai_turn"
    GAME_OVER = "game_over"
    POST_COMBAT = "post_combat"


@dataclass
class CombatState:
    """Current state of the combat encounter"""
    phase: CombatPhase
    turn_number: int
    player_health: int
    player_max_health: int
    player_block: int
    ai_health: int  
    ai_max_health: int
    ai_block: int
    player_hand_size: int = 0
    ai_hand_size: int = 0
    
    def to_game_context(self) -> GameContext:
        """Convert to GameContext for AI decision making"""
        return GameContext(
            player_health=self.player_health,
            player_max_health=self.player_max_health,
            player_block=self.player_block,
            ai_health=self.ai_health,
            ai_max_health=self.ai_max_health,
            ai_block=self.ai_block,
            turn_number=self.turn_number,
            cards_remaining=self.ai_hand_size
        )


class AIManager:
    """Main AI management interface for game integration"""
    
    def __init__(self, config: AIConfig = None):
        if config is None:
            config = AIConfig()
        self.config = config
        self.ai: Optional[BathalaAI] = None
        self.combat_start_time: float = 0
        self.player_action_history: List[PlayerAction] = []
        self.combat_analytics: Dict[str, Any] = {}
        self.current_enemy: Optional[Enemy] = None
        
        # Performance tracking
        self.turn_times: List[float] = []
        self.decision_quality_scores: List[float] = []
        
    def initialize_combat(self, enemy: Enemy) -> None:
        """Initialize AI for a new combat encounter"""
        self.current_enemy = enemy
        self.ai = BathalaAI(enemy, self.config.difficulty_level)
        self.combat_start_time = time.time()
        self.player_action_history.clear()
        self.turn_times.clear()
        self.decision_quality_scores.clear()
        
        # Apply personality override if specified
        if self.config.personality_override:
            from ai_personality import get_personality_by_type
            override_personality = get_personality_by_type(self.config.personality_override)
            self.ai.override_personality(override_personality)
        
        if self.config.debug_mode:
            self._debug_log(f"🤖 AI initialized for {enemy.name}")
            self._debug_log(f"📊 Difficulty Level: {self.config.difficulty_level}")
            self._debug_log(f"🧠 Personality: {self.ai.personality.name}")
            self._debug_log(f"🃏 Starting Cards: {len(self.ai.get_available_cards())}")
    
    def execute_ai_turn(self, combat_state: CombatState) -> AITurnResult:
        """Execute AI turn and return complete results"""
        if not self.ai:
            raise ValueError("AI not initialized. Call initialize_combat() first.")
        
        turn_start_time = time.time()
        
        # Convert combat state to game context
        game_context = combat_state.to_game_context()
        
        # Get AI decision
        decision = self.ai.make_decision(game_context)
        
        # Process the decision and calculate effects
        result = self._process_ai_decision(decision, combat_state)
        
        # Track performance
        turn_time = time.time() - turn_start_time
        self.turn_times.append(turn_time)
        
        # Calculate decision quality score
        quality_score = self._calculate_decision_quality(decision, combat_state)
        self.decision_quality_scores.append(quality_score)
        
        # Auto-adjust difficulty if enabled
        if self.config.auto_adjust_difficulty:
            self._consider_difficulty_adjustment()
        
        # Debug logging
        if self.config.debug_mode:
            self._debug_log_turn_result(result, turn_time, quality_score)
        
        # Advance enemy attack pattern
        self.ai.advance_attack_pattern()
        
        return result
    
    def _process_ai_decision(self, decision: AIDecision, combat_state: CombatState) -> AITurnResult:
        """Process AI decision and calculate all effects"""
        result = AITurnResult(
            decision=decision,
            cards_played=decision.cards.copy(),
            damage_dealt=0,
            block_gained=0,
            special_effects=decision.special_effects.copy(),
            ai_status=self._get_ai_status_string()
        )
        
        if self.config.debug_mode:
            result.debug_info = {
                "ai_statistics": self.ai.get_ai_status(),
                "combat_state": combat_state,
                "turn_time": time.time() - self.combat_start_time,
                "available_cards": [str(card) for card in self.ai.get_available_cards()],
                "decision_breakdown": {
                    "confidence": decision.confidence,
                    "risk_level": decision.risk_level,
                    "bluff_factor": decision.bluff_factor
                }
            }
        
        if decision.action == ActionType.PLAY_HAND:
            # Calculate damage and effects
            result.damage_dealt = self._calculate_damage(decision)
            result.block_gained = self._calculate_block_gained(decision)
            result.special_effects.extend(self._calculate_additional_effects(decision))
            
        elif decision.action == ActionType.SPECIAL_ABILITY:
            # Process special ability effects
            result.special_effects.extend(self._execute_special_ability())
            result.block_gained = self._get_special_ability_block()
            
        return result
    
    def _calculate_damage(self, decision: AIDecision) -> int:
        """Calculate final damage from AI's play"""
        if not decision.evaluation:
            return 0
        
        base_damage = decision.evaluation.total_value
        
        # Apply creature-specific modifiers
        damage = self._apply_creature_damage_modifiers(base_damage, decision)
        
        # Apply difficulty scaling
        damage = int(damage * self.ai.difficulty_modifier)
        
        return max(0, damage)
    
    def _calculate_block_gained(self, decision: AIDecision) -> int:
        """Calculate block gained from AI's play"""
        if not decision.cards:
            return 0
        
        block = 0
        
        # Water cards provide block
        water_cards = sum(1 for card in decision.cards if card.element == Element.WATER)
        block += water_cards * 2
        
        # Earth cards can provide armor/block
        earth_cards = sum(1 for card in decision.cards if card.element == Element.EARTH)
        if earth_cards >= 3:
            block += 5  # Earth mastery defensive bonus
        
        # Personality modifiers
        if self.ai.personality.name == "Cautious":
            block = int(block * 1.5)  # Cautious AI gets more defensive value
        
        return block
    
    def _calculate_additional_effects(self, decision: AIDecision) -> List[str]:
        """Calculate additional special effects from the play"""
        effects = []
        
        if not decision.cards:
            return effects
        
        # Analyze elemental effects
        element_counts = {}
        for card in decision.cards:
            element_counts[card.element] = element_counts.get(card.element, 0) + 1
        
        # Fire effects
        fire_count = element_counts.get(Element.FIRE, 0)
        if fire_count >= 2:
            effects.append(f"🔥 Fire synergy: +{fire_count} burn damage next turn")
        if fire_count >= 3:
            effects.append("🔥 Ignite: Burns through block")
        
        # Air effects
        air_count = element_counts.get(Element.AIR, 0)
        if air_count == len(decision.cards) and len(decision.cards) > 1:
            effects.append("💨 Air mastery: Cannot be blocked")
        
        # Earth effects
        earth_count = element_counts.get(Element.EARTH, 0)
        if earth_count >= 3:
            effects.append("🌍 Earth mastery: +3 armor")
        
        # Creature-specific effects
        effects.extend(self._get_creature_specific_effects(decision))
        
        return effects
    
    def _get_creature_specific_effects(self, decision: AIDecision) -> List[str]:
        """Get creature-specific special effects"""
        effects = []
        creature_name = self.current_enemy.name if self.current_enemy else ""
        
        creature_effects = {
            "Tikbalang": ["🌀 Misdirection: Player loses next card draw"],
            "Kapre": ["🌳 Nature's Blessing: Heals 3 HP"],
            "Manananggal": ["🦇 Terror: Player loses 1 block"],
            "Bakunawa": ["🐉 Dragon Fear: Player cannot gain block next turn"],
            "Aswang": ["👹 Intimidate: Player discards lowest card"],
            "Sigbin": ["👻 Shadow Strike: Ignores 50% of block"],
        }
        
        if creature_name in creature_effects and decision.evaluation and decision.evaluation.total_value > 25:
            effects.extend(creature_effects[creature_name])
        
        return effects
    
    def _apply_creature_damage_modifiers(self, base_damage: int, decision: AIDecision) -> int:
        """Apply creature-specific damage modifiers"""
        if not self.current_enemy:
            return base_damage
        
        damage = base_damage
        creature_name = self.current_enemy.name
        
        # Creature-specific damage modifications
        if creature_name == "Tikbalang":  # Chaotic
            # High variance damage
            variance = 0.7 + (random.random() * 0.6)  # 0.7 to 1.3 multiplier
            damage = int(damage * variance)
            
        elif creature_name in ["Aswang", "Sigbin"]:  # Aggressive
            # Higher damage but with miss chance
            damage = int(damage * 1.2)
            if random.random() < 0.1:  # 10% miss chance
                damage = 0
                
        elif creature_name in ["Dwende", "Tiyanak"]:  # Cautious
            # Lower but more consistent damage
            damage = int(damage * 0.9)
            
        elif creature_name == "Kapre":  # Elemental
            # Bonus for matching elements
            if decision.cards:
                unique_elements = len(set(card.element for card in decision.cards))
                if unique_elements == 1:
                    damage = int(damage * 1.25)
                    
        elif creature_name == "Bakunawa":  # Boss - adaptive
            # Scales with turn number
            turn_bonus = 1.0 + (self.ai.statistics.turns_played * 0.02)
            damage = int(damage * min(turn_bonus, 1.5))
        
        return max(1, damage)  # Minimum 1 damage
    
    def _execute_special_ability(self) -> List[str]:
        """Execute current special ability and return effects"""
        if not self.current_enemy:
            return []
        
        current_action = self.current_enemy.attack_pattern[self.current_enemy.current_pattern_index]
        return [self.ai._get_special_ability_description(current_action)]
    
    def _get_special_ability_block(self) -> int:
        """Get block gained from special abilities"""
        if not self.current_enemy:
            return 0
        
        current_action = self.current_enemy.attack_pattern[self.current_enemy.current_pattern_index]
        
        defensive_abilities = {
            "defend": 10,
            "smoke": 8,
            "block": 12,
            "shapeshift": 5,
        }
        
        return defensive_abilities.get(current_action, 0)
    
    def record_player_action(self, cards_played: List[Card], turn_number: int, combat_state: CombatState):
        """Record player action for AI learning"""
        if not self.ai or not self.config.enable_adaptation:
            return
        
        evaluation = EnhancedHandEvaluator.evaluate_hand(cards_played)
        game_context = combat_state.to_game_context()
        
        player_action = PlayerAction(
            cards_played=cards_played,
            evaluation=evaluation,
            turn_number=turn_number,
            game_context=game_context
        )
        
        self.ai.record_player_action(player_action)
        self.player_action_history.append(player_action)
        
        if self.config.debug_mode:
            self._debug_log(f"📚 Recorded player action: {evaluation.hand_type.value} ({evaluation.total_value} damage)")
    
    def preview_ai_action(self, combat_state: CombatState) -> Optional[AIDecision]:
        """Preview what AI might do without executing (for player planning)"""
        if not self.ai:
            return None
        
        game_context = combat_state.to_game_context()
        return self.ai.simulate_decision(game_context)
    
    def set_difficulty(self, new_level: int):
        """Adjust AI difficulty level"""
        self.config.difficulty_level = max(1, min(10, new_level))
        
        if self.ai:
            # Create new AI with same enemy but new difficulty
            self.ai = BathalaAI(self.current_enemy, self.config.difficulty_level)
        
        if self.config.debug_mode:
            self._debug_log(f"🎚️ AI difficulty adjusted to level {self.config.difficulty_level}")
    
    def _consider_difficulty_adjustment(self):
        """Consider auto-adjusting difficulty based on performance"""
        if len(self.player_action_history) < 5:
            return  # Need more data
        
        # Analyze recent player performance
        recent_actions = self.player_action_history[-5:]
        avg_player_damage = sum(action.evaluation.total_value for action in recent_actions) / len(recent_actions)
        
        # If player is consistently doing high damage, increase AI difficulty
        if avg_player_damage > 30 and self.config.difficulty_level < 8:
            self.set_difficulty(self.config.difficulty_level + 1)
            self._debug_log("📈 Auto-increased difficulty due to strong player performance")
            
        # If player is struggling, decrease difficulty
        elif avg_player_damage < 12 and self.config.difficulty_level > 2:
            self.set_difficulty(self.config.difficulty_level - 1)
            self._debug_log("📉 Auto-decreased difficulty due to weak player performance")
    
    def _calculate_decision_quality(self, decision: AIDecision, combat_state: CombatState) -> float:
        """Calculate quality score for AI decision (0-100)"""
        quality = 50.0  # Base quality
        
        # Confidence factor
        quality += decision.confidence * 20
        
        # Damage efficiency
        if decision.estimated_damage > 0:
            efficiency = decision.estimated_damage / max(1, len(decision.cards))
            quality += min(20, efficiency * 2)
        
        # Context appropriateness
        if combat_state.ai_health < combat_state.ai_max_health * 0.3:
            # Low health - prefer high damage or healing
            if decision.estimated_damage > 25:
                quality += 15
        
        if combat_state.player_health < combat_state.player_max_health * 0.3:
            # Player low - go for kill
            if decision.estimated_damage > 20:
                quality += 20
        
        # Risk appropriateness
        if decision.risk_level < 0.3:  # Safe play
            quality += 5
        elif decision.risk_level > 0.7:  # Risky play
            quality += 10 if combat_state.ai_health < combat_state.ai_max_health * 0.4 else -5
        
        return max(0, min(100, quality))
    
    def get_combat_analytics(self) -> Dict[str, Any]:
        """Get comprehensive combat analytics"""
        combat_duration = time.time() - self.combat_start_time
        
        analytics = {
            "combat_duration": combat_duration,
            "player_actions": len(self.player_action_history),
            "ai_statistics": self.ai.get_ai_status() if self.ai else {},
            "difficulty_level": self.config.difficulty_level,
            "adaptation_enabled": self.config.enable_adaptation,
            "performance_metrics": {
                "average_turn_time": sum(self.turn_times) / max(1, len(self.turn_times)),
                "average_decision_quality": sum(self.decision_quality_scores) / max(1, len(self.decision_quality_scores)),
                "total_turns": len(self.turn_times),
            }
        }
        
        if self.player_action_history:
            player_stats = {
                "average_damage": sum(action.evaluation.total_value for action in self.player_action_history) / len(self.player_action_history),
                "total_cards_played": sum(len(action.cards_played) for action in self.player_action_history),
                "favorite_elements": self._analyze_player_element_preferences(),
            }
            analytics["player_statistics"] = player_stats
        
        return analytics
    
    def _analyze_player_element_preferences(self) -> Dict[str, int]:
        """Analyze player's elemental preferences"""
        element_counts = {}
        for action in self.player_action_history:
            for card in action.cards_played:
                element_counts[card.element.value] = element_counts.get(card.element.value, 0) + 1
        return element_counts
    
    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug mode"""
        self.config.debug_mode = enabled
    
    def reset(self):
        """Reset AI state for new combat"""
        self.ai = None
        self.current_enemy = None
        self.player_action_history.clear()
        self.turn_times.clear()
        self.decision_quality_scores.clear()
        self.combat_start_time = 0
    
    def get_config(self) -> AIConfig:
        """Get current AI configuration"""
        return self.config
    
    def update_config(self, **kwargs):
        """Update AI configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def _get_ai_status_string(self) -> str:
        """Get human-readable AI status"""
        if not self.ai:
            return "AI not initialized"
        
        status = self.ai.get_ai_status()
        return (f"{status['personality']} AI | "
                f"Level {status['difficulty_level']} | "
                f"{status['cards_remaining']} cards | "
                f"Adaptation: {status['statistics']['adaptation_level']:.0f}%")
    
    def _debug_log(self, message: str):
        """Log debug message if debug mode enabled"""
        if self.config.debug_mode:
            print(f"🤖 {message}")
    
    def _debug_log_turn_result(self, result: AITurnResult, turn_time: float, quality_score: float):
        """Log detailed turn result in debug mode"""
        if not self.config.debug_mode:
            return
        
        print(f"🎯 AI Turn Result:")
        print(f"   Action: {result.decision.action.value}")
        if result.cards_played:
            print(f"   Cards: {[str(card) for card in result.cards_played]}")
        print(f"   Damage: {result.damage_dealt}")
        print(f"   Block: {result.block_gained}")
        print(f"   Confidence: {result.decision.confidence:.2f}")
        print(f"   Quality Score: {quality_score:.1f}")
        print(f"   Turn Time: {turn_time:.3f}s")
        print(f"   Reasoning: {result.decision.reasoning}")
        if result.special_effects:
            print(f"   Effects: {', '.join(result.special_effects)}")


# Import random for variance calculations
import random


if __name__ == "__main__":
    # Test the AI Manager system
    print("🎮 AI Manager System Test 🎮\n")
    
    # Create test configuration
    config = AIConfig(
        difficulty_level=3,
        enable_adaptation=True,
        debug_mode=True,
        ai_card_count=8
    )
    
    # Initialize manager
    manager = AIManager(config)
    
    # Create test enemy
    test_enemy = Enemy(
        id="test_kapre",
        name="Kapre",
        max_health=40,
        current_health=40,
        block=0,
        damage=8,
        attack_pattern=["attack", "smoke", "attack"]
    )
    
    # Initialize combat
    manager.initialize_combat(test_enemy)
    
    # Create test combat state
    combat_state = CombatState(
        phase=CombatPhase.AI_TURN,
        turn_number=1,
        player_health=35,
        player_max_health=50,
        player_block=2,
        ai_health=40,
        ai_max_health=40,
        ai_block=0,
        player_hand_size=5,
        ai_hand_size=8
    )
    
    # Execute AI turn
    result = manager.execute_ai_turn(combat_state)
    print(f"📊 Turn Result: {result.get_summary()}")
    
    # Test player action recording
    from enhanced_card_system import CardDeck
    test_deck = CardDeck()
    test_deck.shuffle()
    player_cards = test_deck.draw(3)
    
    manager.record_player_action(player_cards, 1, combat_state)
    
    # Get analytics
    analytics = manager.get_combat_analytics()
    print(f"\n📈 Combat Analytics:")
    print(f"   Duration: {analytics['combat_duration']:.2f}s")
    print(f"   AI Level: {analytics['difficulty_level']}")
    print(f"   Decision Quality: {analytics['performance_metrics']['average_decision_quality']:.1f}")
    print(f"   Player Actions: {analytics['player_actions']}")
    
    # Test preview
    preview = manager.preview_ai_action(combat_state)
    if preview:
        print(f"\n🔮 AI Preview: {preview.reasoning}")
        print(f"   Would deal ~{preview.estimated_damage} damage")