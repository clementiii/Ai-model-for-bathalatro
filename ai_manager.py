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
    auto_adjust_difficulty: bool = False
    personality_override: Optional[AIPersonalityType] = None


@dataclass  
class AITurnResult:
    """Complete result of an AI turn with all effects"""
    decision: AIDecision
    damage_dealt: int
    block_gained: int
    special_effects: List[str]
    ai_status: str
    debug_info: Optional[Dict] = None
    
    def get_summary(self) -> str:
        """Get human-readable summary of the turn"""
        if self.decision.action == ActionType.ATTACK:
            return f"Attacked for {self.damage_dealt} damage"
        elif self.decision.action == ActionType.DEFEND:
            return f"Defended and gained {self.block_gained} block"
        elif self.decision.action == ActionType.STATUS:
            return f"Used status effect: {', '.join(self.special_effects)}"
        else:
            return "Unknown action"


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
            self._debug_log(f"⚔️ Action Preferences: {self.ai.get_current_action_preferences()}")
    
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
            damage_dealt=decision.estimated_damage,
            block_gained=decision.estimated_block,
            special_effects=decision.special_effects.copy(),
            ai_status=self._get_ai_status_string()
        )
        
        if self.config.debug_mode:
            result.debug_info = {
                "ai_statistics": self.ai.get_ai_status(),
                "combat_state": combat_state,
                "turn_time": time.time() - self.combat_start_time,
                "action_preferences": self.ai.get_current_action_preferences(),
                "decision_breakdown": {
                    "confidence": decision.confidence,
                    "risk_level": decision.risk_level,
                    "estimated_damage": decision.estimated_damage,
                    "estimated_block": decision.estimated_block
                }
            }
        
        # Apply difficulty scaling to final values
        if decision.action == ActionType.ATTACK:
            result.damage_dealt = max(1, int(decision.estimated_damage * self.ai.difficulty_modifier))
        elif decision.action == ActionType.DEFEND:
            result.block_gained = max(0, int(decision.estimated_block * self.ai.difficulty_modifier))
        elif decision.action == ActionType.STATUS:
            # Status effects already calculated in the AI decision
            pass
            
        return result
    
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
        
        # Action effectiveness
        if decision.action == ActionType.ATTACK and decision.estimated_damage > 0:
            # More quality for higher damage attacks
            quality += min(20, decision.estimated_damage * 0.8)
        elif decision.action == ActionType.DEFEND and decision.estimated_block > 0:
            # Quality for defensive plays when needed
            if combat_state.ai_health < combat_state.ai_max_health * 0.5:
                quality += min(15, decision.estimated_block * 0.6)
        elif decision.action == ActionType.STATUS:
            # Status effects get moderate quality bonus
            quality += 10
        
        # Context appropriateness
        if combat_state.ai_health < combat_state.ai_max_health * 0.3:
            # Low health - prefer high damage or healing
            if decision.action == ActionType.ATTACK and decision.estimated_damage > 15:
                quality += 15
            elif decision.action == ActionType.DEFEND:
                quality += 10  # Defensive play when low health
        
        if combat_state.player_health < combat_state.player_max_health * 0.3:
            # Player low - go for kill
            if decision.action == ActionType.ATTACK and decision.estimated_damage > 10:
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
        debug_mode=True
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
        ai_hand_size=0  # AI doesn't have cards anymore
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