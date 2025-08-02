"""
Balatro-like Poker Game AI Demo
Demonstrates the complete AI system in action with various scenarios.
"""

import random
from typing import List, Dict
from poker_hand_evaluator import Card, Suit, PokerHandEvaluator, HandType
from ai_decision_engine import AIPersonality, GameState, ActionType
from ai_controller import AIController


def create_deck() -> List[Card]:
    """Create a standard 52-card deck."""
    deck = []
    for suit in Suit:
        for rank in range(1, 14):
            deck.append(Card(rank, suit))
    return deck


def deal_hand(deck: List[Card], num_cards: int = 5) -> List[Card]:
    """Deal a hand from the deck."""
    if len(deck) < num_cards:
        raise ValueError("Not enough cards in deck")
    
    hand = []
    for _ in range(num_cards):
        card = random.choice(deck)
        deck.remove(card)
        hand.append(card)
    
    return hand


def format_hand(hand: List[Card]) -> str:
    """Format hand for display."""
    return " ".join(str(card) for card in hand)


def simulate_poker_round(ai_controller: AIController, player_hand: List[Card], 
                        ai_hand: List[Card], pot_size: int = 100) -> Dict:
    """Simulate a complete poker round."""
    
    # Create game state
    game_state = GameState(
        pot_size=pot_size,
        current_bet=0,
        ai_chips=1000,
        player_chips=1000,
        round_number=1,
        cards_in_hand=5,
        cards_played_this_round=0,
        opponent_recent_actions=[],
        level=ai_controller.current_level
    )
    
    # Get AI decision
    ai_decision = ai_controller.get_ai_decision(ai_hand, game_state)
    
    # Evaluate hands
    evaluator = PokerHandEvaluator()
    player_result = evaluator.evaluate_hand(player_hand)
    ai_result = evaluator.evaluate_hand(ai_hand)
    
    # Determine winner
    comparison = evaluator.compare_hands(player_result, ai_result)
    winner = "Player" if comparison > 0 else "AI" if comparison < 0 else "Tie"
    
    return {
        "player_hand": player_hand,
        "ai_hand": ai_hand,
        "player_hand_type": player_result[0],
        "ai_hand_type": ai_result[0],
        "player_strength": evaluator.get_hand_strength_percentage(player_result[0], player_result[1]),
        "ai_strength": evaluator.get_hand_strength_percentage(ai_result[0], ai_result[1]),
        "ai_decision": ai_decision,
        "winner": winner,
        "game_state": game_state
    }


def demo_ai_personalities():
    """Demonstrate different AI personalities."""
    print("=== AI PERSONALITY DEMONSTRATION ===\n")
    
    # Create test scenario
    deck = create_deck()
    player_hand = [
        Card(8, Suit.HEARTS),
        Card(8, Suit.DIAMONDS),
        Card(7, Suit.CLUBS),
        Card(6, Suit.SPADES),
        Card(2, Suit.HEARTS)
    ]  # Pair of 8s - decent hand
    
    print(f"Player Hand: {format_hand(player_hand)} (Pair of 8s)")
    print("-" * 60)
    
    # Test each personality
    personalities = [
        (AIPersonality.CONSERVATIVE, 2),
        (AIPersonality.AGGRESSIVE, 3),
        (AIPersonality.ADAPTIVE, 4),
        (AIPersonality.CALCULATING, 5),
        (AIPersonality.CHAOTIC, 6)
    ]
    
    for personality, level in personalities:
        ai_controller = AIController(level)
        ai_controller.current_ai_profile.personality = personality
        ai_controller.decision_engine.personality = personality
        ai_controller.decision_engine.personality_config = ai_controller.decision_engine._get_personality_config(personality)
        
        # Deal AI hand
        deck_copy = [c for c in deck if c not in player_hand]
        ai_hand = deal_hand(deck_copy, 5)
        
        # Simulate round
        result = simulate_poker_round(ai_controller, player_hand, ai_hand)
        
        print(f"AI: {ai_controller.current_ai_profile.name} ({personality.value.upper()})")
        print(f"Hand: {format_hand(ai_hand)} ({result['ai_hand_type'].name})")
        print(f"Strength: {result['ai_strength']:.1f}%")
        print(f"Decision: {result['ai_decision'].action.value.upper()}")
        if result['ai_decision'].bet_amount > 0:
            print(f"Bet: {result['ai_decision'].bet_amount}")
        print(f"Confidence: {result['ai_decision'].confidence:.2f}")
        print(f"Reasoning: {result['ai_decision'].reasoning}")
        print(f"Winner: {result['winner']}")
        print("-" * 60)


def demo_difficulty_scaling():
    """Demonstrate difficulty scaling across levels."""
    print("\n=== DIFFICULTY SCALING DEMONSTRATION ===\n")
    
    # Fixed strong player hand for consistent comparison
    player_hand = [
        Card(1, Suit.SPADES),   # Ace
        Card(1, Suit.HEARTS),   # Ace
        Card(13, Suit.DIAMONDS), # King
        Card(12, Suit.CLUBS),   # Queen
        Card(11, Suit.SPADES)   # Jack - Pair of Aces
    ]
    
    print(f"Player Hand: {format_hand(player_hand)} (Pair of Aces - Strong)")
    print("-" * 70)
    
    levels_to_test = [1, 3, 5, 7, 10]
    
    for level in levels_to_test:
        ai_controller = AIController(level)
        
        # Create consistent but varied AI hands
        random.seed(42 + level)  # Consistent randomness for demo
        deck = create_deck()
        deck = [c for c in deck if c not in player_hand]
        ai_hand = deal_hand(deck, 5)
        
        # Simulate multiple decisions to show consistency
        decisions = []
        for _ in range(3):
            result = simulate_poker_round(ai_controller, player_hand, ai_hand)
            decisions.append(result['ai_decision'])
        
        # Show the most common decision
        main_decision = decisions[0]  # For simplicity, show first
        
        print(f"LEVEL {level}: {ai_controller.current_ai_profile.name}")
        print(f"Personality: {ai_controller.current_ai_profile.personality.value}")
        print(f"AI Hand: {format_hand(ai_hand)} ({ai_controller.decision_engine.evaluator.evaluate_hand(ai_hand)[0].name})")
        print(f"Decision: {main_decision.action.value.upper()}")
        if main_decision.bet_amount > 0:
            print(f"Bet Amount: {main_decision.bet_amount}")
        print(f"Confidence: {main_decision.confidence:.2f}")
        print(f"Reasoning: {main_decision.reasoning}")
        print(f"Target Win Rate: {ai_controller.current_ai_profile.win_rate_target:.1%}")
        print("-" * 70)


def demo_adaptive_ai():
    """Demonstrate adaptive AI that learns from player behavior."""
    print("\n=== ADAPTIVE AI DEMONSTRATION ===\n")
    
    ai_controller = AIController(4)  # Adaptive Annie
    
    print(f"AI: {ai_controller.current_ai_profile.name}")
    print(f"Description: {ai_controller.current_ai_profile.description}")
    print(f"Initial Opponent Model: {ai_controller.decision_engine.opponent_behavior_model}")
    print("-" * 70)
    
    # Simulate player being very aggressive
    aggressive_actions = [ActionType.RAISE, ActionType.RAISE, ActionType.ALL_IN, ActionType.RAISE, ActionType.RAISE]
    
    deck = create_deck()
    player_hand = deal_hand(deck, 5)
    ai_hand = deal_hand(deck, 5)
    
    print("Simulating aggressive player behavior...")
    print(f"Player actions: {[action.value for action in aggressive_actions]}")
    
    # Update AI's model of opponent
    ai_controller.decision_engine._update_opponent_model(aggressive_actions)
    
    print(f"Updated Opponent Model: {ai_controller.decision_engine.opponent_behavior_model}")
    
    # Show how this affects AI decisions
    game_state = GameState(
        pot_size=200,
        current_bet=50,
        ai_chips=800,
        player_chips=950,
        round_number=2,
        cards_in_hand=5,
        cards_played_this_round=0,
        opponent_recent_actions=aggressive_actions,
        level=4
    )
    
    ai_decision = ai_controller.get_ai_decision(ai_hand, game_state)
    
    print(f"\nAI Response to Aggressive Player:")
    print(f"Player Hand: {format_hand(player_hand)}")
    print(f"AI Hand: {format_hand(ai_hand)}")
    print(f"AI Decision: {ai_decision.action.value.upper()}")
    if ai_decision.bet_amount > 0:
        print(f"Bet Amount: {ai_decision.bet_amount}")
    print(f"Reasoning: {ai_decision.reasoning}")
    print(f"Confidence: {ai_decision.confidence:.2f}")


def demo_progression_system():
    """Demonstrate the level progression and dynamic difficulty system."""
    print("\n=== PROGRESSION SYSTEM DEMONSTRATION ===\n")
    
    ai_controller = AIController(1)
    ai_controller.set_adaptation_enabled(True)
    
    print("Starting with Tutorial AI...")
    print(f"Initial: {ai_controller.current_ai_profile.name} (Level {ai_controller.current_level})")
    print(f"Target Win Rate: {ai_controller.current_ai_profile.win_rate_target:.1%}")
    print("-" * 50)
    
    # Simulate a series of games where player is winning
    print("Simulating player winning streak...")
    for game in range(12):
        # Player wins 80% of games initially
        ai_won = random.random() < 0.2
        ai_controller.report_game_result(ai_won)
        
        status = ai_controller.get_ai_status()
        
        if game % 3 == 2:  # Report every 3 games
            print(f"Game {game + 1}: Level {status['current_level']} - {status['ai_name']}")
            print(f"  Recent Win Rate: {status['recent_ai_win_rate']:.1%} (Target: {status['target_win_rate']:.1%})")
            print(f"  Record: {status['ai_wins']}-{status['player_wins']}")
    
    print(f"\nFinal Status:")
    final_status = ai_controller.get_ai_status()
    print(f"Level: {final_status['current_level']}")
    print(f"Opponent: {final_status['ai_name']}")
    print(f"Personality: {final_status['personality']}")
    print(f"Overall Record: AI {final_status['ai_wins']} - {final_status['player_wins']} Player")
    
    # Show progression info
    progression = ai_controller.get_level_progression_info()
    print(f"\nProgression Info:")
    print(f"Current: {progression['current_opponent']}")
    print(f"Next Challenge: {progression['next_opponent']} ({progression['next_personality']})")
    print(f"Description: {progression['next_description']}")


def demo_bluffing_system():
    """Demonstrate the AI's bluffing capabilities."""
    print("\n=== BLUFFING SYSTEM DEMONSTRATION ===\n")
    
    # Use aggressive AI for more bluffs
    ai_controller = AIController(5)  # Aggressive Alex
    
    print(f"AI: {ai_controller.current_ai_profile.name}")
    print(f"Personality: {ai_controller.current_ai_profile.personality.value}")
    print(f"Bluff Frequency: {ai_controller.decision_engine.personality_config['bluff_frequency']:.1%}")
    print("-" * 60)
    
    # Test with weak AI hands to see bluffing behavior
    weak_hands = [
        [Card(7, Suit.HEARTS), Card(3, Suit.DIAMONDS), Card(9, Suit.CLUBS), Card(5, Suit.SPADES), Card(2, Suit.HEARTS)],  # High card
        [Card(6, Suit.HEARTS), Card(6, Suit.DIAMONDS), Card(3, Suit.CLUBS), Card(8, Suit.SPADES), Card(2, Suit.HEARTS)],  # Low pair
        [Card(4, Suit.HEARTS), Card(4, Suit.DIAMONDS), Card(9, Suit.CLUBS), Card(9, Suit.SPADES), Card(2, Suit.HEARTS)]   # Two pair
    ]
    
    for i, hand in enumerate(weak_hands, 1):
        print(f"Test Hand {i}: {format_hand(hand)}")
        
        # Run multiple simulations to see bluffing variation
        bluff_count = 0
        aggressive_count = 0
        
        for _ in range(10):  # Run 10 simulations
            game_state = GameState(
                pot_size=100,
                current_bet=20,
                ai_chips=1000,
                player_chips=1000,
                round_number=1,
                cards_in_hand=5,
                cards_played_this_round=0,
                opponent_recent_actions=[],
                level=5
            )
            
            decision = ai_controller.get_ai_decision(hand, game_state)
            
            if decision.bluff_factor > 0.3:
                bluff_count += 1
            
            if decision.action in [ActionType.RAISE, ActionType.ALL_IN]:
                aggressive_count += 1
        
        hand_type, score, _ = ai_controller.decision_engine.evaluator.evaluate_hand(hand)
        strength = ai_controller.decision_engine.evaluator.get_hand_strength_percentage(hand_type, score)
        
        print(f"  Hand Strength: {strength:.1f}% ({hand_type.name})")
        print(f"  Bluffed: {bluff_count}/10 times ({bluff_count*10}%)")
        print(f"  Aggressive Actions: {aggressive_count}/10 times ({aggressive_count*10}%)")
        print("-" * 60)


def main():
    """Run the complete AI demonstration."""
    print("🃏 BALATRO-LIKE POKER GAME AI SYSTEM 🃏")
    print("=" * 80)
    
    # Run all demonstrations
    demo_ai_personalities()
    demo_difficulty_scaling()
    demo_adaptive_ai()
    demo_progression_system()
    demo_bluffing_system()
    
    print("\n" + "=" * 80)
    print("🎯 DEMONSTRATION COMPLETE 🎯")
    print("\nThe AI system includes:")
    print("✅ Comprehensive poker hand evaluation")
    print("✅ 5 distinct AI personalities (Conservative, Aggressive, Adaptive, Calculating, Chaotic)")
    print("✅ Dynamic difficulty scaling (Levels 1-10+)")
    print("✅ Adaptive behavior based on opponent actions")
    print("✅ Strategic bluffing and risk assessment")
    print("✅ Automatic progression system")
    print("✅ Performance tracking and statistics")
    print("\n🎮 Ready for integration into your Balatro-like poker game! 🎮")


if __name__ == "__main__":
    main()