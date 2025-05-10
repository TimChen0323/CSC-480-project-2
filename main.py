import itertools
import random
from collections import Counter
import math
import time

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

# prints cards
def printCards(cards):
    for val, suit in cards:
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


# function to deal cards to both players, setup community cards
def gameSetup(deck):
    player1_hand = drawCards(deck, 2)
    player2_hand = drawCards(deck, 2)
    community_cards = drawCards(deck, 5)
    return player1_hand, player2_hand, community_cards


# a bunch of functions to check specific hands

# helper function to split hands into suits and ranks
def getRanksAndSuits(hand_of_5_cards):
    ranks = sorted([int(card[0]) for card in hand_of_5_cards])
    suits = [card[1] for card in hand_of_5_cards]
    return ranks, suits


def checkRoyalFlush(hand):
    ranks, suits = getRanksAndSuits(hand)
    # checking that all suits are equal, and it is 10 to Ace
    if all(suit == suits[0] for suit in suits) and ranks == [10, 11, 12, 13, 14]:
        return True
    else:
        return False


def checkStraight(hand):
    ranks, suits = getRanksAndSuits(hand)
    is_normal_straight = True
    for i in range(4):
        if ranks[i] + 1 != ranks[i + 1]:
            is_normal_straight = False
            break
    # if it is a straight that doesn't involve a low ace, return true
    if is_normal_straight:
        return True, ranks[4]

    # check for a low ace
    if ranks == [2, 3, 4, 5, 14]:
        return True, 5

    # if not, then false
    return False, 0


def checkFlush(hand):
    ranks, suits = getRanksAndSuits(hand)  # ranks are sorted ascending here
    if all(suit == suits[0] for suit in suits):
        return True, sorted(ranks, reverse=True)  # Return ranks sorted descending to match with rest
    else:
        return False, []


def checkStraightFlush(hand):
    isFlush = checkFlush(hand)[0]
    isStraight, highest = checkStraight(hand)
    if isStraight and isFlush:
        return True, highest
    else:
        return False, 0


# gets counts for every card, allowing us to check for pairs, triples, quadruples, etc
# e.g., for KKKQQ -> [(13,3), (12,2)]
# e.g., for AAAKQ -> [(14,3), (13,1), (12,1)]
def getRankCounts(hand):
    ranks_int = [int(card[0]) for card in hand]
    counts = Counter(ranks_int)

    sorted_rank_counts = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    return sorted_rank_counts


def checkFourOfAKind(hand):
    counts = getRankCounts(hand)
    if counts[0][1] == 4:
        # (True, rank_of_quad, kicker)
        return True, counts[0][0], counts[1][0]
    else:
        return False, 0, 0


def checkFullHouse(hand):
    counts = getRankCounts(hand)
    if counts[0][1] == 3 and counts[1][1] == 2:
        # (True, rank_of_triple, rank_of_pair)
        return True, counts[0][0], counts[1][0]
    else:
        return False, 0, 0


def checkThreeOfAKind(hand):
    counts = getRankCounts(hand)
    if counts[0][1] == 3:
        # (True, rank_of_triple, kicker1, kicker2)
        return True, counts[0][0], sorted([counts[1][0], counts[2][0]], reverse=True)
    else:
        return False, 0, [0, 0]


def checkTwoPair(hand):
    counts = getRankCounts(hand)
    if counts[0][1] == 2 and counts[1][1] == 2:
        # (True, rank_of_pair, rank_of_pair2, kicker)
        return True, [counts[0][0], counts[1][0]], counts[2][0]
    else:
        return False, [0, 0], 0


def checkOnePair(hand):
    counts = getRankCounts(hand)
    if counts[0][1] == 2:
        # (True, rank_of_pair, kicker1, kicker2, kicker3)
        return True, counts[0][0], sorted([counts[1][0], counts[2][0], counts[3][0]], reverse=True)
    else:
        return False, 0, [0, 0, 0]


# function that checks hands in order from highest value to lowest
def checkHand(hand):
    isRF = checkRoyalFlush(hand)
    if isRF:
        return 10, []

    isSF, highestSF = checkStraightFlush(hand)
    if isSF:
        return 9, highestSF

    is4k, rank4k, kicker4k = checkFourOfAKind(hand)
    if is4k:
        return 8, rank4k, kicker4k

    isFH, FHtrip, FHpair = checkFullHouse(hand)
    if isFH:
        return 7, FHtrip, FHpair

    isFlush, ranksFlush = checkFlush(hand)
    if isFlush:
        return 6, ranksFlush

    isStraight, highestStraight = checkStraight(hand)
    if isStraight:
        return 5, highestStraight

    is3k, rank3k, kickers3k = checkThreeOfAKind(hand)
    if is3k:
        return 4, rank3k, kickers3k

    is2p, ranks2p, kicker2p = checkTwoPair(hand)
    if is2p:
        return 3, ranks2p, kicker2p

    is1p, rank1p, kickers1p = checkOnePair(hand)
    if is1p:
        return 2, rank1p, kickers1p

    # high card
    ranks, _ = getRanksAndSuits(hand)
    return 1, sorted(ranks, reverse=True)  # Return rank 1 and list of card ranks as kickers


# a function where given at least 5 cards, returns the best possible hand that can be made
def getBestHand(available_cards):
    if len(available_cards) < 5:
        # this really shouldn't happen
        raise ValueError("Cannot evaluate a hand with fewer than 5 cards.")

    best_eval = (0, [])  # worst possible hand

    # for every combination of 5 within seven cards
    for five_card_combo in itertools.combinations(available_cards, 5):
        current_eval = checkHand(list(five_card_combo))
        if current_eval > best_eval:
            best_eval = current_eval
    return best_eval


# given two hands, return the player that will win as a string. bot = player1, player = player2
def checkHands(hand1, hand2, community_cards):
    player1_hand = hand1 + community_cards
    player2_hand = hand2 + community_cards

    player1_best = getBestHand(player1_hand)
    player2_best = getBestHand(player2_hand)

    # return who has the best hand by directly comparing tuples
    if player1_best > player2_best:
        return "bot"
    elif player2_best > player1_best:
        return "player"
    else:
        return "tie"


# MCTS stuff
max_children = 2048 # limiting to 2048 since from each node there's millions of possible children.
class MonteCarloTreeSearchNode:
    def __init__(self, state, parent=None):
        self.wins = 0
        self.visits = 0
        self.children = []
        self.parent = parent
        # state consists of (bot hand [], opp hand [], known community cards [], deck with known cards subtracted [])
        self.state = state

    def bestChild(self, c_param=1.41):
        best_score = -float('inf')
        best_child = None
        for child in self.children:
            if child.visits == 0:
                # by making unvisited children have infinite score, they get prioritized since inf will always be >
                score = float('inf')
            else:
                # ucb1 score
                score = (child.wins / child.visits) + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            if score > best_score:
                best_score = score
                best_child = child
        return best_child

def monteCarloTreeSearch(root: MonteCarloTreeSearchNode, time_limit_seconds=9.5):
    start_time = time.time()

    while (time.time() - start_time) < time_limit_seconds:
        # does both expansion and selection
        leaf = tree_policy(root)
        # step 3 : rollout
        simulation_result = rollout(leaf)
        # step 4 : backpropogate
        while leaf:
            leaf.visits += 1
            leaf.wins += simulation_result
            leaf = leaf.parent
    return root.wins / root.visits

def tree_policy(node):
    while not isShowdownState(node.state):

        # expansion
        if len(node.children) < max_children:
            return expand(node)

        # selection
        node = node.bestChild()

    return node

def expand(parent):
    my_cards, opp_hand, comm_cards, deck = parent.state

    deck_copy = list(deck)
    random.shuffle(deck_copy)

    new_comm = list(comm_cards)
    while len(new_comm) < 5:
        new_comm.append(deck_copy.pop())

    child_state = (my_cards, opp_hand, new_comm, deck_copy)
    child = MonteCarloTreeSearchNode(child_state, parent)
    parent.children.append(child)
    return child

# represents our terminal node
def isShowdownState(node_state):
    _, _, comm_cards, _ = node_state
    return len(comm_cards) == 5

def rollout(sim_node: MonteCarloTreeSearchNode):
    my_cards, opp_hand, comm_cards, parent_deck = sim_node.state

    # we're making copies so we don't mess up parent deck
    sim_deck = list(parent_deck)
    random.shuffle(sim_deck)
    sim_opp = list(opp_hand) if opp_hand else []
    sim_comm = list(comm_cards) if comm_cards else []

    # 1. Make sure opponent has 2 cards
    if len(sim_opp) < 2:
        needed = 2 - len(sim_opp)
        drawn_for_opp = drawCards(sim_deck, needed)
        sim_opp.extend(drawn_for_opp)

    # 2. Ensure 5 community cards
    if len(sim_comm) < 5:
        needed = 5 - len(sim_comm)
        # Determine how many to draw for flop, turn, river based on current count
        drawn_for_comm = drawCards(sim_deck, needed)
        sim_comm.extend(drawn_for_comm)

    winner = checkHands(my_cards, sim_opp, sim_comm)
    if winner == "bot":
        return 1
    elif winner == "tie":
        return 0.5
    else:
        return 0

def playPoker():
    # pre-flop
    deck = createShuffledDeck()
    player1_hand = drawCards(deck, 2)
    mcts_deck_initial = list(deck)
    player2_hand = drawCards(deck, 2)
    # state consists of (bot hand [], opp hand [], known community cards [], deck with known cards subtracted [])

    pre_flop_node = MonteCarloTreeSearchNode((player1_hand, [], [], mcts_deck_initial))
    if monteCarloTreeSearch(pre_flop_node) < 0.5:
        print("player1 hand (bot)")
        printCards(player1_hand)
        print("player2 hand")
        printCards(player2_hand)
        return "folded in preflop"

    print("proceeding to flop stage")
    # flop
    community_cards = drawCards(mcts_deck_initial, 3)
    mcts_deck_flop = list(mcts_deck_initial)
    flop_node = MonteCarloTreeSearchNode((player1_hand, [], community_cards, mcts_deck_flop))
    if monteCarloTreeSearch(flop_node) < 0.5:
        print("player1 hand (bot)")
        printCards(player1_hand)
        print("player2 hand")
        printCards(player2_hand)
        print("community cards")
        printCards(community_cards)
        return "folded in flop"

    print("proceeding to turn stage")
    # turn
    community_cards.extend(drawCards(mcts_deck_initial, 1))
    mcts_deck_turn = list(mcts_deck_initial)
    turn_node = MonteCarloTreeSearchNode((player1_hand, [], community_cards, mcts_deck_turn))
    if monteCarloTreeSearch(turn_node) < 0.5:
        print("player1 hand (bot)")
        printCards(player1_hand)
        print("player2 hand")
        printCards(player2_hand)
        print("community cards")
        printCards(community_cards)
        return "folded in turn"

    print("proceeding to river stage")
    # river
    community_cards.extend(drawCards(mcts_deck_initial, 1))
    mcts_deck_river = list(mcts_deck_initial)
    river_node = MonteCarloTreeSearchNode((player1_hand, [], community_cards, mcts_deck_river))
    if monteCarloTreeSearch(river_node) < 0.5:
        print("player1 hand (bot)")
        printCards(player1_hand)
        print("player2 hand")
        printCards(player2_hand)
        print("community cards")
        printCards(community_cards)
        return "folded in river"

    # see who wins
    print("showdown!")
    result = checkHands(player1_hand, player2_hand, community_cards)
    if result == "bot":
        print("player1 hand (bot)")
        printCards(player1_hand)
        print("player2 hand")
        printCards(player2_hand)
        print("community cards")
        printCards(community_cards)
        return "bot won"
    elif result == "player":
        print("player1 hand (bot)")
        printCards(player1_hand)
        print("player2 hand")
        printCards(player2_hand)
        print("community cards")
        printCards(community_cards)
        return "player won"
    else:
        print("player1 hand (bot)")
        printCards(player1_hand)
        print("player2 hand")
        printCards(player2_hand)
        print("community cards")
        printCards(community_cards)
        return "tie"

if __name__ == '__main__':
    result = playPoker()
    print(result)

