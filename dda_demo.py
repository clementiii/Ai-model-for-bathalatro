"""
Dynamic Difficulty Adjustment (DDA) System Demonstration

This script demonstrates the complete DDA system functionality, showing how
player performance is tracked and how difficulty adapts in real-time.
"""

import time
import json
from dynamic_difficulty_adjustment import (
    DynamicDifficultyAdjuster, DifficultyTier, get_dda_system, reset_dda_system
)
from enhanced_card_system import Card, CardDeck, EnhancedHandEvaluator, Element, Suit, HandType
from bathala_ai import Enemy
from ai_manager import AIManager, AIConfig


def create_test_cards():
    """Create test cards for demonstration"""
    return [
        Card("A", Suit.HEARTS, Element.FIRE),
        Card("A", Suit.DIAMONDS, Element.FIRE),
        Card("K", Suit.SPADES, Element.WATER),
        Card("Q", Suit.CLUBS, Element.EARTH),
        Card("J", Suit.HEARTS, Element.AIR),
        Card("10", Suit.DIAMONDS, Element.FIRE),
        Card("9", Suit.SPADES, Element.WATER),
        Card("8", Suit.CLUBS, Element.EARTH),
    ]


def create_test_enemy():
    """Create a test enemy for demonstration"""
    return Enemy(
        id="demo_enemy",
        name="Demo Tikbalang",
        max_health=35,
        current_health=35,
        block=0,
        damage=8,
        attack_pattern=["attack", "confuse", "attack", "chaos"]
    )


def simulate_good_performance(dda_system: DynamicDifficultyAdjuster):
    """Simulate a player performing very well"""
    print("\n🎯 SIMULATING EXCELLENT PLAYER PERFORMANCE")
    print("=" * 60)
    
    test_cards = create_test_cards()
    
    # Simulate several successful combats
    for combat_num in range(3):
        print(f"\n--- Combat {combat_num + 1}: High Performance ---")
        
        # Start combat
        combat_id = dda_system.performance_tracker.start_combat(100, f"Enemy_{combat_num}")
        
        # Simulate excellent plays
        for turn in range(1, 4):  # Quick victory in 3 turns
            # Play strong hands
            if turn == 1:
                hand = test_cards[:2]  # Pair of Aces
            elif turn == 2:
                hand = test_cards[2:5]  # Three cards
            else:
                hand = test_cards[:4]  # Four cards
            
            evaluation = EnhancedHandEvaluator.evaluate_hand(hand)
            dda_system.performance_tracker.record_cards_played(evaluation, turn)
            print(f"  Turn {turn}: {evaluation.description} - {evaluation.total_value} damage")
        
        # End combat successfully with minimal damage taken
        dda_system.performance_tracker.record_damage_taken(5, 95, 100)  # Only 5 damage taken
        dda_system.performance_tracker.end_combat(True, 95, 3)  # Victory in 3 turns
        
        # Update difficulty
        dda_system.update_difficulty()
        
        # Show current status
        status = dda_system.get_dda_status()
        print(f"  📊 PPS: {status['performance']['pps']:.2f}")
        print(f"  ⚖️ Tier: {status['current_tier']}")
        
        time.sleep(0.1)  # Small delay for realistic timing


def simulate_poor_performance(dda_system: DynamicDifficultyAdjuster):
    """Simulate a player struggling"""
    print("\n💀 SIMULATING STRUGGLING PLAYER PERFORMANCE")
    print("=" * 60)
    
    test_cards = create_test_cards()
    
    # Simulate several difficult combats
    for combat_num in range(3):
        print(f"\n--- Combat {combat_num + 1}: Poor Performance ---")
        
        # Start combat
        combat_id = dda_system.performance_tracker.start_combat(100, f"Hard_Enemy_{combat_num}")
        
        # Simulate poor plays over many turns
        for turn in range(1, 11):  # Long, drawn-out combat
            # Play weak hands
            hand = [test_cards[turn % len(test_cards)]]  # Single cards only
            
            evaluation = EnhancedHandEvaluator.evaluate_hand(hand)
            dda_system.performance_tracker.record_cards_played(evaluation, turn)
            
            if turn % 3 == 0:  # Take damage frequently
                dda_system.performance_tracker.record_damage_taken(15, 100 - (turn * 8), 100)
            
            if turn % 4 == 0:  # Use resources when struggling
                dda_system.performance_tracker.record_resource_usage("potion")
        
        # End combat with loss or pyrrhic victory
        final_health = max(10, 100 - (combat_num + 1) * 30)
        victory = combat_num < 2  # Lose the last combat
        dda_system.performance_tracker.end_combat(victory, final_health, 10)
        
        # Update difficulty
        dda_system.update_difficulty()
        
        # Show current status
        status = dda_system.get_dda_status()
        print(f"  📊 PPS: {status['performance']['pps']:.2f}")
        print(f"  ⚖️ Tier: {status['current_tier']}")
        
        time.sleep(0.1)


def demonstrate_adaptive_modifiers(dda_system: DynamicDifficultyAdjuster):
    """Demonstrate how difficulty modifiers adapt based on performance"""
    print("\n🔧 DEMONSTRATING ADAPTIVE MODIFIERS")
    print("=" * 60)
    
    base_enemy = create_test_enemy()
    print(f"Base Enemy Stats: {base_enemy.max_health} HP, {base_enemy.damage} damage")
    
    # Show modifiers at different performance levels
    performance_levels = [
        ("Struggling", -3.0),
        ("Learning", -1.0),
        ("Standard", 0.0),
        ("Thriving", 2.0),
        ("Mastering", 5.0)
    ]
    
    for level_name, target_pps in performance_levels:
        # Artificially set PPS to demonstrate different tiers
        dda_system.performance_tracker.pps = target_pps
        dda_system.update_difficulty()
        
        # Apply modifiers to enemy
        modified_enemy = dda_system.apply_enemy_modifiers(base_enemy)
        
        print(f"\n{level_name} Level (PPS: {target_pps:.1f}):")
        print(f"  Enemy HP: {base_enemy.max_health} → {modified_enemy.max_health}")
        print(f"  Enemy Damage: {base_enemy.damage} → {modified_enemy.damage}")
        
        modifiers = dda_system.current_modifiers
        print(f"  Shop Prices: {modifiers.shop_price_modifier:.0%}")
        print(f"  Gold Rewards: {modifiers.gold_reward_modifier:.0%}")
        print(f"  Rest Site Priority: {modifiers.favor_rest_sites}")
        print(f"  Narrative Blessing: {modifiers.narrative_blessing_active}")


def demonstrate_narrative_framing(dda_system: DynamicDifficultyAdjuster):
    """Demonstrate narrative event generation"""
    print("\n✨ DEMONSTRATING NARRATIVE FRAMING")
    print("=" * 60)
    
    # Reset system for clean narrative demonstration
    reset_dda_system()
    dda_system = get_dda_system()
    
    # Simulate progression through difficulty tiers
    tier_transitions = [
        ("Starting at neutral", 0.0),
        ("Performance declining", -1.5),
        ("Struggling significantly", -2.5),
        ("Beginning to improve", -1.0),
        ("Gaining confidence", 1.0),
        ("Showing mastery", 3.0),
        ("Achieving excellence", 5.0)
    ]
    
    for description, target_pps in tier_transitions:
        dda_system.performance_tracker.pps = target_pps
        dda_system.update_difficulty()
        
        current_tier = dda_system.performance_tracker.get_difficulty_tier()
        narrative_events = dda_system.get_recent_narrative_events(1)
        
        print(f"\n{description} (PPS: {target_pps:.1f}):")
        print(f"  Difficulty Tier: {current_tier.name}")
        if narrative_events:
            print(f"  Narrative: \"{narrative_events[-1]}\"")
        else:
            print("  Narrative: (No recent events)")


def demonstrate_academic_features(dda_system: DynamicDifficultyAdjuster):
    """Demonstrate academic research features of the DDA system"""
    print("\n🎓 ACADEMIC RESEARCH DEMONSTRATION")
    print("=" * 60)
    
    # Export comprehensive session data
    session_data = dda_system.export_session_data()
    
    print("\n📊 RESEARCH DATA COLLECTION:")
    print(f"  Total Performance Events: {len(session_data['performance_tracker']['event_history'])}")
    print(f"  Total Combat Sessions: {len(session_data['performance_tracker']['combat_history'])}")
    print(f"  PPS History Length: {len(session_data['performance_tracker']['pps_history'])}")
    print(f"  Session Duration: {session_data['performance_tracker']['session_stats']['session_duration']:.1f}s")
    
    print("\n🔬 RESEARCH METRICS:")
    stats = session_data['performance_tracker']['session_stats']
    print(f"  Win Rate: {stats['win_rate']:.1%}")
    print(f"  Performance Trend: {stats['trend']:.3f}")
    print(f"  Performance Volatility: {stats['volatility']:.3f}")
    
    print("\n📈 TIER PROGRESSION ANALYSIS:")
    tier_progression = session_data['tier_progression']
    if tier_progression:
        tier_changes = len(set(tier for _, tier in tier_progression))
        print(f"  Unique Tiers Visited: {tier_changes}/6")
        print(f"  Final Tier: {DifficultyTier(tier_progression[-1][1]).name}")
    
    print("\n🧪 PROPOSED ML INTEGRATION:")
    print("  Current Implementation: Rule-based reactive system ✓")
    print("  Data Collection: Real-time performance metrics ✓")
    print("  Narrative Integration: In-world difficulty framing ✓")
    print("  Academic Framework: Research question validation ✓")
    print("  Future Work: LSTM-based proactive prediction")
    
    # Save session data for analysis
    with open("dda_session_data.json", "w") as f:
        json.dump(session_data, f, indent=2, default=str)
    print("\n💾 Session data exported to 'dda_session_data.json'")


def main():
    """Main demonstration function"""
    print("🎮 DYNAMIC DIFFICULTY ADJUSTMENT SYSTEM DEMONSTRATION")
    print("=" * 70)
    print("\nThis demonstration showcases the comprehensive DDA system")
    print("designed for academic thesis research on adaptive difficulty.")
    print("\nResearch Question: 'How can a rule-based adaptive difficulty")
    print("system maintain player flow while collecting data for hybrid ML approaches?'")
    
    # Reset and get clean DDA system
    reset_dda_system()
    dda_system = get_dda_system()
    
    # Run demonstrations
    input("\nPress Enter to start excellent performance simulation...")
    simulate_good_performance(dda_system)
    
    input("\nPress Enter to start struggling performance simulation...")
    simulate_poor_performance(dda_system)
    
    input("\nPress Enter to demonstrate adaptive modifiers...")
    demonstrate_adaptive_modifiers(dda_system)
    
    input("\nPress Enter to demonstrate narrative framing...")
    demonstrate_narrative_framing(dda_system)
    
    input("\nPress Enter to show academic research features...")
    demonstrate_academic_features(dda_system)
    
    print("\n🎊 DEMONSTRATION COMPLETE!")
    print("\nThe DDA system has successfully demonstrated:")
    print("• Real-time Player Performance Score (PPS) calculation")
    print("• Six-tier adaptive difficulty system")
    print("• Dynamic enemy stat modification")
    print("• Economic and map generation adjustments")
    print("• Narrative framing for immersion")
    print("• Comprehensive data collection for research")
    print("• Academic framework for thesis validation")
    
    print("\n📚 For full integration, run: python gui_game_demo.py")
    print("💡 For DDA analytics in-game, click the '⚖️ DDA Analytics' button")


if __name__ == "__main__":
    main()