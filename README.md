# Bathala AI System - Python Edition 🐲🃏

A sophisticated AI system for card-based combat games featuring Filipino mythology creatures. Complete Python implementation with advanced intelligence, adaptive learning, and cultural authenticity.

## 🎯 Features

### Core AI Capabilities  
- **Action-Based AI**: AI uses simple attack/defend/status actions instead of cards
- **Player Card System**: Only players use cards with elemental properties (Fire, Water, Earth, Air, Neutral)
- **6 AI Personalities**: Cautious, Aggressive, Calculating, Elemental, Chaotic, Adaptive
- **Filipino Mythology Creatures**: Tikbalang, Kapre, Manananggal, Bakunawa, and more
- **Adaptive Learning**: AI learns from player behavior and adapts strategies
- **Dynamic Difficulty Scaling**: 10+ levels from tutorial to legendary
- **Cultural Authenticity**: Creature behaviors reflect Filipino folklore
- **Production Ready**: Complete integration interface with analytics

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

### Basic Integration (3 lines!)

```python
from ai_manager import AIManager, AIConfig, CombatState, CombatPhase
from bathala_ai import Enemy

# Initialize AI system
ai_manager = AIManager(AIConfig(difficulty_level=5, enable_adaptation=True))

# Create enemy creature  
bakunawa = Enemy("boss", "Bakunawa", 100, 100, 0, 18, ["attack", "eclipse", "devour"])
ai_manager.initialize_combat(bakunawa)

# Create combat state
combat_state = CombatState(
    phase=CombatPhase.AI_TURN,
    turn_number=1,
    player_health=40, player_max_health=50, player_block=0,
    ai_health=100, ai_max_health=100, ai_block=0
)

# Execute AI turn
result = ai_manager.execute_ai_turn(combat_state)

print(f"🐉 AI Action: {result.decision.action.value}")
print(f"🐉 AI Reasoning: {result.decision.reasoning}")
print(f"💥 Damage: {result.damage_dealt}")
print(f"🛡️ Block: {result.block_gained}")
print(f"✨ Effects: {', '.join(result.special_effects)}")
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
├── ai_personality.py       # AI personality system with 6 distinct types
├── enhanced_card_system.py # Advanced card system with elemental properties
├── hand_strategy.py        # Strategic evaluation and combination analysis  
├── bathala_ai.py          # Core AI decision-making controller
├── ai_manager.py          # Main integration interface for games
├── game_integration_demo.py # Complete working game demonstration
├── BATHALA_AI_SYSTEM.md   # Comprehensive documentation
├── __init__.py            # Easy import interface
└── README.md              # This file
```

## 🎮 Integration Guide

### 1. Player Hand Evaluation
Players use cards while AI uses actions. The `EnhancedHandEvaluator` provides poker hand analysis for players:

```python
from enhanced_card_system import EnhancedHandEvaluator, Card, Suit

# Evaluate player's card hand
hand = [Card("A", Suit.SPADES, Element.FIRE), ...]  # Player's cards
evaluation = EnhancedHandEvaluator.evaluate_hand(hand)
damage = evaluation.total_value
```

### 2. AI Action Selection
The AI chooses actions instead of playing cards:

```python
from bathala_ai import BathalaAI, ActionType

# AI selects from attack/defend/status actions
decision = ai.make_decision(game_context)
# decision.action is one of: ATTACK, DEFEND, STATUS
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
if decision.action == ActionType.ATTACK:
    handle_ai_attack(decision.estimated_damage)
elif decision.action == ActionType.DEFEND:
    handle_ai_defend(decision.estimated_block)
elif decision.action == ActionType.STATUS:
    handle_ai_status_effect(decision.special_effects)
# ... etc

# After each game: report result
ai.report_game_result(ai_won=winner == "AI")
```

### 4. Card Combat Adaptations

For card combat games, the AI focuses on actions while players manage cards:

```python
# Custom game context for card combat
class CardCombatContext(GameContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_hand_size = 0    # Player's current hand size
        self.player_deck_size = 0    # Player's remaining deck
        self.special_effects = []    # Active battlefield effects

# AI chooses actions based on player card usage patterns
class EnhancedBathalaAI(BathalaAI):
    def make_decision(self, game_context):
        # AI considers player's card playing patterns
        decision = super().make_decision(game_context)
        
        # Adjust actions based on player behavior
        if self.player_patterns.get("fire", 0) > 5:
            # Player uses lots of fire - AI might defend more
            decision = self._counter_fire_strategy(decision)
        
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

## 🎮 Ready to Battle!

Your Filipino mythology creatures are now powered by sophisticated Python AI that provides:

- **🧠 Strategic Intelligence**: Makes smart action choices based on combat situations
- **🎭 Cultural Authenticity**: Creature behaviors reflecting Filipino folklore  
- **📈 Adaptive Learning**: Evolves and counters player card strategies
- **⚔️ Action-Based Combat**: Simple attack/defend/status actions while players use cards
- **⚡ Production Quality**: Professional-grade system ready for real games
- **🔧 Easy Integration**: Simple 3-line setup with comprehensive documentation

**Run the demo**: `python game_integration_demo.py`

**🇵🇭 ⚔️ 🃏 Good luck, and may the best hand win! 🃏 ⚔️ 🇵🇭**