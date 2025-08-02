"""
AI Decision Engine for Balatro-like Poker Game
Makes strategic decisions based on hand strength, risk tolerance, and game state.
"""

import random
from enum import Enum
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from poker_hand_evaluator import Card, PokerHandEvaluator, HandType


class AIPersonality(Enum):
    CONSERVATIVE = "conservative"  # Plays safe, folds weak hands
    AGGRESSIVE = "aggressive"     # Bets big, bluffs more
    ADAPTIVE = "adaptive"         # Adjusts based on game state
    CALCULATING = "calculating"   # Mathematical, optimal play
    CHAOTIC = "chaotic"          # Unpredictable, high variance


class ActionType(Enum):
    FOLD = "fold"
    CHECK = "check" 
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass
class GameState:
    """Current state of the game that AI needs to consider."""
    pot_size: int
    current_bet: int
    ai_chips: int
    player_chips: int
    round_number: int  # Current betting round
    cards_in_hand: int
    cards_played_this_round: int
    opponent_recent_actions: List[ActionType]  # Last few actions
    level: int  # Difficulty level (1-10+)


@dataclass
class AIDecision:
    """AI's decision with reasoning."""
    action: ActionType
    bet_amount: int  # 0 for fold/check/call
    confidence: float  # 0-1, how confident AI is in this decision
    reasoning: str  # Human-readable explanation
    bluff_factor: float  # 0-1, how much this is a bluff


class AIDecisionEngine:
    """Core AI decision-making engine."""
    
    def __init__(self, personality: AIPersonality = AIPersonality.ADAPTIVE):
        self.personality = personality
        self.evaluator = PokerHandEvaluator()
        
        # Personality-specific parameters
        self.personality_config = self._get_personality_config(personality)
        
        # Memory for adaptive behavior
        self.recent_decisions = []
        self.opponent_behavior_model = {
            "aggression_level": 0.5,  # 0-1
            "bluff_frequency": 0.3,   # 0-1  
            "fold_threshold": 0.4     # 0-1
        }
    
    def _get_personality_config(self, personality: AIPersonality) -> Dict:
        """Get configuration parameters for different AI personalities."""
        configs = {
            AIPersonality.CONSERVATIVE: {
                "risk_tolerance": 0.3,
                "bluff_frequency": 0.1,
                "bet_aggression": 0.4,
                "fold_threshold": 0.6,
                "adaptation_rate": 0.1
            },
            AIPersonality.AGGRESSIVE: {
                "risk_tolerance": 0.8,
                "bluff_frequency": 0.4,
                "bet_aggression": 0.8,
                "fold_threshold": 0.3,
                "adaptation_rate": 0.2
            },
            AIPersonality.ADAPTIVE: {
                "risk_tolerance": 0.5,
                "bluff_frequency": 0.25,
                "bet_aggression": 0.6,
                "fold_threshold": 0.5,
                "adaptation_rate": 0.3
            },
            AIPersonality.CALCULATING: {
                "risk_tolerance": 0.4,
                "bluff_frequency": 0.15,
                "bet_aggression": 0.5,
                "fold_threshold": 0.55,
                "adaptation_rate": 0.05
            },
            AIPersonality.CHAOTIC: {
                "risk_tolerance": 0.7,
                "bluff_frequency": 0.5,
                "bet_aggression": 0.9,
                "fold_threshold": 0.2,
                "adaptation_rate": 0.4
            }
        }
        return configs[personality]
    
    def make_decision(self, hand: List[Card], game_state: GameState) -> AIDecision:
        """
        Make an AI decision based on current hand and game state.
        
        Args:
            hand: Current cards in AI's hand
            game_state: Current game state information
            
        Returns:
            AIDecision with action, bet amount, and reasoning
        """
        # Evaluate hand strength
        if len(hand) == 5:
            hand_type, score, kickers = self.evaluator.evaluate_hand(hand)
            hand_strength = self.evaluator.get_hand_strength_percentage(hand_type, score)
        else:
            # For incomplete hands, estimate strength based on potential
            hand_strength = self._estimate_partial_hand_strength(hand)
            hand_type = HandType.HIGH_CARD
        
        # Apply difficulty scaling
        difficulty_modifier = self._get_difficulty_modifier(game_state.level)
        adjusted_strength = hand_strength * difficulty_modifier
        
        # Get base decision parameters
        config = self.personality_config
        risk_tolerance = config["risk_tolerance"]
        bluff_frequency = config["bluff_frequency"] 
        bet_aggression = config["bet_aggression"]
        fold_threshold = config["fold_threshold"]
        
        # Analyze opponent behavior and adapt
        self._update_opponent_model(game_state.opponent_recent_actions)
        
        # Determine if this should be a bluff
        should_bluff = (
            hand_strength < 50 and  # Weak hand
            random.random() < bluff_frequency and
            game_state.ai_chips > game_state.current_bet * 3  # Can afford to bluff
        )
        
        # Calculate effective hand strength (including bluffs)
        effective_strength = hand_strength
        if should_bluff:
            effective_strength += random.uniform(20, 40)  # Bluff boost
        
        # Make decision based on effective strength and game situation
        decision = self._determine_action(
            effective_strength, 
            game_state, 
            risk_tolerance,
            bet_aggression,
            fold_threshold,
            should_bluff
        )
        
        # Store decision for learning
        self.recent_decisions.append(decision)
        if len(self.recent_decisions) > 20:  # Keep recent history
            self.recent_decisions.pop(0)
        
        return decision
    
    def _estimate_partial_hand_strength(self, hand: List[Card]) -> float:
        """Estimate strength of incomplete hand based on potential."""
        if len(hand) < 2:
            return 30.0  # Conservative estimate
        
        ranks = [card.rank for card in hand]
        suits = [card.suit for card in hand]
        
        strength = 30.0  # Base strength
        
        # Check for pairs
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        max_same_rank = max(rank_counts.values()) if rank_counts else 1
        if max_same_rank >= 2:
            strength += 20 * max_same_rank  # Bonus for pairs/trips
        
        # Check for flush potential
        suit_counts = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
        
        max_same_suit = max(suit_counts.values()) if suit_counts else 1
        if max_same_suit >= 3:
            strength += 15 * max_same_suit  # Flush potential
        
        # Check for straight potential
        sorted_ranks = sorted(set(ranks))
        if len(sorted_ranks) >= 3:
            consecutive_count = self._count_consecutive(sorted_ranks)
            if consecutive_count >= 3:
                strength += 10 * consecutive_count
        
        # High card bonus
        high_card_bonus = max(ranks) if ranks else 0
        strength += high_card_bonus * 2
        
        return min(strength, 85.0)  # Cap at 85% for incomplete hands
    
    def _count_consecutive(self, sorted_ranks: List[int]) -> int:
        """Count consecutive cards in sorted rank list."""
        if len(sorted_ranks) < 2:
            return len(sorted_ranks)
        
        max_consecutive = 1
        current_consecutive = 1
        
        for i in range(1, len(sorted_ranks)):
            if sorted_ranks[i] == sorted_ranks[i-1] + 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
        
        return max_consecutive
    
    def _get_difficulty_modifier(self, level: int) -> float:
        """
        Get difficulty modifier that makes AI stronger at higher levels.
        
        Level 1: 0.7x strength (easier)
        Level 5: 1.0x strength (normal)  
        Level 10+: 1.5x strength (much harder)
        """
        if level <= 1:
            return 0.7
        elif level <= 3:
            return 0.8 + (level - 1) * 0.1
        elif level <= 5:
            return 0.9 + (level - 3) * 0.05
        elif level <= 10:
            return 1.0 + (level - 5) * 0.08
        else:
            return 1.4 + min((level - 10) * 0.02, 0.3)  # Cap at 1.7x
    
    def _update_opponent_model(self, recent_actions: List[ActionType]):
        """Update model of opponent behavior for adaptation."""
        if not recent_actions:
            return
        
        # Analyze aggression
        aggressive_actions = [ActionType.RAISE, ActionType.ALL_IN]
        passive_actions = [ActionType.CHECK, ActionType.CALL]
        
        aggression_score = sum(1 for action in recent_actions if action in aggressive_actions)
        total_actions = len(recent_actions)
        
        if total_actions > 0:
            new_aggression = aggression_score / total_actions
            adaptation_rate = self.personality_config["adaptation_rate"]
            self.opponent_behavior_model["aggression_level"] = (
                self.opponent_behavior_model["aggression_level"] * (1 - adaptation_rate) +
                new_aggression * adaptation_rate
            )
    
    def _determine_action(self, hand_strength: float, game_state: GameState,
                         risk_tolerance: float, bet_aggression: float, 
                         fold_threshold: float, is_bluff: bool) -> AIDecision:
        """Determine the specific action to take."""
        
        # Calculate pot odds and bet sizing
        pot_odds = game_state.current_bet / (game_state.pot_size + game_state.current_bet) if game_state.pot_size > 0 else 0
        
        # Normalize hand strength to decision threshold
        decision_strength = hand_strength / 100.0
        
        # Adjust for opponent behavior
        opponent_aggression = self.opponent_behavior_model["aggression_level"]
        if opponent_aggression > 0.7:  # Very aggressive opponent
            fold_threshold += 0.1  # Be more careful
            decision_strength *= 0.95
        elif opponent_aggression < 0.3:  # Passive opponent
            fold_threshold -= 0.1  # Can be more aggressive
            decision_strength *= 1.05
        
        # Decision logic
        if decision_strength < fold_threshold * (1 - risk_tolerance):
            # Fold weak hands
            return AIDecision(
                action=ActionType.FOLD,
                bet_amount=0,
                confidence=0.8,
                reasoning=f"Hand strength {hand_strength:.1f}% below fold threshold",
                bluff_factor=0.0
            )
        
        elif decision_strength < 0.5:
            # Check or call with medium-weak hands
            if game_state.current_bet == 0:
                return AIDecision(
                    action=ActionType.CHECK,
                    bet_amount=0,
                    confidence=0.6,
                    reasoning="Weak hand, checking to see more cards",
                    bluff_factor=0.0 if not is_bluff else 0.3
                )
            else:
                # Decide whether to call based on pot odds
                if pot_odds < decision_strength * 2:  # Good pot odds
                    return AIDecision(
                        action=ActionType.CALL,
                        bet_amount=game_state.current_bet,
                        confidence=0.5,
                        reasoning="Calling with decent pot odds",
                        bluff_factor=0.0
                    )
                else:
                    return AIDecision(
                        action=ActionType.FOLD,
                        bet_amount=0,
                        confidence=0.7,
                        reasoning="Poor pot odds, folding",
                        bluff_factor=0.0
                    )
        
        elif decision_strength < 0.75:
            # Call or small raise with good hands
            if game_state.current_bet == 0:
                # Make a bet
                bet_size = int(game_state.pot_size * bet_aggression * 0.5)
                bet_size = max(bet_size, game_state.ai_chips // 20)  # Minimum bet
                bet_size = min(bet_size, game_state.ai_chips // 3)   # Maximum bet
                
                return AIDecision(
                    action=ActionType.RAISE,
                    bet_amount=bet_size,
                    confidence=0.7,
                    reasoning=f"Good hand ({hand_strength:.1f}%), making value bet",
                    bluff_factor=0.1 if is_bluff else 0.0
                )
            else:
                # Call or small raise
                if random.random() < bet_aggression:
                    raise_amount = int(game_state.current_bet * (1 + bet_aggression))
                    raise_amount = min(raise_amount, game_state.ai_chips // 2)
                    
                    return AIDecision(
                        action=ActionType.RAISE,
                        bet_amount=raise_amount,
                        confidence=0.6,
                        reasoning="Raising with strong hand",
                        bluff_factor=0.2 if is_bluff else 0.0
                    )
                else:
                    return AIDecision(
                        action=ActionType.CALL,
                        bet_amount=game_state.current_bet,
                        confidence=0.7,
                        reasoning="Calling with strong hand",
                        bluff_factor=0.0
                    )
        
        else:
            # Very strong hand - bet big or all-in
            if decision_strength > 0.9 and random.random() < bet_aggression:
                # Consider all-in with excellent hands
                return AIDecision(
                    action=ActionType.ALL_IN,
                    bet_amount=game_state.ai_chips,
                    confidence=0.9,
                    reasoning=f"Excellent hand ({hand_strength:.1f}%), going all-in",
                    bluff_factor=0.0
                )
            else:
                # Large bet/raise
                if game_state.current_bet == 0:
                    bet_size = int(game_state.pot_size * bet_aggression * 0.8)
                else:
                    bet_size = int(game_state.current_bet * (2 + bet_aggression))
                
                bet_size = min(bet_size, game_state.ai_chips // 2)
                
                return AIDecision(
                    action=ActionType.RAISE,
                    bet_amount=bet_size,
                    confidence=0.85,
                    reasoning=f"Very strong hand ({hand_strength:.1f}%), betting for value",
                    bluff_factor=0.0
                )
    
    def get_personality_description(self) -> str:
        """Get human-readable description of AI personality."""
        descriptions = {
            AIPersonality.CONSERVATIVE: "Plays tight and safe, folds weak hands quickly",
            AIPersonality.AGGRESSIVE: "Bets big and bluffs frequently, high risk/reward",
            AIPersonality.ADAPTIVE: "Adjusts strategy based on opponent behavior",
            AIPersonality.CALCULATING: "Makes mathematically optimal decisions",
            AIPersonality.CHAOTIC: "Unpredictable and wild, keeps opponents guessing"
        }
        return descriptions[self.personality]


if __name__ == "__main__":
    # Test the decision engine
    from poker_hand_evaluator import Suit
    
    # Create test hand and game state
    test_hand = [
        Card(13, Suit.HEARTS),  # King of Hearts
        Card(13, Suit.DIAMONDS),  # King of Diamonds - Pair of Kings
        Card(7, Suit.CLUBS),
        Card(3, Suit.SPADES),
        Card(2, Suit.HEARTS)
    ]
    
    game_state = GameState(
        pot_size=100,
        current_bet=20,
        ai_chips=500,
        player_chips=600,
        round_number=2,
        cards_in_hand=5,
        cards_played_this_round=0,
        opponent_recent_actions=[ActionType.RAISE, ActionType.CALL],
        level=3
    )
    
    # Test different personalities
    personalities = [AIPersonality.CONSERVATIVE, AIPersonality.AGGRESSIVE, AIPersonality.ADAPTIVE]
    
    for personality in personalities:
        ai = AIDecisionEngine(personality)
        decision = ai.make_decision(test_hand, game_state)
        
        print(f"\n{personality.value.upper()} AI:")
        print(f"Decision: {decision.action.value}")
        print(f"Bet Amount: {decision.bet_amount}")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"Reasoning: {decision.reasoning}")
        print(f"Personality: {ai.get_personality_description()}")