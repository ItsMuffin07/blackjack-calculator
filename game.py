"""
game.py : a simple demonstration of the blackjack calculator
          by playing a game of blackjack
"""

from blackjack import *
import random

# Config
DEBUG_MODE = False

EMPTY_DECK = (2, 2, 2, 2,
              3, 3, 3, 3,
              4, 4, 4, 4,
              5, 5, 5, 5,
              6, 6, 6, 6,
              7, 7, 7, 7,
              8, 8, 8, 8,
              9, 9, 9, 9,
              10, 10, 10, 10,
              10, 10, 10, 10,  # Jacks
              10, 10, 10, 10,  # Queens
              10, 10, 10, 10,  # Kings
              11, 11, 11, 11)  # Aces



"""
Game using 8 decks
"""

# Create deck using 8 blank decks
deck = list(EMPTY_DECK)
for i in range(7):
    temp = list(EMPTY_DECK)
    for card in temp:
        deck.append(card)

eight_deck = deck.copy()


# Simple game to test code
for i in range(20):
    # Draw player cards
    hand = random.sample(deck, 2)
    for card in hand:
        deck.remove(card)

    # Draw dealer cards
    dealer_hand = random.sample(deck, 1)
    for card in dealer_hand:
        deck.remove(card)
    print(f"Your cards are: {hand[0]} and {hand[1]}")
    player_total = blackjack(hand)
    if len(player_total) > 1:
        if player_total[1] != player_total[0]:
            print(f"You total is {player_total[0]} / {player_total[1]}")
        else:
            print(f"Your total is {player_total[0]}")
    else:
        print(f"Your total is {player_total[0]}")

    print(f"Dealer's card is: {dealer_hand[0]}")


    game_over = False
    finished = False
    while not finished:
        # winning_probability, stand, hit = calculate_all(deck=tuple(deck), hand=tuple(hand),
        #                                                 dealer_card=tuple(dealer_hand),
        #                                                 debug=DEBUG_MODE)
        # busting_probability = player_probability_busted(deck=tuple(deck), hand=tuple(hand))
        # print(f"Probability of winning: {round(winning_probability * 100, 2)}%")
        # print(f"Probability of win if stand: {round(stand * 100, 2)}%")
        # print(f"Probability of win if hit: {round(hit * 100, 2)}%")
        # print(f"Probability of busting: {round(busting_probability * 100, 2)}%")
        index = calculate_bias(tuple(eight_deck), tuple(deck))
        print(f"Bias index: {index}")
        choice = input("Would you like to hit or stand? (h/s) ")
        print("")
        if choice == "h":
            hand.append(random.choice(deck))
            print(hand[-1])
            deck.remove(hand[-1])
            print(f"You drew a {hand[-1]}")
            player_total = blackjack(hand)
            if player_total == [1, 1]:
                print("Busted! You lose!")
                game_over = True
                finished = True
            elif len(player_total) > 1:
                if player_total[1] != player_total[0]:
                    print(f"You total is {player_total[0]} / {player_total[1]}")
                else:
                    print(f"Your total is {player_total[0]}")
            else:
                print(f"Your total is {player_total[0]}")
        elif choice == "s":
            print("You chose to stand.")
            finished = True

    if not game_over:
        print("Now it's time for the dealer to pick a card!")
        finished = False
        while not finished:
            draw_card = random.choice(deck)
            dealer_hand.append(draw_card)
            deck.remove(dealer_hand[-1])
            dealer_total = blackjack(dealer_hand)
            print(f"The dealer drew a {dealer_hand[-1]}")

            if dealer_total == [1, 1]:
                print("The dealer busted! You win!")
                finished = True
            elif len(dealer_total) > 1 and dealer_total[1] != dealer_total[0] and dealer_total[0] < 17:
                print(f"The dealer's current total is {dealer_total[0]} / {dealer_total[1]}")
            elif dealer_total[0] < 17:
                print(f"The dealer's current total is {dealer_total[0]}")
            else:
                if dealer_total[0] > player_total[0]:
                    print(f"The dealer's total is {dealer_total[0]} and player total is {player_total[0]}. You lose!")
                else:
                    print(f"The dealer's total is {dealer_total[0]} and player total is {player_total[0]}. You win!")
                finished = True
    print("")