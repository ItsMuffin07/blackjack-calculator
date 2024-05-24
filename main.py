from functools import lru_cache
from time import time
import random

CACHE_MAXSIZE = None

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


def blackjack(cards: list) -> list:
    """
    :param cards: list of cards in deck
    :return: list containing total value, index 0 is the higher value if there is an ace
             returns [1,1] if game is over
             returns [value] when at 11, game is busted
             returns [higher value, lower value] for both combinations of ace
    """
    total = [0, 0]
    for card in cards:
        if card != 11:
            total[0] += card
            total[1] += card
        elif total[0] == total[1]:  # First ace
            total[0] += 11  # index 0 is the higher one
            total[1] += 1  # index 1 is the lower one
        else:  # When more than one ace
            total[0] += card
            total[1] += card
    if total[0] > 21 and total[1] > 21:  # Both busted
        return [1, 1]
    elif total[0] > 21 and total[1] <= 21:  # Busted only when Ace is at 11
        return [total[1]]
    else:
        return total


@lru_cache(maxsize=CACHE_MAXSIZE)
def dealer_probability_busted(deck: tuple, dealer_hand: tuple,
                              stand_value: int) -> float:  # Generated by AI by modifying my code
    """
    :param deck: current remaining branch deck
    :param dealer_hand: current branch hand
    :return: probability of current branch busting
    """
    deck = list(deck)
    dealer_hand = list(dealer_hand)

    hand = blackjack(dealer_hand)

    # Check if the dealer has already busted
    if hand == [1, 1]:
        return 1.0

    # Determine the dealer's best hand value
    max_value = hand[0]
    if len(hand) > 1:
        min_value = hand[1]
    else:
        min_value = max_value

    # If the dealer should stand based on the higher value
    if max_value >= stand_value:
        return 0.0

    busted_probability = 0.0

    for card in deck:
        curr_probability = 1 / len(deck)  # Current branch probability

        temp_deck = deck.copy()
        temp_deck.remove(card)  # Remove card from the deck

        new_hand = dealer_hand.copy()
        new_hand.append(card)  # Add new card to hand

        branch_probability = dealer_probability_busted(deck=tuple(temp_deck),
                                                       dealer_hand=tuple(new_hand),
                                                       stand_value=stand_value)
        busted_probability += branch_probability * curr_probability

    return busted_probability


@lru_cache(maxsize=CACHE_MAXSIZE)
def dealer_probability(deck: tuple, dealer_hand: tuple, value: int) -> float:
    '''
    :param deck: current remaining branch deck
    :param dealer_hand: current branch hand
    :param value: target value
    :return: probability of current branch getting exact value
    '''
    deck = list(deck)
    dealer_hand = list(dealer_hand)

    hand = blackjack(dealer_hand)

    # Check if the dealer has already busted
    if hand == [1, 1]:
        return 0.0

    # Determine the dealer's best hand value
    max_value = hand[0]
    if len(hand) > 1:
        min_value = hand[1]
    else:
        min_value = max_value

    # If either value is at the target value
    if max_value == value or min_value == value:
        return 1.0
    elif max_value >= 17:  # No need to count as higher than value already
        return 0

    value_probability = 0.0

    for card in deck:
        curr_probability = 1 / len(deck)  # Current branch probability

        temp_deck = deck.copy()
        temp_deck.remove(card)  # Remove card from the deck

        new_hand = dealer_hand.copy()
        new_hand.append(card)  # Add new card to hand

        branch_probability = dealer_probability(deck=tuple(temp_deck),
                                                dealer_hand=tuple(new_hand),
                                                value=value)
        value_probability += branch_probability * curr_probability

    return value_probability


@lru_cache(maxsize=CACHE_MAXSIZE)
def card_probabilities(deck: tuple, current_hand: tuple, value: int) -> float:  # Generated by AI by modifying my code
    '''
    :param deck: current remaining branch deck
    :param current_hand: current branch hand
    :param value: the probability of getting a certain value
    :return: probability of current branch obtaining certain value or above (BUT VALID)
    '''
    deck = list(deck)
    current_hand = list(current_hand)

    hand = blackjack(current_hand)

    # Check if the hand has already busted
    if hand == [1, 1]:
        return 0.0

    # Determine the dealer's best hand value
    max_value = hand[0]
    if len(hand) > 1:
        min_value = hand[1]
    else:
        min_value = max_value

    # Determine if max value is the value that we are looking for or greater (not busted due to above)
    if max_value >= value or min_value >= value:
        return 1.0

    value_probability = 0.0

    for card in deck:
        curr_probability = 1 / len(deck)  # Current branch probability

        temp_deck = deck.copy()
        temp_deck.remove(card)  # Remove card from the deck

        new_hand = current_hand.copy()
        new_hand.append(card)  # Add new card to hand

        value_branch_probability = card_probabilities(deck=tuple(temp_deck),
                                                      current_hand=tuple(new_hand),
                                                      value=value)
        value_probability += value_branch_probability * curr_probability

    return value_probability


def player_probability_busted(deck: tuple, hand: tuple) -> float:
    '''
    :param deck: The remaining deck before drawing
    :param hand: Player's cards
    :param dealer_card: Dealer's card (optional, but removes it from )
    :return: Probability of busting when pulling one card
    '''
    hand = list(hand)
    deck = list(deck)

    total: list = blackjack(hand)
    maximum_pull: int = 21 - total[-1]
    if total == [1, 1]:  # Busted already
        return 0

    can_pull: int = 0  # Counter for how many player can pull to not bust
    for card in deck:
        new_hand = hand.copy()
        new_hand.append(card)
        new_hand = blackjack(new_hand)[-1]
        if new_hand == 1:
            pass
        elif (new_hand - sum(hand)) <= maximum_pull:
            can_pull += 1

    success_probability: float = 1 - (can_pull / len(deck))

    return success_probability

@lru_cache
def calculate_win(deck: tuple, hand: tuple, dealer_card: tuple) -> float:
    """
    :param deck: The remaining deck
    :param hand: Player's hand
    :param dealer_card: Dealer's card
    :return: Total winning probability
    """
    winning_probability: float = 0.0

    # First case: Dealer busting
    busting_probability = dealer_probability_busted(deck=deck, dealer_hand=dealer_card, stand_value=17)
    winning_probability += busting_probability

    # Next cases: Dealer getting from 17 to 21
    for i in range(17, 22):
        dealer = dealer_probability(deck=deck, dealer_hand=dealer_card, value=i)
        dealer_probability.cache_clear()

        player = card_probabilities(deck=deck, current_hand=hand, value=i)
        card_probabilities.cache_clear()

        case_probability = dealer * player
        winning_probability += case_probability

    return winning_probability

@lru_cache
def calculate_stand(deck: tuple, hand: tuple, dealer_card: tuple) -> float:
    """
    :param deck: The remaining deck
    :param hand: Player's hand
    :param dealer_card: Dealer's card
    :return: winning probability if stand
    """
    winning_probability: float = 0.0

    hand = list(hand)
    hand = blackjack(hand)[0]

    # First case: Dealer busting
    busting_probability = dealer_probability_busted(deck=deck, dealer_hand=dealer_card, stand_value=17)
    winning_probability += busting_probability

    # Next cases: From 17 to card
    end_value = min([hand, 21]) + 1
    if end_value >= 17:
        for i in range(17, end_value):
            dealer = dealer_probability(deck=deck, dealer_hand=dealer_card, value=i)
            dealer_probability.cache_clear()

            case_probability = dealer
            winning_probability += case_probability

    return winning_probability

@lru_cache
def calculate_hit(deck: tuple, hand: tuple, dealer_card: tuple) -> float:
    """
    :param deck: The remaining deck
    :param hand: Player's hand
    :param dealer_card: Dealer's card
    :return: probability of a win if hit
    """
    stand = calculate_stand(deck=deck, hand=hand, dealer_card=dealer_card)
    win = calculate_win(deck=deck, hand=hand, dealer_card=dealer_card)

    return win - stand


def calculate_all(deck: tuple, hand: tuple, dealer_card: tuple) -> tuple[float, float, float]:
    """
    :param deck: The remaining deck
    :param hand: Player's hand
    :param dealer_card: Dealer's card
    :return: winning probability, winning probability if stand, winning probability if hit
    """
    deck = list(deck)
    hand = list(hand)
    dealer_hand = list(dealer_card)

    winning_probability = calculate_win(deck=tuple(deck), hand=tuple(hand), dealer_card=tuple(dealer_hand))
    stand = calculate_stand(deck=tuple(deck), hand=tuple(hand), dealer_card=tuple(dealer_hand))
    hit = calculate_hit(deck=tuple(deck), hand=tuple(hand), dealer_card=tuple(dealer_hand))

    return winning_probability, stand, hit


deck = list(EMPTY_DECK)

for i in range(7):
    temp = list(EMPTY_DECK)
    for card in temp:
        deck.append(card)

# Test dealer_probability function

# start_time = time()

# hand = [11]
# deck.remove(11)
# total = 0
# for i in range(17,22):
#     temp = dealer_probability(deck=tuple(deck), dealer_hand=tuple(hand), value=i)
#     print(i, temp)
#     total += temp
# bust = dealer_probability_busted(deck=tuple(deck),dealer_hand=tuple(hand),stand_value=17)
# print(f"bust: {bust}")
# total += bust
# print(f"total: {total}")
# print(dealer_probability.cache_info())
#
# end_time = time()
#
# print(f"Run time: {(end_time - start_time) * 1000}ms")


# Test card_probabilities and player_probability_busted function

# hand = [10,5]
# deck.remove(11)
# deck.remove(5)
# x = card_probabilities(deck=tuple(deck), current_hand=tuple(hand), value=17)
# y = player_probability_busted(deck=tuple(deck), hand=tuple(hand))
# print(x, y)
# print(x+y)

# Test calculate winning probability functions
for i in range(20):
    # Draw player cards
    hand = random.sample(deck, 2)
    for card in hand:
        deck.remove(card)

    # Draw dealer cards
    dealer_hand = random.sample(deck,1)
    for card in dealer_hand:
        deck.remove(card)

    print(f"Your cards are: {hand[0]} and {hand[1]}")
    print(f"Dealer's cards are: {dealer_hand[0]}")

    winning_probability, stand, hit = calculate_all(deck=tuple(deck),hand=tuple(hand),dealer_card=tuple(dealer_hand))
    print(f"probability of winning: {winning_probability}")
    print(f"probability of win if stand: {stand}")
    print(f"probability of win if hit: {hit}")