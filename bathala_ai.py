"""
Main AI Controller for Bathala-like Card Combat Game
Coordinates all AI systems and provides intelligent decision-making for creature opponents
"""

import random
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from enhanced_card_system import Card, HandEvaluation, EnhancedHandEvaluator, Element, Suit, CardDeck, create_themed_deck
from ai_personality import AIPersonalityConfig, get_personality_for_creature, AIPersonalityType
from hand_strategy import HandStrategy, GameContext, PlayerAction, HandCombination


class ActionType(Enum):
    PLAY_HAND = "play_hand"
    END_TURN = "end_turn"
    SPECIAL_ABILITY = "special_ability"


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
    cards: List[Card]
    evaluation: Optional[HandEvaluation] = None
    confidence: float = 0.5
    reasoning: str = ""
    estimated_damage: int = 0
    risk_level: float = 0.5
    special_effects: List[str] = None
    bluff_factor: float = 0.0
    
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
        self.hand_strategy = HandStrategy(self.personality)
        self.difficulty_modifier = self._calculate_difficulty_modifier(difficulty_level)
        self.available_cards = self._generate_ai_cards()
        self.statistics = AIStatistics(personality_type=self.personality.name)
        
        # Combat memory and learning
        self.combat_memory: List[Dict] = []
        self.player_patterns: Dict[str, int] = {}
        
    def make_decision(self, game_context: GameContext) -> AIDecision:
        """Main decision-making method called each AI turn"""
        self.statistics.turns_played += 1
        
        # Find best hand combination
        best_hand = self.hand_strategy.find_best_hand(self.available_cards, game_context)
        
        if not best_hand:
            return self._create_end_turn_decision("No viable hands available")
        
        # Check if AI should use special ability instead
        special_decision = self._consider_special_ability(game_context, best_hand)
        if special_decision:
            return special_decision
        
        # Apply difficulty modifier to the hand
        modified_evaluation = self._apply_difficulty_modifier(best_hand.evaluation)
        
        # Update statistics
        self._update_statistics(best_hand, modified_evaluation)
        
        # Remove used cards from available pool
        self._remove_used_cards(best_hand.cards)
        
        # Determine if this is a bluff
        bluff_factor = self._calculate_bluff_factor(best_hand, game_context)
        
        # Create decision with enhanced reasoning
        decision = AIDecision(
            action=ActionType.PLAY_HAND,
            cards=best_hand.cards.copy(),
            evaluation=modified_evaluation,
            confidence=best_hand.confidence,
            reasoning=self._enhance_reasoning(best_hand.reasoning, game_context),
            estimated_damage=modified_evaluation.total_value,
            risk_level=best_hand.risk_level,
            special_effects=modified_evaluation.special_effects.copy(),
            bluff_factor=bluff_factor
        )
        
        # Store decision in combat memory
        self._record_decision(decision, game_context)
        
        return decision
    
    def _generate_ai_cards(self) -> List[Card]:
        """Generate AI's starting cards based on creature type and difficulty"""
        card_count = self._get_card_count_for_creature()
        
        # Create themed deck based on creature
        if self.enemy.name in ["Kapre", "Dwende", "Duwende Chief"]:
            deck = create_themed_deck("earth_creature")
        elif self.enemy.name in ["Manananggal", "Tikbalang"]:
            deck = create_themed_deck("air_creature")
        elif self.enemy.name in ["Aswang", "Sigbin"]:
            deck = create_themed_deck("fire_creature")
        elif self.enemy.name == "Bakunawa":
            deck = create_themed_deck("chaos_creature")  # Boss gets mixed elements
        else:
            deck = create_themed_deck("balanced")
        
        deck.shuffle()
        cards = deck.draw(card_count)
        
        # Assign unique IDs
        for i, card in enumerate(cards):
            card.id = f"ai_{self.enemy.name}_{i}"
            card.playable = True
        
        return cards
    
    def _get_card_count_for_creature(self) -> int:
        """Get number of cards based on creature type and difficulty"""
        base_count = 7 + self.difficulty_level
        
        # Boss enemies get more cards
        if self.enemy.max_health > 80:
            return base_count + 4
        # Elite enemies get slightly more
        elif self.enemy.max_health > 40:
            return base_count + 2
        
        return base_count
    
    def _calculate_difficulty_modifier(self, level: int) -> float:
        """Calculate difficulty modifier based on level (1-10+)"""
        # Level 1: 0.7x (easier)
        # Level 5: 1.0x (normal)
        # Level 10: 1.5x (much harder)
        return max(0.6, min(2.0, 0.6 + (level * 0.09)))
    
    def _apply_difficulty_modifier(self, evaluation: HandEvaluation) -> HandEvaluation:
        """Apply difficulty scaling to hand evaluation"""
        modifier = self.difficulty_modifier
        
        return HandEvaluation(
            hand_type=evaluation.hand_type,
            base_value=evaluation.base_value,
            elemental_bonus=int(evaluation.elemental_bonus * modifier),
            total_value=int(evaluation.total_value * modifier),
            description=evaluation.description + (f" (Enhanced x{modifier:.1f})" if modifier > 1.0 else ""),
            confidence=evaluation.confidence,
            special_effects=evaluation.special_effects.copy()
        )
    
    def _consider_special_ability(self, context: GameContext, best_hand: HandCombination) -> Optional[AIDecision]:
        """Consider using special abilities instead of normal attack"""
        current_action = self.enemy.attack_pattern[self.enemy.current_pattern_index]
        
        # Only use special abilities for non-attack patterns
        if current_action == "attack":
            return None
        
        # Evaluate special ability value
        special_value = self._evaluate_special_ability(current_action, context)
        
        # Compare with best hand value
        if special_value > best_hand.strategic_value * 1.3:
            self.statistics.special_abilities_used += 1
            return AIDecision(
                action=ActionType.SPECIAL_ABILITY,
                cards=[],
                confidence=0.8,
                reasoning=f"Using {current_action} special ability instead of attack",
                estimated_damage=0,
                special_effects=[self._get_special_ability_description(current_action)]
            )
        
        return None
    
    def _evaluate_special_ability(self, ability: str, context: GameContext) -> float:
        """Evaluate the strategic value of using a special ability"""
        ability_values = {
            # Defensive abilities
            "defend": 30 if context.get_ai_health_ratio() < 0.5 else 15,
            "smoke": 25 if context.get_ai_health_ratio() < 0.6 else 12,
            "block": 35 if context.get_ai_health_ratio() < 0.4 else 18,
            
            # Buff abilities
            "buff": 40 if context.turn_number < 5 else 20,
            "command": 35 if context.turn_number < 6 else 15,
            "power_up": 30 if context.turn_number < 7 else 10,
            
            # Disruptive abilities
            "confuse": 25 if context.cards_remaining > 5 else 10,
            "mischief": 20 if context.cards_remaining > 4 else 8,
            "deceive": 30 if context.get_player_health_ratio() > 0.6 else 15,
            "invisibility": 35,
            
            # Transformation abilities
            "shapeshift": 25,
            "split": 40 if context.get_ai_health_ratio() < 0.3 else 20,
            "flight": 30,
            
            # Boss abilities
            "eclipse": 45 if context.get_player_health_ratio() < 0.5 else 25,
            "devour": 50 if context.cards_remaining > 6 else 30,
            "summon": 35,
        }
        
        return ability_values.get(ability, 25)
    
    def _get_special_ability_description(self, ability: str) -> str:
        """Get description of special ability effects"""
        descriptions = {
            "confuse": "😵 Confuse: Player discards a random card",
            "smoke": "💨 Smoke Screen: +8 block, reduce player accuracy",
            "mischief": "😈 Mischief: Shuffles player's hand",
            "defend": "🛡️ Defensive Stance: +10 block",
            "buff": "💪 Power Up: +5 damage next turn",
            "command": "👑 Command: Summons ally creature",
            "invisibility": "👻 Invisibility: Next attack ignores block",
            "deceive": "🎭 Deceive: Shows false intent next turn",
            "flight": "🦅 Flight: Immune to ground attacks",
            "split": "✂️ Split: Creates copy with half health",
            "shapeshift": "🔄 Shapeshift: Changes element affinity",
            "eclipse": "🌑 Eclipse: Blocks all healing this turn",
            "devour": "🦈 Devour: Steals player cards and gains health",
        }
        return descriptions.get(ability, f"⚡ {ability.title()}: Special ability activated")
    
    def _calculate_bluff_factor(self, best_hand: HandCombination, context: GameContext) -> float:
        """Calculate if this play contains bluffing elements"""
        bluff = 0.0
        
        # Check personality bluff tendency
        if random.random() < self.personality.bluff_chance:
            # Weak hand with aggressive play = bluff
            if best_hand.evaluation.total_value < 20 and best_hand.strategic_value > 30:
                bluff = 0.7
            # High confidence on mediocre hand = bluff
            elif best_hand.confidence > 0.8 and best_hand.evaluation.total_value < 25:
                bluff = 0.5
        
        # Desperation bluffs
        if context.is_desperate_situation() and best_hand.evaluation.total_value < 15:
            bluff = max(bluff, 0.6)
        
        # Track bluff success/failure
        if bluff > 0.3:
            if best_hand.evaluation.total_value > 20:
                self.statistics.successful_bluffs += 1
            else:
                self.statistics.failed_bluffs += 1
        
        return bluff
    
    def _enhance_reasoning(self, base_reasoning: str, context: GameContext) -> str:
        """Enhance reasoning with creature-specific context and flavor"""
        enhancements = [base_reasoning]
        
        # Add creature-specific flavor text
        creature_flavor = {
            "Tikbalang": "The trickster spirit plays unpredictably",
            "Kapre": "The tree spirit draws power from nature's elements",
            "Manananggal": "The flying terror strikes with supernatural precision",
            "Bakunawa": "The dragon's ancient wisdom guides its strategy",
            "Aswang": "The shapeshifter hunts with primal cunning",
            "Dwende": "The earth spirit plays defensively",
            "Sigbin": "The shadow creature moves with deadly stealth",
            "Tiyanak": "The deceptive spirit lures with false innocence"
        }
        
        if self.enemy.name in creature_flavor:
            enhancements.append(creature_flavor[self.enemy.name])
        
        # Add tactical context
        if context.is_desperate_situation():
            enhancements.append("Desperation drives bold tactics")
        elif context.is_winning_position():
            enhancements.append("Maintaining dominance with calculated aggression")
        elif context.get_player_health_ratio() < 0.4:
            enhancements.append("Victory is within reach")
        
        # Add difficulty context
        if self.difficulty_level >= 7:
            enhancements.append("Master-level strategic thinking")
        elif self.difficulty_level >= 5:
            enhancements.append("Advanced tactical analysis")
        
        return "; ".join(enhancements)
    
    def _create_end_turn_decision(self, reason: str) -> AIDecision:
        """Create a decision to end turn"""
        return AIDecision(
            action=ActionType.END_TURN,
            cards=[],
            confidence=0.3,
            reasoning=reason,
            estimated_damage=0
        )
    
    def _update_statistics(self, hand_combination: HandCombination, modified_evaluation: HandEvaluation):
        """Update AI performance statistics"""
        self.statistics.hands_played += 1
        self.statistics.total_damage_dealt += modified_evaluation.total_value
        self.statistics.average_hand_value = self.statistics.total_damage_dealt / max(1, self.statistics.hands_played)
        
        # Track elemental combos
        elements = set(card.element for card in hand_combination.cards)
        if len(elements) == 1 and len(hand_combination.cards) > 2:
            self.statistics.elemental_combos_played += 1
        
        # Update adaptation level
        self.statistics.adaptation_level = min(100.0, 
            len(self.hand_strategy.player_behavior_memory) * self.personality.adaptation_rate * 5)
    
    def _remove_used_cards(self, used_cards: List[Card]):
        """Remove used cards from available pool"""
        for used_card in used_cards:
            self.available_cards = [card for card in self.available_cards if card.id != used_card.id]
    
    def _record_decision(self, decision: AIDecision, context: GameContext):
        """Record decision in combat memory for analysis"""
        memory_entry = {
            "turn": self.statistics.turns_played,
            "action": decision.action.value,
            "damage": decision.estimated_damage,
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
    
    def record_player_action(self, action: PlayerAction):
        """Record player action for adaptive learning"""
        self.hand_strategy.record_player_action(action)
        
        # Update player pattern tracking
        for card in action.cards_played:
            element_key = card.element.value
            self.player_patterns[element_key] = self.player_patterns.get(element_key, 0) + 1
        
        # Update adaptation level
        self.statistics.adaptation_level = min(100.0,
            len(self.hand_strategy.player_behavior_memory) * self.personality.adaptation_rate * 5)
    
    def refill_cards(self, count: int = 3):
        """Add new cards to AI's hand"""
        # Generate new cards with same themed distribution
        if self.enemy.name in ["Kapre", "Dwende", "Duwende Chief"]:
            new_deck = create_themed_deck("earth_creature")
        elif self.enemy.name in ["Manananggal", "Tikbalang"]:
            new_deck = create_themed_deck("air_creature")
        elif self.enemy.name in ["Aswang", "Sigbin"]:
            new_deck = create_themed_deck("fire_creature")
        elif self.enemy.name == "Bakunawa":
            new_deck = create_themed_deck("chaos_creature")
        else:
            new_deck = create_themed_deck("balanced")
        
        new_deck.shuffle()
        new_cards = new_deck.draw(count)
        
        # Assign unique IDs
        for i, card in enumerate(new_cards):
            card.id = f"ai_{self.enemy.name}_refill_{len(self.available_cards) + i}"
            card.playable = True
        
        self.available_cards.extend(new_cards)
    
    def get_ai_status(self) -> Dict[str, Any]:
        """Get comprehensive AI status and statistics"""
        return {
            "creature": self.enemy.name,
            "personality": self.personality.name,
            "difficulty_level": self.difficulty_level,
            "difficulty_modifier": self.difficulty_modifier,
            "cards_remaining": len(self.available_cards),
            "statistics": {
                "turns_played": self.statistics.turns_played,
                "hands_played": self.statistics.hands_played,
                "total_damage_dealt": self.statistics.total_damage_dealt,
                "average_hand_value": self.statistics.average_hand_value,
                "adaptation_level": self.statistics.adaptation_level,
                "successful_bluffs": self.statistics.successful_bluffs,
                "failed_bluffs": self.statistics.failed_bluffs,
                "special_abilities_used": self.statistics.special_abilities_used,
                "elemental_combos": self.statistics.elemental_combos_played,
            },
            "personality_config": {
                "risk_tolerance": self.personality.risk_tolerance,
                "damage_weight": self.personality.damage_weight,
                "elemental_weight": self.personality.elemental_weight,
                "bluff_chance": self.personality.bluff_chance,
                "adaptation_rate": self.personality.adaptation_rate,
            },
            "learning_progress": self.hand_strategy.get_adaptation_summary(),
            "player_patterns": dict(self.player_patterns),
        }
    
    def simulate_decision(self, context: GameContext) -> AIDecision:
        """Simulate a decision without actually executing it"""
        best_hand = self.hand_strategy.find_best_hand(self.available_cards, context)
        
        if not best_hand:
            return self._create_end_turn_decision("No viable hands in simulation")
        
        modified_evaluation = self._apply_difficulty_modifier(best_hand.evaluation)
        
        return AIDecision(
            action=ActionType.PLAY_HAND,
            cards=best_hand.cards.copy(),
            evaluation=modified_evaluation,
            confidence=best_hand.confidence,
            reasoning=f"[SIMULATION] {best_hand.reasoning}",
            estimated_damage=modified_evaluation.total_value,
            risk_level=best_hand.risk_level,
            special_effects=modified_evaluation.special_effects.copy()
        )
    
    def override_personality(self, new_personality: AIPersonalityConfig):
        """Override AI personality for testing or special scenarios"""
        self.personality = new_personality
        self.hand_strategy = HandStrategy(new_personality)
        self.statistics.personality_type = new_personality.name
    
    def get_available_cards(self) -> List[Card]:
        """Get copy of available cards (for debugging/display)"""
        return self.available_cards.copy()
    
    def advance_attack_pattern(self):
        """Advance to next attack in pattern"""
        self.enemy.current_pattern_index = (self.enemy.current_pattern_index + 1) % len(self.enemy.attack_pattern)


if __name__ == "__main__":
    # Test the Bathala AI system
    print("🐲 Bathala AI System Test 🐲\n")
    
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
            cards_remaining=len(ai.available_cards)
        )
        
        # Make decision
        decision = ai.make_decision(context)
        
        print(f"   🃏 Cards Available: {len(ai.available_cards)}")
        print(f"   🎯 Decision: {decision.action.value}")
        if decision.cards:
            print(f"   🖐️ Played: {[str(card) for card in decision.cards]}")
        print(f"   💥 Estimated Damage: {decision.estimated_damage}")
        print(f"   🎲 Confidence: {decision.confidence:.1%}")
        print(f"   🎭 Reasoning: {decision.reasoning}")
        if decision.special_effects:
            print(f"   ✨ Effects: {', '.join(decision.special_effects)}")
        print()
    
    # Test adaptive learning
    print("🧠 Testing Adaptive Learning:")
    adaptive_ai = BathalaAI(test_enemy, 5)
    
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
    print(f"   Memory: {status['learning_progress']['memory_usage']}")