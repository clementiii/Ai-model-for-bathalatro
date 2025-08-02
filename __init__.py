"""
Bathala AI System - Complete Python Implementation
A sophisticated AI system for card-based combat games with Filipino mythology creatures

Quick Start:
    from ai_manager import AIManager, AIConfig
    from bathala_ai import Enemy
    
    # Setup
    ai_manager = AIManager(AIConfig(difficulty_level=5))
    enemy = Enemy("bakunawa", "Bakunawa", 100, 100, 0, 18, ["attack", "eclipse", "devour"])
    ai_manager.initialize_combat(enemy)
    
    # Execute AI turn
    result = ai_manager.execute_ai_turn(combat_state)
    print(f"AI: {result.decision.reasoning}")
    print(f"Damage: {result.damage_dealt}")

Main Components:
    - ai_personality.py: AI personality system with 6 distinct types
    - enhanced_card_system.py: Card classes and elemental hand evaluation
    - hand_strategy.py: Strategic evaluation and combination analysis
    - bathala_ai.py: Core AI decision-making controller
    - ai_manager.py: Main integration interface
    - game_integration_demo.py: Complete working game demo

Features:
    ✅ 6 AI personalities (Cautious, Aggressive, Calculating, Elemental, Chaotic, Adaptive)
    ✅ Filipino mythology creatures with authentic behaviors
    ✅ Elemental card system (Fire, Water, Earth, Air, Neutral)
    ✅ Strategic hand evaluation (1-5 card combinations)
    ✅ Adaptive learning from player behavior
    ✅ Dynamic difficulty scaling (10+ levels)
    ✅ Comprehensive analytics and debugging
    ✅ Production-ready integration interface
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"
__description__ = "Sophisticated AI system for Bathala-like card combat games"

# Main exports for easy import
from ai_manager import AIManager, AIConfig, CombatState, CombatPhase
from bathala_ai import BathalaAI, Enemy, AIDecision, ActionType
from ai_personality import AIPersonalityType, get_personality_for_creature
from enhanced_card_system import Card, Element, Suit, EnhancedHandEvaluator, CardDeck
from hand_strategy import HandStrategy, GameContext, PlayerAction

__all__ = [
    "AIManager",
    "AIConfig", 
    "CombatState",
    "CombatPhase",
    "BathalaAI",
    "Enemy",
    "AIDecision", 
    "ActionType",
    "AIPersonalityType",
    "get_personality_for_creature",
    "Card",
    "Element", 
    "Suit",
    "EnhancedHandEvaluator",
    "CardDeck",
    "HandStrategy",
    "GameContext",
    "PlayerAction"
]