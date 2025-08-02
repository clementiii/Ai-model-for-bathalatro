"""
Complete Game Integration Demo for Bathala-like AI System
Shows how to integrate the AI system into your card-based combat game
"""

import random
from typing import List, Dict, Optional
from dataclasses import dataclass

# Import our AI system
from ai_manager import AIManager, AIConfig, CombatState, CombatPhase
from bathala_ai import Enemy
from enhanced_card_system import Card, CardDeck, EnhancedHandEvaluator, Element, Suit


@dataclass
class Player:
    """Player data structure"""
    name: str
    max_health: int
    current_health: int
    block: int
    hand: List[Card]
    deck: List[Card]
    discard_pile: List[Card]
    
    def draw_cards(self, count: int = 1) -> List[Card]:
        """Draw cards from deck to hand"""
        drawn = []
        for _ in range(count):
            if self.deck:
                card = self.deck.pop()
                self.hand.append(card)
                drawn.append(card)
            elif self.discard_pile:
                # Shuffle discard pile back into deck
                self.deck = self.discard_pile.copy()
                self.discard_pile.clear()
                random.shuffle(self.deck)
                if self.deck:
                    card = self.deck.pop()
                    self.hand.append(card)
                    drawn.append(card)
        return drawn
    
    def play_cards(self, cards: List[Card]) -> List[Card]:
        """Play cards from hand to discard pile"""
        played = []
        for card in cards:
            if card in self.hand:
                self.hand.remove(card)
                self.discard_pile.append(card)
                played.append(card)
        return played


class GameIntegrationDemo:
    """Complete demo showing AI integration with a card combat game"""
    
    def __init__(self):
        # Initialize AI system
        ai_config = AIConfig(
            difficulty_level=3,
            enable_adaptation=True,
            debug_mode=True,
            auto_adjust_difficulty=False
        )
        self.ai_manager = AIManager(ai_config)
        
        # Game state
        self.player: Optional[Player] = None
        self.current_enemy: Optional[Enemy] = None
        self.combat_state: Optional[CombatState] = None
        self.turn_number = 0
        
        # Available enemies for different difficulties
        self.available_enemies = self._create_enemy_roster()
    
    def _create_enemy_roster(self) -> Dict[str, Enemy]:
        """Create roster of available enemies"""
        return {
            "dwende": Enemy(
                id="forest_dwende",
                name="Dwende",
                max_health=25,
                current_health=25,
                block=0,
                damage=6,
                attack_pattern=["attack", "mischief", "defend"]
            ),
            "tikbalang": Enemy(
                id="wild_tikbalang", 
                name="Tikbalang",
                max_health=35,
                current_health=35,
                block=0,
                damage=8,
                attack_pattern=["attack", "confuse", "attack", "chaos"]
            ),
            "kapre": Enemy(
                id="ancient_kapre",
                name="Kapre",
                max_health=30,
                current_health=30,
                block=0,
                damage=7,
                attack_pattern=["attack", "smoke", "nature_blessing"]
            ),
            "manananggal": Enemy(
                id="elite_manananggal",
                name="Manananggal",
                max_health=50,
                current_health=50,
                block=0,
                damage=12,
                attack_pattern=["attack", "flight", "terror", "split"]
            ),
            "bakunawa": Enemy(
                id="boss_bakunawa",
                name="Bakunawa",
                max_health=100,
                current_health=100,
                block=0,
                damage=18,
                attack_pattern=["attack", "eclipse", "devour", "dragon_fear"]
            )
        }
    
    def start_new_game(self, player_name: str = "Hero"):
        """Start a new game session"""
        print("🎮 Starting New Bathala Card Combat Game! 🎮\n")
        
        # Create player
        deck = CardDeck()
        deck.shuffle()
        starting_cards = deck.draw(20)  # Player gets 20-card deck
        
        self.player = Player(
            name=player_name,
            max_health=50,
            current_health=50,
            block=0,
            hand=[],
            deck=starting_cards,
            discard_pile=[]
        )
        
        # Draw starting hand
        self.player.draw_cards(5)
        
        print(f"👤 Player: {self.player.name}")
        print(f"❤️ Health: {self.player.current_health}/{self.player.max_health}")
        print(f"🃏 Starting Hand: {[str(card) for card in self.player.hand]}")
        print()
    
    def start_combat(self, enemy_name: str):
        """Start combat with specific enemy"""
        if enemy_name not in self.available_enemies:
            print(f"❌ Enemy '{enemy_name}' not found!")
            return False
        
        self.current_enemy = self.available_enemies[enemy_name]
        self.turn_number = 0
        
        # Initialize AI for this enemy
        self.ai_manager.initialize_combat(self.current_enemy)
        
        # Create initial combat state
        self.combat_state = CombatState(
            phase=CombatPhase.PLAYER_TURN,
            turn_number=0,
            player_health=self.player.current_health,
            player_max_health=self.player.max_health,
            player_block=self.player.block,
            ai_health=self.current_enemy.current_health,
            ai_max_health=self.current_enemy.max_health,
            ai_block=self.current_enemy.block,
            player_hand_size=len(self.player.hand),
            ai_hand_size=0  # AI doesn't have cards anymore
        )
        
        print(f"⚔️ Combat Started! 🆚 {self.current_enemy.name}")
        print(f"🐲 Enemy: {self.current_enemy.current_health}/{self.current_enemy.max_health} HP")
        print(f"👤 Player: {self.player.current_health}/{self.player.max_health} HP")
        print(f"🧠 AI Personality: {self.ai_manager.ai.personality.name}")
        print()
        
        return True
    
    def player_turn(self, card_indices: List[int]) -> bool:
        """Execute player turn with selected cards"""
        if not self.player or not self.combat_state:
            print("❌ No active combat!")
            return False
        
        print(f"🎯 Player Turn {self.turn_number + 1}")
        print(f"🖐️ Current Hand: {[f'{i}: {card}' for i, card in enumerate(self.player.hand)]}")
        
        # Validate card selection
        if not card_indices:
            print("❌ No cards selected!")
            return False
        
        selected_cards = []
        for idx in card_indices:
            if 0 <= idx < len(self.player.hand):
                selected_cards.append(self.player.hand[idx])
            else:
                print(f"❌ Invalid card index: {idx}")
                return False
        
        print(f"🃏 Playing: {[str(card) for card in selected_cards]}")
        
        # Evaluate player's hand
        evaluation = EnhancedHandEvaluator.evaluate_hand(selected_cards)
        damage_dealt = evaluation.total_value
        
        print(f"💥 {evaluation.description}: {damage_dealt} damage!")
        if evaluation.special_effects:
            for effect in evaluation.special_effects:
                print(f"   ✨ {effect}")
        
        # Apply damage to enemy
        actual_damage = max(0, damage_dealt - self.current_enemy.block)
        self.current_enemy.current_health -= actual_damage
        self.current_enemy.block = max(0, self.current_enemy.block - damage_dealt)
        
        print(f"   🎯 Dealt {actual_damage} damage to {self.current_enemy.name}")
        
        # Play cards (move to discard pile)
        self.player.play_cards(selected_cards)
        
        # Record player action for AI learning
        self.ai_manager.record_player_action(selected_cards, self.turn_number, self.combat_state)
        
        # Update combat state
        self.combat_state.player_health = self.player.current_health
        self.combat_state.player_block = self.player.block
        self.combat_state.ai_health = self.current_enemy.current_health
        self.combat_state.ai_block = self.current_enemy.block
        self.combat_state.player_hand_size = len(self.player.hand)
        self.combat_state.phase = CombatPhase.AI_TURN
        
        # Check if enemy is defeated
        if self.current_enemy.current_health <= 0:
            print(f"🎉 Victory! {self.current_enemy.name} defeated!")
            self.combat_state.phase = CombatPhase.GAME_OVER
            return True
        
        print()
        return True
    
    def ai_turn(self) -> bool:
        """Execute AI turn"""
        if not self.combat_state or self.combat_state.phase != CombatPhase.AI_TURN:
            return False
        
        print(f"🤖 {self.current_enemy.name}'s Turn")
        
        # Get AI decision and execute turn
        ai_result = self.ai_manager.execute_ai_turn(self.combat_state)
        
        print(f"🎯 AI Action: {ai_result.decision.action.value}")
        print(f"💭 Reasoning: {ai_result.decision.reasoning}")
        
        # Apply AI effects
        if ai_result.damage_dealt > 0:
            actual_damage = max(0, ai_result.damage_dealt - self.player.block)
            self.player.current_health -= actual_damage
            self.player.block = max(0, self.player.block - ai_result.damage_dealt)
            print(f"💥 AI deals {actual_damage} damage to player!")
        
        if ai_result.block_gained > 0:
            self.current_enemy.block += ai_result.block_gained
            print(f"🛡️ AI gains {ai_result.block_gained} block")
        
        if ai_result.special_effects:
            print(f"✨ Special Effects:")
            for effect in ai_result.special_effects:
                print(f"   • {effect}")
        
        # Update combat state
        self.combat_state.turn_number += 1
        self.turn_number += 1
        self.combat_state.player_health = self.player.current_health
        self.combat_state.player_block = self.player.block
        self.combat_state.ai_health = self.current_enemy.current_health
        self.combat_state.ai_block = self.current_enemy.block
        self.combat_state.phase = CombatPhase.PLAYER_TURN
        
        # Check if player is defeated
        if self.player.current_health <= 0:
            print(f"💀 Defeat! {self.current_enemy.name} has won!")
            self.combat_state.phase = CombatPhase.GAME_OVER
            return True
        
        # Player draws a card at start of their turn
        self.player.draw_cards(1)
        
        print(f"📊 Status: Player {self.player.current_health}/{self.player.max_health} HP, "
              f"{self.current_enemy.name} {self.current_enemy.current_health}/{self.current_enemy.max_health} HP")
        print()
        
        return True
    
    def preview_ai_action(self) -> str:
        """Preview what the AI might do (for strategic planning)"""
        if not self.combat_state:
            return "No active combat"
        
        preview = self.ai_manager.preview_ai_action(self.combat_state)
        if preview:
            if preview.action.value == "attack":
                return f"AI might: {preview.action.value} (~{preview.estimated_damage} damage)"
            elif preview.action.value == "defend":
                return f"AI might: {preview.action.value} (~{preview.estimated_block} block)"
            else:
                return f"AI might: {preview.action.value} (status effect)"
        else:
            return "AI is contemplating..."
    
    def show_combat_status(self):
        """Display current combat status"""
        if not self.player or not self.current_enemy or not self.combat_state:
            print("No active combat")
            return
        
        print("=" * 50)
        print(f"⚔️ COMBAT STATUS - Turn {self.turn_number}")
        print(f"👤 {self.player.name}: {self.player.current_health}/{self.player.max_health} HP")
        if self.player.block > 0:
            print(f"   🛡️ Block: {self.player.block}")
        print(f"   🃏 Hand Size: {len(self.player.hand)}")
        
        print(f"🐲 {self.current_enemy.name}: {self.current_enemy.current_health}/{self.current_enemy.max_health} HP")
        if self.current_enemy.block > 0:
            print(f"   🛡️ Block: {self.current_enemy.block}")
        
        print(f"🤖 AI Status: {self.ai_manager._get_ai_status_string()}")
        print(f"🔮 AI Preview: {self.preview_ai_action()}")
        print("=" * 50)
    
    def get_analytics(self):
        """Get detailed combat analytics"""
        return self.ai_manager.get_combat_analytics()
    
    def run_demo_combat(self):
        """Run a complete demo combat scenario"""
        print("🎬 Running Demo Combat Scenario 🎬\n")
        
        # Start new game
        self.start_new_game("Demo Hero")
        
        # Fight progressively harder enemies
        demo_enemies = ["dwende", "tikbalang", "kapre"]
        
        for enemy_name in demo_enemies:
            print(f"\n🎯 Fighting {enemy_name.title()}...")
            
            if not self.start_combat(enemy_name):
                continue
            
            # Simulate several turns
            for turn in range(5):
                if self.combat_state.phase == CombatPhase.GAME_OVER:
                    break
                
                # Show status
                self.show_combat_status()
                
                # Player turn - randomly select 2-3 cards
                if self.combat_state.phase == CombatPhase.PLAYER_TURN:
                    hand_size = len(self.player.hand)
                    if hand_size > 0:
                        num_cards = min(hand_size, random.randint(2, 3))
                        selected_indices = random.sample(range(hand_size), num_cards)
                        self.player_turn(selected_indices)
                
                # AI turn
                if self.combat_state.phase == CombatPhase.AI_TURN:
                    self.ai_turn()
            
            # Show final analytics for this fight
            if enemy_name == demo_enemies[-1]:  # Last enemy
                print("\n📊 Final Combat Analytics:")
                analytics = self.get_analytics()
                print(f"   Combat Duration: {analytics['combat_duration']:.2f}s")
                print(f"   Player Actions: {analytics['player_actions']}")
                print(f"   AI Adaptation: {analytics['ai_statistics']['statistics']['adaptation_level']:.1f}%")
                print(f"   AI Decision Quality: {analytics['performance_metrics']['average_decision_quality']:.1f}")
    
    def run_interactive_demo(self):
        """Run interactive demo where user can make choices"""
        print("🎮 Interactive Bathala AI Demo 🎮")
        print("Commands: 'fight <enemy>', 'status', 'play <card_indices>', 'quit'")
        print(f"Available enemies: {list(self.available_enemies.keys())}")
        print()
        
        self.start_new_game("Interactive Hero")
        
        while True:
            try:
                command = input("🎯 Enter command: ").strip().lower()
                
                if command == "quit":
                    break
                elif command == "status":
                    self.show_combat_status()
                elif command.startswith("fight "):
                    enemy_name = command[6:]
                    self.start_combat(enemy_name)
                elif command.startswith("play "):
                    try:
                        indices_str = command[5:]
                        indices = [int(x) for x in indices_str.split()]
                        self.player_turn(indices)
                        
                        # Auto-execute AI turn
                        if self.combat_state and self.combat_state.phase == CombatPhase.AI_TURN:
                            self.ai_turn()
                    except ValueError:
                        print("❌ Invalid card indices! Use: play 0 1 2")
                else:
                    print("❌ Unknown command!")
                    print("Available: 'fight <enemy>', 'status', 'play <indices>', 'quit'")
                
            except KeyboardInterrupt:
                print("\n👋 Demo ended!")
                break


def main():
    """Main demo function"""
    demo = GameIntegrationDemo()
    
    print("🎯 Choose demo mode:")
    print("1. Automated Demo (watch AI battles)")
    print("2. Interactive Demo (play yourself)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        demo.run_demo_combat()
    elif choice == "2":
        demo.run_interactive_demo()
    else:
        print("Running automated demo by default...")
        demo.run_demo_combat()


if __name__ == "__main__":
    main()