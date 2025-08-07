"""
Dynamic Difficulty Adjustment (DDA) System for Bathala AI Card Combat Game

This module implements a sophisticated rule-based DDA system centered around a 
Player Performance Score (PPS) to maintain player flow state and engagement.

Academic Thesis Research Question:
"How can a rule-based adaptive difficulty system be designed to maintain a state 
of 'flow' for players of varying skill levels in a strategic roguelike game?"
"""

import time
import json
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple, Any
from collections import deque
from enhanced_card_system import HandType, HandEvaluation
from bathala_ai import Enemy


class DifficultyTier(Enum):
    """Hidden difficulty tiers that control game response"""
    STRUGGLING = 0      # Significant assistance needed
    LEARNING_1 = 1      # Gentle learning curve
    LEARNING_2 = 2      # Standard difficulty with minor adjustments
    THRIVING_1 = 3      # Player performing well
    THRIVING_2 = 4      # High performance, increased challenge
    MASTERING = 5       # Maximum challenge, minimal safety nets


class EventType(Enum):
    """Types of events that can affect PPS"""
    COMBAT_START = "combat_start"
    COMBAT_END = "combat_end"
    CARDS_PLAYED = "cards_played"
    DAMAGE_TAKEN = "damage_taken"
    RESOURCE_USED = "resource_used"
    TURN_COMPLETED = "turn_completed"


@dataclass
class PerformanceEvent:
    """Individual event that affects player performance scoring"""
    event_type: EventType
    timestamp: float
    pps_delta: float
    details: Dict[str, Any]
    reasoning: str


@dataclass
class CombatMetrics:
    """Metrics tracked during a single combat encounter"""
    combat_id: str
    start_time: float
    end_time: Optional[float] = None
    
    # Combat Efficiency Metrics
    starting_health: int = 100
    ending_health: int = 100
    health_lost: int = 0
    turns_taken: int = 0
    damage_dealt: int = 0
    damage_received: int = 0
    
    # Resource Management Metrics
    potions_used: int = 0
    discard_charges_used: int = 0
    gold_spent: int = 0
    
    # Strategic Acumen Metrics
    total_hands_played: int = 0
    high_quality_hands: int = 0  # Four of a Kind or better
    average_hand_quality: float = 0.0
    elemental_synergies_used: int = 0
    
    # Efficiency Metrics
    damage_efficiency: float = 0.0  # damage_dealt / turns_taken
    health_efficiency: float = 0.0  # (1 - health_lost/starting_health)
    
    def finalize_combat(self):
        """Calculate final metrics when combat ends"""
        self.end_time = time.time()
        self.health_lost = self.starting_health - self.ending_health
        
        if self.turns_taken > 0:
            self.damage_efficiency = self.damage_dealt / self.turns_taken
        
        if self.starting_health > 0:
            self.health_efficiency = 1.0 - (self.health_lost / self.starting_health)


@dataclass
class AdaptiveModifiers:
    """All current adaptive modifiers applied by the DDA system"""
    # Enemy stat modifiers (multiplicative, 1.0 = no change)
    enemy_health_modifier: float = 1.0
    enemy_damage_modifier: float = 1.0
    enemy_block_modifier: float = 1.0
    
    # Economic modifiers
    shop_price_modifier: float = 1.0
    gold_reward_modifier: float = 1.0
    
    # Map generation hints
    favor_rest_sites: bool = False
    favor_treasure_sites: bool = False
    
    # Narrative event triggers
    narrative_blessing_active: bool = False
    narrative_challenge_active: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class PlayerPerformanceTracker:
    """Core PPS tracking and calculation system"""
    
    def __init__(self):
        # Core PPS value (starts at 0, can be negative)
        self.pps: float = 0.0
        
        # Performance history for trend analysis
        self.pps_history: deque = deque(maxlen=100)  # Last 100 PPS updates
        self.event_history: deque = deque(maxlen=200)  # Last 200 events
        
        # Current combat tracking
        self.current_combat: Optional[CombatMetrics] = None
        self.combat_history: List[CombatMetrics] = []
        
        # Session statistics
        self.session_start_time: float = time.time()
        self.total_combats: int = 0
        self.total_victories: int = 0
        self.total_defeats: int = 0
        
        # Performance trend indicators
        self.recent_trend: float = 0.0  # Positive = improving, negative = declining
        self.volatility: float = 0.0     # How much PPS fluctuates
        
    def start_combat(self, player_health: int, enemy_name: str) -> str:
        """Start tracking a new combat encounter"""
        combat_id = f"combat_{int(time.time())}_{enemy_name}"
        
        self.current_combat = CombatMetrics(
            combat_id=combat_id,
            start_time=time.time(),
            starting_health=player_health
        )
        
        self._record_event(
            EventType.COMBAT_START,
            0.0,
            {"enemy_name": enemy_name, "player_health": player_health},
            "Combat encounter initiated"
        )
        
        return combat_id
    
    def end_combat(self, victory: bool, player_health: int, turns_taken: int):
        """End current combat and calculate performance impact"""
        if not self.current_combat:
            return
        
        # Finalize combat metrics
        self.current_combat.ending_health = player_health
        self.current_combat.turns_taken = turns_taken
        self.current_combat.finalize_combat()
        
        # Calculate PPS impact based on performance
        pps_delta = self._calculate_combat_pps_impact(victory)
        
        # Update PPS and history
        self._update_pps(pps_delta)
        
        # Store combat in history
        self.combat_history.append(self.current_combat)
        self.total_combats += 1
        
        if victory:
            self.total_victories += 1
        else:
            self.total_defeats += 1
        
        # Record event
        self._record_event(
            EventType.COMBAT_END,
            pps_delta,
            {
                "victory": victory,
                "health_lost": self.current_combat.health_lost,
                "turns_taken": turns_taken,
                "health_efficiency": self.current_combat.health_efficiency
            },
            f"Combat {'won' if victory else 'lost'} - health efficiency: {self.current_combat.health_efficiency:.2f}"
        )
        
        self.current_combat = None
    
    def record_cards_played(self, hand_evaluation: HandEvaluation, turn_number: int):
        """Record a hand played by the player"""
        if not self.current_combat:
            return
        
        self.current_combat.total_hands_played += 1
        self.current_combat.damage_dealt += hand_evaluation.total_value
        
        # Track high-quality hands (Four of a Kind or better)
        high_quality_hands = [
            HandType.FOUR_OF_A_KIND,
            HandType.STRAIGHT_FLUSH,
            HandType.ROYAL_FLUSH
        ]
        
        pps_delta = 0.0
        reasoning = f"Played {hand_evaluation.hand_type.value} for {hand_evaluation.total_value} damage"
        
        if hand_evaluation.hand_type in high_quality_hands:
            self.current_combat.high_quality_hands += 1
            pps_delta += 0.2
            reasoning += " - excellent strategic play!"
        
        # Bonus for strong hands played efficiently
        if hand_evaluation.total_value >= 50:  # Strong hand
            pps_delta += 0.1
        elif hand_evaluation.total_value <= 10:  # Weak hand
            pps_delta -= 0.1
        
        # Penalty for taking too long (more than 8 turns for standard enemy)
        if turn_number > 8:
            pps_delta -= 0.25
            reasoning += " - combat taking too long"
        
        if pps_delta != 0:
            self._update_pps(pps_delta)
            self._record_event(
                EventType.CARDS_PLAYED,
                pps_delta,
                {
                    "hand_type": hand_evaluation.hand_type.value,
                    "damage": hand_evaluation.total_value,
                    "turn_number": turn_number
                },
                reasoning
            )
    
    def record_damage_taken(self, damage: int, player_health: int, max_health: int):
        """Record damage taken by player"""
        if not self.current_combat:
            return
        
        self.current_combat.damage_received += damage
        health_percentage = player_health / max_health
        
        pps_delta = 0.0
        reasoning = f"Took {damage} damage (Health: {health_percentage:.1%})"
        
        # Significant penalty if health drops very low
        if health_percentage <= 0.2:  # Below 20% health
            pps_delta -= 0.4
            reasoning += " - critical health level!"
        elif health_percentage <= 0.5:  # Below 50% health
            pps_delta -= 0.2
            reasoning += " - low health"
        
        if pps_delta != 0:
            self._update_pps(pps_delta)
            self._record_event(
                EventType.DAMAGE_TAKEN,
                pps_delta,
                {"damage": damage, "health_percentage": health_percentage},
                reasoning
            )
    
    def record_resource_usage(self, resource_type: str, amount: int = 1):
        """Record usage of resources (potions, discard charges, etc.)"""
        if not self.current_combat:
            return
        
        if resource_type == "potion":
            self.current_combat.potions_used += amount
        elif resource_type == "discard_charge":
            self.current_combat.discard_charges_used += amount
        
        # Minor PPS penalty for resource usage (indicates struggling)
        pps_delta = -0.1 * amount
        reasoning = f"Used {amount} {resource_type}(s)"
        
        self._update_pps(pps_delta)
        self._record_event(
            EventType.RESOURCE_USED,
            pps_delta,
            {"resource_type": resource_type, "amount": amount},
            reasoning
        )
    
    def _calculate_combat_pps_impact(self, victory: bool) -> float:
        """Calculate total PPS impact from a completed combat"""
        if not self.current_combat:
            return 0.0
        
        combat = self.current_combat
        total_delta = 0.0
        
        # Base victory/defeat impact
        if victory:
            total_delta += 0.5
        else:
            total_delta -= 0.8
        
        # Health efficiency bonus/penalty
        if combat.health_efficiency >= 0.9:  # Lost <10% health
            total_delta += 0.3
        elif combat.health_efficiency <= 0.2:  # Lost >80% health
            total_delta -= 0.4
        
        # Turn efficiency
        if combat.turns_taken <= 5:  # Quick victory
            total_delta += 0.2
        elif combat.turns_taken >= 10:  # Prolonged combat
            total_delta -= 0.3
        
        # Strategic quality
        if combat.total_hands_played > 0:
            high_quality_ratio = combat.high_quality_hands / combat.total_hands_played
            if high_quality_ratio >= 0.3:  # 30%+ high quality hands
                total_delta += 0.25
        
        return total_delta
    
    def _update_pps(self, delta: float):
        """Update PPS and related statistics"""
        old_pps = self.pps
        self.pps += delta
        
        # Clamp PPS to reasonable bounds
        self.pps = max(-5.0, min(10.0, self.pps))
        
        # Update history
        self.pps_history.append(self.pps)
        
        # Calculate trend and volatility
        self._update_trend_analysis()
    
    def _update_trend_analysis(self):
        """Update performance trend and volatility metrics"""
        if len(self.pps_history) < 10:
            return
        
        # Calculate recent trend (last 10 PPS values)
        recent_values = list(self.pps_history)[-10:]
        if len(recent_values) >= 2:
            # Simple linear trend
            x = list(range(len(recent_values)))
            y = recent_values
            
            # Calculate slope (trend)
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            if n * sum_x2 - sum_x ** 2 != 0:
                self.recent_trend = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            
            # Calculate volatility (standard deviation of recent changes)
            changes = [y[i] - y[i-1] for i in range(1, len(y))]
            if changes:
                mean_change = sum(changes) / len(changes)
                variance = sum((c - mean_change) ** 2 for c in changes) / len(changes)
                self.volatility = variance ** 0.5
    
    def _record_event(self, event_type: EventType, pps_delta: float, details: Dict[str, Any], reasoning: str):
        """Record a performance event"""
        event = PerformanceEvent(
            event_type=event_type,
            timestamp=time.time(),
            pps_delta=pps_delta,
            details=details,
            reasoning=reasoning
        )
        self.event_history.append(event)
    
    def get_difficulty_tier(self) -> DifficultyTier:
        """Get current difficulty tier based on PPS"""
        if self.pps <= -2.0:
            return DifficultyTier.STRUGGLING
        elif self.pps <= -0.5:
            return DifficultyTier.LEARNING_1
        elif self.pps <= 1.0:
            return DifficultyTier.LEARNING_2
        elif self.pps <= 2.5:
            return DifficultyTier.THRIVING_1
        elif self.pps <= 4.0:
            return DifficultyTier.THRIVING_2
        else:
            return DifficultyTier.MASTERING
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        win_rate = self.total_victories / max(1, self.total_combats)
        
        return {
            "pps": self.pps,
            "difficulty_tier": self.get_difficulty_tier().name,
            "trend": self.recent_trend,
            "volatility": self.volatility,
            "total_combats": self.total_combats,
            "win_rate": win_rate,
            "session_duration": time.time() - self.session_start_time,
            "recent_events": len(self.event_history)
        }


class DynamicDifficultyAdjuster:
    """Main DDA system that applies adaptive modifiers based on player performance"""
    
    def __init__(self):
        self.performance_tracker = PlayerPerformanceTracker()
        self.current_modifiers = AdaptiveModifiers()
        self.narrative_events: List[str] = []
        
        # Tier-specific modifier configurations
        self.tier_configs = self._initialize_tier_configs()
        
        # Adaptation sensitivity settings
        self.adaptation_rate = 0.1  # How quickly to adjust (0.0 to 1.0)
        self.stability_threshold = 0.5  # Minimum change before adjusting
        
    def _initialize_tier_configs(self) -> Dict[DifficultyTier, AdaptiveModifiers]:
        """Initialize adaptive modifier configurations for each difficulty tier"""
        return {
            DifficultyTier.STRUGGLING: AdaptiveModifiers(
                enemy_health_modifier=0.75,  # 25% less enemy health
                enemy_damage_modifier=0.75,  # 25% less enemy damage
                enemy_block_modifier=0.8,
                shop_price_modifier=0.8,     # 20% cheaper items
                gold_reward_modifier=1.2,    # 20% more gold
                favor_rest_sites=True,
                narrative_blessing_active=True
            ),
            
            DifficultyTier.LEARNING_1: AdaptiveModifiers(
                enemy_health_modifier=0.9,   # 10% less enemy health
                enemy_damage_modifier=0.9,   # 10% less enemy damage
                enemy_block_modifier=0.95,
                shop_price_modifier=0.9,     # 10% cheaper items
                gold_reward_modifier=1.1,    # 10% more gold
                favor_rest_sites=True
            ),
            
            DifficultyTier.LEARNING_2: AdaptiveModifiers(
                # Standard difficulty - no major modifications
                enemy_health_modifier=1.0,
                enemy_damage_modifier=1.0,
                enemy_block_modifier=1.0,
                shop_price_modifier=1.0,
                gold_reward_modifier=1.0
            ),
            
            DifficultyTier.THRIVING_1: AdaptiveModifiers(
                enemy_health_modifier=1.1,   # 10% more enemy health
                enemy_damage_modifier=1.05,  # 5% more enemy damage
                enemy_block_modifier=1.1,
                shop_price_modifier=1.0,
                gold_reward_modifier=1.0,
                favor_treasure_sites=True
            ),
            
            DifficultyTier.THRIVING_2: AdaptiveModifiers(
                enemy_health_modifier=1.2,   # 20% more enemy health
                enemy_damage_modifier=1.15,  # 15% more enemy damage
                enemy_block_modifier=1.2,
                shop_price_modifier=1.1,     # 10% more expensive
                gold_reward_modifier=0.95,   # 5% less gold
                favor_treasure_sites=True,
                narrative_challenge_active=True
            ),
            
            DifficultyTier.MASTERING: AdaptiveModifiers(
                enemy_health_modifier=1.25,  # 25% more enemy health
                enemy_damage_modifier=1.25,  # 25% more enemy damage
                enemy_block_modifier=1.25,
                shop_price_modifier=1.2,     # 20% more expensive
                gold_reward_modifier=0.9,    # 10% less gold
                narrative_challenge_active=True
            )
        }
    
    def update_difficulty(self) -> bool:
        """Update difficulty based on current player performance"""
        current_tier = self.performance_tracker.get_difficulty_tier()
        target_modifiers = self.tier_configs[current_tier]
        
        # Check if significant change is needed
        if self._should_adjust_difficulty(target_modifiers):
            # Smoothly transition to new modifiers
            self._apply_modifier_transition(target_modifiers)
            
            # Generate narrative event if tier changed significantly
            self._generate_narrative_event(current_tier)
            
            return True
        
        return False
    
    def _should_adjust_difficulty(self, target_modifiers: AdaptiveModifiers) -> bool:
        """Determine if difficulty adjustment is warranted"""
        current = self.current_modifiers
        
        # Check key modifiers for significant differences
        health_diff = abs(current.enemy_health_modifier - target_modifiers.enemy_health_modifier)
        damage_diff = abs(current.enemy_damage_modifier - target_modifiers.enemy_damage_modifier)
        
        return (health_diff >= self.stability_threshold or 
                damage_diff >= self.stability_threshold)
    
    def _apply_modifier_transition(self, target_modifiers: AdaptiveModifiers):
        """Smoothly transition current modifiers toward target"""
        current = self.current_modifiers
        rate = self.adaptation_rate
        
        # Interpolate numeric modifiers
        current.enemy_health_modifier += (target_modifiers.enemy_health_modifier - current.enemy_health_modifier) * rate
        current.enemy_damage_modifier += (target_modifiers.enemy_damage_modifier - current.enemy_damage_modifier) * rate
        current.enemy_block_modifier += (target_modifiers.enemy_block_modifier - current.enemy_block_modifier) * rate
        current.shop_price_modifier += (target_modifiers.shop_price_modifier - current.shop_price_modifier) * rate
        current.gold_reward_modifier += (target_modifiers.gold_reward_modifier - current.gold_reward_modifier) * rate
        
        # Apply boolean flags directly
        current.favor_rest_sites = target_modifiers.favor_rest_sites
        current.favor_treasure_sites = target_modifiers.favor_treasure_sites
        current.narrative_blessing_active = target_modifiers.narrative_blessing_active
        current.narrative_challenge_active = target_modifiers.narrative_challenge_active
    
    def _generate_narrative_event(self, current_tier: DifficultyTier):
        """Generate narrative framing for difficulty changes"""
        narrative_messages = {
            DifficultyTier.STRUGGLING: [
                "An ancestor's spirit notices your struggle and offers a blessing.",
                "The spirits take pity and weaken your enemies' resolve.",
                "A gentle wind carries the wisdom of ancient protectors."
            ],
            DifficultyTier.LEARNING_1: [
                "The spirits recognize your growing strength.",
                "Your determination catches the attention of benevolent ancestors.",
                "The elements begin to respond to your improving focus."
            ],
            DifficultyTier.LEARNING_2: [
                "The cosmic balance shifts as you find your rhythm.",
                "Your skills stabilize, earning the spirits' neutral regard.",
                "The natural order acknowledges your steady progress."
            ],
            DifficultyTier.THRIVING_1: [
                "The spirits sense your growing power and send stronger trials.",
                "Your enemies, sensing your confidence, fight with renewed vigor.",
                "The elements themselves take notice of your prowess."
            ],
            DifficultyTier.THRIVING_2: [
                "The spirits, impressed by your skill, send greater challenges.",
                "Your reputation spreads - more dangerous foes seek you out.",
                "The cosmic forces align to test your true potential."
            ],
            DifficultyTier.MASTERING: [
                "The spirits unleash their full might to challenge a true master.",
                "Your enemies fight with desperate fury against your dominance.",
                "The universe itself conspires to test your legendary skills."
            ]
        }
        
        if current_tier in narrative_messages:
            import random
            message = random.choice(narrative_messages[current_tier])
            self.narrative_events.append(message)
    
    def apply_enemy_modifiers(self, enemy: Enemy) -> Enemy:
        """Apply current difficulty modifiers to an enemy"""
        modifiers = self.current_modifiers
        
        # Create a modified copy of the enemy
        modified_enemy = Enemy(
            id=enemy.id,
            name=enemy.name,
            max_health=int(enemy.max_health * modifiers.enemy_health_modifier),
            current_health=int(enemy.current_health * modifiers.enemy_health_modifier),
            block=int(enemy.block * modifiers.enemy_block_modifier),
            damage=int(enemy.damage * modifiers.enemy_damage_modifier),
            attack_pattern=enemy.attack_pattern.copy(),
            current_pattern_index=enemy.current_pattern_index,
            status_effects=enemy.status_effects.copy() if enemy.status_effects else []
        )
        
        return modified_enemy
    
    def get_shop_price_modifier(self) -> float:
        """Get current shop price modifier"""
        return self.current_modifiers.shop_price_modifier
    
    def get_gold_reward_modifier(self) -> float:
        """Get current gold reward modifier"""
        return self.current_modifiers.gold_reward_modifier
    
    def should_favor_rest_sites(self) -> bool:
        """Check if map generation should favor rest sites"""
        return self.current_modifiers.favor_rest_sites
    
    def should_favor_treasure_sites(self) -> bool:
        """Check if map generation should favor treasure sites"""
        return self.current_modifiers.favor_treasure_sites
    
    def get_recent_narrative_events(self, count: int = 3) -> List[str]:
        """Get recent narrative events for display"""
        return self.narrative_events[-count:] if self.narrative_events else []
    
    def get_dda_status(self) -> Dict[str, Any]:
        """Get comprehensive DDA system status"""
        return {
            "performance": self.performance_tracker.get_performance_summary(),
            "current_tier": self.performance_tracker.get_difficulty_tier().name,
            "modifiers": self.current_modifiers.to_dict(),
            "narrative_events": self.get_recent_narrative_events(),
            "adaptation_settings": {
                "adaptation_rate": self.adaptation_rate,
                "stability_threshold": self.stability_threshold
            }
        }
    
    def export_session_data(self) -> Dict[str, Any]:
        """Export complete session data for analysis"""
        return {
            "timestamp": time.time(),
            "performance_tracker": {
                "pps": self.performance_tracker.pps,
                "pps_history": list(self.performance_tracker.pps_history),
                "combat_history": [asdict(combat) for combat in self.performance_tracker.combat_history],
                "event_history": [asdict(event) for event in self.performance_tracker.event_history],
                "session_stats": self.performance_tracker.get_performance_summary()
            },
            "dda_status": self.get_dda_status(),
            "tier_progression": [
                (i, self.performance_tracker.get_difficulty_tier().value) 
                for i in range(len(self.performance_tracker.pps_history))
            ]
        }


# Theoretical ML Extension for Academic Thesis
@dataclass
class ProposedMLComponent:
    """
    Theoretical LSTM-based Predictive Layer for Academic Discussion
    
    This component is proposed for future work and demonstrates understanding
    of advanced ML approaches without requiring full implementation.
    """
    
    # Network Architecture (Theoretical)
    lstm_layers: int = 2
    hidden_units: int = 64
    input_features: int = 20  # Player action sequences, game state
    output_classes: int = 3   # Predict: frustration, flow, boredom
    
    # Training Data Requirements (Theoretical)
    min_training_sequences: int = 1000
    sequence_length: int = 50  # Last 50 player actions
    
    # Integration Points (Theoretical) 
    prediction_frequency: str = "every_5_turns"
    confidence_threshold: float = 0.8
    
    def theoretical_integration_notes(self) -> str:
        """Academic notes on how this would integrate with the rule-based system"""
        return """
        Theoretical ML Integration Framework:
        
        1. Data Collection:
           - Player action sequences (card choices, timing, patterns)
           - Game state vectors (health, resources, enemy type)
           - Labeled outcomes (player engagement surveys, session completion rates)
        
        2. LSTM Architecture:
           - Input: Sequence of (action_vector, game_state) tuples
           - Hidden: 2 LSTM layers with 64 units each
           - Output: Softmax over (frustration, flow, boredom) states
        
        3. Proactive Adjustment:
           - When frustration prediction > 0.8: Trigger rule-based assistance
           - When boredom prediction > 0.8: Increase challenge via rule engine
           - Confidence < 0.8: Rely on reactive rule-based system
        
        4. Research Value:
           - Hybrid approach combines interpretable rules with predictive ML
           - Allows for proactive vs reactive difficulty adjustment comparison
           - Enables study of player engagement prediction accuracy
        
        5. Implementation Phases:
           - Phase 1: Rule-based system (current implementation)
           - Phase 2: Data collection during rule-based operation
           - Phase 3: LSTM training on collected data
           - Phase 4: Hybrid system with A/B testing framework
        """


# Global DDA instance for game integration
global_dda_system: Optional[DynamicDifficultyAdjuster] = None


def get_dda_system() -> DynamicDifficultyAdjuster:
    """Get or create the global DDA system instance"""
    global global_dda_system
    if global_dda_system is None:
        global_dda_system = DynamicDifficultyAdjuster()
    return global_dda_system


def reset_dda_system():
    """Reset the global DDA system (for new game sessions)"""
    global global_dda_system
    global_dda_system = None