#!/user/bin/env python3 -tt
"""
Module documentation.
"""

# Imports
import sys
import os
import random
import argparse
import pdb
import numpy as np
import time
from termcolor import cprint

# Global variables

# Class declarations

class Table(object):
    """docstring for Table"""
    def __init__(self, args):
        self.args = args
        self.players = args.players
        self.num_decks = args.decks
        self.pause = args.pause

        self.count = 0
        self.round_end_count = 0
        self.round_start_count = 0
        self.round_count = 0

        # Values to be filled on table build
        self.dealer = None
        self.hands = None
        self.decks = None
        self.playing_cards = None

        self.basic_strategy_no_ace = {
        '2': [0,0,0,0,0,1,2,2,1,1],
        '3': [0,0,0,0,0,1,2,2,2,1],
        '4': [0,0,0,0,0,0,2,2,2,1],
        '5': [0,0,0,0,0,0,2,2,2,1],
        '6': [0,0,0,0,0,0,2,2,2,1],
        '7': [0,1,1,1,1,1,2,2,1,1],
        '8': [0,1,1,1,1,1,2,2,1,1],
        '9': [0,1,1,1,1,1,2,2,1,1],
        '10': [0,1,1,1,1,1,2,1,1,1],
        'Jack': [0,1,1,1,1,1,2,1,1,1],
        'Queen': [0,1,1,1,1,1,2,1,1,1],
        'King': [0,1,1,1,1,1,2,1,1,1],
        'Ace': [0,1,1,1,1,1,2,1,1,1] }
        
        self.basic_strategy_with_ace = {
        '2': [0,0,2,1,1,1,1,1],
        '3': [0,0,2,2,1,1,1,1],
        '4': [0,0,2,2,2,2,1,1],
        '5': [0,0,2,2,2,2,2,2],
        '6': [0,2,2,2,2,2,2,2],
        '7': [0,0,0,1,1,1,1,1],
        '8': [0,0,0,1,1,1,1,1],
        '9': [0,0,1,1,1,1,1,1],
        '10': [0,0,1,1,1,1,1,1],
        'Jack': [0,0,1,1,1,1,1,1],
        'Queen': [0,0,1,1,1,1,1,1],
        'King': [0,0,1,1,1,1,1,1],
        'Ace': [0,0,1,1,1,1,1,1] }

    
    def create_decks(self):
        self.cut = random.randint(25, 52)
        self.decks = []
        self.playing_cards = []
        for i in range(self.num_decks):
            self.decks.append(Deck())

        for deck in self.decks:
            deck.shuffle()
            deck_cards = deck.all_cards()
            self.playing_cards = self.playing_cards + deck_cards

        random.shuffle(self.playing_cards)

    def play_round(self):
        self.deal_cards()
        self.make_decisions()
        self.evaluate()
        self.display(end=True)

    def deal_cards(self):
        self.hands = []
        self.round_count = 0
        for i in range(self.players):
            self.hands.append(Hand())
        self.dealer = Hand()

        self.table_hands = self.hands + [self.dealer]

        for i in range(2):
            for index, hand in enumerate(self.table_hands):
                next_card = self.hit()
                hand.add_card(next_card)
            self.display()
        self.dealer_up = self.table_hands[-1].cards[1].rank

    def make_decisions(self):
        for index, hand in enumerate(self.table_hands):
            if index == len(self.table_hands) - 1:
                dealer = True
            else:
                dealer = False
            self.hit_stay_double_split(hand, dealer)
    
    def evaluate(self):
        dealer = self.table_hands[-1]
        for index, hand in enumerate(self.table_hands):
            if dealer.bust and not hand.bust:
                hand.result = 1
            elif hand.points < dealer.points or hand.bust:
                hand.result = 0
            elif hand.points > dealer.points and not hand.bust:
                hand.result = 1
            elif hand.points == dealer.points:
                hand.result = 2
    
    def display(self, end=False):
        for index, hand in enumerate(self.table_hands):
            if index < (len(self.table_hands) - 1):
                print(f'PLAYER {index} -- {hand.points}')
                if end:
                    if hand.result == 0:
                        cprint(self.ascii_version_of_card(*hand.cards), 'red')
                    elif hand.result == 1:
                        cprint(self.ascii_version_of_card(*hand.cards), 'green')
                    else:
                        cprint(self.ascii_version_of_card(*hand.cards), 'yellow')
                else:
                    print(self.ascii_version_of_card(*hand.cards))
            else:
                print('**************************')
                print(f'DEALER -- {hand.points}')
                if end:
                    if hand.points > 21:
                        cprint(self.ascii_version_of_card(*hand.cards), 'red')
                    else:
                        print(self.ascii_version_of_card(*hand.cards))
                else:
                    print(self.ascii_version_of_hidden_card(*hand.cards))
                print('**************************')
                print(f'\nTABLE COUNT = {self.count}\n\nROUND COUNT = {self.round_count}\n')
            time.sleep(self.pause)   
    
    def update_count(self):
        for index, hand in enumerate(self.table_hands):
            for card in hand.cards:
                if card.points == 10:
                    self.count -= 1
                    self.round_count -= 1
                
                elif card.points < 7:
                    self.count += 1
                    self.round_count += 1
                
    def hit_stay_double_split(self, hand, dealer):
        if dealer:
            while(hand.points < 17):
                new_card = self.hit()
                hand.add_card(new_card)
        else:
            while(hand.playing):
                plan = self.smart_bets(hand)
                if hand.points == 21:
                    hand.playing = False
                if plan > 0:
                    new_card = self.hit()
                    hand.add_card(new_card)
                else:
                    hand.playing = False
                self.show_hand(hand)

    def smart_bets(self, hand):
        if hand.aces > 0 and len(hand.cards) == 2:
            try:
                decision = self.basic_strategy_with_ace[self.dealer_up][self.bet_indexer(hand, ace=True)]
            except:
                # Breaks when player is dealt two aces
                pdb.set_trace()
        else:
            decision = self.basic_strategy_no_ace[self.dealer_up][self.bet_indexer(hand)]
        return decision

    def bet_indexer(self, hand, ace=False):
        if ace:
            if hand.points == 21:
                return 0
            else:
                # This will need to be changed with Splits are added
                return min(20 - hand.points, 7)
        else:
            score = hand.points - 17
            if score >= 0:
                return 0
            elif score < -8:
                return 9
            else:
                return score * -1

    def hit(self):
        card = self.playing_cards.pop()
        if card.points == 10:
            self.count -= 1
            self.round_count -= 1
        elif card.points < 7:
            self.count += 1
            self.round_count += 1
        return card

    def show_hand(self, hand):
        print(self.ascii_version_of_card(*hand.cards))

    def ascii_version_of_hidden_card(self, *cards):
        """
        Essentially the dealers method of print ascii cards. This method hides the first card, shows it flipped over
        :param cards: A list of card objects, the first will be hidden
        :return: A string, the nice ascii version of cards
        """
        # a flipper over card. # This is a list of lists instead of a list of string because appending to a list is better then adding a string
        lines = [['┌─────────┐'],
            ['│░░░░░░░░░│'],
            ['│░░░░░░░░░│'],
            ['│░░░░░░░░░│'],
            ['│░░░░░░░░░│'],
            ['│░░░░░░░░░│'],
            ['│░░░░░░░░░│'],
            ['│░░░░░░░░░│'],
            ['└─────────┘']]

        # store the non-flipped over card after the one that is flipped over
        cards_except_first = self.ascii_version_of_card(*cards[1:], return_string=False)
        for index, line in enumerate(cards_except_first):
            lines[index].append(line)

        # make each line into a single list
        for index, line in enumerate(lines):
            lines[index] = ''.join(line)

        # convert the list into a single string
        return '\n'.join(lines)

    def ascii_version_of_card(self, *cards, return_string=True):
        """
        Instead of a boring text version of the card we render an ASCII image of the card.
        :param cards: One or more card objects
        :param return_string: By default we return the string version of the card, but the dealer hide the 1st card and we
        keep it as a list so that the dealer can add a hidden card in front of the list
        """
        # we will use this to prints the appropriate icons for each card
        suits_name = ['Spades', 'Diamonds', 'Hearts', 'Clubs']
        suits_symbols = ['♠', '♦', '♥', '♣']

        # create an empty list of list, each sublist is a line
        lines = [[] for i in range(9)]

        for index, card in enumerate(cards):
            # "King" should be "K" and "10" should still be "10"
            if card.rank == '10':  # ten is the only one who's rank is 2 char long
                rank = card.rank
                space = ''  # if we write "10" on the card that line will be 1 char to long
            else:
                rank = card.rank[0]  # some have a rank of 'King' this changes that to a simple 'K' ("King" doesn't fit)
                space = ' '  # no "10", we use a blank space to will the void
            # get the cards suit in two steps
            suit = suits_name.index(card.suit)
            suit = suits_symbols[suit]

            # add the individual card on a line by line basis
            lines[0].append('┌─────────┐')
            lines[1].append('│{}{}       │'.format(rank, space))  # use two {} one for char, one for space or char
            lines[2].append('│         │')
            lines[3].append('│         │')
            lines[4].append('│    {}    │'.format(suit))
            lines[5].append('│         │')
            lines[6].append('│         │')
            lines[7].append('│       {}{}│'.format(space, rank))
            lines[8].append('└─────────┘')

        result = []
        for index, line in enumerate(lines):
            result.append(''.join(lines[index]))

        # hidden cards do not use string
        if return_string:
            return '\n'.join(result)
        else:
            return result

class Deck(object):

    def __init__(self):
        self.cards = []
        suits_name = ['Spades', 'Diamonds', 'Hearts', 'Clubs']
        card_values = {
            'Ace': 11,  # value of the ace is high until it needs to be low
            '2': 2,
            '3': 3,
            '4': 4,
            '5': 5,
            '6': 6,
            '7': 7,
            '8': 8,
            '9': 9,
            '10': 10,
            'Jack': 10,
            'Queen': 10,
            'King': 10
        }
        for suit in suits_name:
            for rank in card_values:
                new_card = Card(suit, rank)
                self.cards.append(new_card)

    def shuffle(self):
        random.shuffle(self.cards)

    def all_cards(self):
        return self.cards

class Card(object):

    card_values = {
        'Ace': 11,  # value of the ace is high until it needs to be low
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5,
        '6': 6,
        '7': 7,
        '8': 8,
        '9': 9,
        '10': 10,
        'Jack': 10,
        'Queen': 10,
        'King': 10
    }

    def __init__(self, suit, rank):
        """
        :param suit: The face of the card, e.g. Spade or Diamond
        :param rank: The value of the card, e.g 3 or King
        """
        self.suit = suit.capitalize()
        self.rank = rank
        self.points = self.card_values[rank]
        self.ace = (rank == 'Ace')

    def points(self):
        return self.points

    def is_ace(self):
        return self.ace

class Hand(object):
    """docstring for Hand"""
    def __init__(self):
        self.points = 0
        self.count = 0
        self.cards = []
        self.aces = 0
        self.playing = True
        self.limit = 21
        self.bust = False

    def add_card(self, new_card):
        self.cards.append(new_card)
        if new_card.is_ace():
            self.aces += 1
        self.update()

    def update(self):
        self.count = 0
        self.points = 0
        for card in self.cards:
            self.points += card.points
            if card.points > 9:
                self.count -= 1
            elif card.points < 7:
                self.count += 1
        if self.points > self.limit:
            for i in range(self.aces):
                if self.points > self.limit:
                    self.points -= 10

        if self.points > self.limit:
            self.playing = False
            self.bust = True

    def bust(self):
        self.playing = False
        self.bust = True


def main(args):
    table = Table(args)
    table.create_decks()
    while(len(table.playing_cards) > table.cut):
        table.play_round()
        pdb.set_trace()


# Main body
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Display a blackjack game, keeping count')
    parser.add_argument('--players', default=5, type=int, help='number of players at the table')
    parser.add_argument('--decks', default=6, type=int, help='number of decks on the table')
    parser.add_argument('--pause', default=0, type=int, help='pause between dealt cards')
    args = parser.parse_args()
    main(args)