"""
Hand Strategy Engine for Bathala-like AI
Evaluates possible card combinations and selects optimal plays
"""

import random
import itertools
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import Counter

from enhanced_card_system import Card, HandEvaluation, EnhancedHandEvaluator, Element, HandType
from ai_personality import AIPersonalityConfig


@dataclass
class GameContext:
    """Current game state context for strategic decisions"""
    player_health: int
    player_max_health: int
    player_block: int
    ai_health: int
    ai_max_health: int
    ai_block: int
    turn_number: int
    cards_remaining: int
    
    def get_player_health_ratio(self) -> float:
        return self.player_health / max(1, self.player_max_health)
    
    def get_ai_health_ratio(self) -> float:
        return self.ai_health / max(1, self.ai_max_health)
    
    def is_desperate_situation(self) -> bool:
        return self.get_ai_health_ratio() < 0.3
    
    def is_winning_position(self) -> bool:
        return self.get_player_health_ratio() < 0.3 and self.get_ai_health_ratio() > 0.5


@dataclass
class HandCombination:
    """Represents a potential play with evaluation and strategic analysis"""
    cards: List[Card]
    evaluation: HandEvaluation
    strategic_value: float
    confidence: float
    reasoning: str
    risk_level: float = 0.5  # 0 = safe, 1 = very risky
    elemental_synergy: float = 0.0
    efficiency: float = 0.0  # damage per card
    
    def get_display_string(self) -> str:
        """Get human-readable representation"""
        card_str = " ".join(str(card) for card in self.cards)
        return f"{card_str} ({self.evaluation.total_value} dmg, {self.confidence:.1%} conf)"


@dataclass 
class PlayerAction:
    """Record of player action for AI learning"""
    cards_played: List[Card]
    evaluation: HandEvaluation
    turn_number: int
    game_context: GameContext
    success: bool = True  # Whether this action was effective


class HandStrategy:
    """Strategic hand evaluation and selection engine"""
    
    def __init__(self, personality: AIPersonalityConfig):
        self.personality = personality
        self.player_behavior_memory: List[PlayerAction] = []
        self.learned_patterns: Dict[str, float] = {}
        
    def find_best_hand(self, available_cards: List[Card], context: GameContext) -> Optional[HandCombination]:
        """Find the best hand combination from available cards"""
        if not available_cards:
            return None
        
        # Generate all possible combinations
        all_combinations = self._generate_all_combinations(available_cards)
        
        # Evaluate each combination
        evaluated_combinations = []
        for cards in all_combinations:
            combination = self._evaluate_combination(cards, context)
            if combination.evaluation.total_value >= self.personality.min_hand_threshold:
                evaluated_combinations.append(combination)
        
        if not evaluated_combinations:
            # If no combinations meet threshold, return best available or pass
            if all_combinations:
                best_available = max(
                    [self._evaluate_combination(cards, context) for cards in all_combinations],
                    key=lambda x: x.strategic_value
                )
                if best_available.evaluation.total_value >= 5:  # Minimum viable play
                    return best_available
            return None
        
        # Apply personality-based selection
        return self._select_best_combination(evaluated_combinations, context)
    
    def _generate_all_combinations(self, cards: List[Card]) -> List[List[Card]]:
        """Generate all possible card combinations (1-5 cards)"""
        combinations = []
        
        for r in range(1, min(6, len(cards) + 1)):
            for combo in itertools.combinations(cards, r):
                combinations.append(list(combo))
        
        return combinations
    
    def _evaluate_combination(self, cards: List[Card], context: GameContext) -> HandCombination:
        """Evaluate a specific card combination"""
        evaluation = EnhancedHandEvaluator.evaluate_hand(cards)
        strategic_value = self._calculate_strategic_value(evaluation, cards, context)
        confidence = self._calculate_confidence(evaluation, cards, context)
        reasoning = self._generate_reasoning(evaluation, cards, context, strategic_value)
        risk_level = self._calculate_risk_level(evaluation, cards, context)
        elemental_synergy = self._calculate_elemental_synergy(cards)
        efficiency = evaluation.total_value / len(cards) if cards else 0
        
        return HandCombination(
            cards=cards,
            evaluation=evaluation,
            strategic_value=strategic_value,
            confidence=confidence,
            reasoning=reasoning,
            risk_level=risk_level,
            elemental_synergy=elemental_synergy,
            efficiency=efficiency
        )
    
    def _calculate_strategic_value(self, evaluation: HandEvaluation, cards: List[Card], context: GameContext) -> float:
        """Calculate strategic value based on personality and game context"""
        value = 0.0
        
        # Base damage value
        value += evaluation.total_value * self.personality.damage_weight
        
        # Elemental synergy bonus
        elemental_value = self._calculate_elemental_synergy(cards)
        value += elemental_value * self.personality.elemental_weight
        
        # Hand type bonus
        hand_type_bonus = self._get_hand_type_bonus(evaluation.hand_type)
        value += hand_type_bonus * self.personality.hand_type_weight
        
        # Apply context modifiers
        value = self._apply_context_modifiers(value, evaluation, context)
        
        # Apply personality-specific modifiers
        value = self._apply_personality_modifiers(value, evaluation, cards, context)
        
        # Apply learned behavior adjustments
        value = self._apply_adaptive_adjustments(value, evaluation, cards, context)
        
        return max(0.0, value)
    
    def _calculate_elemental_synergy(self, cards: List[Card]) -> float:
        """Calculate elemental synergy value"""
        if not cards:
            return 0.0
        
        element_counts = Counter(card.element for card in cards)
        synergy = 0.0
        
        # Fire synergy: more fire cards = more damage
        fire_count = element_counts.get(Element.FIRE, 0)
        synergy += fire_count * 3
        
        # Earth synergy: bonus for 2+ earth cards
        earth_count = element_counts.get(Element.EARTH, 0)
        if earth_count >= 2:
            synergy += earth_count * 2 + 3
        
        # Air synergy: massive bonus for all air
        air_count = element_counts.get(Element.AIR, 0)
        if air_count == len(cards) and len(cards) > 1:
            synergy += 20
        
        # Water synergy: defensive value
        water_count = element_counts.get(Element.WATER, 0)
        synergy += water_count * 2
        
        # Pure element bonus
        unique_elements = len([count for count in element_counts.values() if count > 0])
        if unique_elements == 1 and len(cards) > 2:
            synergy += 10
        
        # Mixed element penalty for some personalities
        if unique_elements > 2 and self.personality.name == "Elemental":
            synergy -= 8
        
        return synergy
    
    def _get_hand_type_bonus(self, hand_type: HandType) -> float:
        """Get bonus value for different hand types"""
        bonuses = {
            HandType.HIGH_CARD: 0,
            HandType.PAIR: 5,
            HandType.TWO_PAIR: 10,
            HandType.THREE_OF_A_KIND: 15,
            HandType.STRAIGHT: 20,
            HandType.FLUSH: 20,
            HandType.FULL_HOUSE: 30,
            HandType.FOUR_OF_A_KIND: 40,
            HandType.STRAIGHT_FLUSH: 50,
            HandType.ROYAL_FLUSH: 60,
        }
        return bonuses.get(hand_type, 0)
    
    def _apply_context_modifiers(self, base_value: float, evaluation: HandEvaluation, context: GameContext) -> float:
        """Apply game context modifiers"""
        value = base_value
        
        # Health-based urgency
        ai_health_ratio = context.get_ai_health_ratio()
        if ai_health_ratio < 0.3:
            # Low health: prioritize high damage
            value *= 1.4
        elif ai_health_ratio > 0.8:
            # High health: can afford to be strategic
            value *= 0.9
        
        # Player health consideration
        player_health_ratio = context.get_player_health_ratio()
        if player_health_ratio < 0.3 and evaluation.total_value > 25:
            # Player low on health, go for kill
            value *= 1.6
        
        # Late game modifier
        if context.turn_number > 8:
            if evaluation.total_value > 20:
                value *= 1.3
        
        # Desperation bonus
        if context.is_desperate_situation():
            value *= 1.5
        
        # Winning position bonus
        if context.is_winning_position():
            value *= 1.2
        
        return value
    
    def _apply_personality_modifiers(self, base_value: float, evaluation: HandEvaluation, cards: List[Card], context: GameContext) -> float:
        """Apply personality-specific modifiers"""
        value = base_value
        
        if self.personality.name == "Cautious":
            # Prefer defensive plays when health is low
            if context.get_ai_health_ratio() < 0.5:
                water_cards = sum(1 for card in cards if card.element == Element.WATER)
                value += water_cards * 5
            # Penalty for risky plays
            if evaluation.total_value > 40:
                value *= 0.8
        
        elif self.personality.name == "Aggressive":
            # Prefer high-damage risky plays
            if evaluation.total_value > 30:
                value *= 1.5
            # Penalty for low-damage safe plays
            if evaluation.total_value < 15:
                value *= 0.6
            # Bonus for fire elements
            fire_cards = sum(1 for card in cards if card.element == Element.FIRE)
            value += fire_cards * 3
        
        elif self.personality.name == "Calculating":
            # Prefer mathematically optimal efficiency
            efficiency = evaluation.total_value / len(cards) if cards else 0
            if efficiency > 8:
                value *= 1.3
            # Bonus for consistent plays
            if 15 <= evaluation.total_value <= 35:
                value *= 1.1
        
        elif self.personality.name == "Elemental":
            # Heavy bonus for elemental synergies
            dominant_element = self._get_dominant_element(cards)
            if dominant_element in self.personality.preferred_elements:
                value *= 1.4
            # Massive bonus for pure element hands
            unique_elements = len(set(card.element for card in cards))
            if unique_elements == 1:
                value *= 1.6
        
        elif self.personality.name == "Chaotic":
            # Add randomness and prefer unusual plays
            value += (random.random() - 0.5) * 15
            # Prefer extreme hand sizes
            if len(cards) == 1 or len(cards) >= 4:
                value *= 1.3
            # Random element bonus
            if random.random() < 0.3:
                value *= 1.5
        
        elif self.personality.name == "Adaptive":
            # Adjust based on learned player behavior
            value = self._apply_adaptive_behavior(value, evaluation, cards)
        
        return max(0.0, value)
    
    def _apply_adaptive_adjustments(self, base_value: float, evaluation: HandEvaluation, cards: List[Card], context: GameContext) -> float:
        """Apply learned behavior adjustments"""
        if self.personality.adaptation_rate == 0 or not self.player_behavior_memory:
            return base_value
        
        value = base_value
        
        # Analyze recent player patterns
        recent_actions = self.player_behavior_memory[-5:] if len(self.player_behavior_memory) >= 5 else self.player_behavior_memory
        
        if recent_actions:
            # Player average damage
            avg_player_damage = sum(action.evaluation.total_value for action in recent_actions) / len(recent_actions)
            
            # If player plays aggressively, AI should be more defensive
            if avg_player_damage > 25:
                water_cards = sum(1 for card in cards if card.element == Element.WATER)
                value += water_cards * 3
            
            # If player plays defensively, AI should be more aggressive
            elif avg_player_damage < 15:
                if evaluation.total_value > 20:
                    value *= 1.2
            
            # Analyze player element preferences
            player_elements = [card.element for action in recent_actions for card in action.cards_played]
            if player_elements:
                element_counter = Counter(player_elements)
                most_used_element = element_counter.most_common(1)[0][0]
                
                # Counter player's preferred element
                if most_used_element == Element.FIRE:
                    water_cards = sum(1 for card in cards if card.element == Element.WATER)
                    value += water_cards * 2
                elif most_used_element == Element.WATER:
                    earth_cards = sum(1 for card in cards if card.element == Element.EARTH)
                    value += earth_cards * 2
        
        return value
    
    def _apply_adaptive_behavior(self, base_value: float, evaluation: HandEvaluation, cards: List[Card]) -> float:
        """Apply adaptive personality behavior"""
        # This could be enhanced with machine learning in the future
        value = base_value
        
        # Basic adaptation: counter observed player patterns
        if len(self.player_behavior_memory) > 3:
            recent_avg_damage = sum(action.evaluation.total_value for action in self.player_behavior_memory[-3:]) / 3
            
            if recent_avg_damage > 30:
                # Player is aggressive, be more defensive
                value *= 0.9
            elif recent_avg_damage < 15:
                # Player is defensive, be more aggressive
                value *= 1.1
        
        return value
    
    def _calculate_confidence(self, evaluation: HandEvaluation, cards: List[Card], context: GameContext) -> float:
        """Calculate confidence in the play (0-1)"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for stronger hands
        if evaluation.total_value > 35:
            confidence += 0.3
        elif evaluation.total_value > 20:
            confidence += 0.2
        elif evaluation.total_value > 12:
            confidence += 0.1
        
        # Elemental synergy confidence
        elemental_value = self._calculate_elemental_synergy(cards)
        confidence += min(0.2, elemental_value / 40)
        
        # Personality-based confidence
        confidence += (1 - self.personality.randomness_weight) * 0.2
        
        # Context-based confidence
        if context.is_desperate_situation() and evaluation.total_value > 25:
            confidence += 0.3  # High confidence in strong plays when desperate
        
        # Hand type confidence
        rare_hands = [HandType.FULL_HOUSE, HandType.FOUR_OF_A_KIND, HandType.STRAIGHT_FLUSH, HandType.ROYAL_FLUSH]
        if evaluation.hand_type in rare_hands:
            confidence += 0.2
        
        # Experience-based confidence (more games = more confidence)
        experience_bonus = min(0.1, len(self.player_behavior_memory) / 100)
        confidence += experience_bonus
        
        return max(0.1, min(1.0, confidence))
    
    def _calculate_risk_level(self, evaluation: HandEvaluation, cards: List[Card], context: GameContext) -> float:
        """Calculate risk level of the play (0-1)"""
        risk = 0.5  # Base risk
        
        # High-value plays are riskier
        if evaluation.total_value > 40:
            risk += 0.3
        elif evaluation.total_value < 10:
            risk += 0.2  # Very low plays are also risky (might be ineffective)
        
        # Elemental risk
        unique_elements = len(set(card.element for card in cards))
        if unique_elements > 2:
            risk += 0.1  # Mixed elements can be unpredictable
        
        # Context risk
        if context.is_desperate_situation():
            risk -= 0.2  # Less risky when you have to act
        
        # Hand size risk
        if len(cards) >= 4:
            risk += 0.1  # Using many cards is riskier
        
        return max(0.0, min(1.0, risk))
    
    def _generate_reasoning(self, evaluation: HandEvaluation, cards: List[Card], context: GameContext, strategic_value: float) -> str:
        """Generate human-readable reasoning for the play"""
        reasons = []
        
        # Hand type reasoning
        if evaluation.hand_type != HandType.HIGH_CARD:
            reasons.append(f"Playing {evaluation.hand_type.value.replace('_', ' ')} for {evaluation.base_value} base damage")
        
        # Elemental reasoning
        if evaluation.elemental_bonus > 0:
            dominant_element = self._get_dominant_element(cards)
            reasons.append(f"{dominant_element.value} synergy adds {evaluation.elemental_bonus} damage")
        
        # Strategic reasoning
        if context.is_desperate_situation():
            reasons.append("Desperate situation requires aggressive play")
        elif context.is_winning_position():
            reasons.append("Maintaining pressure in winning position")
        elif strategic_value > 40:
            reasons.append("High strategic value justifies this play")
        
        # Personality reasoning
        reasons.append(f"{self.personality.name} AI strategy")
        
        # Context-specific reasoning
        if context.get_player_health_ratio() < 0.4:
            reasons.append("Player is vulnerable, going for finish")
        elif context.turn_number > 10:
            reasons.append("Late game demands decisive action")
        
        return "; ".join(reasons) if reasons else "Standard play"
    
    def _get_dominant_element(self, cards: List[Card]) -> Element:
        """Get the most common element in the hand"""
        if not cards:
            return Element.NEUTRAL
        
        element_counts = Counter(card.element for card in cards)
        return element_counts.most_common(1)[0][0]
    
    def _select_best_combination(self, combinations: List[HandCombination], context: GameContext) -> HandCombination:
        """Select the best combination from viable options"""
        if not combinations:
            return None
        
        # Sort by strategic value
        combinations.sort(key=lambda x: x.strategic_value, reverse=True)
        
        # Apply personality-based selection logic
        if self.personality.randomness_weight > 0.4:
            # High randomness: sometimes pick suboptimal plays
            if random.random() < 0.3 and len(combinations) > 1:
                return combinations[1]  # Second best
            elif random.random() < 0.1 and len(combinations) > 2:
                return combinations[2]  # Third best
        
        # Risk-based selection for cautious personalities
        if self.personality.name == "Cautious":
            # Prefer lower-risk plays
            safe_plays = [c for c in combinations[:3] if c.risk_level < 0.6]
            if safe_plays:
                return max(safe_plays, key=lambda x: x.strategic_value)
        
        # Efficiency-based selection for calculating personalities
        if self.personality.name == "Calculating":
            # Prefer efficient plays
            efficient_plays = [c for c in combinations[:3] if c.efficiency > 8]
            if efficient_plays:
                return max(efficient_plays, key=lambda x: x.strategic_value)
        
        return combinations[0]  # Default: pick best
    
    def record_player_action(self, action: PlayerAction):
        """Record player action for adaptive learning"""
        self.player_behavior_memory.append(action)
        
        # Keep memory within limits
        if len(self.player_behavior_memory) > self.personality.memory_length:
            self.player_behavior_memory.pop(0)
        
        # Update learned patterns
        self._update_learned_patterns(action)
    
    def _update_learned_patterns(self, action: PlayerAction):
        """Update learned patterns from player behavior"""
        # Simple pattern learning - could be enhanced with ML
        
        # Track element preferences
        for card in action.cards_played:
            element_key = f"prefers_{card.element.value}"
            self.learned_patterns[element_key] = self.learned_patterns.get(element_key, 0) + 1
        
        # Track hand type preferences
        hand_type_key = f"plays_{action.evaluation.hand_type.value}"
        self.learned_patterns[hand_type_key] = self.learned_patterns.get(hand_type_key, 0) + 1
        
        # Track aggression level
        if action.evaluation.total_value > 25:
            self.learned_patterns["aggressive"] = self.learned_patterns.get("aggressive", 0) + 1
        elif action.evaluation.total_value < 15:
            self.learned_patterns["defensive"] = self.learned_patterns.get("defensive", 0) + 1
    
    def get_adaptation_summary(self) -> Dict[str, any]:
        """Get summary of adaptive learning progress"""
        return {
            "actions_observed": len(self.player_behavior_memory),
            "learned_patterns": dict(self.learned_patterns),
            "adaptation_level": min(100, len(self.player_behavior_memory) * self.personality.adaptation_rate * 10),
            "memory_usage": f"{len(self.player_behavior_memory)}/{self.personality.memory_length}"
        }


if __name__ == "__main__":
    # Test the hand strategy system
    from ai_personality import get_personality_for_creature
    from enhanced_card_system import CardDeck
    
    print("🧠 Hand Strategy Engine Test 🧠\n")
    
    # Create test setup
    personality = get_personality_for_creature("Bakunawa")  # Adaptive boss
    strategy = HandStrategy(personality)
    
    # Create test cards
    deck = CardDeck()
    deck.shuffle()
    available_cards = deck.draw(8)
    
    # Create test context
    context = GameContext(
        player_health=30,
        player_max_health=50,
        player_block=5,
        ai_health=25,
        ai_max_health=60,
        ai_block=0,
        turn_number=5,
        cards_remaining=15
    )
    
    print(f"🃏 Available cards: {[str(card) for card in available_cards]}")
    print(f"🎭 AI Personality: {personality.name}")
    print(f"📊 Game Context: AI {context.ai_health}/{context.ai_max_health} HP, Player {context.player_health}/{context.player_max_health} HP")
    
    # Find best hand
    best_hand = strategy.find_best_hand(available_cards, context)
    
    if best_hand:
        print(f"\n🎯 Best Hand Selected:")
        print(f"   Cards: {best_hand.get_display_string()}")
        print(f"   Strategic Value: {best_hand.strategic_value:.1f}")
        print(f"   Confidence: {best_hand.confidence:.1%}")
        print(f"   Risk Level: {best_hand.risk_level:.1%}")
        print(f"   Efficiency: {best_hand.efficiency:.1f} dmg/card")
        print(f"   Reasoning: {best_hand.reasoning}")
        
        if best_hand.evaluation.special_effects:
            print(f"   Special Effects:")
            for effect in best_hand.evaluation.special_effects:
                print(f"     • {effect}")
    else:
        print("❌ No viable hand found (AI passes turn)")
    
    # Test adaptive learning
    print(f"\n🧠 Testing Adaptive Learning:")
    test_player_action = PlayerAction(
        cards_played=deck.draw(3),
        evaluation=EnhancedHandEvaluator.evaluate_hand(deck.draw(3)),
        turn_number=context.turn_number,
        game_context=context
    )
    
    strategy.record_player_action(test_player_action)
    adaptation_summary = strategy.get_adaptation_summary()
    
    print(f"   Actions Observed: {adaptation_summary['actions_observed']}")
    print(f"   Adaptation Level: {adaptation_summary['adaptation_level']:.1f}%")
    print(f"   Memory Usage: {adaptation_summary['memory_usage']}")
    
    if adaptation_summary['learned_patterns']:
        print(f"   Learned Patterns:")
        for pattern, count in adaptation_summary['learned_patterns'].items():
            print(f"     • {pattern}: {count}")