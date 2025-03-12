"""
blackjack.py : all functions related to calculating blackjack probability
"""

from functools import lru_cache
from time import time
from time import sleep

import logging
import sys

# Config
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
CACHE_MAXSIZE = 20_000


def blackjack(cards: list) -> list:
    """
    Calculate the total value of a blackjack hand.

    :param cards: List of cards in the hand
    :return: List containing total value(s):
             - [1, 1] if the game is busted
             - [value] when at 11 or higher
             - [higher value, lower value] when hand contains aces
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
            total[0] += 1
            total[1] += 1
    if total[0] > 21 and total[1] > 21:  # Both busted
        return [1, 1]
    elif total[0] > 21 >= total[1]:  # Busted only when Ace is at 11
        return [total[1]]
    else:
        return total


@lru_cache(maxsize=CACHE_MAXSIZE)
def dealer_probability_busted(deck: tuple, dealer_hand: tuple, stand_value: int) -> float:
    """
    Calculate the probability of the dealer busting.

    :param deck: Tuple containing the remaining cards in the deck
    :param dealer_hand: Tuple containing the dealer's current hand
    :param stand_value: The minimum value at which the dealer must stand
    :return: Probability (0.0-1.0) of the dealer busting
    """
    deck = list(deck)
    dealer_hand = list(dealer_hand)

    hand = blackjack(dealer_hand)

    # Check if the dealer has already busted
    if hand == [1, 1]:
        return 1.0

    # Determine the dealer's best hand value
    max_value = hand[0]

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
    """
    Calculate the probability of the dealer getting an exact hand value.

    :param deck: Tuple containing the remaining cards in the deck
    :param dealer_hand: Tuple containing the dealer's current hand
    :param value: The target hand value to calculate probability for
    :return: Probability (0.0-1.0) of dealer getting exactly this value
    """
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
def card_probabilities(deck: tuple, current_hand: tuple, value: int) -> float:
    """
    Calculate the probability of getting a hand value equal to or greater than the target.

    :param deck: Tuple containing the remaining cards in the deck
    :param current_hand: Tuple containing the current hand cards
    :param value: The minimum target value to calculate probability for
    :return: Probability (0.0-1.0) of achieving the target value or higher
    """
    deck = list(deck)
    current_hand = list(current_hand)

    hand = blackjack(current_hand)

    # Check if the hand has already busted
    if hand == [1, 1]:
        return 0.0

    # Determine the hand's value
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


@lru_cache(maxsize=CACHE_MAXSIZE)
def player_probability_busted(deck: tuple, hand: tuple) -> float:
    """
    Calculate the probability of the player busting if they hit (draw one more card).

    :param deck: Tuple containing the remaining cards in the deck
    :param hand: Tuple containing the player's current hand
    :return: Probability (0.0-1.0) of busting when drawing one more card
    """
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


def calculate_win(deck: tuple, hand: tuple, dealer_card: tuple) -> float:
    """
    Calculate the total probability of winning.

    :param deck: Tuple containing the remaining cards in the deck
    :param hand: Tuple containing the player's current hand
    :param dealer_card: Tuple containing the dealer's current hand
    :return: Probability (0.0-1.0) of winning overall
    """
    winning_probability: float = 0.0

    # First case: Dealer busting
    busting_probability = dealer_probability_busted(deck=deck, dealer_hand=dealer_card, stand_value=17)
    winning_probability += busting_probability

    # Next cases: Dealer getting from 17 to 21
    for i in range(17, 22):
        dealer = dealer_probability(deck=deck, dealer_hand=dealer_card, value=i)

        player = card_probabilities(deck=deck, current_hand=hand, value=i)

        case_probability = dealer * player
        winning_probability += case_probability

    return winning_probability


def calculate_stand(deck: tuple, hand: tuple, dealer_card: tuple) -> float:
    """
    Calculate the probability of winning if the player stands.

    :param deck: Tuple containing the remaining cards in the deck
    :param hand: Tuple containing the player's current hand
    :param dealer_card: Tuple containing the dealer's current hand
    :return: Probability (0.0-1.0) of winning if the player stands
    """
    winning_probability: float = 0.0

    hand = list(hand)
    hand = blackjack(hand)[0]

    # First case: Dealer busting
    busting_probability = dealer_probability_busted(deck=deck, dealer_hand=dealer_card, stand_value=17)
    winning_probability += busting_probability

    # Next cases: From 17 to card, if hand greater than 17
    end_value = hand + 1
    if end_value >= 17:
        for i in range(17, end_value):
            case_probability = dealer_probability(deck=deck, dealer_hand=dealer_card, value=i)

            winning_probability += case_probability
    # print(f"Dealer busting probability: {busting_probability}")
    return winning_probability


def calculate_hit(deck: tuple, hand: tuple, dealer_card: tuple) -> float:
    """
    Calculate the probability of winning if the player hits.

    :param deck: Tuple containing the remaining cards in the deck
    :param hand: Tuple containing the player's current hand
    :param dealer_card: Tuple containing the dealer's current hand
    :return: Probability (0.0-1.0) of winning if the player hits
    """
    stand = calculate_stand(deck=deck, hand=hand, dealer_card=dealer_card)
    win = calculate_win(deck=deck, hand=hand, dealer_card=dealer_card)

    return win - stand


def calculate_all(deck: tuple, hand: tuple, dealer_card: tuple, debug: bool = False) -> tuple[float, float, float]:
    """
    Calculate all key probabilities for the current game state.

    :param deck: Tuple containing the remaining cards in the deck
    :param hand: Tuple containing the player's current hand
    :param dealer_card: Tuple containing the dealer's current hand
    :param debug: Whether to output timing information (default=False)
    :return: Tuple containing (win probability, stand probability, hit probability)
    """
    deck = list(deck)
    hand = list(hand)
    dealer_hand = list(dealer_card)

    start = time()
    winning_probability = calculate_win(deck=tuple(deck), hand=tuple(hand), dealer_card=tuple(dealer_hand))
    end = time()
    winning_probability_time = end - start

    start = time()
    stand = calculate_stand(deck=tuple(deck), hand=tuple(hand), dealer_card=tuple(dealer_hand))
    end = time()
    stand_time = end - start

    hit = winning_probability - stand

    if debug:
        logging.debug(f"win probability time: {winning_probability_time * 1000}ms")
        logging.debug(f"stand time: {stand_time * 1000}ms")
        logging.debug(f"dealer_probability_busted cache info: {dealer_probability_busted.cache_info()}")
        logging.debug(f"     dealer_probability   cache info: {dealer_probability.cache_info()}")
        logging.debug(f"     card_probabilities   cache info: {card_probabilities.cache_info()}")
        sleep(0.005)

    return winning_probability, stand, hit


def calculate_bias(empty_deck: tuple, current_deck: tuple) -> float:
    """
    Calculate the bias of the current deck relative to a complete deck.

    A positive bias means more high cards remain; negative means more low cards remain.

    :param empty_deck: Tuple representing a complete/reference deck
    :param current_deck: Tuple representing the current state of the deck
    :return: Percentage bias index (-100 to 100) indicating deck composition
    """
    empty_deck = sorted(list(empty_deck))
    current_deck = sorted(list(current_deck))

    average_empty_value: float = sum(empty_deck) / len(empty_deck)
    average_current_value: float = sum(current_deck) / len(current_deck)

    # Index calculated by percentage change of average values : Maximum value of 100 (highly unlikely)
    index: float = (100 * (average_current_value - average_empty_value)) / average_empty_value

    return index