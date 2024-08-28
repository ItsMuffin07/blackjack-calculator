"""
v0.2.0
"""
import pygame
import sys
import random
import csv
from datetime import datetime
import os

import blackjack

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1250, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Blackjack Probability Calculator")

# Colors
MAIN_BG = (10, 95, 56)  # #0A5F38
SECONDARY_BG = (9, 66, 41)  # #094229
ACCENT = (212, 175, 55)  # #D4AF37
TEXT = (245, 245, 245)  # #F5F5F5
SECONDARY_TEXT = (204, 204, 204)  # #CCCCCC
ALERT = (196, 30, 58)  # #C41E3A
HOVER = (14, 140, 83)  # #0E8C53
BORDER = (184, 134, 11)  # #B8860B
GREYED = (100, 100, 100)  # #646464

# Fonts
FONT = pygame.font.Font(None, 36)
SMALL_FONT = pygame.font.Font(None, 24)

# Card dimensions
CARD_WIDTH, CARD_HEIGHT = 71, 96

# Probability Bar
BAR_WIDTH = 200
BAR_HEIGHT = 20
BAR_X = 950
BAR_Y = 250
STAND_COLOR = (255, 0, 0)  # Bright green
HIT_COLOR = (0, 255, 0)  # Bright yellow

# Buttons
BUTTON_WIDTH = 250
BUTTON_HEIGHT = 50
SMALL_BUTTON_WIDTH = (BUTTON_WIDTH + 10) / 2
BUTTON_SPACING = 10

# Load card images
card_images = {}
for i in range(1, 53):
    filename = f"images/8BitDeck_opt2_{i:02d}.gif"
    if i in [1, 30]:
        filename = filename.replace(".gif", ".jpg")
    card_images[i] = pygame.image.load(filename)
    card_images[i] = pygame.transform.scale(card_images[i], (CARD_WIDTH, CARD_HEIGHT))

# Card slots
DEALER_SLOTS = [(50 + i * (CARD_WIDTH + 10), 50) for i in range(10)]
PLAYER_SLOTS = [(50 + i * (CARD_WIDTH + 10), 200) for i in range(10)]

# Card piles
PILE_POSITIONS = [(50 + i * (CARD_WIDTH + 10), 400) for i in range(10)]

EMPTY_DECK = (2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7,
              8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
              10, 10, 10, 10, 11, 11, 11, 11)

# Discard Pile
DISCARD_PILE_POS = (950, 120)
DISCARD_PILE_SIZE = (CARD_WIDTH, CARD_HEIGHT)

# Load spectral deck image
spectral_deck_image = pygame.image.load("images/spectral_deck.png")
spectral_deck_image = pygame.transform.scale(spectral_deck_image, DISCARD_PILE_SIZE)

# Discard animation constants
GATHERING_POINT = (590, 150)

# Game state
deck_size = 1
dealer_hand = []
player_hand = []
discard_pile = []
deck = list(EMPTY_DECK)
card_piles = [[] for _ in range(10)]  # 2-9, 10(including J,Q,K), A
probabilities = {"win": 0.00, "stand": 0.00, "hit": 0.00, "bust": 0.00}
bias = 0.00
dragging = False
dragged_card = None
dragged_image = None
current_pile_suits = [random.randint(0, 3) for _ in range(10)]  # 0: hearts, 1: diamonds, 2: clubs, 3: spades
card_suits = {}  # This will store the suit for each placed card
card_face = {}
ten_pile_face = random.randint(0, 3)  # 0: 10, 1: J, 2: Q, 3: K
game_log = []

# Button active states
log_button_active = False
deck_size_minus_active = False
deck_size_plus_active = True


def draw_percentage_bars():
    total_probability = probabilities['stand']+probabilities['hit']
    if total_probability == 0:
        stand_width = 0
        hit_width = 0
    else:
        stand_width = BAR_WIDTH * (probabilities['stand'] / total_probability)
        hit_width = BAR_WIDTH * (probabilities['hit'] / total_probability)

    # Draw background
    pygame.draw.rect(screen, (100, 100, 100), (BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT))

    # Draw stand bar
    pygame.draw.rect(screen, STAND_COLOR, (BAR_X, BAR_Y, stand_width, BAR_HEIGHT))

    # Draw hit bar
    pygame.draw.rect(screen, HIT_COLOR, (BAR_X + stand_width, BAR_Y, hit_width, BAR_HEIGHT))

    # Draw border
    pygame.draw.rect(screen, (255, 255, 255), (BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT), 2)

    # Add text labels
    font = pygame.font.Font(None, 24)  # You can adjust the font size as needed

    # Stand label
    stand_text = font.render("Stand", True, (255, 255, 255))
    stand_text_rect = stand_text.get_rect(topleft=(BAR_X, BAR_Y + BAR_HEIGHT + 5))
    screen.blit(stand_text, stand_text_rect)

    # Hit label
    hit_text = font.render("Hit", True, (255, 255, 255))
    hit_text_rect = hit_text.get_rect(topright=(BAR_X + BAR_WIDTH, BAR_Y + BAR_HEIGHT + 5))
    screen.blit(hit_text, hit_text_rect)


def render_deck_size_text():
    deck_size_text = FONT.render(f"Deck Size: {deck_size}", True, TEXT)
    deck_size_text_rect = deck_size_text.get_rect(center=(1085, 75))
    screen.blit(deck_size_text, deck_size_text_rect)


def update_bias():
    global bias
    full_deck = EMPTY_DECK * deck_size
    bias = blackjack.calculate_bias(full_deck, tuple(deck))


def draw_card_background(surface, position):
    card_bg = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
    card_bg.fill((255, 255, 255))  # White background
    surface.blit(card_bg, position)


def initialize_card_piles():
    global card_piles, deck, current_pile_suits
    card_piles = [[] for _ in range(10)]
    deck = list(EMPTY_DECK) * deck_size
    for card in deck:
        if card == 11:  # Ace
            card_piles[9].append(card)
        elif card == 10:  # 10, J, Q, K
            card_piles[8].append(card)
        else:  # 2-9
            card_piles[card - 2].append(card)
    current_pile_suits = [random.randint(0, 3) for _ in range(10)]


def draw_card_piles():
    global ten_pile_face
    for j, pile in enumerate(card_piles):
        if pile:
            suit = current_pile_suits[j]
            draw_card_background(screen, PILE_POSITIONS[j])
            if j == 8:  # 10, J, Q, K pile
                screen.blit(card_images[9 + ten_pile_face + suit * 13], PILE_POSITIONS[j])
            elif j == 9:  # Ace pile
                screen.blit(card_images[13 + suit * 13], PILE_POSITIONS[j])
            else:
                screen.blit(card_images[j + 1 + suit * 13], PILE_POSITIONS[j])
        pygame.draw.rect(screen, BORDER, (*PILE_POSITIONS[j], CARD_WIDTH, CARD_HEIGHT), 2)
        count = SMALL_FONT.render(str(len(pile)), True, TEXT)
        screen.blit(count, (PILE_POSITIONS[j][0] + 5, PILE_POSITIONS[j][1] + CARD_HEIGHT + 5))


def draw_slots():
    # Draw slots
    for slots in DEALER_SLOTS + PLAYER_SLOTS:
        pygame.draw.rect(screen, BORDER, (*slots, CARD_WIDTH, CARD_HEIGHT), 2)

    font = pygame.font.Font(None, 24)  # You can adjust the font size as needed

    # Dealer label and value
    dealer_label = font.render("Dealer", True, TEXT)
    dealer_label_rect = dealer_label.get_rect(topleft=(10, 10))  # Position in the top-left corner (red circle area)
    screen.blit(dealer_label, dealer_label_rect)

    dealer_value = blackjack.blackjack(dealer_hand)
    if len(dealer_value) == 2 or dealer_value[0] == 0:
        if dealer_value[0] == dealer_value[1]:
            dealer_value = dealer_value[0]
        else:
            dealer_value = str(dealer_value[0])+"/"+str(dealer_value[1])
    dealer_value_text = font.render(f"Value: {dealer_value}" if dealer_value != 1 else "BUST", True, TEXT)
    dealer_value_rect = dealer_value_text.get_rect(topleft=(dealer_label_rect.right + 10, dealer_label_rect.top))
    screen.blit(dealer_value_text, dealer_value_rect)

    # Player label and value
    player_label = font.render("Player", True, TEXT)
    player_label_rect = player_label.get_rect(
        bottomleft=(10, PLAYER_SLOTS[0][1] - 10))  # Position above the player slots (black circle area)
    screen.blit(player_label, player_label_rect)

    player_value = blackjack.blackjack(player_hand)
    if len(player_value) == 2 or player_value[0] == 0:
        if player_value[0] == player_value[1]:
            player_value = player_value[0]
        else:
            player_value = str(player_value[0]) + "/" + str(player_value[1])
    player_value_text = font.render(f"Value: {player_value}" if player_value != 1 else "BUST", True, TEXT)
    player_value_rect = player_value_text.get_rect(bottomleft=(player_label_rect.right + 10, player_label_rect.bottom))
    screen.blit(player_value_text, player_value_rect)


def draw_hands():
    for i, card in enumerate(dealer_hand):
        draw_card_background(screen, DEALER_SLOTS[i])
        card_image = get_card_image(card, dealer_hand, i)
        screen.blit(card_images[card_image], DEALER_SLOTS[i])
    for i, card in enumerate(player_hand):
        draw_card_background(screen, PLAYER_SLOTS[i])
        card_image = get_card_image(card, player_hand, i)
        screen.blit(card_images[card_image], PLAYER_SLOTS[i])


def get_card_image(card_value, hand, index):
    global card_face
    if hand is None or index is None:  # For dragging or discarding
        suit = random.randint(0, 3)
        if card_value == 11:  # Ace
            return 13 + suit * 13
        elif card_value == 10:  # 10, J, Q, K
            face = random.randint(0, 3)
            return 9 + face + suit * 13
        else:
            return (card_value - 1) + suit * 13

    if (card_value, id(hand), index) in card_suits:
        suit = card_suits[(card_value, id(hand), index)]
    else:
        suit = random.randint(0, 3)
        card_suits[(card_value, id(hand), index)] = suit

    if card_value == 11:  # Ace
        return 13 + suit * 13
    elif card_value == 10:  # 10, J, Q, K
        if (card_value, id(hand), index) not in card_face:
            card_face[(card_value, id(hand), index)] = random.randint(0, 3)
        face = card_face[(card_value, id(hand), index)]
        return 9 + face + suit * 13
    else:
        return (card_value - 1) + suit * 13


def draw_probabilities():
    win_text = FONT.render(f"Win: {probabilities['win']:.2%}", True, TEXT)
    stand_text = FONT.render(f"Stand: {probabilities['stand']:.2%}", True, TEXT)
    hit_text = FONT.render(f"Hit: {probabilities['hit']:.2%}", True, TEXT)
    bias_text = FONT.render(f"Bias: {bias:.2f}", True, TEXT)
    bust_text = FONT.render(f"Bust: {probabilities['bust']:.2%}", True, TEXT)

    screen.blit(win_text, (950, 300))
    screen.blit(stand_text, (950, 340))
    screen.blit(hit_text, (950, 380))
    screen.blit(bias_text, (950, 420))
    screen.blit(bust_text, (950, 460))


def draw_buttons():
    pygame.draw.rect(screen, ACCENT, reset_button)
    reset_text = FONT.render("Reset", True, TEXT)
    screen.blit(reset_text, (reset_button.x + 60, reset_button.y + 10))

    pygame.draw.rect(screen, ACCENT, calculate_button)
    calculate_text = FONT.render("Calculate", True, TEXT)
    screen.blit(calculate_text, (calculate_button.x + 40, calculate_button.y + 10))

    pygame.draw.rect(screen, ACCENT, deck_size_minus_button)
    pygame.draw.rect(screen, ACCENT, deck_size_plus_button)
    minus_text = FONT.render("-", True, TEXT)
    plus_text = FONT.render("+", True, TEXT)
    screen.blit(minus_text, (deck_size_minus_button.x + 20, deck_size_minus_button.y + 10))
    screen.blit(plus_text, (deck_size_plus_button.x + 20, deck_size_plus_button.y + 10))

    pygame.draw.rect(screen, ACCENT, discard_button)
    discard_text = FONT.render("Discard All", True, TEXT)
    screen.blit(discard_text, (discard_button.x + 30, discard_button.y + 10))


def card_to_value(card):
    if card == 11:
        return 'A'
    elif card == 10:
        return '10/J/Q/K'
    else:
        return str(card)


def calculate_probabilities():
    global probabilities, bias, deck
    if dealer_hand and player_hand:
        probabilities["win"], probabilities["stand"], probabilities["hit"] = blackjack.calculate_all(tuple(deck),
                                                                                                     tuple(player_hand),
                                                                                                     tuple(dealer_hand))
        bias = blackjack.calculate_bias(EMPTY_DECK, tuple(deck))
        probabilities["bust"] = blackjack.player_probability_busted(tuple(deck), tuple(player_hand))

        # print("Player's hand:", [card_to_value(card) for card in player_hand])
        # print("Dealer's hand:", [card_to_value(card) for card in dealer_hand])
        # print("Remaining deck:", [card_to_value(card) for card in deck])
    else:
        probabilities = {"win": 0.00, "stand": 0.00, "hit": 0.00, "bust": 0.00}
        bias = 0.00


def reset_game():
    global dealer_hand, player_hand, discard_pile, probabilities, bias, deck, \
           card_suits, card_face, ten_pile_face, game_log, log_button_active
    dealer_hand = []
    player_hand = []
    discard_pile = []
    probabilities = {"win": 0.00, "stand": 0.00, "hit": 0.00, "bust": 0.00}
    card_suits.clear()
    card_face.clear()
    ten_pile_face = random.randint(0, 3)
    initialize_card_piles()
    update_bias()
    game_log = []
    log_button_active = False
    log_button.enabled = False
    deck_size_minus_button.enabled = deck_size > 1
    deck_size_plus_button.enabled = deck_size < 8


def change_deck_size(change):
    global deck_size, deck_size_minus_active, deck_size_plus_active
    new_deck_size = max(1, min(8, deck_size + change))
    if new_deck_size != deck_size:
        deck_size = new_deck_size
        reset_game()

    deck_size_minus_active = deck_size > 1
    deck_size_plus_active = deck_size < 8
    deck_size_minus_button.enabled = deck_size_minus_active
    deck_size_plus_button.enabled = deck_size_plus_active


def discard_all_cards():
    global dealer_hand, player_hand, discard_pile, card_suits, game_log, log_button_active
    cards_to_discard = dealer_hand + player_hand
    if cards_to_discard:
        game_log.append({
            'dealer_hand': dealer_hand.copy(),
            'player_hand': player_hand.copy(),
            'dealer_sum': blackjack.blackjack(dealer_hand),
            'player_sum': blackjack.blackjack(player_hand),
        })
        log_button_active = True
        log_button.enabled = True
    # print(f"Cards being discarded: {cards_to_discard}")  # Debug print
    if cards_to_discard:  # Only animate and discard if there are cards to discard
        discard_pile.extend(cards_to_discard)
        dealer_hand = []
        player_hand = []
        animate_discard(cards_to_discard)
        card_suits.clear()
        update_bias()
    # print(f"Discard pile after discard: {discard_pile}")  # Debug print


def return_card_to_pile(card, pile_index):
    global deck
    card_piles[pile_index].append(card)
    deck.append(card)


def draw_discard_pile():
    if discard_pile:
        screen.blit(spectral_deck_image, DISCARD_PILE_POS)
    else:
        pygame.draw.rect(screen, BORDER, (*DISCARD_PILE_POS, *DISCARD_PILE_SIZE), 2)

    count = SMALL_FONT.render(str(len(discard_pile)), True, TEXT)
    screen.blit(count, (DISCARD_PILE_POS[0] + 5, DISCARD_PILE_POS[1] + CARD_HEIGHT + 5))


def show_discard_popup():
    popup_width, popup_height = 300, 400
    popup_x = DISCARD_PILE_POS[0] - popup_width - 10
    popup_y = DISCARD_PILE_POS[1]

    pygame.draw.rect(screen, SECONDARY_BG, (popup_x, popup_y, popup_width, popup_height))
    pygame.draw.rect(screen, BORDER, (popup_x, popup_y, popup_width, popup_height), 2)

    title = FONT.render("Discarded Cards", True, TEXT)
    screen.blit(title, (popup_x + 10, popup_y + 10))

    # Count the occurrences of each card value
    card_counts = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0}
    for card in discard_pile:
        card_counts[card] += 1

    y_offset = 50
    for card_value, count in card_counts.items():
        if count > 0:
            card_text = SMALL_FONT.render(f"{card_to_value(card_value)}: {count}", True, TEXT)
            screen.blit(card_text, (popup_x + 10, popup_y + y_offset))
            y_offset += 30
        if y_offset > popup_height - 30:
            break


def animate_discard(cards_to_discard):
    start_positions = [slot for slot in DEALER_SLOTS + PLAYER_SLOTS if slot[0] < DISCARD_PILE_POS[0]]
    end_position = (DISCARD_PILE_POS[0] + CARD_WIDTH/2, DISCARD_PILE_POS[1] + CARD_HEIGHT / 2)

    clock = pygame.time.Clock()
    total_animation_duration = 2000  # milliseconds
    gather_duration = 1000  # milliseconds for gathering phase
    discard_duration = 1000  # milliseconds for discarding phase
    start_time = pygame.time.get_ticks()

    card_images_to_discard = [get_card_image(card, None, None) for card in cards_to_discard]

    # Ensure we have a starting position for each card
    while len(start_positions) < len(cards_to_discard):
        start_positions.append(start_positions[-1])

    while pygame.time.get_ticks() - start_time < total_animation_duration:
        current_time = pygame.time.get_ticks() - start_time
        screen.fill(MAIN_BG)
        draw_card_piles()
        draw_slots()
        draw_hands()
        draw_probabilities()
        for button in buttons:
            button.draw(screen)
        render_deck_size_text()
        draw_discard_pile()

        for i, card_image in enumerate(card_images_to_discard):
            start_pos = start_positions[i]

            if current_time < gather_duration:
                # Gathering phase
                progress = current_time / gather_duration
                current_pos = (
                    start_pos[0] + (GATHERING_POINT[0] - start_pos[0]) * progress,
                    start_pos[1] + (GATHERING_POINT[1] - start_pos[1]) * progress
                )
            else:
                # Discarding phase
                progress = (current_time - gather_duration) / discard_duration
                current_pos = (
                    GATHERING_POINT[0] + (end_position[0] - GATHERING_POINT[0]) * progress,
                    GATHERING_POINT[1] + (end_position[1] - GATHERING_POINT[1]) * progress
                )

            # Create a white background surface
            bg_surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            bg_surface.fill((255, 255, 255))  # White color

            # Calculate the position to blit the surfaces
            bg_rect = bg_surface.get_rect(center=current_pos)
            card_rect = card_images[card_image].get_rect(center=current_pos)

            # Blit the white background and then the card
            screen.blit(bg_surface, bg_rect)
            screen.blit(card_images[card_image], card_rect)

        pygame.display.flip()
        clock.tick(60)

    # Ensure the final state is drawn
    screen.fill(MAIN_BG)
    draw_card_piles()
    draw_slots()
    draw_hands()
    draw_probabilities()
    for button in buttons:
        button.draw(screen)
    render_deck_size_text()
    draw_discard_pile()
    pygame.display.flip()


def return_card_to_original_pile(card):
    global deck, card_piles, current_pile_suits
    deck.append(card)
    if card == 11:  # Ace
        card_piles[9].append(card)
    elif card == 10:  # 10, J, Q, K
        card_piles[8].append(card)
    else:  # 2-9
        card_piles[card - 2].append(card)
    current_pile_suits[card - 2 if card < 10 else 8 if card == 10 else 9] = random.randint(0, 3)
    update_bias()


def show_popup(message):
    popup_font = pygame.font.Font(None, 24)
    popup_text = popup_font.render(message, True, TEXT)
    popup_rect = popup_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    popup_bg = pygame.Surface((popup_rect.width + 20, popup_rect.height + 20))
    popup_bg.fill(SECONDARY_BG)
    popup_bg_rect = popup_bg.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    screen.blit(popup_bg, popup_bg_rect)
    screen.blit(popup_text, popup_rect)
    pygame.display.flip()

    pygame.time.wait(2000)  # Show the popup for 2 seconds


def log_game():
    global game_log, log_button_active
    if not game_log:
        return

    log_dir = os.path.join(os.getcwd(), "game_logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
    filename = f"blackjack_game_{timestamp}.csv"
    filepath = os.path.join(log_dir, filename)

    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = ['dealer_hand', 'player_hand', 'dealer_sum', 'player_sum']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for hand in game_log:
            writer.writerow(hand)

    show_popup(f"Game logged in {filepath}")
    reset_game()
    log_button_active = False
    log_button.enabled = False
    log_button.reset_state()


class Button:
    def __init__(self, x, y, width, height, text, font, action=None, enabled=True):
        self.x = x
        self.y = y

        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action = action
        self.is_hovered = False
        self.is_clicked = False
        self.enabled = enabled
        self.original_y = y
        self.hover_offset = 3
        self.click_offset = 5

    def draw(self, surface):
        color = ACCENT if self.enabled else GREYED
        text_color = TEXT
        y_offset = 0

        if self.is_clicked:
            color = HOVER
            y_offset = self.click_offset
        elif self.is_hovered:
            color = HOVER
            y_offset = self.hover_offset

        pygame.draw.rect(surface, color, (self.rect.x, self.rect.y + y_offset, self.rect.width, self.rect.height))
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        text_rect.y += y_offset
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if not self.enabled:
            self.reset_state()
        elif event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.is_clicked = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_clicked:
                self.is_clicked = False
                if self.rect.collidepoint(event.pos) and self.action:
                    self.action()

    def reset_state(self):
        self.is_hovered = False
        self.is_clicked = False


# Create button instances
discard_button = Button(950, 500, BUTTON_WIDTH, BUTTON_HEIGHT, "Discard All", FONT, discard_all_cards)
calculate_button = Button(950, 560, BUTTON_WIDTH, BUTTON_HEIGHT, "Calculate", FONT, calculate_probabilities)
reset_button = Button(950, 700, SMALL_BUTTON_WIDTH, BUTTON_HEIGHT, "Reset", FONT, reset_game)
log_button = Button(950 + SMALL_BUTTON_WIDTH + BUTTON_SPACING, 700, SMALL_BUTTON_WIDTH, BUTTON_HEIGHT,
                    "Log Game", FONT, action=None, enabled=False)

deck_size_minus_button = Button(950, 50, 50, 50, "-", FONT, lambda: change_deck_size(-1),
                                enabled=deck_size_minus_active)
deck_size_plus_button = Button(1170, 50, 50, 50, "+", FONT, lambda: change_deck_size(1),
                               enabled=deck_size_plus_active)

buttons = [calculate_button, deck_size_minus_button, deck_size_plus_button, discard_button, reset_button, log_button]

# Main game loop
running = True
initialize_card_piles()
show_discard_info = False
previous_suit = None
dragged_face = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        for button in buttons:
            button.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                if pygame.Rect(*DISCARD_PILE_POS, *DISCARD_PILE_SIZE).collidepoint(event.pos):
                    show_discard_info = True
                else:
                    # Check if a dealer slot was clicked
                    for i, slot in enumerate(DEALER_SLOTS):
                        if pygame.Rect(*slot, CARD_WIDTH, CARD_HEIGHT).collidepoint(event.pos) and i < len(dealer_hand):
                            card_to_return = dealer_hand.pop(i)
                            return_card_to_original_pile(card_to_return)
                            # Remove the card's suit and face information
                            card_suits = {k: v for k, v in card_suits.items() if k[1] != id(dealer_hand) or k[2] != i}
                            card_face = {k: v for k, v in card_face.items() if k[1] != id(dealer_hand) or k[2] != i}
                            update_bias()
                            break

                    # Check if a player slot was clicked
                    for i, slot in enumerate(PLAYER_SLOTS):
                        if pygame.Rect(*slot, CARD_WIDTH, CARD_HEIGHT).collidepoint(event.pos) and i < len(player_hand):
                            card_to_return = player_hand.pop(i)
                            return_card_to_original_pile(card_to_return)
                            # Remove the card's suit and face information
                            card_suits = {k: v for k, v in card_suits.items() if k[1] != id(player_hand) or k[2] != i}
                            card_face = {k: v for k, v in card_face.items() if k[1] != id(player_hand) or k[2] != i}
                            update_bias()
                            break

                    # Check if a pile was clicked (for dragging)
                    for i, pile_pos in enumerate(PILE_POSITIONS):
                        if pygame.Rect(*pile_pos, CARD_WIDTH, CARD_HEIGHT).collidepoint(event.pos) and card_piles[i]:
                            dragging = True
                            if i == 8:  # 10, J, Q, K pile
                                dragged_card = 10
                                dragged_face = ten_pile_face
                                dragged_image = 9 + dragged_face + current_pile_suits[i] * 13
                            elif i == 9:  # Ace pile
                                dragged_card = 11
                                dragged_image = 13 + current_pile_suits[i] * 13
                            else:
                                dragged_card = i + 2  # Correct card value (2-9)
                                dragged_image = i + 1 + current_pile_suits[i] * 13
                            deck.remove(dragged_card)
                            card_piles[i].pop()
                            previous_suit = current_pile_suits[i]
                            current_pile_suits[i] = random.randint(0, 3)
                            if i == 8:  # If we took from the 10's pile, change its face
                                ten_pile_face = random.randint(0, 3)
                            update_bias()
                            break

                # Handle log button click
                if log_button.rect.collidepoint(event.pos) and log_button_active:
                    log_game()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and dragging:
                card_placed = False
                for i, slot in enumerate(DEALER_SLOTS):
                    if pygame.Rect(*slot, CARD_WIDTH, CARD_HEIGHT).collidepoint(event.pos):
                        dealer_hand.append(dragged_card)
                        card_suits[(dragged_card, id(dealer_hand), len(dealer_hand) - 1)] = previous_suit
                        if dragged_card == 10:
                            card_face[(dragged_card, id(dealer_hand), len(dealer_hand) - 1)] = dragged_face
                        card_placed = True
                        update_bias()
                        break
                for i, slot in enumerate(PLAYER_SLOTS):
                    if pygame.Rect(*slot, CARD_WIDTH, CARD_HEIGHT).collidepoint(event.pos):
                        player_hand.append(dragged_card)
                        card_suits[(dragged_card, id(player_hand), len(player_hand) - 1)] = previous_suit
                        if dragged_card == 10:
                            card_face[(dragged_card, id(player_hand), len(player_hand) - 1)] = dragged_face
                        card_placed = True
                        update_bias()
                        break

                if not card_placed:
                    return_card_to_pile(dragged_card,
                                        dragged_card - 2 if dragged_card < 10 else 8 if dragged_card == 10 else 9)
                    current_pile_suits[
                        dragged_card - 2 if dragged_card < 10 else 8 if dragged_card == 10 else 9] = previous_suit
                    update_bias()

                dragging = False
                dragged_card = None
                dragged_image = None

            show_discard_info = False

    screen.fill(MAIN_BG)
    draw_card_piles()
    draw_slots()
    draw_hands()
    draw_probabilities()
    draw_percentage_bars()
    for button in buttons:
        button.draw(screen)
    render_deck_size_text()
    draw_discard_pile()

    if dragging and dragged_image:
        mouse_pos = pygame.mouse.get_pos()
        drag_pos = (mouse_pos[0] - CARD_WIDTH // 2, mouse_pos[1] - CARD_HEIGHT // 2)
        draw_card_background(screen, drag_pos)
        screen.blit(card_images[dragged_image], drag_pos)

    if show_discard_info:
        show_discard_popup()

    pygame.display.flip()

pygame.quit()
sys.exit()
