import itertools
import random

# the actual texas holdem game code
def createShuffledDeck():
    # 11 = jack, 12 = queen, 13 = king, 14 = ace
    vals = ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14']
    suits = ['spades', 'clubs', 'hearts', 'diamonds']

    # combine into all possible cartesian products of the two lists in the form of tuples, forming our deck
    deck = list(itertools.product(vals, suits))

    # shuffle the deck
    random.shuffle(deck)

    return deck

def printDeck(deck):
    for val, suit in deck:
        print('The %s of %s' % (val, suit))

# the function to draw cards from the deck
def drawCards(deck, num):
    if not deck:
        return "Deck is empty"
    cards = []
    i = 0
    while i < num:
        cards.append(deck.pop())
        i = i + 1
    return cards

# function to deal cards to both players
def gameSetup(deck):
    player1_hand = drawCards(deck, 2)
    player2_hand = drawCards(deck, 2)
    community_cards = drawCards(deck, 5)