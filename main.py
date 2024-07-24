import pygame
import sys
import random
import blackjack

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Blackjack Probability Calculator")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (220, 220, 220)

# Fonts
FONT = pygame.font.Font(None, 36)
SMALL_FONT = pygame.font.Font(None, 24)

# Card dimensions
CARD_WIDTH, CARD_HEIGHT = 71, 96

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

# Buttons
reset_button = pygame.Rect(950, 700, 200, 50)
calculate_button = pygame.Rect(950, 600, 200, 50)
deck_size_minus_button = pygame.Rect(950, 50, 50, 50)
deck_size_plus_button = pygame.Rect(1100, 50, 50, 50)
discard_button = pygame.Rect(950, 500, 200, 50)

# Card piles
PILE_POSITIONS = [(50 + i * (CARD_WIDTH + 10), 400) for i in range(10)]

EMPTY_DECK = (2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7,
              8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
              10, 10, 10, 10, 11, 11, 11, 11)

# Game state
deck_size = 1
dealer_hand = []
player_hand = []
discard_pile = []
deck = list(EMPTY_DECK)
card_piles = [[] for _ in range(10)]  # 2-9, 10(including J,Q,K), A
probabilities = {"win": 0.00, "stand": 0.00, "hit": 0.00}
bias = 0.00
dragging = False
dragged_card = None
dragged_image = None
current_pile_suits = [random.randint(0, 3) for _ in range(10)]  # 0: hearts, 1: diamonds, 2: clubs, 3: spades
card_suits = {}  # This will store the suit for each placed card


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
    for i, pile in enumerate(card_piles):
        if pile:
            suit = current_pile_suits[i]
            if i == 8:  # 10, J, Q, K pile
                screen.blit(card_images[9 + suit * 13], PILE_POSITIONS[i])
            elif i == 9:  # Ace pile
                screen.blit(card_images[13 + suit * 13], PILE_POSITIONS[i])
            else:
                screen.blit(card_images[i + 1 + suit * 13], PILE_POSITIONS[i])
        pygame.draw.rect(screen, BLACK, (*PILE_POSITIONS[i], CARD_WIDTH, CARD_HEIGHT), 2)
        count = SMALL_FONT.render(str(len(pile)), True, BLACK)
        screen.blit(count, (PILE_POSITIONS[i][0] + 5, PILE_POSITIONS[i][1] + CARD_HEIGHT + 5))

def draw_slots():
    for slot in DEALER_SLOTS + PLAYER_SLOTS:
        pygame.draw.rect(screen, GRAY, (*slot, CARD_WIDTH, CARD_HEIGHT), 2)


def draw_hands():
    for i, card in enumerate(dealer_hand):
        card_image = get_card_image(card, dealer_hand, i)
        screen.blit(card_images[card_image], DEALER_SLOTS[i])
    for i, card in enumerate(player_hand):
        card_image = get_card_image(card, player_hand, i)
        screen.blit(card_images[card_image], PLAYER_SLOTS[i])


def get_card_image(card_value, hand, index):
    global card_face
    if hand is None or index is None:  # For dragging
        suit = random.randint(0, 3)
        if card_value == 11:  # Ace
            return 13 + suit * 13
        elif card_value == 10:  # 10, J, Q, K
            return 9 + suit * 13  # Always use 10 for dragging
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
    win_text = FONT.render(f"Win: {probabilities['win']:.2%}", True, BLACK)
    stand_text = FONT.render(f"Stand: {probabilities['stand']:.2%}", True, BLACK)
    hit_text = FONT.render(f"Hit: {probabilities['hit']:.2%}", True, BLACK)
    bias_text = FONT.render(f"Bias: {bias:.2f}", True, BLACK)

    screen.blit(win_text, (950, 300))
    screen.blit(stand_text, (950, 350))
    screen.blit(hit_text, (950, 400))
    screen.blit(bias_text, (950, 450))


def draw_buttons():
    pygame.draw.rect(screen, LIGHT_GRAY, reset_button)
    reset_text = FONT.render("Reset", True, BLACK)
    screen.blit(reset_text, (reset_button.x + 60, reset_button.y + 10))

    pygame.draw.rect(screen, LIGHT_GRAY, calculate_button)
    calculate_text = FONT.render("Calculate", True, BLACK)
    screen.blit(calculate_text, (calculate_button.x + 40, calculate_button.y + 10))

    pygame.draw.rect(screen, LIGHT_GRAY, deck_size_minus_button)
    pygame.draw.rect(screen, LIGHT_GRAY, deck_size_plus_button)
    minus_text = FONT.render("-", True, BLACK)
    plus_text = FONT.render("+", True, BLACK)
    screen.blit(minus_text, (deck_size_minus_button.x + 20, deck_size_minus_button.y + 10))
    screen.blit(plus_text, (deck_size_plus_button.x + 20, deck_size_plus_button.y + 10))

    deck_size_text = FONT.render(f"Deck Size: {deck_size}", True, BLACK)
    screen.blit(deck_size_text, (1010, 60))

    pygame.draw.rect(screen, LIGHT_GRAY, discard_button)
    discard_text = FONT.render("Discard All", True, BLACK)
    screen.blit(discard_text, (discard_button.x + 30, discard_button.y + 10))


def card_to_value(card):
    if card == 11:
        return 'A'
    elif card == 10:
        return '10'
    else:
        return str(card)


def calculate_probabilities():
    global probabilities, bias
    if dealer_hand and player_hand:
        probabilities["win"], probabilities["stand"], probabilities["hit"] = blackjack.calculate_all(tuple(deck),
                                                                                                     tuple(player_hand),
                                                                                                     tuple(dealer_hand))
        bias = blackjack.calculate_bias(EMPTY_DECK,
                                        tuple(set(deck) - set(dealer_hand) - set(player_hand) - set(discard_pile)))

        print("Player's hand:", [card_to_value(card) for card in player_hand])
        print("Dealer's hand:", [card_to_value(card) for card in dealer_hand])
        print("Remaining deck:", [card_to_value(card) for card in deck])
    else:
        probabilities = {"win": 0.00, "stand": 0.00, "hit": 0.00}
        bias = 0.00


def reset_game():
    global dealer_hand, player_hand, discard_pile, probabilities, bias, deck, card_suits
    dealer_hand = []
    player_hand = []
    discard_pile = []
    probabilities = {"win": 0.00, "stand": 0.00, "hit": 0.00}
    bias = 0.00
    card_suits.clear()
    initialize_card_piles()


def change_deck_size(change):
    global deck_size
    deck_size = max(1, min(8, deck_size + change))
    reset_game()


def discard_all_cards():
    global dealer_hand, player_hand, discard_pile, deck, card_suits
    discard_pile.extend(dealer_hand + player_hand)
    for card in dealer_hand + player_hand:
        deck.remove(card)
    dealer_hand = []
    player_hand = []
    card_suits.clear()


def return_card_to_pile(card, pile_index):
    global deck
    card_piles[pile_index].append(card)
    deck.append(card)


# Main game loop
running = True
initialize_card_piles()
card_face = {}

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                if reset_button.collidepoint(event.pos):
                    reset_game()
                elif calculate_button.collidepoint(event.pos):
                    calculate_probabilities()
                elif deck_size_minus_button.collidepoint(event.pos):
                    change_deck_size(-1)
                elif deck_size_plus_button.collidepoint(event.pos):
                    change_deck_size(1)
                elif discard_button.collidepoint(event.pos):
                    discard_all_cards()
                else:
                    for i, pile_pos in enumerate(PILE_POSITIONS):
                        if pygame.Rect(*pile_pos, CARD_WIDTH, CARD_HEIGHT).collidepoint(event.pos) and card_piles[i]:
                            dragging = True
                            if i == 8:  # 10, J, Q, K pile
                                dragged_card = 10
                            elif i == 9:  # Ace pile
                                dragged_card = 11
                            else:
                                dragged_card = i + 2  # Correct card value (2-9)
                            dragged_image = i + 1 + current_pile_suits[i] * 13
                            deck.remove(dragged_card)
                            card_piles[i].pop()
                            previous_suit = current_pile_suits[i]
                            current_pile_suits[i] = random.randint(0, 3)
                            break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and dragging:
                card_placed = False
                for i, slot in enumerate(DEALER_SLOTS):
                    if pygame.Rect(*slot, CARD_WIDTH, CARD_HEIGHT).collidepoint(event.pos):
                        dealer_hand.append(dragged_card)
                        card_suits[(dragged_card, id(dealer_hand), len(dealer_hand) - 1)] = previous_suit
                        if dragged_card == 10:
                            card_face[(dragged_card, id(dealer_hand), len(dealer_hand) - 1)] = random.randint(0, 3)
                        card_placed = True
                        break
                for i, slot in enumerate(PLAYER_SLOTS):
                    if pygame.Rect(*slot, CARD_WIDTH, CARD_HEIGHT).collidepoint(event.pos):
                        player_hand.append(dragged_card)
                        card_suits[(dragged_card, id(player_hand), len(player_hand) - 1)] = previous_suit
                        if dragged_card == 10:
                            card_face[(dragged_card, id(player_hand), len(player_hand) - 1)] = random.randint(0, 3)
                        card_placed = True
                        break

                if not card_placed:
                    return_card_to_pile(dragged_card,
                                        dragged_card - 2 if dragged_card < 10 else 8 if dragged_card == 10 else 9)
                    current_pile_suits[
                        dragged_card - 2 if dragged_card < 10 else 8 if dragged_card == 10 else 9] = previous_suit

                dragging = False
                dragged_card = None
                dragged_image = None

    screen.fill(WHITE)
    draw_card_piles()
    draw_slots()
    draw_hands()
    draw_probabilities()
    draw_buttons()

    if dragging and dragged_image:
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(card_images[dragged_image], (mouse_pos[0] - CARD_WIDTH // 2, mouse_pos[1] - CARD_HEIGHT // 2))

    pygame.display.flip()

pygame.quit()
sys.exit()