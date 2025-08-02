"""
Main AI Controller for Balatro-like Poker Game
Coordinates all AI systems and provides high-level game interface.
"""

import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from poker_hand_evaluator import Card, Suit, PokerHandEvaluator, HandType
from ai_decision_engine import AIDecisionEngine, AIPersonality, GameState, AIDecision, ActionType


class DifficultyLevel(Enum):
    TUTORIAL = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    EXPERT = 5
    NIGHTMARE = 6


@dataclass
class AIProfile:
    """Complete AI profile with personality and stats."""
    name: str
    personality: AIPersonality
    level: int
    description: str
    win_rate_target: float  # Expected win rate against average player
    special_abilities: List[str] = field(default_factory=list)


@dataclass
class GameSession:
    """Tracks an entire game session with the AI."""
    ai_profile: AIProfile
    games_played: int = 0
    ai_wins: int = 0
    player_wins: int = 0
    total_hands: int = 0
    ai_bluffs_successful: int = 0
    ai_bluffs_failed: int = 0


class AIController:
    """
    Main controller that manages AI behavior across the entire game.
    Handles difficulty progression, AI personality selection, and game flow.
    """
    
    # Predefined AI profiles for different levels
    AI_PROFILES = {
        1: AIProfile("Rookie", AIPersonality.CONSERVATIVE, 1, "A beginner AI that plays it safe", 0.3),
        2: AIProfile("Cautious Carl", AIPersonality.CONSERVATIVE, 2, "Still learning the ropes", 0.4),
        3: AIProfile("Steady Steve", AIPersonality.CALCULATING, 3, "Makes solid, mathematical plays", 0.5),
        4: AIProfile("Adaptive Annie", AIPersonality.ADAPTIVE, 4, "Learns from your playing style", 0.55),
        5: AIProfile("Aggressive Alex", AIPersonality.AGGRESSIVE, 5, "Plays bold and takes big risks", 0.6),
        6: AIProfile("Wild Card", AIPersonality.CHAOTIC, 6, "Completely unpredictable opponent", 0.55),
        7: AIProfile("The Calculator", AIPersonality.CALCULATING, 7, "Near-perfect mathematical play", 0.65),
        8: AIProfile("Poker Master", AIPersonality.ADAPTIVE, 8, "Reads you like an open book", 0.7),
        9: AIProfile("The Shark", AIPersonality.AGGRESSIVE, 9, "Ruthless and relentless", 0.75),
        10: AIProfile("The Legend", AIPersonality.ADAPTIVE, 10, "Legendary poker AI", 0.8)
    }
    
    def __init__(self, starting_level: int = 1):
        """
        Initialize AI controller.
        
        Args:
            starting_level: Starting difficulty level (1-10+)
        """
        self.current_level = starting_level
        self.current_ai_profile = self.AI_PROFILES.get(starting_level, self._create_dynamic_profile(starting_level))
        self.decision_engine = AIDecisionEngine(self.current_ai_profile.personality)
        self.session = GameSession(self.current_ai_profile)
        
        # Performance tracking for dynamic difficulty
        self.recent_performance = []  # List of recent win/loss results
        self.adaptation_enabled = True
        
    def _create_dynamic_profile(self, level: int) -> AIProfile:
        """Create AI profile for levels beyond predefined ones."""
        # Cycle through personalities for high levels
        personalities = list(AIPersonality)
        personality = personalities[(level - 1) % len(personalities)]
        
        # Scale difficulty
        win_rate = min(0.85, 0.4 + (level - 1) * 0.05)
        
        # Generate names for high levels
        names = ["The Machine", "Grandmaster", "AI Overlord", "The Terminator", "Deep Blue Jr."]
        name = names[(level - 11) % len(names)] if level > 10 else f"Level {level} AI"
        
        return AIProfile(
            name=name,
            personality=personality,
            level=level,
            description=f"Advanced AI opponent (Level {level})",
            win_rate_target=win_rate
        )
    
    def get_ai_decision(self, ai_hand: List[Card], game_state: GameState) -> AIDecision:
        """
        Get AI decision for current game state.
        
        Args:
            ai_hand: Cards currently in AI's hand
            game_state: Current game state
            
        Returns:
            AIDecision with action and reasoning
        """
        # Update game state with current level
        game_state.level = self.current_level
        
        # Get decision from engine
        decision = self.decision_engine.make_decision(ai_hand, game_state)
        
        # Apply level-specific modifications
        decision = self._apply_level_modifications(decision, game_state)
        
        # Track decision for analysis
        self.session.total_hands += 1
        
        return decision
    
    def _apply_level_modifications(self, decision: AIDecision, game_state: GameState) -> AIDecision:
        """Apply level-specific modifications to AI decisions."""
        
        # Higher levels get bonus abilities
        if self.current_level >= 5:
            # Can occasionally make "perfect" reads
            if random.random() < 0.1 * (self.current_level - 4):
                decision.confidence = min(decision.confidence + 0.2, 1.0)
                decision.reasoning += " (Advanced read)"
        
        if self.current_level >= 7:
            # Better bluff detection
            if decision.bluff_factor > 0:
                decision.confidence = min(decision.confidence + 0.15, 1.0)
                decision.reasoning += " (Expert bluff)"
        
        if self.current_level >= 9:
            # Occasionally makes "impossible" plays that work out
            if random.random() < 0.05:
                # Increase bet size or change action to more aggressive
                if decision.action in [ActionType.CALL, ActionType.CHECK]:
                    decision.action = ActionType.RAISE
                    decision.bet_amount = max(decision.bet_amount, game_state.current_bet * 2)
                    decision.reasoning = "Master-level aggressive play"
                    decision.confidence = 0.9
        
        return decision
    
    def report_game_result(self, ai_won: bool, hand_results: Optional[Dict] = None):
        """
        Report the result of a completed game.
        
        Args:
            ai_won: True if AI won the game
            hand_results: Optional detailed results from the hand
        """
        self.session.games_played += 1
        
        if ai_won:
            self.session.ai_wins += 1
        else:
            self.session.player_wins += 1
        
        # Track recent performance for adaptation
        self.recent_performance.append(ai_won)
        if len(self.recent_performance) > 10:
            self.recent_performance.pop(0)
        
        # Dynamic difficulty adjustment
        if self.adaptation_enabled and len(self.recent_performance) >= 5:
            self._adjust_difficulty()
    
    def _adjust_difficulty(self):
        """Adjust difficulty based on recent performance."""
        recent_ai_win_rate = sum(self.recent_performance) / len(self.recent_performance)
        target_win_rate = self.current_ai_profile.win_rate_target
        
        # If AI is winning too much, consider increasing difficulty
        if recent_ai_win_rate > target_win_rate + 0.15:
            if self.current_level < 15:  # Cap at level 15
                self._level_up()
        
        # If AI is losing too much, consider decreasing difficulty  
        elif recent_ai_win_rate < target_win_rate - 0.15:
            if self.current_level > 1:
                self._level_down()
    
    def _level_up(self):
        """Increase AI difficulty level."""
        self.current_level += 1
        old_profile = self.current_ai_profile
        self.current_ai_profile = self.AI_PROFILES.get(self.current_level, self._create_dynamic_profile(self.current_level))
        
        # Create new decision engine with new personality
        self.decision_engine = AIDecisionEngine(self.current_ai_profile.personality)
        
        print(f"AI difficulty increased! Now facing: {self.current_ai_profile.name} (Level {self.current_level})")
        print(f"Personality changed from {old_profile.personality.value} to {self.current_ai_profile.personality.value}")
    
    def _level_down(self):
        """Decrease AI difficulty level."""
        self.current_level -= 1
        old_profile = self.current_ai_profile
        self.current_ai_profile = self.AI_PROFILES.get(self.current_level, self._create_dynamic_profile(self.current_level))
        
        # Create new decision engine with new personality
        self.decision_engine = AIDecisionEngine(self.current_ai_profile.personality)
        
        print(f"AI difficulty decreased. Now facing: {self.current_ai_profile.name} (Level {self.current_level})")
    
    def force_level_change(self, new_level: int):
        """Manually set AI level (for level progression in game)."""
        if new_level < 1:
            new_level = 1
        
        self.current_level = new_level
        self.current_ai_profile = self.AI_PROFILES.get(new_level, self._create_dynamic_profile(new_level))
        self.decision_engine = AIDecisionEngine(self.current_ai_profile.personality)
        
        # Reset session tracking
        self.session = GameSession(self.current_ai_profile)
        self.recent_performance = []
    
    def get_ai_status(self) -> Dict:
        """Get current AI status and statistics."""
        win_rate = 0.0
        if self.session.games_played > 0:
            win_rate = self.session.ai_wins / self.session.games_played
        
        recent_win_rate = 0.0
        if len(self.recent_performance) > 0:
            recent_win_rate = sum(self.recent_performance) / len(self.recent_performance)
        
        return {
            "current_level": self.current_level,
            "ai_name": self.current_ai_profile.name,
            "personality": self.current_ai_profile.personality.value,
            "description": self.current_ai_profile.description,
            "games_played": self.session.games_played,
            "ai_wins": self.session.ai_wins,
            "player_wins": self.session.player_wins,
            "overall_ai_win_rate": win_rate,
            "recent_ai_win_rate": recent_win_rate,
            "target_win_rate": self.current_ai_profile.win_rate_target,
            "total_hands": self.session.total_hands,
            "personality_description": self.decision_engine.get_personality_description()
        }
    
    def get_level_progression_info(self) -> Dict:
        """Get information about level progression and next opponent."""
        next_level = self.current_level + 1
        next_profile = self.AI_PROFILES.get(next_level, self._create_dynamic_profile(next_level))
        
        return {
            "current_level": self.current_level,
            "current_opponent": self.current_ai_profile.name,
            "next_level": next_level,
            "next_opponent": next_profile.name,
            "next_personality": next_profile.personality.value,
            "next_description": next_profile.description,
            "progression_games_needed": max(0, 5 - len([x for x in self.recent_performance if not x])),  # Games without AI winning
            "can_progress": len([x for x in self.recent_performance[-5:] if not x]) >= 3 if len(self.recent_performance) >= 5 else False
        }
    
    def reset_session(self):
        """Reset the current session statistics."""
        self.session = GameSession(self.current_ai_profile)
        self.recent_performance = []
    
    def set_adaptation_enabled(self, enabled: bool):
        """Enable or disable dynamic difficulty adaptation."""
        self.adaptation_enabled = enabled
    
    def simulate_hand_preview(self, player_hand: List[Card], community_cards: List[Card] = None) -> Dict:
        """
        Simulate how AI would play against a specific hand (for testing/preview).
        
        Args:
            player_hand: Player's cards
            community_cards: Community cards if any
            
        Returns:
            Dictionary with AI's likely strategy and reasoning
        """
        # Generate a random hand for AI
        all_cards = []
        for suit in Suit:
            for rank in range(1, 14):
                all_cards.append(Card(rank, suit))
        
        # Remove known cards
        for card in player_hand:
            all_cards = [c for c in all_cards if not (c.rank == card.rank and c.suit == card.suit)]
        
        if community_cards:
            for card in community_cards:
                all_cards = [c for c in all_cards if not (c.rank == card.rank and c.suit == card.suit)]
        
        # Deal AI hand
        ai_hand = random.sample(all_cards, 5)
        
        # Create sample game state
        game_state = GameState(
            pot_size=100,
            current_bet=20,
            ai_chips=1000,
            player_chips=1000,
            round_number=1,
            cards_in_hand=5,
            cards_played_this_round=0,
            opponent_recent_actions=[],
            level=self.current_level
        )
        
        # Get AI decision
        decision = self.get_ai_decision(ai_hand, game_state)
        
        # Evaluate both hands for comparison
        evaluator = PokerHandEvaluator()
        ai_result = evaluator.evaluate_hand(ai_hand)
        player_result = evaluator.evaluate_hand(player_hand)
        
        comparison = evaluator.compare_hands(ai_result, player_result)
        winner = "AI" if comparison > 0 else "Player" if comparison < 0 else "Tie"
        
        return {
            "ai_hand": [str(card) for card in ai_hand],
            "ai_hand_type": ai_result[0].name,
            "ai_hand_strength": evaluator.get_hand_strength_percentage(ai_result[0], ai_result[1]),
            "player_hand_type": player_result[0].name,
            "player_hand_strength": evaluator.get_hand_strength_percentage(player_result[0], player_result[1]),
            "winner": winner,
            "ai_decision": {
                "action": decision.action.value,
                "bet_amount": decision.bet_amount,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "bluff_factor": decision.bluff_factor
            },
            "ai_profile": {
                "name": self.current_ai_profile.name,
                "personality": self.current_ai_profile.personality.value,
                "level": self.current_level
            }
        }


if __name__ == "__main__":
    # Test the AI controller
    print("=== Balatro-like Poker Game AI Controller Test ===\n")
    
    # Initialize AI controller
    ai_controller = AIController(starting_level=3)
    
    # Show initial status
    status = ai_controller.get_ai_status()
    print(f"Current Opponent: {status['ai_name']} (Level {status['current_level']})")
    print(f"Personality: {status['personality']} - {status['personality_description']}")
    print(f"Description: {status['description']}\n")
    
    # Test with sample hands
    from poker_hand_evaluator import Suit
    
    # Create sample player hand (pair of aces)
    player_hand = [
        Card(1, Suit.SPADES),   # Ace of Spades
        Card(1, Suit.HEARTS),   # Ace of Hearts  
        Card(13, Suit.DIAMONDS), # King of Diamonds
        Card(12, Suit.CLUBS),   # Queen of Clubs
        Card(11, Suit.SPADES)   # Jack of Spades
    ]
    
    print("=== Hand Simulation ===")
    print(f"Player Hand: {[str(card) for card in player_hand]}")
    
    # Simulate AI response
    simulation = ai_controller.simulate_hand_preview(player_hand)
    
    print(f"\nAI Hand: {simulation['ai_hand']}")
    print(f"Player Hand Strength: {simulation['player_hand_strength']:.1f}% ({simulation['player_hand_type']})")
    print(f"AI Hand Strength: {simulation['ai_hand_strength']:.1f}% ({simulation['ai_hand_type']})")
    print(f"Expected Winner: {simulation['winner']}")
    
    print(f"\nAI Decision: {simulation['ai_decision']['action'].upper()}")
    if simulation['ai_decision']['bet_amount'] > 0:
        print(f"Bet Amount: {simulation['ai_decision']['bet_amount']}")
    print(f"Confidence: {simulation['ai_decision']['confidence']:.2f}")
    print(f"Reasoning: {simulation['ai_decision']['reasoning']}")
    
    # Test level progression
    print(f"\n=== Level Progression Info ===")
    progression = ai_controller.get_level_progression_info()
    print(f"Current: {progression['current_opponent']} (Level {progression['current_level']})")
    print(f"Next: {progression['next_opponent']} (Level {progression['next_level']}) - {progression['next_personality']}")
    print(f"Description: {progression['next_description']}")
    
    # Simulate some games to test adaptation
    print(f"\n=== Testing Dynamic Difficulty ===")
    print("Simulating games with player winning most...")
    
    for i in range(8):
        # Player wins most games
        ai_won = random.random() < 0.2  # AI only wins 20% of the time
        ai_controller.report_game_result(ai_won)
        
        if i % 3 == 2:  # Check status every few games
            status = ai_controller.get_ai_status()
            print(f"After {status['games_played']} games: Level {status['current_level']}, Recent AI win rate: {status['recent_ai_win_rate']:.2f}")
    
    final_status = ai_controller.get_ai_status()
    print(f"\nFinal Status:")
    print(f"Opponent: {final_status['ai_name']} (Level {final_status['current_level']})")
    print(f"Games Played: {final_status['games_played']}")
    print(f"AI Wins: {final_status['ai_wins']}, Player Wins: {final_status['player_wins']}")
    print(f"Overall AI Win Rate: {final_status['overall_ai_win_rate']:.2f}")
    print(f"Recent AI Win Rate: {final_status['recent_ai_win_rate']:.2f}")
    print(f"Target Win Rate: {final_status['target_win_rate']:.2f}")