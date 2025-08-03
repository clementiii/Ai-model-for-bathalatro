"""
PyQt GUI Interface for Bathala AI Card Combat Game
Complete graphical interface for the card-based combat game with AI integration
"""

import sys
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QPushButton, QLabel, QTextEdit, QProgressBar,
    QComboBox, QGroupBox, QScrollArea, QFrame, QSizePolicy,
    QMessageBox, QSpacerItem, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QBrush

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


class CardWidget(QPushButton):
    """Custom widget for displaying and selecting cards"""
    
    def __init__(self, card: Card, index: int):
        super().__init__()
        self.card = card
        self.index = index
        self.selected = False
        
        self.setFixedSize(120, 160)
        self.setCheckable(True)
        self.update_display()
        
        # Style the card with improved user-friendly design
        self.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 3px solid #e2e8f0;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
                padding: 6px;
                color: #2d3748;
                text-align: center;
                line-height: 1.2;
            }
            QPushButton:checked {
                background-color: #e6fffa;
                border-color: #38b2ac;
                font-weight: bolder;
                border-width: 4px;
            }
            QPushButton:hover {
                background-color: #f7fafc;
                border-color: #a0aec0;
                border-width: 3px;
            }
            QPushButton:checked:hover {
                background-color: #e6fffa;
                border-color: #319795;
                font-weight: bolder;
                border-width: 4px;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """)
        
        # Add tooltip
        self.setToolTip(f"{self.card.rank} of {self.card.suit.name.title()} ({self.card.element.name.title()})\nValue: {self.card.get_rank_value()}\nClick to select/deselect")
    
    def update_display(self):
        """Update the card display text with improved formatting"""
        suit_symbols = {"HEARTS": "♥", "DIAMONDS": "♦", "CLUBS": "♣", "SPADES": "♠"}
        element_symbols = {"FIRE": "🔥", "WATER": "💧", "EARTH": "🌍", "AIR": "💨", "NEUTRAL": "⚪"}
        
        suit_symbol = suit_symbols.get(self.card.suit.name, self.card.suit.name)
        element_symbol = element_symbols.get(self.card.element.name, self.card.element.name)
        
        # Create better formatted card text with consistent layout
        rank_display = self.card.rank
        value_display = self.card.get_rank_value()
        
        card_text = f"{rank_display}\n{suit_symbol}\n\n{element_symbol}\n\nVal: {value_display}"
        self.setText(card_text)


class BathalaGameGUI(QMainWindow):
    """Main GUI window for the Bathala AI card combat game"""
    
    def __init__(self):
        super().__init__()
        self.game = None
        self.card_widgets = []
        self.selected_cards = []
        
        self.init_game()
        self.init_ui()
        self.setup_styles()
        
    def init_game(self):
        """Initialize the game system"""
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
            "Dwende": Enemy(
                id="forest_dwende",
                name="Dwende",
                max_health=25,
                current_health=25,
                block=0,
                damage=6,
                attack_pattern=["attack", "mischief", "defend"]
            ),
            "Tikbalang": Enemy(
                id="wild_tikbalang", 
                name="Tikbalang",
                max_health=35,
                current_health=35,
                block=0,
                damage=8,
                attack_pattern=["attack", "confuse", "attack", "chaos"]
            ),
            "Kapre": Enemy(
                id="ancient_kapre",
                name="Kapre",
                max_health=30,
                current_health=30,
                block=0,
                damage=7,
                attack_pattern=["attack", "smoke", "nature_blessing"]
            ),
            "Manananggal": Enemy(
                id="elite_manananggal",
                name="Manananggal",
                max_health=50,
                current_health=50,
                block=0,
                damage=12,
                attack_pattern=["attack", "flight", "terror", "split"]
            ),
            "Bakunawa": Enemy(
                id="boss_bakunawa",
                name="Bakunawa",
                max_health=100,
                current_health=100,
                block=0,
                damage=18,
                attack_pattern=["attack", "eclipse", "devour", "dragon_fear"]
            )
        }
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("🎮 Bathala AI Card Combat Game - Ready to Play!")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QGridLayout(central_widget)
        
        # Create UI sections
        self.create_game_controls(main_layout)
        self.create_combat_status(main_layout)
        self.create_player_area(main_layout)
        self.create_enemy_area(main_layout)
        self.create_combat_log(main_layout)
        self.create_action_buttons(main_layout)
        
    def create_game_controls(self, layout):
        """Create game control section"""
        controls_group = QGroupBox("🎯 Game Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        # New Game button
        self.new_game_btn = QPushButton("🆕 New Game")
        self.new_game_btn.setObjectName("newGameBtn")
        self.new_game_btn.setToolTip("Start a new game with fresh deck and full health")
        self.new_game_btn.clicked.connect(self.start_new_game)
        controls_layout.addWidget(self.new_game_btn)
        
        # Enemy selection
        enemy_label = QLabel("Select Enemy:")
        enemy_label.setToolTip("Choose your opponent - difficulty increases from top to bottom")
        self.enemy_combo = QComboBox()
        
        # Add enemies with difficulty indicators
        enemy_descriptions = [
            "Dwende (Easy) - 25 HP",
            "Tikbalang (Medium) - 35 HP", 
            "Kapre (Medium) - 30 HP",
            "Manananggal (Hard) - 50 HP",
            "Bakunawa (Boss) - 100 HP"
        ]
        self.enemy_combo.addItems(enemy_descriptions)
        self.enemy_combo.setToolTip("Select enemy difficulty - start with Dwende for beginners!")
        controls_layout.addWidget(enemy_label)
        controls_layout.addWidget(self.enemy_combo)
        
        # Start Combat button
        self.start_combat_btn = QPushButton("⚔️ Start Combat")
        self.start_combat_btn.setObjectName("startCombatBtn")
        self.start_combat_btn.setToolTip("Begin combat with the selected enemy")
        self.start_combat_btn.clicked.connect(self.start_combat)
        self.start_combat_btn.setEnabled(False)
        controls_layout.addWidget(self.start_combat_btn)
        
        # Spacer
        controls_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # AI Debug checkbox
        self.debug_checkbox = QCheckBox("🔍 AI Debug Mode")
        self.debug_checkbox.setChecked(True)
        controls_layout.addWidget(self.debug_checkbox)
        
        layout.addWidget(controls_group, 0, 0, 1, 3)
    
    def create_combat_status(self, layout):
        """Create combat status display"""
        status_group = QGroupBox("📊 Combat Status")
        status_layout = QGridLayout(status_group)
        
        # Turn counter
        self.turn_label = QLabel("Turn: 0")
        self.turn_label.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout.addWidget(self.turn_label, 0, 0, 1, 2)
        
        # AI Preview
        self.ai_preview_label = QLabel("AI Next Action: Ready...")
        status_layout.addWidget(self.ai_preview_label, 1, 0, 1, 2)
        
        layout.addWidget(status_group, 1, 0, 1, 3)
    
    def create_player_area(self, layout):
        """Create player status and hand area"""
        player_group = QGroupBox("👤 Player")
        player_layout = QVBoxLayout(player_group)
        
        # Player status
        status_layout = QHBoxLayout()
        
        self.player_name_label = QLabel("Hero")
        self.player_name_label.setObjectName("statusLabel")
        self.player_name_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        status_layout.addWidget(self.player_name_label)
        
        # Health bar
        health_layout = QVBoxLayout()
        self.player_health_label = QLabel("❤️ Health: 50/50")
        self.player_health_label.setObjectName("healthLabel")
        self.player_health_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.player_health_bar = QProgressBar()
        self.player_health_bar.setMaximum(50)
        self.player_health_bar.setValue(50)
        self.player_health_bar.setMinimumHeight(25)
        self.player_health_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                text-align: center;
                background-color: #f7fafc;
                color: #333333;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #48bb78;
                border-radius: 4px;
                margin: 1px;
            }
        """)
        self.player_health_bar.setToolTip("Your current health - don't let it reach zero!")
        health_layout.addWidget(self.player_health_label)
        health_layout.addWidget(self.player_health_bar)
        status_layout.addLayout(health_layout)
        
        # Block display
        self.player_block_label = QLabel("🛡️ Block: 0")
        self.player_block_label.setToolTip("Block absorbs incoming damage")
        status_layout.addWidget(self.player_block_label)
        
        # Deck info
        self.deck_info_label = QLabel("📚 Deck: 20 | 🗑️ Discard: 0")
        self.deck_info_label.setToolTip("Cards remaining in deck and discarded cards")
        status_layout.addWidget(self.deck_info_label)
        
        status_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        player_layout.addLayout(status_layout)
        
        # Hand area
        hand_label = QLabel("🖐️ Hand:")
        hand_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        player_layout.addWidget(hand_label)
        
        # Scrollable hand area
        self.hand_scroll = QScrollArea()
        self.hand_widget = QWidget()
        self.hand_layout = QHBoxLayout(self.hand_widget)
        self.hand_layout.setSpacing(8)  # Add consistent spacing between cards
        self.hand_layout.setContentsMargins(10, 5, 10, 5)  # Add margins
        self.hand_scroll.setWidget(self.hand_widget)
        self.hand_scroll.setWidgetResizable(True)
        self.hand_scroll.setFixedHeight(180)  # Increased height for larger cards
        self.hand_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.hand_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        player_layout.addWidget(self.hand_scroll)
        
        # Hand Preview Area
        preview_group = QGroupBox("🔮 Hand Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_group.setMaximumHeight(100)
        
        self.preview_label = QLabel("Select cards to see preview...")
        self.preview_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.preview_label.setObjectName("statusLabel")
        self.preview_label.setWordWrap(True)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(35)
        preview_layout.addWidget(self.preview_label)
        
        # Action preview (attack/block values)
        action_preview_layout = QHBoxLayout()
        
        self.attack_preview_label = QLabel("⚔️ Attack: --")
        self.attack_preview_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.attack_preview_label.setStyleSheet("color: #e53e3e; padding: 5px;")
        self.attack_preview_label.setAlignment(Qt.AlignCenter)
        self.attack_preview_label.setToolTip("Damage this hand would deal")
        action_preview_layout.addWidget(self.attack_preview_label)
        
        self.block_preview_label = QLabel("🛡️ Block: --")
        self.block_preview_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.block_preview_label.setStyleSheet("color: #3182ce; padding: 5px;")
        self.block_preview_label.setAlignment(Qt.AlignCenter)
        self.block_preview_label.setToolTip("Block this hand would provide")
        action_preview_layout.addWidget(self.block_preview_label)
        
        preview_layout.addLayout(action_preview_layout)
        player_layout.addWidget(preview_group)
        
        layout.addWidget(player_group, 2, 0, 2, 2)
    
    def create_enemy_area(self, layout):
        """Create enemy status area"""
        enemy_group = QGroupBox("🐲 Enemy")
        enemy_layout = QVBoxLayout(enemy_group)
        
        # Enemy status
        self.enemy_name_label = QLabel("No Enemy")
        self.enemy_name_label.setObjectName("statusLabel")
        self.enemy_name_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        enemy_layout.addWidget(self.enemy_name_label)
        
        # Health bar
        health_layout = QVBoxLayout()
        self.enemy_health_label = QLabel("💀 Health: 0/0")
        self.enemy_health_label.setObjectName("healthLabel")
        self.enemy_health_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.enemy_health_bar = QProgressBar()
        self.enemy_health_bar.setMinimumHeight(25)
        self.enemy_health_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                text-align: center;
                background-color: #f7fafc;
                color: #333333;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #f56565;
                border-radius: 4px;
                margin: 1px;
            }
        """)
        self.enemy_health_bar.setToolTip("Enemy's remaining health")
        health_layout.addWidget(self.enemy_health_label)
        health_layout.addWidget(self.enemy_health_bar)
        enemy_layout.addLayout(health_layout)
        
        # Block display
        self.enemy_block_label = QLabel("🛡️ Block: 0")
        self.enemy_block_label.setToolTip("Enemy's defensive block")
        enemy_layout.addWidget(self.enemy_block_label)
        
        # AI Status
        self.ai_status_label = QLabel("🤖 AI Status: Ready")
        self.ai_status_label.setToolTip("Current AI decision-making status")
        enemy_layout.addWidget(self.ai_status_label)
        
        # AI Personality
        self.ai_personality_label = QLabel("🧠 Personality: None")
        self.ai_personality_label.setToolTip("AI's current behavioral personality")
        enemy_layout.addWidget(self.ai_personality_label)
        
        layout.addWidget(enemy_group, 2, 2, 2, 1)
    
    def create_combat_log(self, layout):
        """Create combat log area"""
        log_group = QGroupBox("📜 Combat Log")
        log_layout = QVBoxLayout(log_group)
        
        self.combat_log = QTextEdit()
        self.combat_log.setReadOnly(True)
        self.combat_log.setFont(QFont("Segoe UI", 10))
        self.combat_log.append("🎮 Welcome to Bathala AI Card Combat Game! 🎮")
        self.combat_log.append("")
        self.combat_log.append("📖 How to Play:")
        self.combat_log.append("1️⃣ Click 'New Game' to create your hero and deck")
        self.combat_log.append("2️⃣ Select an enemy from the dropdown")
        self.combat_log.append("3️⃣ Click 'Start Combat' to begin battle")
        self.combat_log.append("4️⃣ Click cards in your hand to select them")
        self.combat_log.append("5️⃣ Watch the preview to see your poker hand")
        self.combat_log.append("6️⃣ Click '⚔️ Attack' to damage enemy or '🛡️ Block' to defend")
        self.combat_log.append("7️⃣ The AI will respond automatically")
        self.combat_log.append("")
        self.combat_log.append("💡 Tip: Hover over cards to see details!")
        self.combat_log.append("💡 Tip: Try different card combinations!")
        self.combat_log.append("💡 Tip: Block to survive powerful enemy attacks!")
        self.combat_log.append("💡 Tip: Higher poker hands = more damage/block!")
        self.combat_log.append("")
        self.combat_log.append("Ready to begin? Click 'New Game' above! ⬆️")
        
        log_layout.addWidget(self.combat_log)
        
        layout.addWidget(log_group, 4, 0, 2, 3)
    
    def create_action_buttons(self, layout):
        """Create action button area"""
        actions_group = QGroupBox("🎯 Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        # Attack button
        self.attack_btn = QPushButton("⚔️ Attack")
        self.attack_btn.setToolTip("Use your selected cards to attack the enemy")
        self.attack_btn.clicked.connect(lambda: self.play_selected_cards("attack"))
        self.attack_btn.setEnabled(False)
        actions_layout.addWidget(self.attack_btn)
        
        # Block button
        self.block_btn = QPushButton("🛡️ Block")
        self.block_btn.setToolTip("Use your selected cards to gain defensive block")
        self.block_btn.clicked.connect(lambda: self.play_selected_cards("block"))
        self.block_btn.setEnabled(False)
        actions_layout.addWidget(self.block_btn)
        
        # End Turn button
        self.end_turn_btn = QPushButton("⏭️ End Turn")
        self.end_turn_btn.setToolTip("End your turn without playing cards")
        self.end_turn_btn.clicked.connect(self.end_turn)
        self.end_turn_btn.setEnabled(False)
        actions_layout.addWidget(self.end_turn_btn)
        
        # Clear Selection button
        self.clear_selection_btn = QPushButton("🗑️ Clear Selection")
        self.clear_selection_btn.setToolTip("Deselect all currently selected cards")
        self.clear_selection_btn.clicked.connect(self.clear_card_selection)
        self.clear_selection_btn.setEnabled(False)
        actions_layout.addWidget(self.clear_selection_btn)
        
        # Analytics button
        self.analytics_btn = QPushButton("📊 Show Analytics")
        self.analytics_btn.setToolTip("View detailed combat statistics and AI performance")
        self.analytics_btn.clicked.connect(self.show_analytics)
        self.analytics_btn.setEnabled(False)
        actions_layout.addWidget(self.analytics_btn)
        
        layout.addWidget(actions_group, 6, 0, 1, 3)
    
    def setup_styles(self):
        """Setup application styles with improved user-friendliness"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
                color: #333333;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #d0d0d0;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #ffffff;
                color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #2c5282;
            }
            QPushButton {
                background-color: #4299e1;
                border: 2px solid #3182ce;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11px;
                color: white;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #3182ce;
                border-color: #2c5282;
            }
            QPushButton:pressed {
                background-color: #2c5282;
            }
            QPushButton:disabled {
                background-color: #a0a0a0;
                border-color: #808080;
                color: #e0e0e0;
            }
            QPushButton#newGameBtn {
                background-color: #48bb78;
                border-color: #38a169;
                font-size: 12px;
                padding: 12px 24px;
            }
            QPushButton#newGameBtn:hover {
                background-color: #38a169;
            }
            QPushButton#startCombatBtn {
                background-color: #ed8936;
                border-color: #dd6b20;
            }
            QPushButton#startCombatBtn:hover {
                background-color: #dd6b20;
            }
            QLabel {
                color: #333333;
                padding: 4px;
                font-size: 11px;
            }
            QLabel#statusLabel {
                font-size: 13px;
                font-weight: bold;
                color: #2d3748;
            }
            QLabel#healthLabel {
                font-size: 12px;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #ffffff;
                color: #333333;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 10px;
                padding: 8px;
            }
            QProgressBar {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                text-align: center;
                background-color: #f7fafc;
                color: #333333;
                font-weight: bold;
                height: 20px;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                margin: 1px;
            }
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333333;
                font-size: 11px;
                min-height: 15px;
            }
            QComboBox:hover {
                border-color: #cbd5e0;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666666;
            }
            QScrollArea {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                background-color: #f7fafc;
            }
            QCheckBox {
                color: #333333;
                font-size: 11px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #cbd5e0;
                border-radius: 3px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #4299e1;
                border-color: #3182ce;
            }
        """)
    
    def log_message(self, message: str):
        """Add message to combat log with improved formatting"""
        # Add some spacing for better readability
        if message.startswith("🎯") or message.startswith("🤖"):
            self.combat_log.append("")  # Add blank line before turn announcements
        
        self.combat_log.append(message)
        self.combat_log.ensureCursorVisible()
        
        # Auto-scroll to bottom
        scrollbar = self.combat_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def start_new_game(self):
        """Start a new game session"""
        self.log_message("\n🎮 Starting New Bathala Card Combat Game! 🎮")
        
        # Create player
        deck = CardDeck()
        deck.shuffle()
        starting_cards = deck.draw(20)  # Player gets 20-card deck
        
        self.player = Player(
            name="Hero",
            max_health=50,
            current_health=50,
            block=0,
            hand=[],
            deck=starting_cards,
            discard_pile=[]
        )
        
        # Draw starting hand
        self.player.draw_cards(5)
        
        self.log_message(f"👤 Player: {self.player.name}")
        self.log_message(f"❤️ Health: {self.player.current_health}/{self.player.max_health}")
        self.log_message(f"🃏 Starting Hand: {len(self.player.hand)} cards")
        
        # Enable controls
        self.start_combat_btn.setEnabled(True)
        
        # Update UI
        self.update_player_display()
        self.update_hand_display()
    
    def start_combat(self):
        """Start combat with selected enemy"""
        enemy_display = self.enemy_combo.currentText()
        # Extract enemy name from display text (e.g., "Dwende (Easy) - 25 HP" -> "Dwende")
        enemy_name = enemy_display.split(" (")[0]
        
        if not self.player:
            QMessageBox.warning(self, "Warning", "Please start a new game first!")
            return
        
        if enemy_name not in self.available_enemies:
            QMessageBox.warning(self, "Warning", f"Enemy '{enemy_name}' not found!")
            return
        
        self.current_enemy = self.available_enemies[enemy_name]
        self.turn_number = 0
        
        # Reset enemy health
        self.current_enemy.current_health = self.current_enemy.max_health
        self.current_enemy.block = 0
        
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
            ai_hand_size=0
        )
        
        self.log_message(f"\n⚔️ Combat Started! 🆚 {self.current_enemy.name}")
        self.log_message(f"🐲 Enemy: {self.current_enemy.current_health}/{self.current_enemy.max_health} HP")
        self.log_message(f"👤 Player: {self.player.current_health}/{self.player.max_health} HP")
        self.log_message(f"🧠 AI Personality: {self.ai_manager.ai.personality.name}")
        
        # Enable combat controls
        self.attack_btn.setEnabled(False)  # Will be enabled when cards are selected
        self.block_btn.setEnabled(False)   # Will be enabled when cards are selected
        self.end_turn_btn.setEnabled(True)
        self.clear_selection_btn.setEnabled(True)
        self.analytics_btn.setEnabled(True)
        
        # Initialize preview
        self.update_hand_preview()
        
        # Update displays
        self.update_enemy_display()
        self.update_turn_display()
        self.update_ai_preview()
    
    def update_hand_display(self):
        """Update the player's hand display"""
        # Clear existing cards
        for widget in self.card_widgets:
            widget.setParent(None)
        self.card_widgets.clear()
        
        if not self.player:
            return
        
        # Add cards to hand
        for i, card in enumerate(self.player.hand):
            card_widget = CardWidget(card, i)
            card_widget.clicked.connect(lambda checked, idx=i: self.toggle_card_selection(idx))
            self.card_widgets.append(card_widget)
            self.hand_layout.addWidget(card_widget)
        
        # Add spacer to push cards to the left
        self.hand_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
    
    def toggle_card_selection(self, card_index: int):
        """Toggle card selection with improved feedback and preview"""
        if card_index < len(self.card_widgets):
            card_widget = self.card_widgets[card_index]
            
            if card_widget.isChecked():
                if card_index not in self.selected_cards:
                    self.selected_cards.append(card_index)
                    card_name = f"{self.player.hand[card_index].rank} of {self.player.hand[card_index].suit.name.title()}"
                    self.log_message(f"✅ Selected: {card_name} (Total: {len(self.selected_cards)} cards)")
            else:
                if card_index in self.selected_cards:
                    self.selected_cards.remove(card_index)
                    card_name = f"{self.player.hand[card_index].rank} of {self.player.hand[card_index].suit.name.title()}"
                    self.log_message(f"❌ Deselected: {card_name} (Total: {len(self.selected_cards)} cards)")
            
            # Update action button states and preview
            has_selection = len(self.selected_cards) > 0
            self.attack_btn.setEnabled(has_selection)
            self.block_btn.setEnabled(has_selection)
            self.update_hand_preview()
    
    def clear_card_selection(self):
        """Clear all card selections with user feedback"""
        if len(self.selected_cards) > 0:
            for card_widget in self.card_widgets:
                card_widget.setChecked(False)
            cleared_count = len(self.selected_cards)
            self.selected_cards.clear()
            self.log_message(f"🗑️ Cleared {cleared_count} selected card{'s' if cleared_count != 1 else ''}")
        else:
            self.log_message("💡 No cards were selected to clear")
        
        # Update action button states and preview
        self.attack_btn.setEnabled(False)
        self.block_btn.setEnabled(False)
        self.update_hand_preview()
    
    def update_hand_preview(self):
        """Update the hand preview showing what poker hand would be formed"""
        if not self.player or len(self.selected_cards) == 0:
            self.preview_label.setText("Select cards to see preview...")
            self.attack_preview_label.setText("⚔️ Attack: --")
            self.block_preview_label.setText("🛡️ Block: --")
            return
        
        # Get selected cards
        selected_card_objects = [self.player.hand[i] for i in self.selected_cards]
        
        # Evaluate the hand
        evaluation = EnhancedHandEvaluator.evaluate_hand(selected_card_objects)
        
        # Update preview text
        preview_text = f"🃏 {evaluation.description}"
        if evaluation.special_effects:
            preview_text += f"\n✨ {', '.join(evaluation.special_effects[:2])}"  # Show first 2 effects
        
        self.preview_label.setText(preview_text)
        
        # Calculate attack and block values
        attack_value = evaluation.total_value
        # Block value is typically 50-75% of attack value for balance
        block_value = int(attack_value * 0.6)
        
        self.attack_preview_label.setText(f"⚔️ Attack: {attack_value}")
        self.block_preview_label.setText(f"🛡️ Block: {block_value}")
    
    def play_selected_cards(self, action_type="attack"):
        """Play the selected cards for attack or block"""
        if not self.player or not self.combat_state:
            QMessageBox.warning(self, "Warning", "No active combat!")
            return
        
        if not self.selected_cards:
            QMessageBox.warning(self, "Warning", "No cards selected!")
            return
        
        if self.combat_state.phase != CombatPhase.PLAYER_TURN:
            QMessageBox.warning(self, "Warning", "Not your turn!")
            return
        
        self.player_turn(self.selected_cards, action_type)
    
    def player_turn(self, card_indices: List[int], action_type: str = "attack") -> bool:
        """Execute player turn with selected cards for attack or block"""
        action_emoji = "⚔️" if action_type == "attack" else "🛡️"
        action_name = action_type.title()
        
        self.log_message(f"\n🎯 Player Turn {self.turn_number + 1} - {action_emoji} {action_name}")
        
        # Get selected cards
        selected_cards = []
        for idx in card_indices:
            if 0 <= idx < len(self.player.hand):
                selected_cards.append(self.player.hand[idx])
            else:
                self.log_message(f"❌ Invalid card index: {idx}")
                return False
        
        self.log_message(f"🃏 Playing: {[str(card) for card in selected_cards]}")
        
        # Evaluate player's hand
        evaluation = EnhancedHandEvaluator.evaluate_hand(selected_cards)
        base_value = evaluation.total_value
        
        self.log_message(f"🎲 {evaluation.description}: {base_value} base value")
        if evaluation.special_effects:
            for effect in evaluation.special_effects:
                self.log_message(f"   ✨ {effect}")
        
        if action_type == "attack":
            # Attack mode - deal damage to enemy
            damage_dealt = base_value
            actual_damage = max(0, damage_dealt - self.current_enemy.block)
            self.current_enemy.current_health -= actual_damage
            self.current_enemy.block = max(0, self.current_enemy.block - damage_dealt)
            
            self.log_message(f"   💥 Dealt {actual_damage} damage to {self.current_enemy.name}!")
            
        else:  # block mode
            # Block mode - gain defensive block
            block_gained = int(base_value * 0.6)  # Block is 60% of attack value
            self.player.block += block_gained
            
            self.log_message(f"   🛡️ Gained {block_gained} block! (Total: {self.player.block})")
        
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
        
        # Clear selection
        self.clear_card_selection()
        
        # Update displays
        self.update_player_display()
        self.update_enemy_display()
        self.update_hand_display()
        
        # Check if enemy is defeated (only possible in attack mode)
        if action_type == "attack" and self.current_enemy.current_health <= 0:
            self.log_message(f"🎉 Victory! {self.current_enemy.name} defeated!")
            self.combat_state.phase = CombatPhase.GAME_OVER
            self.end_combat()
            return True
        
        # Auto-execute AI turn after short delay
        QTimer.singleShot(1000, self.ai_turn)
        
        return True
    
    def ai_turn(self) -> bool:
        """Execute AI turn"""
        if not self.combat_state or self.combat_state.phase != CombatPhase.AI_TURN:
            return False
        
        self.log_message(f"\n🤖 {self.current_enemy.name}'s Turn")
        
        # Get AI decision and execute turn
        ai_result = self.ai_manager.execute_ai_turn(self.combat_state)
        
        self.log_message(f"🎯 AI Action: {ai_result.decision.action.value}")
        if self.debug_checkbox.isChecked():
            self.log_message(f"💭 Reasoning: {ai_result.decision.reasoning}")
        
        # Apply AI effects
        if ai_result.damage_dealt > 0:
            actual_damage = max(0, ai_result.damage_dealt - self.player.block)
            self.player.current_health -= actual_damage
            self.player.block = max(0, self.player.block - ai_result.damage_dealt)
            self.log_message(f"💥 AI deals {actual_damage} damage to player!")
        
        if ai_result.block_gained > 0:
            self.current_enemy.block += ai_result.block_gained
            self.log_message(f"🛡️ AI gains {ai_result.block_gained} block")
        
        if ai_result.special_effects:
            self.log_message(f"✨ Special Effects:")
            for effect in ai_result.special_effects:
                self.log_message(f"   • {effect}")
        
        # Update combat state
        self.combat_state.turn_number += 1
        self.turn_number += 1
        self.combat_state.player_health = self.player.current_health
        self.combat_state.player_block = self.player.block
        self.combat_state.ai_health = self.current_enemy.current_health
        self.combat_state.ai_block = self.current_enemy.block
        self.combat_state.phase = CombatPhase.PLAYER_TURN
        
        # Update displays
        self.update_player_display()
        self.update_enemy_display()
        self.update_turn_display()
        self.update_ai_preview()
        
        # Check if player is defeated
        if self.player.current_health <= 0:
            self.log_message(f"💀 Defeat! {self.current_enemy.name} has won!")
            self.combat_state.phase = CombatPhase.GAME_OVER
            self.end_combat()
            return True
        
        # Player draws a card at start of their turn
        drawn_cards = self.player.draw_cards(1)
        if drawn_cards:
            self.log_message(f"📜 Drew: {drawn_cards[0]}")
        
        self.update_hand_display()
        
        self.log_message(f"📊 Status: Player {self.player.current_health}/{self.player.max_health} HP, "
                        f"{self.current_enemy.name} {self.current_enemy.current_health}/{self.current_enemy.max_health} HP")
        
        return True
    
    def end_turn(self):
        """End turn without playing cards"""
        if not self.combat_state or self.combat_state.phase != CombatPhase.PLAYER_TURN:
            return
        
        self.log_message("⏭️ Player ends turn without playing cards")
        self.combat_state.phase = CombatPhase.AI_TURN
        
        # Clear selection
        self.clear_card_selection()
        
        # Auto-execute AI turn
        QTimer.singleShot(500, self.ai_turn)
    
    def end_combat(self):
        """End current combat"""
        # Disable combat controls
        self.attack_btn.setEnabled(False)
        self.block_btn.setEnabled(False)
        self.end_turn_btn.setEnabled(False)
        self.clear_selection_btn.setEnabled(False)
        
        # Reset preview
        self.update_hand_preview()
        
        self.log_message("⚔️ Combat ended!")
    
    def update_player_display(self):
        """Update player status display"""
        if not self.player:
            return
        
        self.player_health_label.setText(f"❤️ Health: {self.player.current_health}/{self.player.max_health}")
        self.player_health_bar.setMaximum(self.player.max_health)
        self.player_health_bar.setValue(self.player.current_health)
        self.player_health_bar.setFormat(f"{self.player.current_health}/{self.player.max_health}")
        self.player_block_label.setText(f"🛡️ Block: {self.player.block}")
        self.deck_info_label.setText(f"📚 Deck: {len(self.player.deck)} | 🗑️ Discard: {len(self.player.discard_pile)}")
        
        # Update health bar color based on health percentage
        health_percent = (self.player.current_health / self.player.max_health) * 100
        if health_percent > 60:
            chunk_color = "#48bb78"
        elif health_percent > 30:
            chunk_color = "#ed8936"
        else:
            chunk_color = "#f56565"
        
        self.player_health_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                text-align: center;
                background-color: #f7fafc;
                color: #333333;
                font-weight: bold;
                font-size: 11px;
            }}
            QProgressBar::chunk {{
                background-color: {chunk_color};
                border-radius: 4px;
                margin: 1px;
            }}
        """)
    
    def update_enemy_display(self):
        """Update enemy status display"""
        if not self.current_enemy:
            return
        
        self.enemy_name_label.setText(self.current_enemy.name)
        self.enemy_health_label.setText(f"💀 Health: {self.current_enemy.current_health}/{self.current_enemy.max_health}")
        self.enemy_health_bar.setMaximum(self.current_enemy.max_health)
        self.enemy_health_bar.setValue(self.current_enemy.current_health)
        self.enemy_health_bar.setFormat(f"{self.current_enemy.current_health}/{self.current_enemy.max_health}")
        self.enemy_block_label.setText(f"🛡️ Block: {self.current_enemy.block}")
        
        # Update enemy health bar with consistent styling
        self.enemy_health_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                text-align: center;
                background-color: #f7fafc;
                color: #333333;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #f56565;
                border-radius: 4px;
                margin: 1px;
            }
        """)
        
        if hasattr(self.ai_manager, 'ai') and self.ai_manager.ai:
            self.ai_personality_label.setText(f"🧠 Personality: {self.ai_manager.ai.personality.name}")
            self.ai_status_label.setText(f"🤖 AI Status: {self.ai_manager._get_ai_status_string()}")
    
    def update_turn_display(self):
        """Update turn counter display"""
        self.turn_label.setText(f"Turn: {self.turn_number + 1}")
    
    def update_ai_preview(self):
        """Update AI action preview"""
        if not self.combat_state:
            self.ai_preview_label.setText("AI Next Action: Ready...")
            return
        
        preview = self.ai_manager.preview_ai_action(self.combat_state)
        if preview:
            if preview.action.value == "attack":
                preview_text = f"AI might: {preview.action.value} (~{preview.estimated_damage} damage)"
            elif preview.action.value == "defend":
                preview_text = f"AI might: {preview.action.value} (~{preview.estimated_block} block)"
            else:
                preview_text = f"AI might: {preview.action.value} (status effect)"
        else:
            preview_text = "AI is contemplating..."
        
        self.ai_preview_label.setText(f"🔮 {preview_text}")
    
    def show_analytics(self):
        """Show detailed combat analytics"""
        if not hasattr(self.ai_manager, 'get_combat_analytics'):
            QMessageBox.information(self, "Analytics", "Analytics not available")
            return
        
        analytics = self.ai_manager.get_combat_analytics()
        
        analytics_text = f"""
📊 Combat Analytics:
━━━━━━━━━━━━━━━━━━━━━━━━━

🕐 Combat Duration: {analytics.get('combat_duration', 0):.2f}s
🎯 Player Actions: {analytics.get('player_actions', 0)}
🤖 AI Adaptation: {analytics.get('ai_statistics', {}).get('statistics', {}).get('adaptation_level', 0):.1f}%
📈 AI Decision Quality: {analytics.get('performance_metrics', {}).get('average_decision_quality', 0):.1f}
🎮 Turn Number: {self.turn_number}

Current Combat State:
👤 Player: {self.player.current_health if self.player else 0}/{self.player.max_health if self.player else 0} HP
🐲 Enemy: {self.current_enemy.current_health if self.current_enemy else 0}/{self.current_enemy.max_health if self.current_enemy else 0} HP
"""
        
        QMessageBox.information(self, "📊 Combat Analytics", analytics_text)


def main():
    """Main function to run the GUI application"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Bathala AI Card Combat")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Bathala Games")
    
    # Create and show main window
    window = BathalaGameGUI()
    window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()