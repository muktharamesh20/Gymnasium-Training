from collections import defaultdict
from enum import Enum
from enum import IntEnum
from collections import defaultdict

class Suite(IntEnum):
    def __eq__(self, other):
        return int(self) == other

    def __hash__(self):
        return hash(int(self))
    SPADE=0
    HEART=1
    DIAMOND=2
    CLUB=3
class Rank(IntEnum):
    TWO = 0
    THREE = 1
    FOUR = 2
    FIVE = 3
    SIX = 4
    SEVEN = 5
    EIGHT = 6
    NINE = 7
    TEN = 8
    JACK = 9
    QUEEN = 10
    KING = 11
    ACE = 12

class GameCard():
    def str_version(self):
        suite = self.convert_value_to_string("Suite")
        rank = self.convert_value_to_string("Rank")

        rank_dict = {"2":"2", "3":"3", "4":"4", "5":"5", "6":"6", "7":"7", "8":"8", "9":"9", "10":"10", "JACK":"J", "QUEEN":"Q", "KING":"K", "ACE": "A"}
        suite_dict = {"SPADE": "♠️","HEART": "♥️", "DIAMOND": "♦️","CLUB":"♣️"}
        return rank_dict[rank] + suite_dict[suite]
    def convert(s):
        rank_map = {"A": 12, "K": 11, "Q": 10, "J": 9, "T": 10}  # Map for face cards
        value1 = 0
        value2 = 0
        if s[0] in rank_map:
            value1 = rank_map[s[0]]
            if s[1] == "s":
                value2 = 0
            elif s[1] == "h":
                value2 = 1
            elif s[1] == "d":
                value2 = 2
            elif s[1] == "c":
                value2 = 3
        elif s[0] == str(1) and s[1] == str(0):
            value1 = 8
            if s[2] == "s":
                value2 = 0
            elif s[2] == "h":
                value2 = 1
            elif s[2] == "d":
                value2 = 2
            elif s[2] == "c":
                value2 = 3
        else:
            value1 = int(s[0]) - 2  # For numeric ranks 2-9
        # Handle suite parsing
            if s[1] == "s":
                value2 = 0  # Spades
            elif s[1] == "h":
                value2 = 1  # Hearts
            elif s[1] == "d":
                value2 = 2  # Diamonds
            elif s[1] == "c":
                value2 = 3  # Clubs
        return (value1, value2)
    def __init__(self, rank_value, suit_value):
        self._rank = Rank(rank_value)
        self._suite = Suite(suit_value)
        self.hashable_value = str(rank_value) + str(suit_value)
    def __iter__(self):
        return iter(self.value)
    def __str__(self):
        return f"{self.__class__.__name__}({self.rank.name}, {self.suite.name})"
    def __repr__(self):
        return self.__str__()
    def __lt__(self, other):
        return self.rank < other.rank
    
    @property
    def rank(self):
        return self._rank

    @rank.setter
    def rank(self, new_value):
        raise AttributeError("Cannot modify the rank attribute")
    @property
    def suite(self):
        return self._suite

    @suite.setter
    def suite(self, new_value):
        raise AttributeError("Cannot modify the suite attribute")
    
    def flush(cards):
        suit_dict = defaultdict(list)
        for card in cards:
            suit_dict[card.suite].append(card)
        return max([len(suit_dict[val]) for val in suit_dict]) >= 5
    
    def straight(cards):
        num_dict = defaultdict(int)
        for card in cards:
            num_dict[int(card.rank)] += 1
        straights = 0
        for card in cards:
            if all([num_dict[card.rank+i] >= 1 for i in range(5)]):
                straights += 1
        if all([num_dict[i] >= 1 for i in {12, 0, 1, 2, 3}]):
            straights += 1
        return straights >= 1
    
    def four_of_a_kind(cards):
        num_dict = defaultdict(int)
        for card in cards:
            num_dict[card.rank] += 1
        return max(num_dict.values()) >= 4
    
    def full_house(cards):
        num_dict = defaultdict(int)
        for card in cards:
            num_dict[card.rank] += 1
        val1 = max(num_dict.values())
        val2 = max([num_dict[val] for val in num_dict if val != val1])
        return val1 >= 3 and val2 >= 2
    
    def three_of_kind(cards):
        num_dict = defaultdict(int)
        for card in cards:
            num_dict[card.rank] += 1
        return max(num_dict.values()) >= 3
    
    def two_pair(cards):
        num_dict = defaultdict(int)
        for card in cards:
            num_dict[card.rank] += 1
        max_ind = 0
        max_val = 0
        for ind in num_dict:
            if num_dict[ind] > max_val:
                max_ind = ind
                max_val = num_dict[ind]
        val2 = max([num_dict[val] for val in num_dict if val != max_ind])
        return max_val >= 2 and val2 >= 2 
    
    def pair(cards):
        num_dict = defaultdict(int)
        for card in cards:
            num_dict[card.rank] += 1
        val1 = max(num_dict.values())
        return val1 >= 2

    #to let us use sets and stuff
    def __hash__(self):
        return hash(self.hashable_value)
    
    def __getitem__(self, name):
        if name == "Suite" or name == 1:
            return self.suite
        if name == "Rank" or name == 0:
            return self.rank
        raise KeyError
    
    def all_Cards():
        all_cards = set()
        for val1 in {"2","3","4","5","6","7","8","9","10","J","Q","K","A"}:
            for val2 in {"s", "d", "c", "h"}:
                s = val1 + val2
                all_cards.add(GameCard(GameCard.convert(s)[0], GameCard.convert(s)[1]))
        return all_cards

    #to let us use sets and stuff
    def __hash__(self):
        return hash(self.hashable_value)
    
    def __getitem__(self, name):
        if name == "Suite" or name == 1:
            return self.suite
        if name == "Rank" or name == 0:
            return self.rank
        raise KeyError
    

    #Methods to make the hands class easier to code :O
    def convert_value_to_string(self,rank_or_suite):
        rank_dict = {0:"2", 1:"3", 2:"4", 3:"5", 4:"6", 5:"7", 6:"8", 7:"9", 8:"10", 9:"JACK", 10:"QUEEN", 11:"KING", 12:"ACE"}
        suite_dict = {0:"SPADE",1:"HEART",2:"DIAMOND",3:"CLUB"}
        if rank_or_suite.lower() == "rank":
            return rank_dict[self.rank]
        elif rank_or_suite.lower() == "suite":
            return suite_dict[self.suite]
        else:
            raise KeyError("Please input rank or suite")
        
    def value_to_string(self,rank_or_suite, value):
        rank_dict = {0:"2", 1:"3", 2:"4", 3:"5", 4:"6", 5:"7", 6:"8", 7:"9", 8:"10", 9:"JACK", 10:"QUEEN", 11:"KING", 12:"ACE"}
        suite_dict = {0:"SPADE",1:"HEART",2:"DIAMOND",3:"CLUB"}
        if rank_or_suite.lower() == "rank":
            return rank_dict[value]
        elif rank_or_suite.lower() == "suite":
            return suite_dict[value]
        else:
            raise KeyError("Please input rank or suite")
        
    def string_to_value(self, rank_or_suite, value):
        rank_dict = {"2":0, "3":1, "4":2, "5":3, "6":4, "7":5, "8":6, "9":7, "10":8, "JACK":9, "QUEEN":10, "KING":11, "ACE":12}
        suite_dict = {"SPADE":0,"HEART":1,"DIAMOND":2,"CLUB":3}
        if rank_or_suite.lower() == "rank":
            return rank_dict[value]
        elif rank_or_suite.lower() == "suite":
            return suite_dict[value]
        else:
            raise KeyError("Please input rank or suite")
    
    SPADE_2 = (Rank.TWO, Suite.SPADE)
    SPADE_3 = (Rank.THREE, Suite.SPADE)
    SPADE_4 = (Rank.FOUR, Suite.SPADE)
    SPADE_5 = (Rank.FIVE, Suite.SPADE)
    SPADE_6 = (Rank.SIX, Suite.SPADE)
    SPADE_7 = (Rank.SEVEN, Suite.SPADE)
    SPADE_8 = (Rank.EIGHT, Suite.SPADE)
    SPADE_9 = (Rank.NINE, Suite.SPADE)
    SPADE_10 = (Rank.TEN, Suite.SPADE)
    SPADE_J = (Rank.JACK, Suite.SPADE)
    SPADE_Q = (Rank.QUEEN, Suite.SPADE)
    SPADE_K = (Rank.KING, Suite.SPADE)
    SPADE_A = (Rank.ACE, Suite.SPADE)

    HEART_2 = (Rank.TWO, Suite.HEART)
    HEART_3 = (Rank.THREE, Suite.HEART)
    HEART_4 = (Rank.FOUR, Suite.HEART)
    HEART_5 = (Rank.FIVE, Suite.HEART)
    HEART_6 = (Rank.SIX, Suite.HEART)
    HEART_7 = (Rank.SEVEN, Suite.HEART)
    HEART_8 = (Rank.EIGHT, Suite.HEART)
    HEART_9 = (Rank.NINE, Suite.HEART)
    HEART_10 = (Rank.TEN, Suite.HEART)
    HEART_J = (Rank.JACK, Suite.HEART)
    HEART_Q = (Rank.QUEEN, Suite.HEART)
    HEART_K = (Rank.KING, Suite.HEART)
    HEART_A = (Rank.ACE, Suite.HEART)

    DIAMOND_2 = (Rank.TWO, Suite.DIAMOND)
    DIAMOND_3 = (Rank.THREE, Suite.DIAMOND)
    DIAMOND_4 = (Rank.FOUR, Suite.DIAMOND)
    DIAMOND_5 = (Rank.FIVE, Suite.DIAMOND)
    DIAMOND_6 = (Rank.SIX, Suite.DIAMOND)
    DIAMOND_7 = (Rank.SEVEN, Suite.DIAMOND)
    DIAMOND_8 = (Rank.EIGHT, Suite.DIAMOND)
    DIAMOND_9 = (Rank.NINE, Suite.DIAMOND)
    DIAMOND_10 = (Rank.TEN, Suite.DIAMOND)
    DIAMOND_J = (Rank.JACK, Suite.DIAMOND)
    DIAMOND_Q = (Rank.QUEEN, Suite.DIAMOND)
    DIAMOND_K = (Rank.KING, Suite.DIAMOND)
    DIAMOND_A = (Rank.ACE, Suite.DIAMOND)

    CLUB_2 = (Rank.TWO, Suite.CLUB)
    CLUB_3 = (Rank.THREE, Suite.CLUB)
    CLUB_4 = (Rank.FOUR, Suite.CLUB)
    CLUB_5 = (Rank.FIVE, Suite.CLUB)
    CLUB_6 = (Rank.SIX, Suite.CLUB)
    CLUB_7 = (Rank.SEVEN, Suite.CLUB)
    CLUB_8 = (Rank.EIGHT, Suite.CLUB)
    CLUB_9 = (Rank.NINE, Suite.CLUB)
    CLUB_10 = (Rank.TEN, Suite.CLUB)
    CLUB_J = (Rank.JACK, Suite.CLUB)
    CLUB_Q = (Rank.QUEEN, Suite.CLUB)
    CLUB_K = (Rank.KING, Suite.CLUB)
    CLUB_A = (Rank.ACE, Suite.CLUB)

    def bucket(cards, current_suite=Suite.SPADE, found_suites = None):
        if(found_suites == None):
            found_suites = [None, None, None, None]
        cards = cards.copy()
        for i in range(len(cards)):
            card=cards[i]
            if found_suites[card.suite] == None:
                found_suites[card.suite]=current_suite
                current_suite+=1
            cards[i]=card(card.rank, found_suites[card.suite])
        return cards
    
    def bucket_ret_suite(cards, current_suite=Suite.SPADE, found_suites = None):
        if(found_suites == None):
            found_suites = [None, None, None, None]
        cards = cards.copy()
        for i in range(len(cards)):
            card=cards[i]
            if found_suites[card.suite] == None:
                found_suites[card.suite]=current_suite
                current_suite+=1
            cards[i]=card(card.rank, found_suites[card.suite])
        return (cards, current_suite)