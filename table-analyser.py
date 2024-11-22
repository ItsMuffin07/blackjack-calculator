import tkinter as tk
from tkinter import ttk
import numpy as np
from typing import List, Dict
import blackjack
import csv
import os


class BlackjackAnalyzer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Blackjack Strategy Map")
        self.geometry("1000x800")

        # Initialize deck
        self.full_deck = self._create_standard_deck()

        # Load probabilities from CSV
        self.probability_cache = self._load_probability_cache()

        # Create UI elements
        self._create_widgets()

        # Initial calculation
        self.update_grid()

    @staticmethod
    def _create_standard_deck() -> List[int]:
        """Create a standard 52-card deck represented as values"""
        deck = []
        for i in range(2, 10):
            deck.extend([i] * 4)
        deck.extend([10] * 16)
        deck.extend([11] * 4)
        return deck

    @staticmethod
    def _load_probability_cache() -> Dict:
        """Load all probabilities from CSV files"""
        cache = {}
        for dealer_card in range(2, 12):
            filename = os.path.join('single_deck_table', f"blackjack_probs_{dealer_card}.csv")
            if os.path.exists(filename):
                cache[dealer_card] = {}
                with open(filename, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        card1 = int(row['card1'])
                        card2 = int(row['card2'])
                        cache[dealer_card][(card1, card2)] = {
                            'total_prob': float(row['total_prob']),
                            'stand_prob': float(row['stand_prob']),
                            'hit_prob': float(row['hit_prob'])
                        }
        return cache

    def _create_widgets(self):
        # Top frame for dealer selection and stats
        top_frame = ttk.Frame(self)
        top_frame.pack(pady=10)

        # Dealer card selection
        dealer_frame = ttk.Frame(top_frame)
        dealer_frame.pack(side=tk.LEFT, padx=20)

        ttk.Label(dealer_frame, text="Dealer's Card:").pack(side=tk.LEFT)
        self.dealer_var = tk.StringVar(value="10")
        dealer_combo = ttk.Combobox(dealer_frame, textvariable=self.dealer_var,
                                    values=["2", "3", "4", "5", "6", "7", "8", "9", "10", "11"])
        dealer_combo.pack(side=tk.LEFT, padx=5)
        dealer_combo.bind('<<ComboboxSelected>>', lambda e: self.update_grid())

        # Expected value display
        self.ev_label = ttk.Label(top_frame, text="Expected Win: 0.00%")
        self.ev_label.pack(side=tk.LEFT, padx=20)

        # Dealer bust probability display
        self.bust_label = ttk.Label(top_frame, text="Dealer Bust: 0.00%")
        self.bust_label.pack(side=tk.LEFT, padx=20)

        # Grid frame
        self.grid_frame = ttk.Frame(self)
        self.grid_frame.pack(padx=20, pady=20, expand=True, fill=tk.BOTH)

        # Create headers
        ttk.Label(self.grid_frame, text="").grid(row=0, column=0)
        for i, val in enumerate(range(2, 12)):
            ttk.Label(self.grid_frame, text=str(val)).grid(row=0, column=i + 1)

        for i, val in enumerate(range(2, 12)):
            ttk.Label(self.grid_frame, text=str(val)).grid(row=i + 1, column=0)

        # Create grid cells
        self.cells = {}
        for row in range(10):
            for col in range(10):
                cell_frame = tk.Frame(self.grid_frame, padx=2, pady=2, width=80, height=60)
                cell_frame.grid(row=row + 1, column=col + 1, sticky="nsew")
                cell_frame.grid_propagate(False)

                action_label = tk.Label(cell_frame, text="", font=('Arial', 8, 'bold'))
                action_label.pack(expand=True)

                prob_label = tk.Label(cell_frame, text="", font=('Arial', 7))
                prob_label.pack(expand=True)

                ratio_label = tk.Label(cell_frame, text="", font=('Arial', 7))
                ratio_label.pack(expand=True)

                self.cells[(row, col)] = {
                    'frame': cell_frame,
                    'action': action_label,
                    'prob': prob_label,
                    'ratio': ratio_label
                }

        # Configure grid weights
        for i in range(11):
            self.grid_frame.grid_columnconfigure(i, weight=1)
            self.grid_frame.grid_rowconfigure(i, weight=1)

    @staticmethod
    def _get_color(probability: float, is_hit: bool) -> str:
        """Generate color based on probability - darker means higher probability"""
        enhanced_prob = probability ** 1.5
        darkness = 1.0 - (enhanced_prob * 0.85)

        if is_hit:
            return f'#{int(30 * darkness):02x}{int(144 * darkness):02x}{int(255 * darkness):02x}'
        else:
            return f'#{int(255 * darkness):02x}{int(20 * darkness):02x}{int(20 * darkness):02x}'

    def _calculate_dealer_bust_probability(self, dealer_card: int, used_cards: List[int]) -> float:
        """Calculate the dealer's probability of busting"""
        deck = self.full_deck.copy()
        for card in used_cards:
            deck.remove(card)
        return blackjack.dealer_probability_busted(tuple(deck), tuple([dealer_card]), 17)

    def update_grid(self):
        dealer_card = int(self.dealer_var.get())
        all_probabilities = []

        # Calculate dealer bust probability
        dealer_bust_prob = self._calculate_dealer_bust_probability(dealer_card, [dealer_card])
        self.bust_label.config(text=f"Dealer Bust: {dealer_bust_prob * 100:.2f}%")

        for row in range(10):
            for col in range(10):
                card1 = row + 2
                card2 = col + 2

                # Get probabilities from cache
                probs = self.probability_cache[dealer_card][(card1, card2)]
                total_prob = probs['total_prob']
                stand_prob = probs['stand_prob']
                hit_prob = probs['hit_prob']

                hand = [card1, card2]
                hand_total = blackjack.blackjack(hand)[0]

                all_probabilities.append(total_prob)

                # Calculate hit/stand ratio
                hit_ratio = hit_prob / total_prob if total_prob > 0 else 0
                stand_ratio = stand_prob / total_prob if total_prob > 0 else 0

                # Determine action
                if hand_total <= 11:
                    action = "Hit"
                else:
                    action = "Hit" if hit_ratio > stand_ratio else "Stand"

                # Update cell
                cell = self.cells[(row, col)]
                cell['action'].config(text=action)
                cell['prob'].config(text=f"Win: {total_prob * 100:.1f}%")
                cell['ratio'].config(text=f"H/S: {hit_ratio:.2f}/{stand_ratio:.2f}")

                # Color coding
                color = self._get_color(total_prob, action == "Hit")
                text_color = 'white' if total_prob > 0.4 else 'black'

                cell['frame'].configure(bg=color)
                cell['action'].configure(bg=color, fg=text_color)
                cell['prob'].configure(bg=color, fg=text_color)
                cell['ratio'].configure(bg=color, fg=text_color)

        # Update expected value
        expected_value = np.mean(all_probabilities) * 100
        self.ev_label.config(text=f"Expected Win: {expected_value:.2f}%")


def generate_probability_files():
    """Generate CSV files containing all probabilities for each dealer card"""
    # Create directory if it doesn't exist
    if not os.path.exists('single_deck_table'):
        os.makedirs('single_deck_table')

    deck = []
    for i in range(2, 10):
        deck.extend([i] * 4)
    deck.extend([10] * 16)
    deck.extend([11] * 4)

    # Generate for each dealer card
    for dealer_card in range(2, 12):
        filename = os.path.join('single_deck_table', f"blackjack_probs_{dealer_card}.csv")

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['card1', 'card2', 'total_prob', 'stand_prob', 'hit_prob'])

            for card1 in range(2, 12):
                for card2 in range(2, 12):
                    # Calculate remaining deck
                    remaining_deck = deck.copy()
                    remaining_deck.remove(card1)
                    remaining_deck.remove(card2)
                    remaining_deck.remove(dealer_card)

                    # Calculate probabilities
                    total_prob, stand_prob, hit_prob = blackjack.calculate_all(
                        tuple(remaining_deck),
                        tuple([card1, card2]),
                        tuple([dealer_card])
                    )

                    writer.writerow([card1, card2, total_prob, stand_prob, hit_prob])

        print(f"Generated {filename}")


if __name__ == "__main__":
    if not os.path.exists('single_deck_table') or \
            not all(os.path.exists(os.path.join('single_deck_table', f"blackjack_probs_{i}.csv"))
                    for i in range(2, 12)):
        print("Generating probability files...")
        generate_probability_files()

    app = BlackjackAnalyzer()
    app.mainloop()
