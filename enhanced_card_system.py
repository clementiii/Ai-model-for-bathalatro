"""
Enhanced Card System for Bathala-like Game
Includes elemental cards, hand evaluation, and strategic analysis
"""

import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter


class Suit(Enum):
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"


class Element(Enum):
    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"
    AIR = "air"
    NEUTRAL = "neutral"


class HandType(Enum):
    HIGH_CARD = "high_card"
    PAIR = "pair"
    TWO_PAIR = "two_pair"
    THREE_OF_A_KIND = "three_of_a_kind"
    STRAIGHT = "straight"
    FLUSH = "flush"
    FULL_HOUSE = "full_house"
    FOUR_OF_A_KIND = "four_of_a_kind"
    STRAIGHT_FLUSH = "straight_flush"
    ROYAL_FLUSH = "royal_flush"


@dataclass
class Card:
    """Enhanced card with elemental properties"""
    rank: str  # A, 2-10, J, Q, K
    suit: Suit
    element: Element
    id: str = ""
    selected: bool = False
    playable: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = f"{self.rank}_{self.suit.value}_{self.element.value}"
    
    def __str__(self):
        suit_symbols = {
            Suit.HEARTS: "♥️",
            Suit.DIAMONDS: "♦️", 
            Suit.CLUBS: "♣️",
            Suit.SPADES: "♠️"
        }
        element_symbols = {
            Element.FIRE: "🔥",
            Element.WATER: "💧",
            Element.EARTH: "🌍",
            Element.AIR: "💨",
            Element.NEUTRAL: "⚪"
        }
        return f"{self.rank}{suit_symbols[self.suit]}{element_symbols[self.element]}"
    
    def get_rank_value(self) -> int:
        """Get numerical value of rank for comparison"""
        rank_values = {
            "A": 14, "K": 13, "Q": 12, "J": 11, "10": 10,
            "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2
        }
        return rank_values.get(self.rank, 0)


@dataclass
class HandEvaluation:
    """Result of evaluating a poker hand with elemental bonuses"""
    hand_type: HandType
    base_value: int
    elemental_bonus: int
    total_value: int
    description: str
    confidence: float = 1.0  # How reliable this evaluation is
    special_effects: List[str] = None
    
    def __post_init__(self):
        if self.special_effects is None:
            self.special_effects = []


class EnhancedHandEvaluator:
    """Advanced hand evaluator with elemental bonuses and strategic analysis"""
    
    # Base values for different hand types
    HAND_BASE_VALUES = {
        HandType.HIGH_CARD: 5,
        HandType.PAIR: 10,
        HandType.TWO_PAIR: 20,
        HandType.THREE_OF_A_KIND: 30,
        HandType.STRAIGHT: 40,
        HandType.FLUSH: 50,
        HandType.FULL_HOUSE: 70,
        HandType.FOUR_OF_A_KIND: 100,
        HandType.STRAIGHT_FLUSH: 150,
        HandType.ROYAL_FLUSH: 200,
    }
    
    @classmethod
    def evaluate_hand(cls, cards: List[Card]) -> HandEvaluation:
        """Evaluate a hand of 1-5 cards with elemental bonuses"""
        if len(cards) == 0:
            return HandEvaluation(
                hand_type=HandType.HIGH_CARD,
                base_value=0,
                elemental_bonus=0,
                total_value=0,
                description="No cards played"
            )
        
        # Determine basic poker hand type
        hand_type = cls._determine_hand_type(cards)
        base_value = cls.HAND_BASE_VALUES[hand_type]
        
        # Calculate elemental bonuses
        elemental_bonus, special_effects = cls._calculate_elemental_bonus(cards, hand_type)
        
        # Calculate total value
        total_value = base_value + elemental_bonus
        
        # Generate description
        description = cls._generate_hand_description(hand_type, cards, elemental_bonus)
        
        return HandEvaluation(
            hand_type=hand_type,
            base_value=base_value,
            elemental_bonus=elemental_bonus,
            total_value=total_value,
            description=description,
            special_effects=special_effects
        )
    
    @classmethod
    def _determine_hand_type(cls, cards: List[Card]) -> HandType:
        """Determine the poker hand type"""
        if len(cards) == 1:
            return HandType.HIGH_CARD
        
        ranks = [card.rank for card in cards]
        suits = [card.suit for card in cards]
        
        # Count rank frequencies
        rank_counts = Counter(ranks)
        count_values = sorted(rank_counts.values(), reverse=True)
        
        # Check for flush and straight
        is_flush = len(set(suits)) == 1 and len(cards) >= 5
        is_straight = cls._is_straight(ranks) and len(cards) >= 5
        
        # Determine hand type
        if is_straight and is_flush:
            if cls._is_royal_flush(ranks):
                return HandType.ROYAL_FLUSH
            return HandType.STRAIGHT_FLUSH
        elif count_values[0] == 4:
            return HandType.FOUR_OF_A_KIND
        elif count_values[0] == 3 and len(count_values) > 1 and count_values[1] == 2:
            return HandType.FULL_HOUSE
        elif is_flush:
            return HandType.FLUSH
        elif is_straight:
            return HandType.STRAIGHT
        elif count_values[0] == 3:
            return HandType.THREE_OF_A_KIND
        elif count_values[0] == 2 and len(count_values) > 1 and count_values[1] == 2:
            return HandType.TWO_PAIR
        elif count_values[0] == 2:
            return HandType.PAIR
        else:
            return HandType.HIGH_CARD
    
    @classmethod
    def _is_straight(cls, ranks: List[str]) -> bool:
        """Check if ranks form a straight"""
        if len(ranks) < 5:
            return False
        
        # Convert ranks to numerical values
        values = []
        for rank in ranks:
            if rank == "A":
                values.append(14)  # Ace high
            elif rank == "K":
                values.append(13)
            elif rank == "Q":
                values.append(12)
            elif rank == "J":
                values.append(11)
            else:
                values.append(int(rank))
        
        values = sorted(set(values))
        
        # Check for consecutive values
        if len(values) >= 5:
            for i in range(len(values) - 4):
                if values[i+4] - values[i] == 4:
                    return True
        
        # Check for ace-low straight (A, 2, 3, 4, 5)
        if set([14, 2, 3, 4, 5]).issubset(set(values)):
            return True
        
        return False
    
    @classmethod
    def _is_royal_flush(cls, ranks: List[str]) -> bool:
        """Check if hand is a royal flush"""
        royal_ranks = {"A", "K", "Q", "J", "10"}
        return set(ranks) == royal_ranks
    
    @classmethod
    def _calculate_elemental_bonus(cls, cards: List[Card], hand_type: HandType) -> Tuple[int, List[str]]:
        """Calculate elemental bonuses and special effects"""
        element_counts = Counter(card.element for card in cards)
        bonus = 0
        effects = []
        
        # Fire: +2 damage per fire card
        fire_count = element_counts.get(Element.FIRE, 0)
        if fire_count > 0:
            fire_bonus = fire_count * 2
            bonus += fire_bonus
            effects.append(f"🔥 Fire synergy: +{fire_bonus} damage")
            
            # Fire special: ignite effect for 3+ fire cards
            if fire_count >= 3:
                bonus += 5
                effects.append("🔥 Ignite: Burn damage over time")
        
        # Water: +2 block per water card (defensive bonus)
        water_count = element_counts.get(Element.WATER, 0)
        if water_count > 0:
            water_bonus = water_count * 2
            effects.append(f"💧 Water synergy: +{water_bonus} block")
            
            # Water special: healing for 3+ water cards
            if water_count >= 3:
                effects.append("💧 Healing Spring: Restore health")
        
        # Earth: +1 damage per earth card, bonus for multiple
        earth_count = element_counts.get(Element.EARTH, 0)
        if earth_count > 0:
            earth_bonus = earth_count
            if earth_count >= 3:
                earth_bonus += 5  # Bonus for earth mastery
                effects.append("🌍 Earth Mastery: +5 damage and armor")
            else:
                effects.append(f"🌍 Earth synergy: +{earth_bonus} damage")
            bonus += earth_bonus
        
        # Air: Double damage if all cards are air
        air_count = element_counts.get(Element.AIR, 0)
        if air_count == len(cards) and len(cards) > 1:
            air_bonus = cls.HAND_BASE_VALUES[hand_type]  # Double the base
            bonus += air_bonus
            effects.append(f"💨 Air Mastery: Double damage (+{air_bonus})")
        elif air_count > 0:
            effects.append(f"💨 Air synergy: +{air_count} speed")
        
        # Mixed element penalties for some combinations
        unique_elements = len([count for count in element_counts.values() if count > 0])
        if unique_elements > 3:
            penalty = 3
            bonus -= penalty
            effects.append(f"⚡ Elemental chaos: -{penalty} damage")
        
        # Pure element bonuses
        if unique_elements == 1 and len(cards) > 2:
            pure_bonus = 3
            bonus += pure_bonus
            dominant_element = max(element_counts.keys(), key=lambda x: element_counts[x])
            effects.append(f"✨ Pure {dominant_element.value}: +{pure_bonus} damage")
        
        return max(0, bonus), effects
    
    @classmethod
    def _generate_hand_description(cls, hand_type: HandType, cards: List[Card], elemental_bonus: int) -> str:
        """Generate human-readable description of the hand"""
        hand_names = {
            HandType.HIGH_CARD: "High Card",
            HandType.PAIR: "Pair", 
            HandType.TWO_PAIR: "Two Pair",
            HandType.THREE_OF_A_KIND: "Three of a Kind",
            HandType.STRAIGHT: "Straight",
            HandType.FLUSH: "Flush",
            HandType.FULL_HOUSE: "Full House",
            HandType.FOUR_OF_A_KIND: "Four of a Kind",
            HandType.STRAIGHT_FLUSH: "Straight Flush",
            HandType.ROYAL_FLUSH: "Royal Flush",
        }
        
        # Find dominant element
        element_counts = Counter(card.element for card in cards)
        dominant_element = max(element_counts.keys(), key=lambda x: element_counts[x])
        
        base_desc = hand_names[hand_type]
        if elemental_bonus > 0:
            return f"{base_desc} ({dominant_element.value} enhanced)"
        else:
            return f"{base_desc} ({dominant_element.value})"
    
    @classmethod
    def compare_hands(cls, hand1: List[Card], hand2: List[Card]) -> int:
        """Compare two hands. Returns 1 if hand1 wins, -1 if hand2 wins, 0 if tie"""
        eval1 = cls.evaluate_hand(hand1)
        eval2 = cls.evaluate_hand(hand2)
        
        if eval1.total_value > eval2.total_value:
            return 1
        elif eval1.total_value < eval2.total_value:
            return -1
        else:
            # Tie-breaker: compare hand types
            hand_type_order = list(HandType)
            type1_rank = hand_type_order.index(eval1.hand_type)
            type2_rank = hand_type_order.index(eval2.hand_type)
            
            if type1_rank > type2_rank:
                return 1
            elif type1_rank < type2_rank:
                return -1
            else:
                return 0


class CardDeck:
    """Enhanced deck with elemental cards"""
    
    def __init__(self, include_elements: bool = True):
        self.cards: List[Card] = []
        self.include_elements = include_elements
        self._create_deck()
    
    def _create_deck(self):
        """Create a full deck with elemental assignments"""
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        
        for suit in Suit:
            for rank in ranks:
                if self.include_elements:
                    element = self._assign_element(rank, suit)
                else:
                    element = Element.NEUTRAL
                
                card = Card(rank=rank, suit=suit, element=element)
                self.cards.append(card)
    
    def _assign_element(self, rank: str, suit: Suit) -> Element:
        """Assign elements based on suit and rank"""
        # Base element by suit
        suit_elements = {
            Suit.HEARTS: Element.FIRE,
            Suit.DIAMONDS: Element.EARTH,
            Suit.CLUBS: Element.WATER,
            Suit.SPADES: Element.AIR,
        }
        
        base_element = suit_elements[suit]
        
        # Special cases for face cards and aces
        if rank in ["J", "Q", "K"]:
            # Face cards can be neutral or keep their suit element
            return Element.NEUTRAL if random.random() < 0.3 else base_element
        elif rank == "A":
            # Aces can be any element (wild cards)
            return random.choice(list(Element))
        else:
            return base_element
    
    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)
    
    def draw(self, count: int = 1) -> List[Card]:
        """Draw cards from the deck"""
        drawn = []
        for _ in range(min(count, len(self.cards))):
            if self.cards:
                drawn.append(self.cards.pop())
        return drawn
    
    def reset(self):
        """Reset and recreate the deck"""
        self.cards.clear()
        self._create_deck()
        self.shuffle()
    
    def cards_remaining(self) -> int:
        """Get number of cards remaining in deck"""
        return len(self.cards)
    
    def peek(self, count: int = 1) -> List[Card]:
        """Peek at top cards without removing them"""
        return self.cards[-count:] if count <= len(self.cards) else self.cards[:]


def create_custom_deck(element_distribution: Dict[Element, float] = None) -> CardDeck:
    """Create a custom deck with specific elemental distribution"""
    if element_distribution is None:
        element_distribution = {
            Element.FIRE: 0.25,
            Element.WATER: 0.25,
            Element.EARTH: 0.25,
            Element.AIR: 0.15,
            Element.NEUTRAL: 0.10,
        }
    
    deck = CardDeck(include_elements=False)
    
    # Reassign elements based on distribution
    elements = list(element_distribution.keys())
    weights = list(element_distribution.values())
    
    for card in deck.cards:
        card.element = random.choices(elements, weights=weights)[0]
    
    return deck


def create_themed_deck(theme: str) -> CardDeck:
    """Create a themed deck for specific creatures or scenarios"""
    deck = CardDeck(include_elements=False)
    
    themes = {
        "fire_creature": {Element.FIRE: 0.6, Element.AIR: 0.2, Element.NEUTRAL: 0.2},
        "water_creature": {Element.WATER: 0.6, Element.EARTH: 0.2, Element.NEUTRAL: 0.2},
        "earth_creature": {Element.EARTH: 0.6, Element.WATER: 0.2, Element.NEUTRAL: 0.2},
        "air_creature": {Element.AIR: 0.6, Element.FIRE: 0.2, Element.NEUTRAL: 0.2},
        "chaos_creature": {e: 0.2 for e in Element},  # Equal distribution
        "balanced": {Element.FIRE: 0.2, Element.WATER: 0.2, Element.EARTH: 0.2, 
                    Element.AIR: 0.2, Element.NEUTRAL: 0.2},
    }
    
    distribution = themes.get(theme, themes["balanced"])
    elements = list(distribution.keys())
    weights = list(distribution.values())
    
    for card in deck.cards:
        card.element = random.choices(elements, weights=weights)[0]
    
    return deck


if __name__ == "__main__":
    # Test the enhanced card system
    print("🃏 Enhanced Card System Test 🃏\n")
    
    # Create and test deck
    deck = CardDeck()
    deck.shuffle()
    
    print(f"📦 Created deck with {deck.cards_remaining()} cards")
    
    # Draw a test hand
    hand = deck.draw(5)
    print(f"🖐️ Drew hand: {[str(card) for card in hand]}")
    
    # Evaluate the hand
    evaluation = EnhancedHandEvaluator.evaluate_hand(hand)
    print(f"📊 Hand Evaluation:")
    print(f"   Type: {evaluation.hand_type.value}")
    print(f"   Base Value: {evaluation.base_value}")
    print(f"   Elemental Bonus: {evaluation.elemental_bonus}")
    print(f"   Total Value: {evaluation.total_value}")
    print(f"   Description: {evaluation.description}")
    
    if evaluation.special_effects:
        print(f"   Special Effects:")
        for effect in evaluation.special_effects:
            print(f"     • {effect}")
    
    # Test themed deck
    print(f"\n🔥 Fire Creature Themed Deck:")
    fire_deck = create_themed_deck("fire_creature")
    fire_hand = fire_deck.draw(5)
    print(f"🖐️ Fire hand: {[str(card) for card in fire_hand]}")
    
    fire_eval = EnhancedHandEvaluator.evaluate_hand(fire_hand)
    print(f"🔥 Fire evaluation: {fire_eval.total_value} damage")
    if fire_eval.special_effects:
        for effect in fire_eval.special_effects:
            print(f"     • {effect}")
    
    # Test hand comparison
    print(f"\n⚔️ Hand Comparison Test:")
    normal_deck = CardDeck()
    normal_deck.shuffle()
    hand2 = normal_deck.draw(5)
    
    comparison = EnhancedHandEvaluator.compare_hands(hand, hand2)
    result = "Hand 1 wins" if comparison > 0 else "Hand 2 wins" if comparison < 0 else "Tie"
    print(f"Result: {result}")
    print(f"Hand 1: {[str(card) for card in hand]} ({evaluation.total_value})")
    print(f"Hand 2: {[str(card) for card in hand2]} ({EnhancedHandEvaluator.evaluate_hand(hand2).total_value})")