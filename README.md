# Balatro-like Poker Game AI System

A comprehensive AI system for enemy NPCs in a Balatro-style poker game, featuring dynamic difficulty scaling, multiple AI personalities, strategic decision-making, and adaptive behavior.

## 🎯 Features

### Core AI Capabilities
- **Poker Hand Evaluation**: Complete poker hand ranking and scoring system
- **Strategic Decision Making**: AI considers hand strength, pot odds, bluffing opportunities, and risk tolerance
- **5 Distinct Personalities**: Conservative, Aggressive, Adaptive, Calculating, and Chaotic AI types
- **Dynamic Difficulty Scaling**: 10+ difficulty levels with automatic progression
- **Adaptive Behavior**: AI learns from and adapts to player behavior patterns
- **Bluffing System**: Realistic bluffing based on personality and game state
- **Performance Tracking**: Comprehensive statistics and win rate monitoring

### AI Personalities

1. **Conservative** - Plays tight and safe, folds weak hands quickly
2. **Aggressive** - Bets big and bluffs frequently, high risk/reward style
3. **Adaptive** - Adjusts strategy based on opponent behavior patterns
4. **Calculating** - Makes mathematically optimal decisions
5. **Chaotic** - Unpredictable and wild, keeps opponents guessing

### Difficulty Progression

- **Level 1**: Tutorial AI (30% target win rate)
- **Level 3**: Steady strategic play (50% target win rate)
- **Level 5**: Advanced tactics (60% target win rate)
- **Level 7**: Expert-level play (65% target win rate)
- **Level 10+**: Legendary opponents (70%+ target win rate)

## 🚀 Quick Start

### Basic Integration

```python
from ai_controller import AIController
from poker_hand_evaluator import Card, Suit
from ai_decision_engine import GameState, ActionType

# Initialize AI for level 3
ai_controller = AIController(starting_level=3)

# Create AI hand
ai_hand = [
    Card(13, Suit.HEARTS),  # King of Hearts
    Card(13, Suit.DIAMONDS), # King of Diamonds
    Card(7, Suit.CLUBS),    # 7 of Clubs
    Card(3, Suit.SPADES),   # 3 of Spades
    Card(2, Suit.HEARTS)    # 2 of Hearts
]

# Define game state
game_state = GameState(
    pot_size=100,
    current_bet=20,
    ai_chips=1000,
    player_chips=1000,
    round_number=1,
    cards_in_hand=5,
    cards_played_this_round=0,
    opponent_recent_actions=[],
    level=3
)

# Get AI decision
decision = ai_controller.get_ai_decision(ai_hand, game_state)

print(f"AI Decision: {decision.action.value}")
print(f"Bet Amount: {decision.bet_amount}")
print(f"Confidence: {decision.confidence:.2f}")
print(f"Reasoning: {decision.reasoning}")
```

### Advanced Usage

```python
# Set specific AI personality
ai_controller = AIController(5)
ai_controller.current_ai_profile.personality = AIPersonality.AGGRESSIVE

# Enable/disable dynamic difficulty adaptation
ai_controller.set_adaptation_enabled(True)

# Report game results for AI learning
ai_controller.report_game_result(ai_won=False)

# Get detailed AI statistics
status = ai_controller.get_ai_status()
print(f"Current Level: {status['current_level']}")
print(f"AI Win Rate: {status['overall_ai_win_rate']:.2%}")

# Force level progression
ai_controller.force_level_change(7)  # Jump to level 7

# Preview AI strategy against specific hands
preview = ai_controller.simulate_hand_preview(player_hand)
print(f"AI would play: {preview['ai_decision']['action']}")
```

## 📁 File Structure

```
├── poker_hand_evaluator.py  # Core poker hand evaluation system
├── ai_decision_engine.py    # AI decision-making logic and personalities
├── ai_controller.py         # Main AI controller and game interface
├── game_demo.py            # Comprehensive demonstration and examples
└── README.md               # This file
```

## 🎮 Integration Guide

### 1. Hand Evaluation
The `PokerHandEvaluator` provides comprehensive poker hand analysis:

```python
from poker_hand_evaluator import PokerHandEvaluator, Card, Suit

evaluator = PokerHandEvaluator()
hand = [Card(1, Suit.SPADES), ...]  # Your 5-card hand
hand_type, score, kickers = evaluator.evaluate_hand(hand)
strength_percentage = evaluator.get_hand_strength_percentage(hand_type, score)
```

### 2. AI Decision Making
The `AIDecisionEngine` handles strategic decisions:

```python
from ai_decision_engine import AIDecisionEngine, AIPersonality

# Create AI with specific personality
ai = AIDecisionEngine(AIPersonality.AGGRESSIVE)

# Get decision based on hand and game state
decision = ai.make_decision(hand, game_state)
```

### 3. Game Integration
The `AIController` provides the main game interface:

```python
from ai_controller import AIController

# Initialize AI system
ai = AIController(starting_level=1)

# Each turn: get AI decision
decision = ai.get_ai_decision(ai_hand, game_state)

# Process decision in your game logic
if decision.action == ActionType.RAISE:
    handle_ai_raise(decision.bet_amount)
elif decision.action == ActionType.FOLD:
    handle_ai_fold()
# ... etc

# After each game: report result
ai.report_game_result(ai_won=winner == "AI")
```

### 4. Balatro-specific Adaptations

For Balatro-like mechanics, you can extend the system:

```python
# Custom game state for Balatro mechanics
class BalatroGameState(GameState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.joker_cards = []        # Active joker cards
        self.score_multiplier = 1.0  # Current score multiplier
        self.special_hands = []      # Available special hand types

# Extend AI decision engine for Balatro rules
class BalatroAI(AIDecisionEngine):
    def make_decision(self, hand, game_state):
        # Consider Balatro-specific factors
        decision = super().make_decision(hand, game_state)
        
        # Adjust for joker effects
        if game_state.joker_cards:
            decision = self._apply_joker_strategy(decision, game_state)
        
        return decision
```

## 🔧 Customization

### Adding New Personalities

```python
# Define new personality configuration
new_personality_config = {
    "risk_tolerance": 0.6,
    "bluff_frequency": 0.3,
    "bet_aggression": 0.7,
    "fold_threshold": 0.4,
    "adaptation_rate": 0.2
}

# Add to decision engine
ai.personality_config = new_personality_config
```

### Custom Difficulty Scaling

```python
def custom_difficulty_modifier(level):
    """Custom difficulty scaling function"""
    return min(2.0, 0.5 + level * 0.15)

# Override in decision engine
ai.decision_engine._get_difficulty_modifier = custom_difficulty_modifier
```

### Event Callbacks

```python
# Monitor AI decisions
def on_ai_decision(decision, game_state):
    print(f"AI chose {decision.action} with {decision.confidence:.2f} confidence")

# Add to your game loop
decision = ai.get_ai_decision(hand, game_state)
on_ai_decision(decision, game_state)
```

## 📊 Performance Tuning

### Memory Usage
- The AI maintains limited history (20 recent decisions)
- Opponent behavior model uses simple moving averages
- Card objects are lightweight (rank + suit only)

### CPU Usage
- Hand evaluation: O(1) for 5-card hands
- Decision making: O(1) with minimal branching
- No complex tree search or simulation

### Balancing
- Adjust personality parameters for desired difficulty
- Modify target win rates per level
- Tune adaptation rates for player behavior learning

## 🧪 Testing

Run the demo to see all features in action:

```bash
python game_demo.py
```

This demonstrates:
- All 5 AI personalities
- Difficulty scaling across levels
- Adaptive behavior learning
- Bluffing mechanics
- Progression system

## 📈 Statistics Tracking

The system tracks comprehensive statistics:

```python
status = ai.get_ai_status()
# Returns: level, wins, losses, win rates, personality info, etc.

progression = ai.get_level_progression_info()
# Returns: current/next opponents, progression requirements
```

## 🎯 Best Practices

1. **Start Simple**: Begin with level 1-3 AIs for new players
2. **Enable Adaptation**: Let the AI learn from player behavior for more engaging gameplay
3. **Monitor Win Rates**: Use the statistics to balance difficulty
4. **Vary Personalities**: Switch between different AI types to keep gameplay fresh
5. **Custom Integration**: Extend the base classes for game-specific mechanics

## 🤝 Contributing

The AI system is designed to be modular and extensible. Key areas for enhancement:

- Additional AI personalities
- More sophisticated bluffing strategies
- Integration with specific Balatro mechanics
- Performance optimizations
- Advanced difficulty scaling algorithms

## 📄 License

This AI system is provided as-is for integration into your Balatro-like poker game. Feel free to modify and adapt it to your specific needs.

---

## 🎮 Ready to Play!

Your AI opponents are ready to challenge players with strategic depth, adaptive behavior, and engaging personality-driven gameplay. From tutorial-level opponents to legendary poker masters, this system provides a complete AI solution for your Balatro-like poker game.

**Good luck, and may the best hand win!** 🃏