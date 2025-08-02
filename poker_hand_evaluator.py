"""
Poker Hand Evaluator for Balatro-like Game AI
Evaluates and ranks different poker hands with scoring system.
"""

from enum import Enum
from typing import List, Tuple, Dict
from collections import Counter
import random


class Suit(Enum):
    HEARTS = "H"
    DIAMONDS = "D" 
    CLUBS = "C"
    SPADES = "S"


class Card:
    def __init__(self, rank: int, suit: Suit):
        """
        Initialize a card.
        Args:
            rank: 1-13 (Ace=1, Jack=11, Queen=12, King=13)
            suit: Suit enum value
        """
        self.rank = rank
        self.suit = suit
    
    def __str__(self):
        rank_names = {1: "A", 11: "J", 12: "Q", 13: "K"}
        rank_str = rank_names.get(self.rank, str(self.rank))
        return f"{rank_str}{self.suit.value}"
    
    def __repr__(self):
        return self.__str__()


class HandType(Enum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10


class PokerHandEvaluator:
    """Evaluates poker hands and provides scoring for AI decision making."""
    
    # Base scores for different hand types
    HAND_TYPE_SCORES = {
        HandType.HIGH_CARD: 100,
        HandType.PAIR: 200,
        HandType.TWO_PAIR: 300,
        HandType.THREE_OF_A_KIND: 400,
        HandType.STRAIGHT: 500,
        HandType.FLUSH: 600,
        HandType.FULL_HOUSE: 700,
        HandType.FOUR_OF_A_KIND: 800,
        HandType.STRAIGHT_FLUSH: 900,
        HandType.ROYAL_FLUSH: 1000
    }
    
    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[HandType, int, List[int]]:
        """
        Evaluate a 5-card poker hand.
        
        Returns:
            Tuple of (hand_type, score, kickers)
            - hand_type: The type of poker hand
            - score: Numerical score for comparison
            - kickers: Relevant card ranks for tiebreaking
        """
        if len(cards) != 5:
            raise ValueError("Hand must contain exactly 5 cards")
        
        # Sort cards by rank for easier evaluation
        sorted_cards = sorted(cards, key=lambda x: x.rank, reverse=True)
        ranks = [card.rank for card in sorted_cards]
        suits = [card.suit for card in sorted_cards]
        
        # Count rank frequencies
        rank_counts = Counter(ranks)
        count_values = sorted(rank_counts.values(), reverse=True)
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        is_straight = PokerHandEvaluator._is_straight(ranks)
        
        # Determine hand type and calculate score
        if is_straight and is_flush:
            if ranks == [1, 13, 12, 11, 10]:  # Royal flush (A, K, Q, J, 10)
                return HandType.ROYAL_FLUSH, PokerHandEvaluator.HAND_TYPE_SCORES[HandType.ROYAL_FLUSH], [1]
            else:
                return HandType.STRAIGHT_FLUSH, PokerHandEvaluator.HAND_TYPE_SCORES[HandType.STRAIGHT_FLUSH] + max(ranks), [max(ranks)]
        
        elif count_values == [4, 1]:  # Four of a kind
            four_kind = [rank for rank, count in rank_counts.items() if count == 4][0]
            kicker = [rank for rank, count in rank_counts.items() if count == 1][0]
            score = PokerHandEvaluator.HAND_TYPE_SCORES[HandType.FOUR_OF_A_KIND] + four_kind
            return HandType.FOUR_OF_A_KIND, score, [four_kind, kicker]
        
        elif count_values == [3, 2]:  # Full house
            three_kind = [rank for rank, count in rank_counts.items() if count == 3][0]
            pair = [rank for rank, count in rank_counts.items() if count == 2][0]
            score = PokerHandEvaluator.HAND_TYPE_SCORES[HandType.FULL_HOUSE] + three_kind
            return HandType.FULL_HOUSE, score, [three_kind, pair]
        
        elif is_flush:
            score = PokerHandEvaluator.HAND_TYPE_SCORES[HandType.FLUSH] + sum(ranks[:3])  # Top 3 cards
            return HandType.FLUSH, score, ranks
        
        elif is_straight:
            high_card = max(ranks) if ranks != [1, 13, 12, 11, 10] else 1  # Ace-low straight
            score = PokerHandEvaluator.HAND_TYPE_SCORES[HandType.STRAIGHT] + high_card
            return HandType.STRAIGHT, score, [high_card]
        
        elif count_values == [3, 1, 1]:  # Three of a kind
            three_kind = [rank for rank, count in rank_counts.items() if count == 3][0]
            kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
            score = PokerHandEvaluator.HAND_TYPE_SCORES[HandType.THREE_OF_A_KIND] + three_kind
            return HandType.THREE_OF_A_KIND, score, [three_kind] + kickers
        
        elif count_values == [2, 2, 1]:  # Two pair
            pairs = sorted([rank for rank, count in rank_counts.items() if count == 2], reverse=True)
            kicker = [rank for rank, count in rank_counts.items() if count == 1][0]
            score = PokerHandEvaluator.HAND_TYPE_SCORES[HandType.TWO_PAIR] + pairs[0] + pairs[1]
            return HandType.TWO_PAIR, score, pairs + [kicker]
        
        elif count_values == [2, 1, 1, 1]:  # One pair
            pair = [rank for rank, count in rank_counts.items() if count == 2][0]
            kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
            score = PokerHandEvaluator.HAND_TYPE_SCORES[HandType.PAIR] + pair
            return HandType.PAIR, score, [pair] + kickers
        
        else:  # High card
            score = PokerHandEvaluator.HAND_TYPE_SCORES[HandType.HIGH_CARD] + sum(ranks[:3])
            return HandType.HIGH_CARD, score, ranks
    
    @staticmethod
    def _is_straight(ranks: List[int]) -> bool:
        """Check if ranks form a straight."""
        # Special case for Ace-low straight (A, 2, 3, 4, 5)
        if ranks == [1, 5, 4, 3, 2]:
            return True
        
        # Regular straight check
        sorted_ranks = sorted(ranks)
        for i in range(1, len(sorted_ranks)):
            if sorted_ranks[i] != sorted_ranks[i-1] + 1:
                return False
        return True
    
    @staticmethod
    def get_hand_strength_percentage(hand_type: HandType, score: int) -> float:
        """
        Convert hand strength to percentage (0-100).
        Used by AI for decision making.
        """
        max_possible_score = PokerHandEvaluator.HAND_TYPE_SCORES[HandType.ROYAL_FLUSH] + 100
        return min(100.0, (score / max_possible_score) * 100)
    
    @staticmethod
    def compare_hands(hand1_result: Tuple[HandType, int, List[int]], 
                     hand2_result: Tuple[HandType, int, List[int]]) -> int:
        """
        Compare two evaluated hands.
        Returns: 1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        _, score1, kickers1 = hand1_result
        _, score2, kickers2 = hand2_result
        
        if score1 > score2:
            return 1
        elif score1 < score2:
            return -1
        else:
            # Same hand type and primary score, compare kickers
            for k1, k2 in zip(kickers1, kickers2):
                if k1 > k2:
                    return 1
                elif k1 < k2:
                    return -1
            return 0  # Complete tie


def create_sample_hand() -> List[Card]:
    """Create a sample hand for testing."""
    return [
        Card(1, Suit.SPADES),   # Ace of Spades
        Card(13, Suit.SPADES),  # King of Spades  
        Card(12, Suit.SPADES),  # Queen of Spades
        Card(11, Suit.SPADES),  # Jack of Spades
        Card(10, Suit.SPADES)   # 10 of Spades - Royal Flush!
    ]


if __name__ == "__main__":
    # Test the evaluator
    evaluator = PokerHandEvaluator()
    
    # Test royal flush
    royal_flush = create_sample_hand()
    hand_type, score, kickers = evaluator.evaluate_hand(royal_flush)
    strength = evaluator.get_hand_strength_percentage(hand_type, score)
    
    print(f"Hand: {royal_flush}")
    print(f"Type: {hand_type.name}")
    print(f"Score: {score}")
    print(f"Strength: {strength:.1f}%")